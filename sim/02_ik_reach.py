"""
RoboSketch-RL  |  Phase B, milestone B4
-------------------------------------------------
Inverse Kinematics (IK): tell the arm "put the pen at (x, y) on the paper"
and let PyBullet work out the joint angles.

Why this matters: the RL agent will think in PEN space ("move the pen here"),
not joint space. IK is the bridge that turns that wish into joint commands.
It is also what makes the policy portable to a different arm later.

Two accuracy fixes over naive IK (a plain calculateInverseKinematics call
left ~3.4 cm of error, which would ruin a drawing):
  1. Constrain the pen ORIENTATION to point straight down, so the arm cannot
     satisfy the position by tilting the pen at a silly angle.
  2. Give the solver joint limits/ranges + many more iterations, and re-solve
     a few times (iterative refinement) to converge much closer.

Controls (sliders, top-right of the GUI):
  target_x / target_y : where on the paper the pen should go
  pen_down            : 1 = pen touches paper (z=0), 0 = lifted above it

Run:  conda run -n robosketch python sim/02_ik_reach.py
"""
import math

import pybullet as p
import pybullet_data

from viewer import connect_gui, label

# --- VIRTUAL PEN -----------------------------------------------------------
# The robot's wrist link is a solid body: if we ask its own frame to sit 2 cm
# above the floor it COLLIDES with the floor and cannot get there (measured:
# ~35 mm error). A real drawing robot holds a pen, so we model one.
#
# The pen is a PEN_LENGTH rod pointing straight down from the wrist:
#     wrist z  = paper z + PEN_LENGTH      <- what IK aims for
#     pen tip  = wrist z - PEN_LENGTH      <- what touches the paper
# Measured: the wrist needs >= 0.06 m of clearance; 0.10 m gives margin.
PAPER_Z = 0.0        # the paper lies on the ground plane
PEN_LENGTH = 0.10    # distance from wrist frame down to the pen tip
PEN_LIFT = 0.05      # how far the pen rises when lifted off the paper

WRIST_DOWN_Z = PAPER_Z + PEN_LENGTH              # pen tip touching paper
WRIST_UP_Z = PAPER_Z + PEN_LENGTH + PEN_LIFT     # pen lifted

# --- VERIFIED SAFE DRAWING AREA -------------------------------------------
# Measured by commanding the motors and letting physics settle (see
# docs/RESEARCH_LOG.md). Inside this box the pen reaches its target to <1 mm
# with the pen exactly vertical, and no joint limit is exceeded.
#
# Outside it the arm cannot fold tightly enough: at x <= 0.35 the elbow
# (joint 3) is driven ~9 deg past its limit and the pen lands ~70 mm off.
X_MIN, X_MAX = 0.45, 0.65
Y_MIN, Y_MAX = -0.20, 0.20

# A comfortable starting pose ("elbow down") to seed the arm at startup.
HOME_POSE = [0.0, 0.5, 0.0, -1.5, 0.0, 1.2, 0.0]


def solve_ik(arm, pen_tip_link, target_xyz):
    """Solve IK for the pen tip, with the pen pointing straight DOWN.

    Measured accuracy (see docs/RESEARCH_LOG.md): ~0.01 mm position error and
    0.00 deg pen tilt.

    Two things matter here, both found experimentally:
      * We MUST pass targetOrientation. Position-only IK reaches the point but
        leaves the pen tilted ~41 deg, which is useless for drawing.
      * We must NOT pass the null-space hints (lowerLimits/upperLimits/
        jointRanges/restPoses). They look helpful but degrade accuracy from
        ~0.01 mm to ~2.8 mm - far too sloppy for a clean line.
    """
    # Pen points straight down: rotate 180 deg about X so the tool's +Z faces -Z world.
    down_orientation = p.getQuaternionFromEuler([math.pi, 0, 0])

    return p.calculateInverseKinematics(
        arm,
        pen_tip_link,
        target_xyz,
        targetOrientation=down_orientation,
        maxNumIterations=200,
        residualThreshold=1e-5,
    )


