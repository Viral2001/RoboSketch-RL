"""
RoboSketch-RL  |  watch.py - run and WATCH the simulation, any time
-------------------------------------------------
One entry point for *seeing* the project run. Everything else in `rl/` trains,
measures or plots; nothing until now simply showed a trained agent drawing.

What it shows, side by side:

    TARGET            what the agent is asked to draw
    LIVE DRAWING      the ink it is laying down, right now, step by step
    CAMERA SEES       the same ink after the camera's resolution loss +
                      threshold - the ONLY thing a vision-reward agent is paid
                      on (the project's H2 novelty)

and, with --view arm/both, a 3D PyBullet window where the KUKA arm physically
traces the same path on the textured paper.

IMPORTANT - this is a viewer, not a new experiment. The episode is the exact
deterministic evaluation `train.py::evaluate` runs (kinematic env, fixed start,
deterministic policy, seed 1000), so what you watch is the number the README
reports. The arm window is a MIRROR: it follows env.pen_xy by IK and never
feeds anything back, so opening it cannot change the drawing or the IoU.

The HUD reports true IoU and *peak* IoU together on purpose: agents trace the
shape in the first ~15% of the episode and then overshoot it (rl/overrun.py),
so the gap between the two lines is the overshoot, live.

Run (or just double-click watch.bat in the project root):
  conda run -n robosketch python rl/watch.py
  conda run -n robosketch python rl/watch.py --shape circle --reward-mode vision
  conda run -n robosketch python rl/watch.py --shape all --view both --save
  conda run -n robosketch python rl/watch.py --list

Keys in the drawing window:
  SPACE pause/resume   R restart episode   N next shape   S snapshot
  + / - faster/slower  Q or ESC quit
"""
import argparse
import glob
import os
import shutil
import sys
from datetime import datetime

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "sim"))

from draw_env import DrawEnv, PAPER_CX, PAPER_CY, PAPER_HALF

OUT = os.path.join(ROOT, "output")
WATCH_DIR = os.path.join(OUT, "watch")
MODELS = os.path.join(ROOT, "models")
PAPER_OBJ = os.path.join(ROOT, "assets", "paper_quad.obj")
SHAPES = ["line", "circle", "square", "triangle"]
WIN = "RoboSketch-RL  |  live"

PANEL = 300          # each of the three image panels, in pixels
HUD_H = 132          # the strip under them: text + the IoU trace


# ----------------------------------------------------------------- models --
def model_tag(shape, mode, time_obs=False):
    tag = f"{shape}_kin"
    if mode != "truth":
        tag += f"_{mode}"
    if time_obs:
        tag += "_t"
    return tag


def model_path(shape, mode, time_obs=False):
    return os.path.join(MODELS, f"ppo_{model_tag(shape, mode, time_obs)}.zip")


def available():
    """Every trained agent on disk, as (shape, reward_mode, path)."""
    out = []
    for f in sorted(glob.glob(os.path.join(MODELS, "ppo_*.zip"))):
        name = os.path.basename(f)[4:-4]          # strip "ppo_" and ".zip"
        parts = name.split("_")
        if len(parts) < 2 or parts[0] not in SHAPES:
            continue
        mode = "_".join(parts[2:]) or "truth"
        out.append((parts[0], mode, f))
    return out


def print_models():
    print("\nTrained agents in models/ :\n")
    for shape, mode, f in available():
        mb = os.path.getsize(f) / 1e6
        print(f"  --shape {shape:8s} --reward-mode {mode:12s}"
              f"   ({os.path.basename(f)}, {mb:.1f} MB)")
    print()


# ------------------------------------------------------------- 2D panels --
def _frame(gray_target, gray_ink, tint=(0, 0, 0)):
    """White paper, light-red target outline, ink in `tint` (BGR)."""
    r = gray_ink.shape[0]
    img = np.full((r, r, 3), 255, np.uint8)
    img[gray_target > 127] = (185, 185, 255)
    img[gray_ink > 127] = tint
    return img


