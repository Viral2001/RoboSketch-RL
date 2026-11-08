"""
RoboSketch-RL  |  Phase B, milestone B5
-------------------------------------------------
The pen finally leaves a MARK.

The arm moves its pen across the paper and every point it touches is inked.
Two things happen at once, and the distinction matters:

  * the CANVAS  - a numpy image we paint into. This is the DATA: the actual
    drawing, saved to output/. It is what the reward function will eventually
    score, and what the vision pipeline will compare against a target.

  * the PAPER   - a textured object in the 3D world. We upload the canvas to
    it so you can watch the line appear under the pen.

Why a texture and not p.addUserDebugLine? Measured (see docs/RESEARCH_LOG.md):
debug lines are viewer-only overlays and are INVISIBLE to a rendered camera,
so a stroke drawn that way would look right on screen but be invisible to the
vision pipeline in B6. Texture ink is real scene content and renders properly.

Run:  conda run -n robosketch python sim/03_draw_line.py
      conda run -n robosketch python sim/03_draw_line.py square
"""
import math
import os
import sys

import cv2
import numpy as np
import pybullet as p
import pybullet_data

from viewer import connect_gui

# --- paper geometry -------------------------------------------------------
# Sits inside the verified safe drawing area (x[0.45,0.65], y[-0.20,0.20]);
# see sim/02_ik_reach.py for how those bounds were measured.
PAPER_CX, PAPER_CY = 0.55, 0.0
PAPER_HALF = 0.10                 # 0.20 m x 0.20 m sheet
PAPER_TOP_Z = 0.003               # top surface height
RES = 512                         # canvas resolution in pixels

# --- virtual pen ----------------------------------------------------------
PEN_LENGTH = 0.10                 # wrist sits this far above the pen tip
PEN_LIFT = 0.05
WRIST_DOWN_Z = PAPER_TOP_Z + PEN_LENGTH
WRIST_UP_Z = WRIST_DOWN_Z + PEN_LIFT
PEN_RADIUS_PX = max(1, int(0.0015 / (2 * PAPER_HALF) * RES))   # ~1.5 mm nib
REFRESH_EVERY = 20        # points between visible paper refreshes (see below)

HOME_POSE = [0.0, 0.5, 0.0, -1.5, 0.0, 1.2, 0.0]
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(_ROOT, "output")
PAPER_OBJ = os.path.join(_ROOT, "assets", "paper_quad.obj")


# ---------------------------------------------------------------- canvas --
def world_to_px(x, y):
    """Map a world (x, y) on the paper to a canvas pixel (col, row).

    Standard image convention:
        column follows world +x        row follows world -y

    VERIFIED, not assumed: ink painted at a world point renders within ~3 px
    of a reference sphere placed at that same world point, on all four edges
    of the sheet (see docs/RESEARCH_LOG.md). An earlier guess had the two axes
    transposed, which would have mirrored every drawing.
    """
    col = int(round((x - (PAPER_CX - PAPER_HALF)) / (2 * PAPER_HALF) * (RES - 1)))
    row = int(round(((PAPER_CY + PAPER_HALF) - y) / (2 * PAPER_HALF) * (RES - 1)))
    return col, row


def on_paper(x, y):
    return (abs(x - PAPER_CX) <= PAPER_HALF) and (abs(y - PAPER_CY) <= PAPER_HALF)


_refresh_counter = [0]


def refresh_paper(paper, canvas, seq=None):
    """Push the canvas onto the paper so you can watch the stroke appear.

    Goes via a PNG on disk rather than p.changeTexture(): changeTexture is a
    no-op in this PyBullet build (measured 0/4 on every probe, both renderers),
    while reloading from a file updates reliably.

    CRUCIAL: each call writes a UNIQUE filename. p.loadTexture caches by path,
    so reusing a filename returns the STALE first version - which silently
    froze the displayed/photographed paper at an early frame (verified). The
    saved canvas was always correct; only the texture was stale.
    """
    _refresh_counter[0] += 1
    path = os.path.join(OUT_DIR, f"_paper_{_refresh_counter[0]:05d}.png")
    cv2.imwrite(path, canvas)
    p.changeVisualShape(paper, -1, textureUniqueId=p.loadTexture(path))
    # keep only the most recent few frames on disk
    old = _refresh_counter[0] - 3
    if old > 0:
        stale = os.path.join(OUT_DIR, f"_paper_{old:05d}.png")
        if os.path.exists(stale):
            try:
                os.remove(stale)
            except OSError:
                pass


def ink(canvas, x, y):
    """Deposit ink at world position (x, y). Returns True if it landed on paper."""
    if not on_paper(x, y):
        return False
    col, row = world_to_px(x, y)
    cv2.circle(canvas, (col, row), PEN_RADIUS_PX, (0, 0, 0), -1, lineType=cv2.LINE_AA)
    return True


# ------------------------------------------------------------------ paths --
def line_path(x0, y0, x1, y1, steps=240):
    """Straight line. Many small steps: IK is seeded from the arm's current
    pose, so small continuous moves track far better than big jumps."""
    return [(x0 + (x1 - x0) * i / steps, y0 + (y1 - y0) * i / steps)
            for i in range(steps + 1)]


