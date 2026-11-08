"""
RoboSketch-RL  |  interactive drawing sandbox
-------------------------------------------------
YOU drive the pen and it leaves real ink on the paper.

Unlike 04_camera_capture.py (which runs a fixed square by itself and then
photographs it), this script is hands-on and has NO capture camera - the only
camera is your viewport (your mouse). Just you, the pen, and the paper.

Controls (the sliders on the right, under "Params"):
    pen_x     - move the pen across the paper (left/right)
    pen_y     - move the pen across the paper (near/far)
    pen_down  - 1 = pen touches paper and INKS, 0 = lifted (move without drawing)
    clear     - drag it fully right to wipe the paper clean

So: set pen_down to 1, then drag pen_x / pen_y to draw. Set pen_down to 0 to
move without leaving a mark (lift the pen between strokes).

Run:  conda run -n robosketch python sim/05_interactive_draw.py
"""
import importlib.util
import os
import sys

import cv2
import numpy as np
import pybullet as p
import pybullet_data

from viewer import connect_gui, label

# reuse the verified drawing machinery from B5
_HERE = os.path.dirname(os.path.abspath(__file__))
_spec = importlib.util.spec_from_file_location("draw_line",
                                               os.path.join(_HERE, "03_draw_line.py"))
D = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(D)


def ink_segment(canvas, x0, y0, x1, y1):
    """Draw a continuous ink stroke from world (x0,y0) to (x1,y1) on the canvas.

    A line, not just a dot, so strokes stay connected even when the slider
    jumps. Only the part that lies on the paper is inked.
    """
    if not (D.on_paper(x0, y0) or D.on_paper(x1, y1)):
        return
    c0 = D.world_to_px(x0, y0)
    c1 = D.world_to_px(x1, y1)
    cv2.line(canvas, c0, c1, (0, 0, 0), thickness=max(2, 2 * D.PEN_RADIUS_PX),
             lineType=cv2.LINE_AA)


def main():
    connect_gui(p)
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    # zoom the viewport in on the paper so the drawing is big and clear
    p.resetDebugVisualizerCamera(cameraDistance=0.55, cameraYaw=50,
                                 cameraPitch=-55,
                                 cameraTargetPosition=[D.PAPER_CX, D.PAPER_CY, 0.0])
    p.loadURDF("plane.urdf")

    # --- paper (mesh so the whole canvas maps onto it) ---
    canvas = np.full((D.RES, D.RES, 3), 255, dtype=np.uint8)
    os.makedirs(D.OUT_DIR, exist_ok=True)
    tex_path = os.path.join(D.OUT_DIR, "_paper_texture.png")
    cv2.imwrite(tex_path, canvas)
    vis = p.createVisualShape(p.GEOM_MESH, fileName=D.PAPER_OBJ,
                              meshScale=[D.PAPER_HALF, D.PAPER_HALF, 1.0],
                              rgbaColor=[1, 1, 1, 1])
    paper = p.createMultiBody(baseMass=0, baseVisualShapeIndex=vis,
                              basePosition=[D.PAPER_CX, D.PAPER_CY, D.PAPER_TOP_Z])
    p.changeVisualShape(paper, -1, textureUniqueId=p.loadTexture(tex_path))

    arm = p.loadURDF("kuka_iiwa/model.urdf", useFixedBase=True)
    nj = p.getNumJoints(arm)
    tip = nj - 1
    for j in range(nj):
        p.resetJointState(arm, j, D.HOME_POSE[j])

    # --- controls ---
    s_x = p.addUserDebugParameter(label("pen_x"), D.PAPER_CX - D.PAPER_HALF,
                                  D.PAPER_CX + D.PAPER_HALF, D.PAPER_CX)
    s_y = p.addUserDebugParameter(label("pen_y"), D.PAPER_CY - D.PAPER_HALF,
                                  D.PAPER_CY + D.PAPER_HALF, D.PAPER_CY)
    s_down = p.addUserDebugParameter(label("pen_down"), 0, 1, 0)
    s_clear = p.addUserDebugParameter(label("clear"), 0, 1, 0)

    print("Move pen_x / pen_y to position the pen.")
    print("Set pen_down = 1 to draw, 0 to lift. Drag 'clear' right to wipe.\n")

    last_ink = None            # last inked world point (for continuous strokes)
    clear_prev = 0.0
    dirty = True
    since_refresh = 0

    while p.isConnected():
        try:
            px = p.readUserDebugParameter(s_x)
            py = p.readUserDebugParameter(s_y)
            pen_down = p.readUserDebugParameter(s_down) > 0.5
            clear_val = p.readUserDebugParameter(s_clear)

            # clear button: fire when it crosses to the right
            if clear_val > 0.5 and clear_prev <= 0.5:
                canvas[:] = 255
                last_ink = None
                dirty = True
            clear_prev = clear_val

            wrist_z = D.WRIST_DOWN_Z if pen_down else D.WRIST_UP_Z
            angles = D.solve_ik(arm, tip, [px, py, wrist_z])
            for j in range(nj):
                p.setJointMotorControl2(arm, j, p.POSITION_CONTROL,
                                        targetPosition=angles[j],
                                        force=800, maxVelocity=10)
            p.stepSimulation()

            # ink at the pen's ACTUAL position
            wx, wy, _ = p.getLinkState(arm, tip)[4]
            if pen_down:
                if last_ink is not None:
                    ink_segment(canvas, last_ink[0], last_ink[1], wx, wy)
                    dirty = True
                last_ink = (wx, wy)
            else:
                last_ink = None       # pen lifted -> break the stroke

            # push the canvas to the paper every few steps (texture reload is
            # slow, so not every step)
            since_refresh += 1
            if dirty and since_refresh >= 8:
                D.refresh_paper(paper, canvas)
                dirty = False
                since_refresh = 0
        except p.error:
            break

    # save whatever the user drew
    out = os.path.join(D.OUT_DIR, "drawing_interactive.png")
    cv2.imwrite(out, canvas)
    print(f"\nSaved your drawing to: {out}")


if __name__ == "__main__":
    main()