def _panel(img, title, accent=(60, 60, 60)):
    big = cv2.resize(img, (PANEL, PANEL), interpolation=cv2.INTER_NEAREST)
    big = cv2.copyMakeBorder(big, 28, 8, 8, 8, cv2.BORDER_CONSTANT,
                             value=(248, 248, 248))
    cv2.rectangle(big, (8, 28), (8 + PANEL - 1, 28 + PANEL - 1), (210, 210, 210), 1)
    cv2.putText(big, title, (10, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.46, accent, 1,
                cv2.LINE_AA)
    return big


def _trace_plot(w, h, ious, peaks, max_steps):
    """Small live plot: true IoU per step, with the running peak behind it."""
    img = np.full((h, w, 3), 250, np.uint8)
    cv2.rectangle(img, (0, 0), (w - 1, h - 1), (225, 225, 225), 1)
    for frac in (0.25, 0.5, 0.75):
        y = int(h - frac * (h - 2)) - 1
        cv2.line(img, (1, y), (w - 2, y), (238, 238, 238), 1)
    cv2.putText(img, "true IoU per step  (grey = peak so far)", (6, 13),
                cv2.FONT_HERSHEY_SIMPLEX, 0.36, (150, 150, 150), 1, cv2.LINE_AA)
    if len(ious) < 2:
        return img
    n = max(max_steps, len(ious))

    def pts(series):
        return np.array([[1 + int(i / max(1, n - 1) * (w - 3)),
                          h - 2 - int(min(1.0, v) * (h - 4))]
                         for i, v in enumerate(series)], np.int32)

    cv2.polylines(img, [pts(peaks)], False, (200, 200, 200), 3, cv2.LINE_AA)
    cv2.polylines(img, [pts(ious)], False, (150, 90, 20), 2, cv2.LINE_AA)
    return img


def compose(env, info, ious, peaks, meta, paused, fps):
    """The whole window: three panels over a HUD strip."""
    tgt = env.target
    goal = _panel(_frame(tgt, np.zeros_like(tgt)), "TARGET", (60, 60, 190))
    live = _panel(_frame(tgt, env.canvas), "LIVE DRAWING  (ink)", (30, 30, 30))
    seen = _panel(_frame(tgt, env._perceive(env.canvas), (150, 90, 20)),
                  "CAMERA SEES  (vision reward)", (150, 90, 20))
    row = np.hstack([goal, live, seen])
    w = row.shape[1]

    hud = np.full((HUD_H, w, 3), 248, np.uint8)
    f = cv2.FONT_HERSHEY_SIMPLEX
    iou = float(info.get("iou", 0.0))
    peak = peaks[-1] if peaks else 0.0
    line1 = f"{meta['shape']}   reward: {meta['mode']}   {meta['model']}"
    line2 = (f"step {env.steps:3d}/{env.max_steps}    IoU {iou:.3f}    "
             f"peak {peak:.3f}    (overshoot {iou - peak:+.3f})")
    cv2.putText(hud, line1, (10, 20), f, 0.48, (70, 70, 70), 1, cv2.LINE_AA)
    cv2.putText(hud, line2, (10, 43), f, 0.56, (20, 20, 20), 1, cv2.LINE_AA)
    tail = "PAUSED - space to resume" if paused else f"{fps:.0f} fps"
    cv2.putText(hud, tail, (w - 250, 20), f, 0.46,
                (30, 30, 190) if paused else (150, 150, 150), 1, cv2.LINE_AA)
    cv2.putText(hud, "space pause | R restart | N next | S snap | +/- speed | Q quit",
                (w - 470, 43), f, 0.4, (150, 150, 150), 1, cv2.LINE_AA)
    plot = _trace_plot(w - 20, HUD_H - 58, ious, peaks, env.max_steps)
    hud[52:52 + plot.shape[0], 10:10 + plot.shape[1]] = plot
    return np.vstack([row, hud])


# ------------------------------------------------------- the 3D arm view --
class ArmView:
    """A PyBullet GUI window whose KUKA arm mirrors the env's pen.

    Read-only by design: it takes env.pen_xy and drives the arm there with IK.
    Nothing it computes ever returns to the environment, so the episode you
    watch is identical to the same episode with the window closed.
    """

    def __init__(self, width=1280, height=820):
        import pybullet as p
        import pybullet_data
        from pybullet_utils import bullet_client
        from viewer import crisp_window

        crisp_window()                                   # sharp on Windows HiDPI
        self.p = p
        self.bc = bullet_client.BulletClient(
            connection_mode=p.GUI, options=f"--width={width} --height={height}")
        bc = self.bc
        bc.setAdditionalSearchPath(pybullet_data.getDataPath())
        for flag in (p.COV_ENABLE_RGB_BUFFER_PREVIEW,
                     p.COV_ENABLE_DEPTH_BUFFER_PREVIEW,
                     p.COV_ENABLE_SEGMENTATION_MARK_PREVIEW):
            bc.configureDebugVisualizer(flag, 0)
        bc.setGravity(0, 0, -9.81)
        bc.resetDebugVisualizerCamera(cameraDistance=0.62, cameraYaw=48,
                                      cameraPitch=-52,
                                      cameraTargetPosition=[PAPER_CX, PAPER_CY, 0.05])
        bc.loadURDF("plane.urdf")

        # the paper: a UV-mapped quad MESH (not a box - a box's top face samples
        # a tiny uniform patch of the texture, so most of a drawing never shows)
        self.texdir = os.path.join(OUT, "_watch_tex")
        os.makedirs(self.texdir, exist_ok=True)
        self._tex_n = 0
        vis = bc.createVisualShape(p.GEOM_MESH, fileName=PAPER_OBJ,
                                   meshScale=[PAPER_HALF, PAPER_HALF, 1.0],
                                   rgbaColor=[1, 1, 1, 1])
        self.paper = bc.createMultiBody(baseMass=0, baseVisualShapeIndex=vis,
                                        basePosition=[PAPER_CX, PAPER_CY, 0.003])
        self.set_texture(np.full((128, 128, 3), 255, np.uint8))

        self.arm = bc.loadURDF("kuka_iiwa/model.urdf", useFixedBase=True)
        self.nj = bc.getNumJoints(self.arm)
        self.tip = self.nj - 1
        home = [0.0, 0.5, 0.0, -1.5, 0.0, 1.2, 0.0]
        for j in range(self.nj):
            bc.resetJointState(self.arm, j, home[j])
        self.z_down = 0.003 + 0.10                       # paper top + pen length
        self.z_up = self.z_down + 0.05
        self.q_down = bc.getQuaternionFromEuler([np.pi, 0, 0])
        self._text = -1

    def set_texture(self, bgr):
        """Push the canvas onto the paper.

        Every call writes a UNIQUE filename: p.loadTexture caches by path, so
        reusing one silently freezes the paper at its first frame (measured in
        B5 - see sim/03_draw_line.py).
        """
        self._tex_n += 1
        path = os.path.join(self.texdir, f"t{self._tex_n:06d}.png")
        cv2.imwrite(path, bgr)
        self.bc.changeVisualShape(self.paper, -1,
                                  textureUniqueId=self.bc.loadTexture(path))
        stale = os.path.join(self.texdir, f"t{self._tex_n - 3:06d}.png")
        if os.path.exists(stale):
            try:
                os.remove(stale)
            except OSError:
                pass

    def goto(self, x, y, pen_down=True, settle=4):
        bc = self.bc
        z = self.z_down if pen_down else self.z_up
        a = bc.calculateInverseKinematics(self.arm, self.tip, [x, y, z],
                                          targetOrientation=self.q_down,
                                          maxNumIterations=120,
                                          residualThreshold=1e-4)
        for j in range(self.nj):
            bc.setJointMotorControl2(self.arm, j, bc.POSITION_CONTROL,
                                     targetPosition=a[j], force=800, maxVelocity=10)
        for _ in range(settle):
            bc.stepSimulation()

    def caption(self, text):
        kw = dict(textPosition=[PAPER_CX - PAPER_HALF,
                                PAPER_CY - PAPER_HALF - 0.03, 0.16],
                  textColorRGB=[0.1, 0.1, 0.1], textSize=1.3)
        if self._text >= 0:
            kw["replaceItemUniqueId"] = self._text
        try:
            self._text = self.bc.addUserDebugText(text, **kw)
        except Exception:
            pass

    def alive(self):
        try:
            return bool(self.bc.isConnected())
        except Exception:
            return False

    def close(self):
        try:
            self.bc.disconnect()
        except Exception:
            pass
        shutil.rmtree(self.texdir, ignore_errors=True)


# -------------------------------------------------------------- the loop --
def run_episode(model, shape, mode, args, arm=None):
    """One deterministic evaluation episode, drawn live. Returns the last key."""
    env = DrawEnv(shape=shape, max_steps=args.max_steps, step_size_m=args.step_size,
                  reward_mode=mode, plateau_patience=args.plateau_patience or None,
                  seed=999)
    obs, _ = env.reset(seed=args.eval_seed)
    meta = {"shape": shape, "mode": mode,
            "model": "RANDOM policy (untrained)" if args.random
                     else os.path.basename(model_path(shape, mode))}
    if arm is not None:
        arm.goto(float(env.pen_xy[0]), float(env.pen_xy[1]), True, settle=40)

    ious, peaks = [], []
    best = (-1.0, None)
    writer, vid_path = None, None
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    fps, paused, done, key = float(args.fps), False, False, -1
    info = {}

    while True:
        if not paused and not done:
            if args.random:
                action = env.action_space.sample()
            else:
                action, _ = model.predict(obs, deterministic=True)
            obs, _r, term, trunc, info = env.step(action)
            done = bool(term or trunc)
            ious.append(float(info["iou"]))
            peaks.append(max(peaks[-1], ious[-1]) if peaks else ious[-1])
            if ious[-1] > best[0]:
                best = (ious[-1], _frame(env.target, env.canvas))
            if arm is not None and arm.alive():
                arm.goto(float(env.pen_xy[0]), float(env.pen_xy[1]), True)
                if env.steps % max(1, args.tex_every) == 0 or done:
                    arm.set_texture(_frame(env.target, env.canvas))
                arm.caption(f"{shape} / {mode}   step {env.steps}   "
                            f"IoU {ious[-1]:.3f}")

        frame = compose(env, info, ious, peaks, meta, paused, fps)

        if args.save and writer is None:
            os.makedirs(WATCH_DIR, exist_ok=True)
            vid_path = os.path.join(WATCH_DIR,
                                    f"watch_{model_tag(shape, mode)}_{stamp}.mp4")
            writer = cv2.VideoWriter(vid_path, cv2.VideoWriter_fourcc(*"mp4v"),
                                     max(5.0, fps),
                                     (frame.shape[1], frame.shape[0]))
        if writer is not None and not paused:
            writer.write(frame)

        if args.no_window:
            if done:
                break
            continue

        cv2.imshow(WIN, frame)
        wait = 60 if (paused or done) else max(1, int(1000.0 / fps))
        key = cv2.waitKey(wait) & 0xFF
        if key in (ord("q"), 27) or key in (ord("r"), ord("n")):
            break
        if key == ord(" "):
            paused = not paused
        elif key in (ord("+"), ord("=")):
            fps = min(240.0, fps * 1.5)
        elif key == ord("-"):
            fps = max(2.0, fps / 1.5)
        elif key == ord("s"):
            os.makedirs(WATCH_DIR, exist_ok=True)
            snap = os.path.join(WATCH_DIR, f"snap_{model_tag(shape, mode)}_"
                                           f"{stamp}_{env.steps:03d}.png")
            cv2.imwrite(snap, frame)
            print(f"  snapshot -> {os.path.relpath(snap, ROOT)}")
        if arm is not None and not arm.alive():
            key = ord("q")
            break

    if writer is not None:
        writer.release()
        print(f"  video    -> {os.path.relpath(vid_path, ROOT)}")
    if args.save and ious:
        os.makedirs(WATCH_DIR, exist_ok=True)
        fin = os.path.join(WATCH_DIR, f"final_{model_tag(shape, mode)}_{stamp}.png")
        pk = os.path.join(WATCH_DIR, f"peak_{model_tag(shape, mode)}_{stamp}.png")
        cv2.imwrite(fin, _frame(env.target, env.canvas))
        cv2.imwrite(pk, best[1])
        print(f"  final    -> {os.path.relpath(fin, ROOT)}")
        print(f"  peak     -> {os.path.relpath(pk, ROOT)}")
    if ious:
        print(f"  {shape:9s} {mode:12s}  final IoU {ious[-1]:.3f}   "
              f"peak {best[0]:.3f}   overshoot {ious[-1] - best[0]:+.3f}   "
              f"steps {len(ious)}")
    env.close()
    return key


def main():
    ap = argparse.ArgumentParser(description="Watch a trained RoboSketch agent draw.")
    ap.add_argument("--shape", default="line",
                    help="line | circle | square | triangle | all")
    ap.add_argument("--reward-mode", default="truth",
                    choices=["truth", "vision", "vision_real"],
                    help="which trained agent: ground-truth reward or camera reward")
    ap.add_argument("--view", default="canvas", choices=["canvas", "arm", "both"],
                    help="canvas = 2D window only; arm/both also opens the 3D robot")
    ap.add_argument("--fps", type=float, default=30.0)
    ap.add_argument("--max-steps", type=int, default=240)
    ap.add_argument("--step-size", type=float, default=0.014)
    ap.add_argument("--eval-seed", type=int, default=1000,
                    help="the seed train.py::evaluate uses, so IoU matches the reports")
    ap.add_argument("--plateau-patience", type=int, default=0,
                    help="end the episode after N steps with no improvement "
                         "(0 = off = faithful to the published numbers)")
    ap.add_argument("--tex-every", type=int, default=2,
                    help="refresh the 3D paper texture every N steps")
    ap.add_argument("--random", action="store_true",
                    help="watch an UNTRAINED random policy (the 'before' picture)")
    ap.add_argument("--loop", action="store_true", help="repeat forever")
    ap.add_argument("--save", action="store_true",
                    help="record mp4 + final/peak PNGs into output/watch/")
    ap.add_argument("--no-window", action="store_true",
                    help="headless: no OpenCV window (use with --save)")
    ap.add_argument("--list", action="store_true", help="list trained agents and exit")
    args = ap.parse_args()

    if args.list:
        print_models()
        return

    shapes = SHAPES if args.shape == "all" else [args.shape]
    for s in shapes:
        if s not in SHAPES:
            sys.exit(f"unknown shape '{s}' - pick from {SHAPES} or 'all'")

    models = {}
    if not args.random:
        from stable_baselines3 import PPO
        for s in shapes:
            path = model_path(s, args.reward_mode)
            if not os.path.exists(path):
                print(f"\n! no trained agent at models/{os.path.basename(path)}")
                print_models()
                sys.exit(f"train one first:  python rl/train.py --shape {s} "
                         f"--timesteps 400000"
                         + ("" if args.reward_mode == "truth"
                            else f" --reward-mode {args.reward_mode}"))
            models[s] = PPO.load(path, device="cpu")

    arm = ArmView() if args.view in ("arm", "both") else None
    print(f"\nwatching: {', '.join(shapes)}   reward={args.reward_mode}   "
          f"view={args.view}")
    print("keys: SPACE pause | R restart | N next | S snapshot | +/- speed | Q quit\n")
    try:
        while True:
            for s in shapes:
                key = run_episode(models.get(s), s, args.reward_mode, args, arm)
                if key in (ord("q"), 27):
                    return
                if arm is not None and not arm.alive():
                    return
            if not args.loop:
                if args.no_window:
                    return
                print("\ndone - press any key in the window to replay, Q to quit")
                if (cv2.waitKey(0) & 0xFF) in (ord("q"), 27):
                    return
    finally:
        if arm is not None:
            arm.close()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
