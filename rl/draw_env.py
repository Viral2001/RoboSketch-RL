"""
RoboSketch-RL  |  Phase C - the RL drawing environment
-------------------------------------------------
A Gymnasium environment where an agent learns to reproduce a target shape by
moving a pen across paper. This is the heart of the project.

THE FOUR RL CONCEPTS (see docs/RESEARCH_LOG.md), made concrete here:

  State / observation : a small multi-channel image -
        channel 0 = the TARGET shape to reproduce
        channel 1 = what has been DRAWN so far
        channel 2 = a marker at the current PEN position
        channel 3 = elapsed fraction of the episode (only if time_in_obs=True;
                    see O1 in docs/PROJECT_PROPOSAL_v2.md 3.1)
  Action              : [dx, dy, pen_down] - nudge the pen, and whether it inks.
        The agent thinks in PEN space (portable across arms); if use_arm=True an
        IK-driven KUKA actually carries the pen there (realistic, includes the
        motor tracking lag measured in B5). use_arm=False moves the pen point
        directly (fast, for quick RL iteration) - the drawing/reward logic is
        identical either way.
  Reward              : dense shaping toward higher IoU -
        + for newly covering target pixels, - for stray ink off the target,
        - a small per-step cost to encourage efficiency.
        reward_mode="truth" uses the real canvas (the H2 BASELINE). A vision
        reward (camera + OpenCV) is the H2 experiment, added later.
  Episode             : ends at max_steps, or when coverage is essentially done.
"""
import os
import sys

import cv2
import gymnasium as gym
import numpy as np
from gymnasium import spaces

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "sim"))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import targets as T
import metrics as M
import disturb as DIST

# paper geometry (world metres) - matches the simulator (sim/03_draw_line.py)
PAPER_CX, PAPER_CY, PAPER_HALF = 0.55, 0.0, 0.10