def square_path(cx, cy, half, steps_per_side=120):
    corners = [(cx - half, cy - half), (cx + half, cy - half),
               (cx + half, cy + half), (cx - half, cy + half), (cx - half, cy - half)]
    pts = []
    for i in range(4):
        (ax, ay), (bx, by) = corners[i], corners[i + 1]
        pts += line_path(ax, ay, bx, by, steps_per_side)
    return pts


# -------------------------------------------------------------------- arm --
def solve_ik(arm, tip, target):
    """Pen vertical, no null-space hints - the configuration measured most
    accurate (~0.01 mm). See sim/02_ik_reach.py for the comparison."""
    down = p.getQuaternionFromEuler([math.pi, 0, 0])
    return p.calculateInverseKinematics(arm, tip, target, targetOrientation=down,
                                        maxNumIterations=200, residualThreshold=1e-5)


def drive(arm, tip, num_joints, target, settle=1):
    angles = solve_ik(arm, tip, target)
    for j in range(num_joints):
        p.setJointMotorControl2(arm, j, p.POSITION_CONTROL, targetPosition=angles[j],
                                force=800, maxVelocity=10)
    for _ in range(settle):
        p.stepSimulation()
    return p.getLinkState(arm, tip)[4]        # index 4 = link frame, NOT [0] (CoM)


def main():
    shape = sys.argv[1] if len(sys.argv) > 1 else "line"
    os.makedirs(OUT_DIR, exist_ok=True)

    connect_gui(p)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    p.resetDebugVisualizerCamera(cameraDistance=0.75, cameraYaw=45,
                                 cameraPitch=-40,
                                 cameraTargetPosition=[PAPER_CX, PAPER_CY, 0.05])
    p.loadURDF("plane.urdf")

    # --- the paper: a flat quad MESH wearing our canvas as a texture ---
    # A mesh, not GEOM_BOX: a box's top face samples only a tiny uniform patch
    # of the texture, so most of a drawing would simply never appear on it.
    canvas = np.full((RES, RES, 3), 255, dtype=np.uint8)
    tex_path = os.path.join(OUT_DIR, "_paper_texture.png")
    cv2.imwrite(tex_path, canvas)
    vis = p.createVisualShape(p.GEOM_MESH, fileName=PAPER_OBJ,
                              meshScale=[PAPER_HALF, PAPER_HALF, 1.0],
                              rgbaColor=[1, 1, 1, 1])
    paper = p.createMultiBody(baseMass=0, baseVisualShapeIndex=vis,
                              basePosition=[PAPER_CX, PAPER_CY, PAPER_TOP_Z])
    p.changeVisualShape(paper, -1, textureUniqueId=p.loadTexture(tex_path))

    arm = p.loadURDF("kuka_iiwa/model.urdf", useFixedBase=True)
    num_joints = p.getNumJoints(arm)
    tip = num_joints - 1
    for j in range(num_joints):
        p.resetJointState(arm, j, HOME_POSE[j])

    # --- choose what to draw ---
    if shape == "square":
        path = square_path(PAPER_CX, PAPER_CY, 0.06)
    else:
        path = line_path(PAPER_CX - 0.07, 0.0, PAPER_CX + 0.07, 0.0)
    print(f"Drawing '{shape}' - {len(path)} pen positions.")

    # --- approach: move above the first point with the pen UP ---
    sx, sy = path[0]
    for i in range(1, 81):
        t = i / 80.0
        cur = p.getLinkState(arm, tip)[4]
        drive(arm, tip, num_joints,
              [cur[0] + (sx - cur[0]) * t, cur[1] + (sy - cur[1]) * t, WRIST_UP_Z])
    for _ in range(60):                      # settle before touching down
        drive(arm, tip, num_joints, [sx, sy, WRIST_UP_Z])
    for i in range(1, 41):                   # lower the pen
        t = i / 40.0
        drive(arm, tip, num_joints,
              [sx, sy, WRIST_UP_Z + (WRIST_DOWN_Z - WRIST_UP_Z) * t])

    # --- draw ---
    inked = 0
    max_err = 0.0
    for n, (tx, ty) in enumerate(path):
        wx, wy, wz = drive(arm, tip, num_joints, [tx, ty, WRIST_DOWN_Z], settle=2)
        max_err = max(max_err, math.dist((wx, wy), (tx, ty)))
        # ink goes where the pen ACTUALLY is, not where we asked it to be
        if ink(canvas, wx, wy):
            inked += 1
        if n % REFRESH_EVERY == 0:           # refresh the visible paper
            refresh_paper(paper, canvas, n // REFRESH_EVERY)
            print(f"\r  point {n+1}/{len(path)}  inked={inked}  "
                  f"max_err={max_err*1000:.3f} mm", end="", flush=True)

    refresh_paper(paper, canvas, 999)

    # --- lift the pen ---
    for i in range(1, 41):
        t = i / 40.0
        drive(arm, tip, num_joints,
              [path[-1][0], path[-1][1],
               WRIST_DOWN_Z + (WRIST_UP_Z - WRIST_DOWN_Z) * t])

    out = os.path.join(OUT_DIR, f"drawing_{shape}.png")
    cv2.imwrite(out, canvas)
    print(f"\n\nDone. {inked} inked points, worst tracking error "
          f"{max_err*1000:.3f} mm")
    print(f"Drawing saved to: {out}")
    print("Look at the paper in the 3D view - the stroke is really there.")
    print("Close the window to exit.")

    while p.isConnected():
        try:
            p.stepSimulation()
        except p.error:
            break


if __name__ == "__main__":
    main()
