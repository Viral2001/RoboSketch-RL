"""
RoboSketch-RL  |  Phase B, milestone B6
-------------------------------------------------
The robot SEES its own drawing.

A virtual camera above the paper takes a picture, and OpenCV turns that picture
back into a clean binary drawing - the perception pipeline that, on the real
robot, replaces "we happen to know the pen position" with "we can only see the
result through a camera".

This closes the loop from the project architecture:
    robot draws -> CAMERA captures -> OpenCV extracts -> (reward compares)

We also compute IoU (Intersection-over-Union) between what the camera perceived
and the ground-truth canvas. IoU is one of the project's headline metrics, and
here it doubles as a check that the perception pipeline recovers the drawing.

Reuses the verified drawing machinery from 03_draw_line.py.

Run:  conda run -n robosketch python sim/04_camera_capture.py
      conda run -n robosketch python sim/04_camera_capture.py square
"""
import importlib.util
import os
import sys

import cv2
import numpy as np
import pybullet as p
import pybullet_data

from viewer import connect_gui

# --- reuse everything we already built and verified in B5 ------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("draw_line",
                                               os.path.join(_HERE, "03_draw_line.py"))
D = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(D)

CAM_RES = 480          # pixels of the virtual camera image (square)

# Pose the arm adopts for the photo. Straight up over its base (far from the
# paper at x=0.55), it leaves the paper 100% visible with ZERO occlusion
# (measured). Real drawing rigs do the same: move the arm aside, then shoot.
PARK_POSE = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]


# ------------------------------------------------------------------ camera --
def top_down_camera():
    """View + projection matrices for a camera looking straight down at the paper.

    up = +y is chosen so the captured image shares the canvas convention
    (column follows world +x, row follows world -y). VERIFIED by calibration in
    the B6 validation (a corner ink dot lands in the matching image corner).
    """
    eye = [D.PAPER_CX, D.PAPER_CY, 0.55]
    target = [D.PAPER_CX, D.PAPER_CY, D.PAPER_TOP_Z]
    view = p.computeViewMatrix(eye, target, cameraUpVector=[0, 1, 0])
    # narrow FOV so the 0.20 m paper nearly fills the frame from 0.55 m up
    proj = p.computeProjectionMatrixFOV(fov=24, aspect=1.0, nearVal=0.1, farVal=1.0)
    return view, proj


def capture(view, proj, renderer):
    """Grab an RGB frame and the segmentation mask from the virtual camera."""
    w, h, rgb, _, seg = p.getCameraImage(CAM_RES, CAM_RES, view, proj,
                                         renderer=renderer)
    rgb = np.reshape(np.array(rgb, dtype=np.uint8), (h, w, 4))[:, :, :3]
    seg = np.reshape(np.array(seg), (h, w))
    return rgb, seg


def extract_drawing(rgb, seg, paper_id, out_res=None):
    """Turn a camera frame into a clean binary drawing (255=ink, 0=blank).

    Steps, all standard OpenCV:
      1. use the segmentation mask to isolate the paper and crop to it
         (on the real robot this is a colour/contour step instead)
      2. greyscale + Otsu threshold -> ink vs paper
      3. resize to the canvas resolution so it can be compared to ground truth
    """
    if out_res is None:
        out_res = D.RES
    paper = (seg == paper_id)
    if paper.sum() < 50:
        return np.zeros((out_res, out_res), np.uint8), None
    ys, xs = np.nonzero(paper)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1

    crop = rgb[y0:y1, x0:x1]
    grey = cv2.cvtColor(crop, cv2.COLOR_RGB2GRAY)
    # Anything not on the paper (should be nothing once the arm is parked) is
    # forced to white so it can never be mistaken for ink.
    grey[~paper[y0:y1, x0:x1]] = 255
    # Fixed threshold: in this controlled scene paper is bright (~230) and ink
    # is dark (<100), so a mid split is robust. (Otsu was fooled when the dark
    # arm was in frame - hence parking the arm above.)
    _, binv = cv2.threshold(grey, 128, 255, cv2.THRESH_BINARY_INV)
    resized = cv2.resize(binv, (out_res, out_res), interpolation=cv2.INTER_AREA)
    resized = (resized > 40).astype(np.uint8) * 255
    return resized, (x0, y0, x1, y1)


def iou(a, b):
    """Intersection-over-Union of two binary images (255=foreground)."""
    A = a > 127
    B = b > 127
    union = np.logical_or(A, B).sum()
    return float(np.logical_and(A, B).sum()) / float(union) if union else 1.0


# -------------------------------------------------------------------- scene --
def build_scene():
    """Paper mesh + arm, identical setup to B5 (kept in sync via D.*)."""
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    p.loadURDF("plane.urdf")

    canvas = np.full((D.RES, D.RES, 3), 255, dtype=np.uint8)
    tex_path = os.path.join(D.OUT_DIR, "_paper_texture.png")
    os.makedirs(D.OUT_DIR, exist_ok=True)
    cv2.imwrite(tex_path, canvas)
    vis = p.createVisualShape(p.GEOM_MESH, fileName=D.PAPER_OBJ,
                              meshScale=[D.PAPER_HALF, D.PAPER_HALF, 1.0],
                              rgbaColor=[1, 1, 1, 1])
    paper = p.createMultiBody(baseMass=0, baseVisualShapeIndex=vis,
                              basePosition=[D.PAPER_CX, D.PAPER_CY, D.PAPER_TOP_Z])
    p.changeVisualShape(paper, -1, textureUniqueId=p.loadTexture(tex_path))

    arm = p.loadURDF("kuka_iiwa/model.urdf", useFixedBase=True)
    nj = p.getNumJoints(arm)
    for j in range(nj):
        p.resetJointState(arm, j, D.HOME_POSE[j])
    return paper, arm, nj, canvas