class DrawEnv(gym.Env):
    metadata = {"render_modes": ["rgb_array"]}

    def __init__(self, shape="line", obs_res=64, canvas_res=128, max_steps=120,
                 step_size_m=0.012, pen_radius_px=None, use_arm=False,
                 reward_mode="truth", cam_px=150, iou_weight=10.0, time_penalty=0.0,
                 prox_weight=0.4, smooth_penalty=0.02, done_iou=0.60,
                 pen_always_down=True, start_on_target=True,
                 time_in_obs=False, allow_stop=False, plateau_patience=None,
                 plateau_eps=1e-4, cam_split=None, obs_source="true",
                 disturbance=None, disturb_scale=1.0, pen_marker_frame="world",
                 target_split=None, obs_view="global", ego_win=64, coord_channels=False,
                 render_mode=None, seed=None):
        super().__init__()
        # Proposal O2. "global" (default) = the whole sheet at obs_res, as in every result
        # before 2026-11-01. "ego" = an egocentric window of `ego_win` canvas px centred on the
        # pen (zero-padded off the sheet): channel 0 target, 1 drawn, 2 the sheet-extent mask
        # (255 on paper) instead of the pen marker - the pen is always at the window centre.
        # Privileged observation only (the camera / FK / disturbance paths are not ported).
        assert obs_view in ("global", "ego"), obs_view
        if obs_view == "ego":
            assert obs_source == "true" and disturbance is None \
                and pen_marker_frame == "world" and pen_always_down, \
                "obs_view='ego' is only implemented for the undisturbed setting (privileged canvas, or a cam_split camera)"
        self.obs_view = obs_view
        self.ego_win = ego_win
        # Proposal 5.4. None (default) = the one fixed target per shape name, as in
        # every result before 2026-10-30. "train" / "heldout" = at every reset, draw
        # a new size and rotation of that shape from targets.PARAM_RANGES, using the
        # env's own RNG (so reset(seed=k) gives a reproducible, distinct target).
        assert target_split in (None, "train", "heldout", "heldout_scale",
                                "heldout_rot"), target_split
        self.target_split = target_split
        assert reward_mode in ("truth", "vision", "vision_real"), reward_mode
        # validated, not silently coerced: `sample_params` falls through to
        # HELDOUT for anything that is not exactly "fixed" or "train", so a typo
        # like "Train" would train an arm on the held-out distribution and
        # produce a plausible-looking, wrong result.
        assert cam_split in (None, "fixed", "train", "heldout"), cam_split
        # H4 (proposal 4.3). obs_source decides WHOSE VERSION of the drawing the
        # agent acts on - the whole experiment turns on this one choice:
        #   "true"   privileged; the real ink. No robot has this. A ceiling only.
        #   "fk"     D01's condition: what the agent's own kinematics say it
        #            drew - commanded positions, ink assumed to have landed,
        #            no knowledge of any disturbance.
        #   "camera" ours: a photograph of the paper as it actually is.
        assert obs_source in ("true", "fk", "camera"), obs_source
        assert disturbance in (None,) + DIST.KINDS, disturbance
        if obs_source == "camera":
            assert cam_split, "obs_source='camera' needs a cam_split"
        self.obs_source = obs_source
        self.disturbance = disturbance
        self.disturb_scale = disturb_scale
        # "truth"  = reward from the exact canvas (ground-truth baseline, H2 control)
        # "vision" = reward from a CAMERA-PERCEIVED version of the canvas (the
        #            project's novelty; H2 experiment). Perception is modelled by
        #            the camera's resolution loss + thresholding, characterised
        #            against the real B6 camera pipeline (perceived-vs-truth
        #            IoU ~0.88). The true IoU is still reported for evaluation.
        # H4 v3 (2026-10-29). Where the observation's pen marker is drawn:
        #   "world"  from the pen's WORLD position, with no sheet offset. This is
        #            what every result recorded before v3 used, and it is the
        #            default so none of them move.
        #   "sheet"  from where the pen actually LANDS on the sheet (world
        #            position plus the paper-shift offset), i.e. the pen tip seen
        #            against the paper - what a camera that sees both gives and
        #            forward kinematics cannot. Ignored when obs_source="fk": FK
        #            has no way to know the sheet moved.
        # Found because after a paper shift the "world" marker and the ink
        # disagree by 5-10 px and an agent has to INFER the offset; an oracle
        # that is handed it loses 0.013 IoU where trained arms lose 0.13
        # (RESEARCH_LOG 2026-10-29).
        assert pen_marker_frame in ("world", "sheet", "estimated"), pen_marker_frame
        self.pen_marker_frame = pen_marker_frame
        self.reward_mode = reward_mode
        self.cam_px = cam_px
        self.shape_name = shape
        self.obs_res = obs_res
        self.canvas_res = canvas_res
        self.max_steps = max_steps
        self.step_size = step_size_m
        self.use_arm = use_arm
        self.iou_weight = iou_weight
        self.time_penalty = time_penalty
        self.prox_weight = prox_weight
        self.smooth_penalty = smooth_penalty
        self.pen_always_down = pen_always_down
        self.start_on_target = start_on_target
        # O1 (proposal 3.1): the episode is hard-truncated at max_steps, but the
        # agent cannot see how many steps remain - so two identical canvases
        # with 5 vs 100 steps left look the same and demand different actions.
        # The task is therefore PARTIALLY OBSERVABLE. Adding a constant-valued
        # 4th channel = 255 * (steps / max_steps) closes that. D02 puts the step
        # number in the state for exactly this reason. Default False so every
        # result recorded before this change stays reproducible; turn it on with
        # DrawEnv(time_in_obs=True) / `train.py --time-obs` and A/B it.
        self.time_in_obs = time_in_obs
        # --- the two overrun switches (measured 2026-08-23) ----------------
        # allow_stop      : give the agent a 4th action, "I am finished". The
        #                   overshoot happens because it CANNOT stop - having
        #                   traced the shape it must keep moving with the pen
        #                   down, and drifts past the outline before settling.
        # plateau_patience: end the episode after this many steps with no
        #                   improvement in the reward IoU. Blunter than a stop
        #                   action (the environment decides, not the policy) but
        #                   it needs no change to the action space, so an agent
        #                   trained without it can still be evaluated with it.
        # Both default to off, so nothing recorded before today moves.
        # cam_split (proposal 4.1): None keeps the original fixed `_perceive`,
        # so every result recorded before 2026-09-12 is untouched. "fixed",
        # "train" or "heldout" route the vision reward through perception.Camera
        # instead, with parameters RESAMPLED EACH EPISODE from that distribution.
        # Per-episode and not per-step: the reward is iou(t) - iou(t-1), so a
        # camera that changed between two steps would put camera noise into the
        # difference and the agent would be scored for things it did not do.
        self.cam_split = cam_split
        self._cam = None
        self.allow_stop = allow_stop
        self.plateau_patience = plateau_patience
        self.plateau_eps = plateau_eps
        self.done_iou = done_iou
        self.render_mode = render_mode
        # pen ink width, chosen to roughly match the target stroke width so a
        # centred trace can actually fill the target (thin pen on a wide target
        # can never reach high IoU, and vice-versa).
        self.pen_radius_px = pen_radius_px or max(2, int(0.0035 / (2 * PAPER_HALF) * canvas_res))

        # action: dx, dy in [-1,1] (scaled by step_size), pen_down in [0,1],
        # and - only when allow_stop - a 4th "finished" head in [0,1].
        lo, hi = [-1.0, -1.0, 0.0], [1.0, 1.0, 1.0]
        if allow_stop:
            lo.append(0.0)
            hi.append(1.0)
        self.action_space = spaces.Box(low=np.array(lo, np.float32),
                                       high=np.array(hi, np.float32))
        # observation: uint8 image (target, drawn, pen marker [, time left])
        # O3 CoordConv: two extra planes (column ramp, row ramp, 0..255) so a plain CNN can read
        # absolute position everywhere. Global view only; default off.
        assert not (coord_channels and obs_view == "ego"), "coord_channels is for the global view"
        self.coord_channels = coord_channels
        self.obs_channels = (4 if time_in_obs else 3) + (2 if coord_channels else 0)
        self.observation_space = spaces.Box(
            low=0, high=255, shape=(obs_res, obs_res, self.obs_channels),
            dtype=np.uint8)

        self._rng = np.random.default_rng(seed)
        self.target_params = (1.0, 0.0)             # (scale, rotation deg) of the target
        # Stage 6 step 2b (additive, default OFF): a shape name that is a digit
        # '0'..'9' selects the multi-stroke glyph target from rl/glyphs.py. Every
        # existing shape name takes the unchanged T.make path.
        self._is_glyph = shape in "0123456789" and len(shape) == 1
        if self._is_glyph:
            assert not target_split, "glyph targets do not support target_split"
            import glyphs as _G
            self._set_target(_G.make_glyph(shape, res=512))
        else:
            self._set_target(T.make(shape, res=512))

        self._arm = None
        if use_arm:
            self._setup_arm()

        # reward_mode="vision_real": an ACTUAL PyBullet camera render + OpenCV
        # per step (the real B6 pipeline), instead of the fast _perceive proxy.
        # Validated to give the same signal as the proxy (mean IoU gap 0.010).
        self._realcam = None
        if reward_mode == "vision_real":
            from camera import RealCamera
            DrawEnv._cam_n = getattr(DrawEnv, "_cam_n", 0) + 1
            self._realcam = RealCamera(canvas_res=canvas_res, paper_cx=PAPER_CX,
                                       paper_cy=PAPER_CY, paper_half=PAPER_HALF,
                                       instance=DrawEnv._cam_n)

        # must exist before the first _world_to_px call, which happens inside
        # reset() while choosing the start point - earlier than the H4 block
        self._paper_off = np.zeros(2, np.float32)
        self.canvas = None
        self.pen_xy = None
        self.pen_down = False
        self.steps = 0
        self._prev_cov = 0
        self._prev_stray = 0

    # ---------------------------------------------------------------- arm --
    def _setup_arm(self):
        import pybullet as p
        import pybullet_data
        from pybullet_utils import bullet_client
        self._bc = bullet_client.BulletClient(connection_mode=p.DIRECT)
        self._bc.setAdditionalSearchPath(pybullet_data.getDataPath())
        self._bc.setGravity(0, 0, -9.81)
        self._bc.loadURDF("plane.urdf")
        self._arm = self._bc.loadURDF("kuka_iiwa/model.urdf", useFixedBase=True)
        self._nj = self._bc.getNumJoints(self._arm)
        self._tip = self._nj - 1
        self._home = [0.0, 0.5, 0.0, -1.5, 0.0, 1.2, 0.0]
        self._pen_len = 0.10
        self._wrist_down = 0.003 + self._pen_len
        self._wrist_up = self._wrist_down + 0.05
        self._down = self._bc.getQuaternionFromEuler([np.pi, 0, 0])
        for j in range(self._nj):
            self._bc.resetJointState(self._arm, j, self._home[j])

    def _move_arm(self, x, y, pen_down):
        bc = self._bc
        wrist_z = self._wrist_down if pen_down else self._wrist_up
        a = bc.calculateInverseKinematics(self._arm, self._tip, [x, y, wrist_z],
                                          targetOrientation=self._down,
                                          maxNumIterations=120, residualThreshold=1e-4)
        for j in range(self._nj):
            bc.setJointMotorControl2(self._arm, j, bc.POSITION_CONTROL,
                                     targetPosition=a[j], force=800, maxVelocity=10)
        for _ in range(6):
            bc.stepSimulation()
        wx, wy, _ = bc.getLinkState(self._arm, self._tip)[4]
        return wx, wy

    # ------------------------------------------------------ coord mapping --
    def _world_to_px(self, x, y, ignore_paper_shift=False):
        """Where a world point lands on the SHEET.

        `_paper_off` is how far the sheet has slid under the pen (H4's
        paper_shift). Ink already on the paper moved with it, so the mapping
        from a fixed world position to a sheet pixel changes by that offset.
        Forward kinematics knows nothing about it, so the belief canvas is
        rendered with `ignore_paper_shift=True`.
        """
        r = self.canvas_res
        col = (x - (PAPER_CX - PAPER_HALF)) / (2 * PAPER_HALF) * (r - 1)
        row = ((PAPER_CY + PAPER_HALF) - y) / (2 * PAPER_HALF) * (r - 1)
        if not ignore_paper_shift:
            col += float(self._paper_off[0])
            row += float(self._paper_off[1])
        return (int(np.clip(round(col), 0, r - 1)),
                int(np.clip(round(row), 0, r - 1)))

    def _px_to_world(self, col, row):
        r = self.canvas_res
        x = (PAPER_CX - PAPER_HALF) + col / (r - 1) * 2 * PAPER_HALF
        y = (PAPER_CY + PAPER_HALF) - row / (r - 1) * 2 * PAPER_HALF
        return float(x), float(y)

    def _on_paper(self, x, y):
        return (abs(x - PAPER_CX) <= PAPER_HALF) and (abs(y - PAPER_CY) <= PAPER_HALF)

    def _set_target(self, mask512):
        """Install a 512-px target mask at canvas resolution, plus the quantities
        derived from it."""
        res = self.canvas_res
        self.target = cv2.resize(mask512, (res, res), interpolation=cv2.INTER_AREA)
        self.target = (self.target > 127).astype(np.uint8) * 255
        self._target_area = max(1, int((self.target > 127).sum()))
        # distance (px) from every pixel to the nearest TARGET ink pixel; used
        # for dense proximity shaping so the pen is pulled toward the target
        # even before it starts covering it (fixes the "learn to draw nothing"
        # local optimum from a sparse coverage-only reward).
        self._target_dt = cv2.distanceTransform(
            255 - self.target, cv2.DIST_L2, 3).astype(np.float32) / res

    # --------------------------------------------------------------- gym --
    def reset(self, *, seed=None, options=None):
        if seed is not None:
            self._rng = np.random.default_rng(seed)
        if self.target_split:
            self.target_params = T.sample_params(self._rng, self.target_split)
            self._set_target(T.make_param(self.shape_name, *self.target_params, res=512))
        self.canvas = np.zeros((self.canvas_res, self.canvas_res), np.uint8)
        self._paper_off = np.zeros(2, np.float32)   # the sheet has not moved yet
        # Start the pen ON a random point of the target shape, not at the paper
        # centre. Starting at the centre with pen-always-down left a stray "tail"
        # from centre to shape in every drawing (the biggest IoU loss); starting
        # on the shape removes it and mimics placing the pen where a stroke begins.
        if self.start_on_target:
            # DETERMINISTIC start: the target pixel nearest the paper centre.
            # (A *random* on-target start was tried and hurt — it adds episode
            # variance the policy must absorb, dropping the line from 0.51 to
            # 0.22. Deterministic keeps the line's start ~centre, which is
            # already on the line, and still removes the centre-to-shape tail on
            # closed shapes because the start sits on the outline.)
            ys, xs = np.nonzero(self.target > 127)
            cc, cr = self._world_to_px(PAPER_CX, PAPER_CY)
            i = int(np.argmin((xs - cc) ** 2 + (ys - cr) ** 2))
            self.pen_xy = np.array(self._px_to_world(xs[i], ys[i]), np.float32)
        else:
            self.pen_xy = np.array([PAPER_CX, PAPER_CY], np.float32)
        self.pen_down = False
        self.steps = 0
        self._prev_iou = 0.0
        self._prev_phi = self._potential()
        self._prev_action = np.zeros(self.action_space.shape[0], np.float32)
        self._path_len_px = 0.0
        if self.cam_split:
            import perception as PC
            self._cam = PC.Camera(self.canvas_res,
                                  PC.sample_params(self._rng, self.cam_split),
                                  self._rng)
        self._seen_at, self._seen_img = -1, None
        # H4 episode state. `_belief` is the canvas the agent's kinematics think
        # it has drawn: commanded positions, ink assumed to land, disturbances
        # unknown. `_paper_off` is how far the sheet has slid under the pen.
        self._dist = DIST.make(self.disturbance, self._rng, self.max_steps,
                               self.canvas_res, self.disturb_scale)
        self._belief = np.zeros((self.canvas_res, self.canvas_res), np.uint8)
        self._belief_xy = np.array(self.pen_xy, np.float32)
        self._peak_iou = 0.0
        self._best_reward_iou = -1.0
        self._stale = 0
        if self.use_arm:
            for j in range(self._nj):
                self._bc.resetJointState(self._arm, j, self._home[j])
        return self._obs(), {}

    def _perceive(self, canvas):
        """Model what the camera + OpenCV would recover from the drawing.

        The real B6 pipeline (render -> capture -> threshold) loses resolution
        and slightly thickens strokes (perceived-vs-truth IoU ~0.88). We
        reproduce that cheaply for fast training: capture at the camera's
        effective pixel count (resolution loss), binarise (the threshold step),
        then map back to canvas resolution. This is the H2 'vision' signal - the
        agent is rewarded for what is SEEN, not the exact ink.
        """
        r = self.canvas_res
        cam = max(48, int(self.cam_px))
        small = cv2.resize(canvas, (cam, cam), interpolation=cv2.INTER_AREA)
        small = (small > 60).astype(np.uint8) * 255          # camera threshold
        back = cv2.resize(small, (r, r), interpolation=cv2.INTER_LINEAR)
        return (back > 50).astype(np.uint8) * 255

    def _potential(self):
        """Potential Phi = -(distance of pen to nearest target ink). Higher is
        better (pen on the target -> 0). Potential-based shaping with this term
        adds dense guidance without changing the optimal policy."""
        col, row = self._world_to_px(*self.pen_xy)
        return -float(self._target_dt[row, col])

    def step(self, action):
        action = np.asarray(action, np.float32)
        dx, dy = float(action[0]) * self.step_size, float(action[1]) * self.step_size
        # pen_always_down = the first, simplest task rung (just trace the shape);
        # multi-stroke shapes (letters) will use the pen-up/down decision later.
        pen_down = True if self.pen_always_down else bool(action[2] > 0.5)

        # proposed new pen position, clamped to the paper
        nx = float(np.clip(self.pen_xy[0] + dx, PAPER_CX - PAPER_HALF, PAPER_CX + PAPER_HALF))
        ny = float(np.clip(self.pen_xy[1] + dy, PAPER_CY - PAPER_HALF, PAPER_CY + PAPER_HALF))

        if self.use_arm:
            ax, ay = self._move_arm(nx, ny, pen_down)   # real pen may lag target
        else:
            ax, ay = nx, ny

        # --- H4 disturbances, applied to REALITY only ---------------------
        # The commanded motion (nx, ny) is what the agent asked for and what its
        # kinematics will believe happened. Reality may differ, and nothing tells
        # the agent so.
        d = self._dist
        px_per_m = (self.canvas_res - 1) / (2 * PAPER_HALF)
        if d["kind"] == "slip" and self.steps == d["at"]:
            # the pen is knocked sideways; the command stream is unchanged
            ax += d["dcol"] / px_per_m
            ay -= d["drow"] / px_per_m
        elif d["kind"] == "paper_shift" and self.steps == d["at"]:
            # the sheet slides under the pen: ink already on the paper travels
            # with it, and from now on the pen lands somewhere else on the sheet
            self._paper_off += np.array([d["dcol"], d["drow"]], np.float32)
        inking = pen_down and self.pen_down
        if d["kind"] == "ink_failure" and d["at"] <= self.steps < d["until"]:
            inking = False          # the paper stays blank; the belief will not

        # ink a connected segment from the previous pen point to the new one
        if inking:
            c0 = self._world_to_px(*self.pen_xy)
            c1 = self._world_to_px(ax, ay)
            cv2.line(self.canvas, c0, c1, 255, max(2, 2 * self.pen_radius_px),
                     lineType=cv2.LINE_AA)
        # The belief canvas: what forward kinematics says was drawn. It follows
        # the COMMANDED position, assumes the ink landed, and never sees a
        # disturbance - which is exactly D01's epistemic position.
        if self.obs_source == "fk" or self.pen_marker_frame == "estimated":
            if pen_down and self.pen_down:
                b0 = self._world_to_px(*self._belief_xy, ignore_paper_shift=True)
                b1 = self._world_to_px(nx, ny, ignore_paper_shift=True)
                cv2.line(self._belief, b0, b1, 255, max(2, 2 * self.pen_radius_px),
                         lineType=cv2.LINE_AA)
            self._belief_xy = np.array([nx, ny], np.float32)
        # how far the pen actually travelled this step, in canvas pixels.
        # Accumulated over the episode this gives path_ratio (metrics.py):
        # travel / target-outline-length, which exposes the zig-zag and the
        # off-outline spurs that IoU only partly penalises.
        travel_m = float(np.hypot(ax - self.pen_xy[0], ay - self.pen_xy[1]))
        self._path_len_px += travel_m / (2 * PAPER_HALF) * (self.canvas_res - 1)
        self.pen_xy = np.array([ax, ay], np.float32)
        self.pen_down = pen_down
        self.steps += 1

        true_iou = M.iou(self.canvas, self.target)
        # the reward's IoU is what the agent is scored on: the exact canvas
        # (truth baseline) or the camera-perceived canvas (vision, H2 novelty).
        if self.reward_mode == "vision":
            seen = self._seen() if self._cam else self._perceive(self.canvas)
            reward_iou = M.iou(seen, self.target)
        elif self.reward_mode == "vision_real":
            reward_iou = M.iou(self._realcam.perceive(self.canvas), self.target)
        else:
            reward_iou = true_iou
        reward = self._reward(reward_iou)
        # smoothness: discourage jerky direction changes -> straighter strokes
        # Averaged over the first THREE dims only, so the penalty keeps the same
        # scale whether or not the stop head exists. Averaging over all dims made
        # dx/dy smoothing 25% weaker in the allow_stop arm and charged the stop
        # head for its own exploration jitter - a confound in what is meant to be
        # a one-variable ablation. With 3 dims this is identical to before.
        reward -= self.smooth_penalty * float(
            np.abs(action[:3] - self._prev_action[:3]).mean())
        self._prev_action = action.copy()

        # --- overrun handling (2026-08-23; see RESEARCH_LOG) ---------------
        # Measured: agents trace the shape in the first ~15% of the episode,
        # overshoot it by 0.03-0.13 IoU in the few steps after completing, then
        # sit on a frozen canvas for ~74% of the remaining steps. All three
        # switches below are OFF by default so the recorded results stand.
        self._peak_iou = max(self._peak_iou, true_iou)
        if reward_iou > self._best_reward_iou + self.plateau_eps:
            self._best_reward_iou = reward_iou
            self._stale = 0
        else:
            self._stale += 1

        # `reached` is the SUCCESS condition and the only thing the +2.0 bonus
        # may be paid for. Keeping it separate from `terminated` matters: the
        # first version of allow_stop set `terminated = True` for the stop
        # action and the bonus was gated on `terminated`, so pressing stop paid
        # +2.0 on a blank canvas (measured: +1.99 at step 1, IoU 0.000). Since
        # done_iou=0.60 is never actually reached (best peak_iou on record is
        # 0.516), the baseline never collected that bonus and the stop arm
        # collected it every episode - the two arms were optimising different
        # reward functions, and the stop arm's collapse was bought, not learned.
        reached = reward_iou >= self.done_iou
        terminated = reached
        truncated = self.steps >= self.max_steps
        # the agent asks to stop (allow_stop): a real decision to end, so it is
        # a termination, not a truncation - but it earns no success bonus.
        if self.allow_stop and float(action[3]) > 0.5:
            terminated = True
        # plateau stop: an artificial cutoff - the episode COULD have continued,
        # so it is a truncation and the value function should still bootstrap.
        if self.plateau_patience and self._stale >= self.plateau_patience:
            truncated = True
        # info always reports the TRUE IoU, so a vision-trained agent is judged
        # fairly by real drawing quality, not by its own (noisy) perception.
        # reward_iou is what the agent is OPTIMISING (its perception); iou is
        # the truth. Their gap over training is the H3 reward-exploitation test.
        info = {"coverage": M.coverage(self.canvas, self.target),
                "iou": true_iou, "reward_iou": reward_iou,
                "iou_gap": reward_iou - true_iou,
                # peak_iou is the best drawing the policy actually produced this
                # episode; `iou` is what it is scored on, AFTER any overshoot.
                # Reporting only the second understates every policy we have.
                "peak_iou": self._peak_iou,
                "overshoot": self._peak_iou - true_iou,
                "steps_used": self.steps,
                "path_len_px": self._path_len_px,
                "path_ratio": M.path_ratio(self._path_len_px, self.target),
                "snr": M.snr(self.canvas, self.target)}
        if reached:
            reward += 2.0                        # bonus for reaching the shape
        return self._obs(), float(reward), terminated, truncated, info

    def _reward(self, iou):
        # IoU-delta reward: rewards covering the target AND penalises stray ink
        # (stray lowers IoU), so scribbling to fake coverage is not rewarded.
        # Telescopes over the episode to the final IoU -> maximising return =
        # maximising the drawing's IoU with the target.
        d_iou = iou - self._prev_iou
        self._prev_iou = iou
        r = self.iou_weight * d_iou
        # potential-based proximity shaping: guides the pen toward the target
        phi = self._potential()
        r += self.prox_weight * (phi - self._prev_phi)
        self._prev_phi = phi
        r -= self.time_penalty
        return r

    def _seen(self):
        """This step's camera image, computed at most once.

        Both the reward and the observation need it, and perceive() is the most
        expensive thing in the step (measured ~0.6 ms for a randomised camera vs
        ~0.08 ms for the fixed one), so it is cached against the step counter
        rather than recomputed. Note the cache key is `self.steps`, which
        advances exactly once per step - and the camera itself is fixed for the
        episode, so within a step the image is genuinely the same picture.
        """
        if self._seen_at != self.steps:
            self._seen_img = self._cam.perceive(self.canvas)
            self._seen_at = self.steps
        return self._seen_img

    def _estimate_offset(self, min_response=0.05):
        """Sheet offset (canvas px: col, row) seen by the camera: the translation
        that carries the belief canvas onto the photograph. (0, 0) when either
        has no ink or the correlation peak is weak."""
        photo = self._seen()
        if not self._belief.any() or not photo.any():
            return (0.0, 0.0)
        (dx, dy), resp = cv2.phaseCorrelate(self._belief.astype(np.float32),
                                            photo.astype(np.float32))
        if resp < min_response:
            return (0.0, 0.0)
        return (dx, dy)

    def _obs(self):
        # When a camera is in the loop (cam_split), the agent SEES its drawing
        # through that camera too, not just gets rewarded through it.
        #
        # This was found the hard way. With the camera attached only to the
        # reward, evaluating a trained policy under different cameras gave
        # byte-identical drawings: the policy acts on the observation, the
        # observation was the true canvas, and at evaluation there is no reward
        # for the camera to affect. "Test on a held-out camera" was measuring
        # nothing. Proposal 4.1 assumed otherwise, and so did this code.
        #
        # Routing the observation through the camera is also simply the honest
        # setup: a real robot has no privileged access to the ink it laid down -
        # it only has the photograph. `cam_split=None` keeps the privileged
        # true-canvas observation, so every earlier result is untouched.
        if self.obs_view == "ego":
            return self._obs_ego()
        if self.obs_source == "fk":
            source = self._belief          # what kinematics think is on the page
        elif self.obs_source == "camera" or self._cam:
            source = self._seen()          # a photograph of the real page
        else:
            source = self.canvas           # privileged: the real ink
        drawn = cv2.resize(source, (self.obs_res, self.obs_res),
                           interpolation=cv2.INTER_AREA)
        tgt = cv2.resize(self.target, (self.obs_res, self.obs_res),
                         interpolation=cv2.INTER_AREA)
        pen = np.zeros((self.obs_res, self.obs_res), np.uint8)
        # pen marker in obs space
        col = (self.pen_xy[0] - (PAPER_CX - PAPER_HALF)) / (2 * PAPER_HALF) * (self.obs_res - 1)
        row = ((PAPER_CY + PAPER_HALF) - self.pen_xy[1]) / (2 * PAPER_HALF) * (self.obs_res - 1)
        if self.pen_marker_frame == "sheet" and self.obs_source != "fk":
            # same arithmetic plus the sheet offset (canvas px -> obs px), so with
            # no shift this is bit-identical to the "world" marker
            k = (self.obs_res - 1) / (self.canvas_res - 1)
            col += float(self._paper_off[0]) * k
            row += float(self._paper_off[1]) * k
        elif self.pen_marker_frame == "estimated" and self.obs_source != "fk":
            # H4 v4: the sheet offset is ESTIMATED from the photograph by phase
            # correlation against the kinematic belief canvas (what the arm
            # thinks it drew). No privileged `_paper_off` is read here.
            est = self._estimate_offset()
            k = (self.obs_res - 1) / (self.canvas_res - 1)
            col += float(est[0]) * k
            row += float(est[1]) * k
        col, row = int(col), int(row)
        col = int(np.clip(col, 0, self.obs_res - 1))
        row = int(np.clip(row, 0, self.obs_res - 1))
        cv2.circle(pen, (col, row), max(1, self.obs_res // 32),
                   255 if self.pen_down else 128, -1)
        chans = [tgt, drawn, pen]
        if self.time_in_obs:
            # constant-valued plane: 0 at the start of the episode -> 255 at
            # truncation. A plain CNN reads this as a global scalar.
            frac = min(1.0, self.steps / float(max(1, self.max_steps)))
            chans.append(np.full((self.obs_res, self.obs_res),
                                 int(round(frac * 255)), np.uint8))
        if self.coord_channels:
            ramp = np.round(np.linspace(0, 255, self.obs_res)).astype(np.uint8)
            chans.append(np.tile(ramp[None, :], (self.obs_res, 1)))     # column coordinate
            chans.append(np.tile(ramp[:, None], (1, self.obs_res)))     # row coordinate
        return np.stack(chans, axis=-1).astype(np.uint8)

    def _obs_ego(self):
        """O2 egocentric observation: an `ego_win`-px square of the canvas centred on the pen,
        shown at obs_res (zero outside the sheet). The shift is a whole number of canvas px,
        so the window is an exact crop, not a resampled one."""
        col, row = self._world_to_px(*self.pen_xy)
        s = self.obs_res / float(self.ego_win)
        half = self.ego_win / 2.0
        M = np.array([[s, 0.0, (half - col) * s], [0.0, s, (half - row) * s]], np.float64)
        win = lambda img: cv2.warpAffine(img, M, (self.obs_res, self.obs_res),
                                         flags=cv2.INTER_AREA if s < 1 else cv2.INTER_NEAREST,
                                         borderMode=cv2.BORDER_CONSTANT, borderValue=0)
        sheet = win(np.full((self.canvas_res, self.canvas_res), 255, np.uint8))
        drawn = self._seen() if self._cam else self.canvas   # camera in the loop: the agent sees the photo
        chans = [win(self.target), win(drawn), sheet]
        if self.time_in_obs:
            frac = min(1.0, self.steps / float(max(1, self.max_steps)))
            chans.append(np.full((self.obs_res, self.obs_res), int(round(frac * 255)), np.uint8))
        return np.stack(chans, axis=-1).astype(np.uint8)

    def render(self):
        # white paper, black ink, red target outline, for human viewing
        img = np.full((self.canvas_res, self.canvas_res, 3), 255, np.uint8)
        img[self.target > 127] = (180, 180, 255)      # target in light red
        img[self.canvas > 127] = (0, 0, 0)            # ink in black
        return img

    def close(self):
        if self._arm is not None:
            try:
                self._bc.disconnect()
            except Exception:
                pass
        if self._realcam is not None:
            self._realcam.close()
