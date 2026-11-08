"""
RoboSketch-RL  |  Phase B, milestones B1-B3
-------------------------------------------------
B1: Load a 6/7-DOF arm + a flat "paper" plane in the PyBullet GUI.
B2: Add a slider per joint so you can move the arm by hand.
B3: Continuously read out the pen-tip (end-effector) world position.

No RL, no vision yet. Goal: confirm the robot loads, moves, and that we
can always answer "where is the pen tip right now?".

Run:  python sim/01_manual_control.py
Close the GUI window (or Ctrl+C in the terminal) to quit.
"""
import pybullet as p
import pybullet_data

from viewer import connect_gui, label


def main():
    # --- connect to the physics server with a GUI window ---
    connect_gui(p)          # DPI-aware + roomy window + panels tidied
    p.setAdditionalSearchPath(pybullet_data.getDataPath())  # so built-in URDFs are found
    p.setGravity(0, 0, -9.81)
    p.resetDebugVisualizerCamera(cameraDistance=1.5, cameraYaw=50,
                                 cameraPitch=-35, cameraTargetPosition=[0, 0, 0.3])

    # --- Layer 3: the "paper" is just the ground plane at z = 0 ---
    p.loadURDF("plane.urdf")

    # --- Layer 1: the robot arm (KUKA iiwa, bundled with PyBullet) ---
    arm = p.loadURDF("kuka_iiwa/model.urdf", basePosition=[0, 0, 0], useFixedBase=True)
    num_joints = p.getNumJoints(arm)

    # The pen would be attached to the last link -> treat it as the pen tip for now.
    pen_tip_link = num_joints - 1

    # --- Layer 2 (setup): one debug slider per revolute joint ---
    # Labels are short AND passed through label(), which prepends a space:
    # PyBullet chops the first character off every debug label, so the space is
    # sacrificed instead of the "j" in "joint_1". See sim/viewer.py.
    sliders = []
    for j in range(num_joints):
        info = p.getJointInfo(arm, j)
        urdf_name = info[1].decode("utf-8")       # e.g. "lbr_iiwa_joint_1"
        lower, upper = info[8], info[9]          # joint limits from the URDF
        if lower >= upper:                        # fixed / unlimited joint -> give a default range
            lower, upper = -3.14, 3.14
        sliders.append(p.addUserDebugParameter(label(f"joint_{j + 1}"),
                                               lower, upper, 0.0))
        print(f"  slider 'joint_{j + 1}'  ->  {urdf_name}"
              f"  limits ({lower:+.2f}, {upper:+.2f})")

    print(f"Loaded arm with {num_joints} joints. Pen-tip link index = {pen_tip_link}")
    print("Drag the sliders (top-right of the GUI) to move the arm.\n")

    text_id = None  # handle for the on-screen pen-tip readout
    step = 0        # used to throttle the terminal printout

    # --- main loop ---
    while p.isConnected():
        # Closing the window can drop the connection part-way through a frame,
        # so any call below may raise. Catch it and leave quietly instead of
        # dumping a traceback at the user.
        try:
            # B2: send each slider value to its joint as a position target
            for j, s in enumerate(sliders):
                target = p.readUserDebugParameter(s)
                p.setJointMotorControl2(arm, j, p.POSITION_CONTROL,
                                        targetPosition=target)

            p.stepSimulation()

            # B3: read the pen-tip world position and show it on screen
            tip_state = p.getLinkState(arm, pen_tip_link)
            # NOTE: index 4 is worldLinkFramePosition (the URDF link frame,
            # which is what IK targets). Index 0 is the CENTRE OF MASS, which
            # sits ~20 mm away and would silently bias every measurement.
            x, y, z = tip_state[4]
            # NB: not named `label` - that would shadow the imported label()
            # helper for the whole function (Python makes any assigned name
            # local throughout), breaking the slider setup above.
            readout = f"Pen tip:  x={x:+.3f}  y={y:+.3f}  z={z:+.3f}"
            # Small text size: this is 3D "billboard" text drawn inside the
            # world, so it goes chunky when the camera is near. The crisp copy
            # is the one printed to the terminal below.
            text_id = p.addUserDebugText(readout, [0, 0, 1.45], textColorRGB=[0, 0, 0],
                                         textSize=0.9,
                                         replaceItemUniqueId=text_id if text_id else -1)

            # Readable, sharp readout in the terminal (~4x a second, same line).
            step += 1
            if step % 60 == 0:
                print(f"\r{readout}   ", end="", flush=True)
        except p.error:
            break

    print("\nWindow closed - simulation ended.")


if __name__ == "__main__":
    main()