def main():
    connect_gui(p)          # DPI-aware + roomy window + panels tidied
    p.setAdditionalSearchPath(pybullet_data.getDataPath())
    p.setGravity(0, 0, -9.81)
    p.resetDebugVisualizerCamera(cameraDistance=1.2, cameraYaw=50,
                                 cameraPitch=-35, cameraTargetPosition=[0.55, 0, 0.05])

    p.loadURDF("plane.urdf")                                   # the "paper"
    arm = p.loadURDF("kuka_iiwa/model.urdf", useFixedBase=True)
    num_joints = p.getNumJoints(arm)
    pen_tip_link = num_joints - 1

    # Start from a comfortable pose so the first IK solve is well seeded.
    for j in range(num_joints):
        p.resetJointState(arm, j, HOME_POSE[j])

    # Sliders are clamped to the verified safe drawing area.
    # label() prepends a space - PyBullet chops the first character off every
    # debug label, so the space is sacrificed instead of a real letter.
    s_x = p.addUserDebugParameter(label("target_x"), X_MIN, X_MAX, 0.55)
    s_y = p.addUserDebugParameter(label("target_y"), Y_MIN, Y_MAX, 0.0)
    s_down = p.addUserDebugParameter(label("pen_down"), 0, 1, 1)

    # Outline the safe drawing area on the ground so it is visible.
    corners = [(X_MIN, Y_MIN), (X_MAX, Y_MIN), (X_MAX, Y_MAX), (X_MIN, Y_MAX)]
    for i in range(4):
        a = corners[i]
        b = corners[(i + 1) % 4]
        p.addUserDebugLine([a[0], a[1], 0.001], [b[0], b[1], 0.001],
                           lineColorRGB=[0.2, 0.4, 1.0], lineWidth=2)

    print("Drag target_x / target_y to move the pen. pen_down=1 touches the paper.")

    text_id = None
    marker_id = None
    step = 0        # used to throttle the terminal printout

    while p.isConnected():
        # Closing the window can drop the connection part-way through a frame,
        # so any call below may raise. Catch it and leave quietly instead of
        # dumping a traceback at the user.
        try:
            tx = p.readUserDebugParameter(s_x)
            ty = p.readUserDebugParameter(s_y)
            pen_is_down = p.readUserDebugParameter(s_down) > 0.5
            wrist_z = WRIST_DOWN_Z if pen_is_down else WRIST_UP_Z
            target = [tx, ty, wrist_z]          # IK aims the WRIST here

            angles = solve_ik(arm, pen_tip_link, target)
            for j in range(num_joints):
                # force/maxVelocity matter: the motors must be strong and quick
                # enough to actually arrive, otherwise the pen lags behind the
                # target and the "error" readout is really just tracking lag.
                p.setJointMotorControl2(arm, j, p.POSITION_CONTROL,
                                        targetPosition=angles[j],
                                        force=800, maxVelocity=10)
            p.stepSimulation()

            # How close did the pen actually get?
            # Index 4 = worldLinkFramePosition (what IK targets). Index 0 is
            # the centre of mass, ~20 mm off, which would fake a large error.
            wx, wy, wz = p.getLinkState(arm, pen_tip_link)[4]
            err = math.dist((wx, wy, wz), target)
            # the pen tip hangs PEN_LENGTH below the wrist
            pen_tip = (wx, wy, wz - PEN_LENGTH)

            # NB: not named `label` - that would shadow the imported label()
            # helper for the whole function (Python makes any assigned name
            # local throughout), breaking the slider setup above.
            readout = (f"target=({tx:+.3f},{ty:+.3f})  "
                       f"pen tip=({pen_tip[0]:+.3f},{pen_tip[1]:+.3f},{pen_tip[2]:+.3f})  "
                       f"{'DOWN' if pen_is_down else 'UP'}  err={err*1000:6.2f} mm")
            # Small on-screen text (3D billboard text goes chunky up close);
            # the sharp copy is printed to the terminal below.
            text_id = p.addUserDebugText(readout, [0, 0, 1.45], textColorRGB=[0, 0, 0],
                                         textSize=0.9,
                                         replaceItemUniqueId=text_id if text_id else -1)

            step += 1
            if step % 60 == 0:
                print(f"\r{readout}   ", end="", flush=True)

            # Draw the virtual pen as a line from the wrist down to the tip.
            marker_id = p.addUserDebugLine([wx, wy, wz], pen_tip,
                                           lineColorRGB=[1, 0, 0], lineWidth=4,
                                           replaceItemUniqueId=marker_id if marker_id else -1)
        except p.error:
            break

    print("\nWindow closed - simulation ended.")


if __name__ == "__main__":
    main()