def draw_shape(arm, tip, nj, canvas, paper, shape):
    """Drive the pen along the shape, inking the canvas (reuses B5 helpers)."""
    if shape == "square":
        path = D.square_path(D.PAPER_CX, D.PAPER_CY, 0.06)
    else:
        path = D.line_path(D.PAPER_CX - 0.07, 0.0, D.PAPER_CX + 0.07, 0.0)

    sx, sy = path[0]
    for i in range(1, 81):
        t = i / 80.0
        cur = p.getLinkState(arm, tip)[4]
        D.drive(arm, tip, nj, [cur[0] + (sx - cur[0]) * t,
                               cur[1] + (sy - cur[1]) * t, D.WRIST_UP_Z])
    for i in range(1, 41):
        t = i / 40.0
        D.drive(arm, tip, nj, [sx, sy, D.WRIST_UP_Z
                               + (D.WRIST_DOWN_Z - D.WRIST_UP_Z) * t])

    inked = 0
    for n, (tx, ty) in enumerate(path):
        wx, wy, _ = D.drive(arm, tip, nj, [tx, ty, D.WRIST_DOWN_Z], settle=2)
        if D.ink(canvas, wx, wy):
            inked += 1
        if n % D.REFRESH_EVERY == 0:
            D.refresh_paper(paper, canvas, n // D.REFRESH_EVERY)
    D.refresh_paper(paper, canvas, 999)
    for i in range(1, 41):                                  # lift pen
        t = i / 40.0
        D.drive(arm, tip, nj, [path[-1][0], path[-1][1],
                               D.WRIST_DOWN_Z + (D.WRIST_UP_Z - D.WRIST_DOWN_Z) * t])
    return inked


def main():
    shape = sys.argv[1] if len(sys.argv) > 1 else "line"
    gui = "--headless" not in sys.argv
    if gui:
        connect_gui(p)
        p.resetDebugVisualizerCamera(cameraDistance=0.7, cameraYaw=45,
                                     cameraPitch=-50,
                                     cameraTargetPosition=[D.PAPER_CX, D.PAPER_CY, 0.05])
        renderer = p.ER_BULLET_HARDWARE_OPENGL
    else:
        p.connect(p.DIRECT)
        renderer = p.ER_TINY_RENDERER

    paper, arm, nj, canvas = build_scene()
    tip = nj - 1

    print(f"Drawing '{shape}' ...")
    inked = draw_shape(arm, tip, nj, canvas, paper, shape)

    # --- park the arm aside so it does not block the camera, then look ---
    print("Parking the arm and capturing the paper through the virtual camera ...")
    for j in range(nj):
        p.resetJointState(arm, j, PARK_POSE[j])
    for _ in range(30):
        p.stepSimulation()
    view, proj = top_down_camera()
    rgb, seg = capture(view, proj, renderer)
    perceived, bbox = extract_drawing(rgb, seg, paper)

    # ground truth = the canvas we inked (binary)
    gt = (cv2.cvtColor(canvas, cv2.COLOR_BGR2GRAY) < 128).astype(np.uint8) * 255

    score = iou(perceived, gt)

    # --- save the whole pipeline for inspection / the paper ---
    os.makedirs(D.OUT_DIR, exist_ok=True)
    cv2.imwrite(os.path.join(D.OUT_DIR, f"cam_raw_{shape}.png"),
                cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    cv2.imwrite(os.path.join(D.OUT_DIR, f"cam_perceived_{shape}.png"), perceived)
    cv2.imwrite(os.path.join(D.OUT_DIR, f"cam_groundtruth_{shape}.png"), gt)
    # overlay: green = ground truth, red = perceived, yellow = both agree
    overlay = np.zeros((D.RES, D.RES, 3), np.uint8)
    overlay[..., 1] = gt
    overlay[..., 2] = perceived
    cv2.imwrite(os.path.join(D.OUT_DIR, f"cam_overlay_{shape}.png"), overlay)

    print(f"\n  inked points        : {inked}")
    print(f"  paper seen (px)      : {int((seg == paper).sum())}")
    print(f"  perceived ink (px)   : {int((perceived > 127).sum())}")
    print(f"  ground-truth ink (px): {int((gt > 127).sum())}")
    print(f"  IoU (perceived vs gt): {score:.3f}")
    print(f"\n  saved cam_raw / cam_perceived / cam_groundtruth / cam_overlay"
          f"_{shape}.png to output/")

    if gui:
        print("\nClose the window to exit.")
        while p.isConnected():
            try:
                p.stepSimulation()
            except p.error:
                break
    return score


if __name__ == "__main__":
    main()
