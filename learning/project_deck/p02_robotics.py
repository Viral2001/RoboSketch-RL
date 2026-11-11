"""Section 2 - robotics from scratch."""
from kit import *  # noqa: F401,F403
from teach_figs import TOY


def build(prs, toc):
    section(prs, 2, "Robotics from scratch",
            "Before any learning: what an arm is, how joint angles map to a pen position and back, "
            "why the agent thinks in pen space, and how the simulator models pen and paper.",
            ["Links, joints, degrees of freedom", "Forward kinematics", "Jacobian & inverse kinematics",
             "Damped least squares (PyBullet)", "World ↔ pixel mapping", "Pen space vs joint space",
             "PyBullet, pen & paper"],
            """
Section 2: robotics ki basics. Physics background ke saath yeh aapko sabse aasaan lagega -
yeh mostly geometry aur linear algebra hai. Do cheezen yaad rakhni hain: forward kinematics
(angles se position) aasaan aur unique hai; inverse kinematics (position se angles) mushkil hai
aur numerically solve hoti hai. Aur hamara agent joints nahi, PEN ko control karta hai.""", toc)

    figure(prs, "02 · robots", "A robot arm: links, joints, degrees of freedom",
           "A chain of rigid links joined by motorised joints, ending in a tool (our pen).",
           "two_link_arm.png",
           ["Link = a rigid piece (your forearm). Joint = a motor that rotates one link relative to "
            "the previous one (your elbow).",
            "Degrees of freedom (DOF) = number of independent joints.",
            "End-effector = the tool at the tip; here a pen.",
            "Simulation arm: KUKA iiwa, 7 joints, bundled with PyBullet (kuka_iiwa/model.urdf).",
            "A pen on a flat sheet needs x, y, up/down and a vertical pen: 6 DOF is enough; 7 gives "
            "redundancy (many poses reach one point)."],
           take="Why KUKA for now: free with PyBullet, well-tested IK; the learning part never "
                "talks to joints, so the arm can be swapped later.", take_color=VIOLET,
           notes="""
Robot arm = links (sakht tukde) + joints (motor wale jod). Apna haath socho: kandha, kohni,
kalaai joints hain; upper arm, forearm, haath links hain; ungliyon me pen end-effector hai.

DOF = kitne independent joints. Paper par pen ke liye x, y, z (upar-neeche) aur pen ko seedha
rakhna - 6 DOF kaafi. KUKA iiwa me 7 joints hain - ek extra, isliye ek hi point tak kai tarah se
pahunch sakta hai (redundancy).

KUKA kyun? PyBullet ke saath free aata hai, uska IK achha tested hai, to drawing engine jaldi ban
gaya. Aur kyunki hamara agent sirf "pen kidhar jaye" bolta hai (joints nahi), baad me sasta arm
lagana = sirf robot model aur IK badalna; seekhne wala dimaag wahi rehta hai.

Figure ek 2-link toy arm hai (agle slide ka example) - KUKA ka nahi.
""", source="rl/draw_env.py _setup_arm (kuka_iiwa/model.urdf, 7-value home pose); "
            "RESEARCH_LOG 2026-07-23 'Decision - robot arm model for simulation'; figure = toy (teach_figs.py)")

    f = TOY["fk"]
    eq_slide(prs, "02 · kinematics", "Forward kinematics: joint angles → pen position",
             "The easy direction: know every angle, and geometry gives the tip position (unique).",
             r"x = L_1\cos\theta_1 + L_2\cos(\theta_1+\theta_2)",
             [(r"L_1,\ L_2", "lengths of link 1 and link 2 (metres)"),
              (r"\theta_1", "angle of link 1, measured from the x-axis"),
              (r"\theta_2", "angle of link 2, measured from link 1 (relative angle)"),
              (r"(x,\ y)", "position of the pen tip in the arm's base frame")],
             example=[f"Toy arm: L1 = {f['L1']:.2f} m, L2 = {f['L2']:.2f} m,",
                      f"θ1 = {f['t1']:.0f}°, θ2 = {f['t2']:.0f}°",
                      f"→ x = {f['x']:.3f} m,  y = {f['y']:.3f} m",
                      "(computed by teach_figs.py, not a project result)"],
             extra=[r"y = L_1\sin\theta_1 + L_2\sin(\theta_1+\theta_2)"],
             why_text="The fk arm in H4 'sees' only what kinematics predicts - this mapping. It cannot "
                      "know if the sheet moved under the pen.",
             label="Forward kinematics (2-link)", group="Robotics",
             notes="""
Forward kinematics (FK): saare joint angles pata hain to pen ki position nikaalo. Har link apna
vector jodta hai: pehla link L1 lamba, angle theta1; doosra link L2 lamba, angle (theta1+theta2)
kyunki theta2 pehle link se naapa jaata hai. x components cos se, y components sin se.

Physics wala intuition: yeh bas vectors ka sum hai - jaise do displacement vectors jodna.

Example (toy, script ne compute kiya): L1=0.40 m, L2=0.30 m, theta1=30 deg, theta2=45 deg
-> x ~0.424 m, y ~0.490 m.

Project me kahan? H4 ka `fk` arm (D01 ki condition) apni drawing ka "belief" isi tarah banata
hai - jahan pen jaana chahiye tha, wahan ink maan leta hai. FK hamesha unique hai: ek set of angles
-> ek hi position. Problem yeh hai ki FK ko duniya ki khabar nahi - paper khiska to FK ko pata
nahi chalega.
""", source="standard planar kinematics; toy numbers computed by learning/project_deck/teach_figs.py")

    steps_slide(prs, "02 · kinematics", "Forward kinematics for a real arm: chain the transforms",
                "Each joint contributes one 4×4 'homogeneous transform' (a rotation plus a translation).",
                [("one joint", r"T_{i-1,i}(\theta_i)=\left[\genfrac{}{}{0}{}{R_i(\theta_i)}{0\ 0\ 0}\quad\genfrac{}{}{0}{}{p_i}{1}\right]",
                  ["R = 3×3 rotation, p = 3-vector offset of the next frame.",
                   "Packing both in one 4×4 matrix makes chaining a simple product."]),
                 ("the chain", r"T_{0n}=T_{01}(\theta_1)\,T_{12}(\theta_2)\cdots T_{n-1,n}(\theta_n)",
                  ["Multiply base → tip. For the KUKA, n = 7 joints.",
                   "The last column of T₀ₙ is the tool position.", ], "FK as a chain of transforms"),
                 ("in code", r"\mathtt{getLinkState(arm,\ link)[4]}",
                  ["PyBullet does the chain for us.",
                   "Real bug found: index [0] is the link's centre of mass, not its frame - a silent "
                   "~20 mm error at every target until changed to index [4]."])],
                take="FK is cheap and exact; the hard part is the inverse - and checking which point "
                     "you are actually measuring.", group="Robotics",
                notes="""
Asli arm 2D nahi hota, aur har joint ek alag axis par ghoomta hai. Isliye har joint ke liye ek
4x4 "homogeneous transform" matrix T hoti hai - jisme 3x3 rotation R aur 3-vector translation p
dono hote hain (aakhri row 0 0 0 1). Fayda: rotation + translation dono ek hi matrix multiply se.

Poore arm ka FK = sab matrices ka product, base se tip tak. Result ka aakhri column = tool ki
position.

Code me PyBullet yeh sab karta hai: getLinkState. Ek real bug yahan mila tha: index [0] link ka
centre of mass deta hai, link ka frame nahi. Isse har target par ~20 mm ki chupi hui galti dikhti
thi. Index [4] (worldLinkFramePosition) lagane se theek hua. Lesson: "kaunsa point naap rahe ho"
pehle confirm karo.
""", source="RESEARCH_LOG '### B4 - Inverse Kinematics, built and experimentally validated' (Problem 1)")

    eq_slide(prs, "02 · inverse kinematics", "The Jacobian: how small joint moves move the pen",
             "Inverse kinematics (IK) asks the reverse: which angles put the pen at (x, y, z)?",
             r"\Delta x \approx J(\theta)\,\Delta\theta,\qquad J_{ij}=\frac{\partial x_i}{\partial \theta_j}",
             [(r"\theta", "vector of all joint angles (7 for the KUKA)"),
              (r"x", "pen pose: position (and orientation) of the tip"),
              (r"J(\theta)", "Jacobian matrix: column j = how the tip moves when joint j turns a little"),
              (r"\Delta x,\ \Delta\theta", "small change of tip pose / of joint angles")],
             example=["IK has no simple formula for a 7-joint arm, and may have many answers "
                      "(redundancy) or none (out of reach).",
                      "So it is solved numerically: linearise with J, take a small step, repeat.",
                      "This is why small continuous pen moves are reliable and big jumps are not."],
             example_title="WHY NUMERICAL", example_color=PRIMARY,
             why_text="Every pen move the agent asks for must become joint angles; the Jacobian is "
                      "the local 'exchange rate' between the two.",
             label="Jacobian (linearised kinematics)", group="Robotics",
             notes="""
IK ulti direction hai: pen ko (x, y, z) par chahiye - joints kitne ghumaun? 7 joints wale arm ke
liye koi seedha formula nahi hai. Kai jawab ho sakte hain (redundancy) ya ek bhi nahi (point
pahunch se bahar).

Physics student ke liye intuition: Jacobian ek "local linearisation" hai - jaise Taylor series ka
first-order term. J ka har column batata hai: joint j ko thoda sa ghumao to pen kis direction me
kitna khiskega. Chhote changes ke liye delta x ~ J * delta theta.

Hum ulta chahte hain: delta x pata hai (pen kahan le jaana hai), delta theta chahiye. J aksar
square nahi hota (7 joints, 6 pose numbers) aur kabhi kabhi "singular" hota hai - isliye seedha
inverse nahi le sakte. Agla slide batata hai PyBullet kya karta hai.

Design lesson: IK current pose se shuru hota hai, isliye chhote, lagataar moves bahut reliable
hain - aur drawing naturally chhote steps me hoti hai.
""", source="standard robotics (Jacobian); RESEARCH_LOG B4 'Transferable lessons' (small steps more reliable)")

    eq_slide(prs, "02 · inverse kinematics", "Damped least squares: the IK step PyBullet takes",
             "PyBullet's calculateInverseKinematics uses damped least squares (DLS) by default.",
             r"\Delta\theta = J^{\mathrm{T}}\left(JJ^{\mathrm{T}}+\lambda^{2}I\right)^{-1} e",
             [(r"e", "error: target pose minus current pose of the tip"),
              (r"J^{\mathrm{T}}", "transpose of the Jacobian"),
              (r"\lambda", "damping factor: keeps the step finite near singular poses"),
              (r"I", "identity matrix"),
              (r"\theta\leftarrow\theta+\Delta\theta", "repeat until the error is tiny")],
             example=["Our call: maxNumIterations = 120, residualThreshold = 1e-4, target orientation "
                      "= pen pointing straight down.",
                      "λ = 0 is plain least squares: fast, but explodes near singularities (JJᵀ nearly "
                      "non-invertible).",
                      "λ > 0 trades a little accuracy for a stable, smooth step."],
             example_title="IN OUR CODE", example_color=PRIMARY,
             why_text="DLS is robust for a redundant 7-joint arm doing many small moves - exactly a pen "
                      "drawing - so no custom IK solver was needed.",
             label="Damped least-squares IK step", group="Robotics",
             notes="""
Damped least squares (DLS): IK ka standard numerical tareeka. Error e = jahan pen chahiye minus
jahan abhi hai. Step delta theta = J-transpose (J J-transpose + lambda^2 I)^-1 e. Phir theta
update karo aur dobara karo - jab tak error bahut chhota na ho.

Lambda kyun? Kuch poses me arm "singular" hota hai (jaise bilkul seedha phaila hua haath) - wahan
J J-transpose almost non-invertible hota hai aur bina damping ke step infinite jaisa ho jaata hai.
Lambda^2 I add karne se matrix hamesha invertible rehti hai - thodi accuracy ke badle stability.
(Least squares + regularisation - jaise ridge regression.)

Hamare code me: draw_env.py ka _move_arm calculateInverseKinematics ko 120 iterations tak aur
residual 1e-4 tak chalata hai, aur target orientation "pen neeche ki taraf" deta hai. Phir motors
ko POSITION_CONTROL se target angles dete hain aur 6 physics steps chalate hain.

Note: PyBullet ka default solver DLS hai (PyBullet quickstart guide ke mutabik); lambda ki value
hamne set nahi ki - default use hoti hai.
""", source="rl/draw_env.py _move_arm (maxNumIterations=120, residualThreshold=1e-4, targetOrientation); "
            "PyBullet quickstart guide (calculateInverseKinematics, default solver IK_DLS)")

    tabular(prs, "02 · inverse kinematics", "IK in this project: measured, not assumed",
            "Four problems had to be found and fixed before drawing-grade accuracy (B4, 24 Jul 2026).",
            ["IK variant (6 targets)", "mean position error", "pen tilt", "verdict"],
            [["position only", "0.003 mm", "41°", "pen slanted - useless"],
             ["position only + null-space hints", "0.911 mm", "41°", "worse"],
             ["position + orientation (pen vertical)", "0.007 mm", "0.00°", "CHOSEN"],
             ["position + orientation + null-space", "2.835 mm", "0.06°", "~400× worse"]],
            colw=[4.6, 2.4, 1.6, 3.2], cell_colors={(2, 3): GOOD, (0, 3): BAD, (3, 3): BAD},
            below=["Problems solved: measuring the wrong point (index [0] vs [4]) · pen orientation · "
                   "reachable area (safe box x 0.45–0.65 m, y ±0.20 m) · the wrist hitting the floor "
                   "(fixed with a virtual 0.10 m pen).",
                   "Final check, 81-point raster: worst pen-down error 0.108 mm, tilt 0.001°, 0 points above 1 mm.",
                   "Lesson: validate through motors + settled physics, never by teleporting joints "
                   "(resetJointState ignores joint limits and over-reports accuracy)."],
            take="Result: the simulated arm can place a pen to ~0.1 mm - the arm is not the bottleneck.",
            notes="""
IK ko configure karna khud ek mini-experiment tha. Sirf position maangne par error tiny tha par
pen 41 degree tircha tha - drawing ke liye bekaar. Position + orientation (pen seedha neeche)
maangne par 0.007 mm error aur 0 degree tilt - yeh chuna. "Null-space hints" (joint limits,
rest poses) madadgar lagte hain par accuracy ~400 guna kharab karte hain.

Chaar problems: (1) galat point naapna (index 0 vs 4), (2) pen ka angle, (3) arm kahan tak pahunch
sakta hai - safe box x 0.45-0.65 m, y +/-0.20 m, (4) kalaai zameen se takrati thi - hal: 10 cm ka
virtual pen jo kalaai se latakta hai, IK kalaai ko paper se 10 cm upar aim karta hai.

Final: 81 points ke raster par sabse badi galti 0.108 mm. Matlab arm accuracy bottleneck nahi
hai - problem learning/reward/vision me hai.

Ek aur lesson: resetJointState joints ko "teleport" karta hai aur joint limits ignore karta hai -
isse accuracy zyada achhi dikhti hai jitni asli me hai. Hamesha motors chala ke, physics settle
karke naapo.
""", source="RESEARCH_LOG '### B4 - Inverse Kinematics, built and experimentally validated (2026-07-24)'")

    w = TOY["w2p"]
    sh = TOY["sheet"]
    eq_slide(prs, "02 · frames", "From metres on the sheet to pixels on the canvas",
             "The drawing lives in an image; the pen lives in world metres. This mapping joins them.",
             r"\mathrm{col}=\frac{x-x_{min}}{w}\,(R-1),\qquad \mathrm{row}=\frac{y_{max}-y}{h}\,(R-1)",
             [(r"x,\ y", "pen position in world metres (sheet centre at x = 0.55, y = 0)"),
              (r"x_{min},\ y_{max}", "left edge and top edge of the sheet"),
              (r"w,\ h", "sheet width and height (0.20 m each)"),
              (r"R", f"canvas resolution ({sh['canvas_res']} px)")],
             example=[f"Pen at x = {w['x']:.2f}, y = {w['y']:.2f} m",
                      f"→ col = {w['col']:.2f}, row = {w['row']:.2f}",
                      f"1 canvas px ≈ {sh['mm_per_px']:.2f} mm",
                      "Note row uses y_max - y: image rows grow DOWNWARD while world y grows up.",
                      "(computed by teach_figs.py)"],
             why_text="A bug here mirrors every drawing and the reward scores a mirrored image. The "
                      "first version WAS transposed; it was caught by checking against physics.",
             label="World → canvas pixel mapping", group="Robotics",
             notes="""
Pen duniya me metres me hai, drawing ek image (pixels) me. Yeh formula dono ko jodta hai. Column
x ke saath badhta hai; row ULTA - kyunki image me row neeche ki taraf badhti hai jabki world y
upar ki taraf. Isliye (y_max - y).

Example (toy): pen x=0.60, y=0.05 -> col ~95.25, row ~31.75 (128 px canvas par). Ek canvas pixel
lagbhag 1.6 mm ka hai.

Bug story (B5): pehla version x ko row se aur y ko column se map kar raha tha - transposed. Agar
pakda na jaata to har drawing mirror hoti aur reward ek mirrored image ko target se compare
karta. Pakda kaise? Ink ek world point par paint ki, wahi point par ek reference sphere rakha,
aur dono ko compare kiya - charon edges par ~3 px ke andar match.

H4 me yahi function ek "sheet offset" bhi add karta hai: paper khisakne par ink wahan girti hai
jahan sheet ab hai - kinematics ko yeh pata nahi.
""", source="rl/draw_env.py _world_to_px (PAPER_CX 0.55, PAPER_CY 0.0, PAPER_HALF 0.10); "
            "RESEARCH_LOG '### B5 - the pen leaves a mark' finding 4; toy numbers by teach_figs.py")

    concept(prs, "02 · design choice", "The agent controls the PEN, not the joints",
            "Task-space action: 'move the pen by (dx, dy)'. IK turns it into joint angles.",
            ["Joint-space action: one number per motor (7 for the KUKA). Tied to one specific arm.",
             "Task-space action (ours): [dx, dy, pen] - each in [-1, 1] / [0, 1], dx and dy scaled by "
             "the step size (0.014 m in the experiments).",
             "Portable: moving to a cheaper arm changes the robot model + IK, not what the policy means.",
             "Physically realisable: D01 rejects curve-based (Bézier) strokes because real arms cannot "
             "execute them; FRIDA measures the cost of an unrealistic action space.",
             "In all experiments the pen point is moved directly (fast backend); the IK-driven KUKA "
             "exists and was used for validation only."],
            cards=[("BACKEND A: use_arm=False", ["Pen point moves exactly as commanded. Fast: the "
                                                  "whole step is image maths. Used for training."], PRIMARY),
                   ("BACKEND B: use_arm=True", ["The real IK KUKA carries the pen; it lags the command "
                                                "by 2.8–4.8 mm while drawing (corners get rounded). "
                                                "Validation only."], ACCENT)],
            take="Pen-space actions keep the learned 'brain' independent of the arm and of IK quirks.",
            take_color=VIOLET,
            notes="""
Agent kya control kare? Do raaste the. Joint space: har motor ko alag se bolo kitna ghume - yeh
ek specific arm se bandh jaata hai. Task space (hamara): agent sirf bolta hai "pen ko dx, dy
khiskao, aur pen neeche/upar". IK use joint angles me badalta hai.

Analogy: driver ko "10 meter uttar jao" bolna, na ki "steering 12 degree ghumao, pedal 30%
dabao". Pehli instruction kisi bhi gaadi me chalti hai.

Literature support: D01 Bezier curves reject karta hai kyunki asli arm unhe execute nahi kar
sakta; FRIDA unrealistic action space ki keemat naapta hai. To hamara conservative (dx, dy) sahi
side par hai.

Honest detail: saare experiments fast backend par chale - pen point seedha commanded jagah jaata
hai. KUKA + IK wala backend realistic hai (motor lag 2.8-4.8 mm, corners round ho jaate hain) par
slow; isse validation hua. Paper me bhi yahi likha hai.
""", source="rl/draw_env.py (action_space, step(), use_arm); docs/paper/main.tex Setup; "
            "docs/PROJECT_PROPOSAL_v2.md section 7; RESEARCH_LOG B5 'Motor tracking lag'")

    grid(prs, "02 · simulation", "Why simulate first - and why PyBullet",
         "RL needs hundreds of thousands of tries. On a real arm that is weeks of wear; in simulation, hours.",
         [("WHAT A PHYSICS SIMULATOR DOES", ["Steps rigid bodies forward in time under motor torques, "
                                             "gravity and contact; gives exact ground truth for free."], PRIMARY),
          ("PYBULLET (CHOSEN)", ["Native on Windows, fast headless stepping, pure Python, common in RL "
                                 "robotics. Installed from conda-forge (no Windows pip wheel)."], GOOD),
          ("GAZEBO (REJECTED)", ["Built for full-system realism with ROS; effectively needs Linux/WSL2; "
                                 "not built for RL throughput."], BAD),
          ("MUJOCO (ESCAPE HATCH)", ["Faster, better contacts, free. Not switched: our setup was already "
                                     "validated to 0.1 mm; the bottleneck is reward + vision."], WARN),
          ("DIRECT vs GUI", ["GUI = a window to watch; DIRECT = headless, used for all training and "
                             "for the camera renders."], ACCENT),
          ("THE PRICE", ["Simulation is never reality: servo lag, stroke width, lighting all have to be "
                         "measured on hardware later (sim-to-real)."], WARN)],
         cols=3, take="Simulation-first is the standard lesson for real-robot RL (R03 in the library).",
         notes="""
Simulation kyun? RL ko laakhon koshishen chahiye. Asli arm par yeh hafton ka ghisaav, toot-phoot
aur reset ka jhanjhat hai. Simulation me ghante.

PyBullet kyun: Windows par native chalta hai, headless (bina window) tez chalta hai, Python hai,
RL papers me common hai. Pip se Windows par install nahi hota - conda-forge se hota hai (yeh ek
real blocker tha, log me hai).

Gazebo reject: ROS ke saath Linux maangta hai, RL throughput ke liye nahi bana. MuJoCo achha
alternative tha (tez, free) - par jab setup 0.1 mm tak validate ho chuka tha aur bottleneck physics
nahi balki reward aur vision tha, to switch karne ka fayda nahi.

Keemat: simulation kabhi reality nahi. Servo lag, stroke ki motai, roshni - sab hardware par
dobara naapna padega. Ise sim-to-real gap kehte hain (Section 11).
""", source="RESEARCH_LOG '### Decision - simulator choice (PyBullet vs Gazebo vs MuJoCo; Colab)', "
            "'### RESOLVED - PyBullet via conda-forge'; AGENTS.md section 3")

    concept(prs, "02 · pen & paper", "How ink and paper are modelled",
            "The canvas (a numpy image) is the authoritative drawing; the textured 3-D paper is only a picture of it.",
            ["Ink = a straight anti-aliased line from the previous pen point to the new one, drawn into a "
             f"{TOY['sheet']['canvas_res']}×{TOY['sheet']['canvas_res']} canvas, "
             f"{TOY['sheet']['line_px']} px thick (pen radius from 3.5 mm).",
             "For training, ink is drawn straight into the image - far faster than rendering 3-D.",
             "B5 findings: debug lines are invisible to a camera (0 pixels changed); a box shape does not "
             "UV-map a texture (paper became a mesh quad); changeTexture is a no-op (texture reloaded "
             "from disk instead); the world→pixel map was transposed.",
             "B6 finding: loadTexture caches by FILENAME - the camera saw a frozen early frame until "
             "every refresh used a unique file name."],
            cards=[("WHY A NUMPY CANVAS", ["Exact, fast, and it is what the reward scores. The camera "
                                          "path is a separate, imperfect view of it - by design."], PRIMARY),
                   ("LESSON", ["Each of these bugs would have silently corrupted the vision pipeline. "
                               "All were found by MEASURING (pixel counts), not by looking."], WARN)],
            notes="""
Ink kaise banti hai: har step par pichhle pen point se naye point tak ek seedhi line canvas
(numpy image) me draw hoti hai. Yahi canvas "sach" hai - isi par true IoU naapa jaata hai.
3-D paper par texture sirf dekhne ke liye hai.

B5/B6 me chaar-paanch bugs mile - sab measurement se:
- PyBullet ki debug lines camera ko dikhti hi nahi (0 pixel badle) -> ink asli scene content
  honi chahiye.
- Box shape texture ko sahi map nahi karta -> paper ko mesh quad banaya.
- changeTexture kaam nahi karta -> texture disk se reload.
- loadTexture filename se cache karta hai -> camera purani frame dekh raha tha; har baar unique
  filename se theek hua.

Lesson: aankh se dekh kar "theek lag raha hai" kaafi nahi; pixel count karke check karo. Yahi
attitude poore project me hai.
""", source="rl/draw_env.py (pen_radius_px from 0.0035 m, cv2.line into self.canvas); RESEARCH_LOG "
            "'### B5 - the pen leaves a mark' and '### B6 - the robot sees its own drawing'; "
            "line thickness computed by teach_figs.py")
