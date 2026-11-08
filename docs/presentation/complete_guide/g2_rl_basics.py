"""Part 2 - machine learning and reinforcement-learning foundations, neural networks, CNNs."""
from gk import (ACCENT, BAD, BODY, CW, GOOD, INK, LINE, M, MUTED, PRIMARY, SLATE, VIOLET,
                WARN, WASH, WHITE, arrow, bullets, card, chip, concept, eqn, grid, node,
                note, rect, section, slide, steps, strip, tabular, txt, analogy)
from pptx.enum.shapes import MSO_SHAPE


def ml_kinds(prs):
    grid(prs, "02 · machine learning", "Three ways a machine can learn",
         "The difference is what kind of feedback the learner gets.",
         [("SUPERVISED", ["Learns from labelled examples: (input → correct answer).",
                          "Example: 10,000 photos each labelled 'cat' or 'dog'.",
                          "Feedback: 'the right answer was X'.",
                          "Needs someone to produce the answers."], PRIMARY),
          ("UNSUPERVISED", ["Finds structure in data with no labels at all.",
                            "Example: grouping customers into similar types.",
                            "Feedback: none — only the data itself."], SLATE),
          ("REINFORCEMENT", ["Learns by acting and receiving a score.",
                             "Example: a game player, a walking robot, our drawing arm.",
                             "Feedback: 'that was worth +0.3' — never 'the right move was X'.",
                             "Needs only a way to score outcomes."], VIOLET)],
         cols=3,
         take="Why RL here: nobody knows the 'correct' pen nudge at step 137 of a circle, but "
              "anyone can score the finished drawing. A score is all RL needs.",
         take_color=VIOLET,
         notes="""
Machine learning ke teen tareeke hain, aur farak sirf feedback ka hai.
Supervised: har example ke saath sahi jawab diya jaata hai (yeh billi hai, yeh kutta).
Unsupervised: koi jawab nahi, sirf data me pattern dhoondo.
Reinforcement: koi sahi jawab nahi batata; bas kaam karne ke baad ek score milta hai.

Hamare project me RL kyun? Kyunki circle banate waqt step 137 par "sahi" pen movement kya
hai, yeh koi nahi jaanta. Lekin poori drawing ko score karna aasaan hai — target se kitna
milti hai. RL ko sirf score chahiye.
""")


def rl_loop(prs):
    s = slide(prs, "The reinforcement-learning loop", "02 · rl basics",
              "Agent and environment take turns, forever: observe → act → get reward → observe …")
    node(s, M + 0.3, 2.10, 3.0, 1.55, "AGENT", "the learner\n(neural network = policy)",
         color=VIOLET, title_size=16, sub_size=11)
    node(s, M + 8.6, 2.10, 3.0, 1.55, "ENVIRONMENT", "the world it acts in\n(arm + paper + camera)",
         color=PRIMARY, title_size=16, sub_size=11)
    arrow(s, M + 3.35, 2.45, M + 8.55, 2.45, color=VIOLET, lw=2.2,
          label="action  aₜ   (move pen by dx, dy)", label_w=4.2, label_dy=-0.36)
    arrow(s, M + 8.55, 3.05, M + 3.35, 3.05, color=ACCENT, lw=2.2,
          label="observation  sₜ₊₁   (image of target + drawing + pen)", label_w=5.0,
          label_dy=0.06)
    arrow(s, M + 8.55, 3.45, M + 3.35, 3.45, color=GOOD, lw=2.2,
          label="reward  rₜ₊₁   (did IoU go up?)", label_w=4.2, label_dy=0.06)
    defs = [("STATE / OBSERVATION", "What the agent can see right now.", ACCENT),
            ("ACTION", "What the agent decides to do.", VIOLET),
            ("REWARD", "One number: how good was that step.", GOOD),
            ("EPISODE", "One attempt, start to end (240 steps).", PRIMARY),
            ("POLICY  π", "The agent's rule: observation → action.", VIOLET)]
    w = (CW - 4 * 0.15) / 5
    for i, (t, d, c) in enumerate(defs):
        card(s, M + i * (w + 0.15), 4.25, w, 1.30, t, [d], accent=c, body_size=11.5,
             title_size=11)
    strip(s, "Goal of learning: find the policy that collects the most total reward over an "
          "episode — not the most reward right now.", VIOLET, y=5.85)
    analogy(s, "Training a dog: it does something (action), gets a treat or not (reward), and "
          "slowly learns which behaviours lead to treats (policy).", y=6.42)
    note(s, """
RL ka loop: agent (dimaag) environment (duniya) ko dekhta hai, ek action leta hai, aur badle
me use naya observation aur ek reward milta hai. Yeh baar-baar chalta hai.

Hamare case me: observation = target, ab tak ki drawing aur pen ki jagah wali image. Action =
pen ko dx, dy khiskao. Reward = kya IoU badha? Episode = ek poori koshish (240 steps). Policy =
agent ka niyam: yeh dekha to yeh karo.

Dhyan do: lakshya turant reward nahi, poore episode ka kul reward hai. Kutte ki training jaisa:
woh kuch karta hai, treat milti hai ya nahi, aur dheere-dheere seekhta hai kaunsa vyavhaar treat
dilata hai.
""")


def mdp(prs):
    steps(prs, "02 · formal", "The Markov Decision Process (MDP)",
          "The mathematical object every RL algorithm is built on.",
          [("tuple", "MDP = ( S, A, P, R, γ )",
            ["S = set of states, A = set of actions.",
             "P(s′ | s, a) = probability of landing in s′ after doing a in s.",
             "R(s, a) = reward; γ in [0, 1) = discount factor."]),
           ("Markov", "P(sₜ₊₁ | sₜ, aₜ, sₜ₋₁, …, s₀) = P(sₜ₊₁ | sₜ, aₜ)",
            ["The future depends only on the present state, not on how we got there.",
             "Our observation (target + drawing so far + pen) is designed so this holds."]),
           ("trajectory", "τ = (s₀, a₀, r₁, s₁, a₁, r₂, …, s_T)",
            ["One episode written out. RL samples many trajectories and learns from them."]),
           ("broke", "two identical canvases, 5 vs 100 steps left → different best actions",
            ["Our first observation had no clock, so the task was NOT fully Markov. Adding "
             "remaining time as a 4th channel (O1) fixed it — and gave a modest, shape-dependent +0.039 IoU."])],
          take="If the observation does not contain everything that matters, the agent is "
               "partially blind — 'partially observable'.",
          notes="""
MDP RL ki ganit wali neev hai: states, actions, transition probability (yeh karne par kahan
pahunchoge), reward, aur discount factor gamma.

Markov property: aage kya hoga, yeh sirf abhi ki state par depend karta hai, itihaas par
nahi. Hamari observation is tarah banayi gayi ki yeh sach rahe.

Ek jagah yeh toot gaya tha: episode 240 steps par khatam hota hai, par agent ko ghadi nahi
dikhti thi. Do bilkul same drawings — ek me 5 step bache, ek me 100 — inke liye best action
alag hai, par agent farak nahi kar sakta. Isse "partially observable" kehte hain. Remaining
time ka 4th channel jodne (O1) se yeh theek hua aur ~0.04 IoU ka fayda hua.
""")


def returns(prs):
    steps(prs, "02 · formal", "Return and discounting: what 'total reward' means",
          "The quantity the agent actually tries to maximise.",
          [("return", "Gₜ = rₜ₊₁ + γ·rₜ₊₂ + γ²·rₜ₊₃ + …  =  Σₖ γᵏ · rₜ₊ₖ₊₁",
            ["Sum of all future rewards, each shrunk by γ for every step of delay."]),
           ("example", "r = 1, 1, 1 with γ = 0.9  →  G = 1 + 0.9 + 0.81 = 2.71",
            ["Rewards far in the future count a little less than rewards now."]),
           ("horizon", "effective horizon ≈ 1 / (1 − γ)  →  γ = 0.99 gives ≈ 100 steps",
            ["We use γ = 0.99: the agent plans about 100 steps ahead — enough for a "
             "~30–40-step shape plus slack."]),
           ("objective", "J(π) = E_τ∼π [ G₀ ]",
            ["Expected return when acting with policy π. Every algorithm in this deck is a "
             "way of making J bigger."])],
          take="Our reward is an IoU difference, so the undiscounted return telescopes to the "
               "final IoU — maximising return = maximising drawing accuracy (proof: Section 7).",
          notes="""
Return = aage ke saare rewards ka jod, par har step der ke liye gamma se thoda chhota karke.
Example: teen baar reward 1, gamma 0.9 → 1 + 0.9 + 0.81 = 2.71.

Gamma 0.99 ka matlab agent lagbhag 100 steps aage tak sochta hai (1/(1−gamma)). Hamari shape
30–40 steps me ban jaati hai, to yeh kaafi hai.

J(pi) = expected return — har algorithm bas isi ko badhane ka tareeka hai.

Hamara reward IoU ka badlav hai (pichle step se kitna badha). Isko jodne par beech ke terms
cancel ho jaate hain aur bachta hai final IoU. Matlab reward maximise karna = drawing ki
accuracy maximise karna. Iska proof Section 7 me hai.
""")


def policy(prs):
    steps(prs, "02 · formal", "The policy: how the agent chooses actions",
          "Our actions are continuous numbers, so the policy outputs a probability distribution.",
          [("deterministic", "a = μθ(s)",
            ["Always the same action for the same observation. Used at evaluation time "
             "(deterministic=True) to score the agent."]),
           ("stochastic", "a ∼ πθ(a | s) = 𝒩( μθ(s), σ² )",
            ["During training the network outputs a mean μ; the action is sampled around it "
             "with spread σ. The randomness is how it explores."]),
           ("log-prob", "log πθ(a|s) = −(a − μ)² / (2σ²) − log σ − ½ log 2π   (per dimension)",
            ["The policy-gradient maths needs this quantity; for a Gaussian it is cheap and exact."]),
           ("ours", "μ ∈ ℝ³ for [dx, dy, pen]   ·   learned log σ ≈ (−0.66, −0.65, −0.14)",
            ["Measured on the trained square agent: σ ≈ 0.52 for dx, dy — it still explores "
             "about half the action range. θ = all 602,791 network weights."])],
          take="θ (theta) always means 'the network's weights'. Learning = changing θ.",
          notes="""
Policy agent ka niyam hai. Hamare actions continuous numbers hain (dx, dy), isliye policy ek
probability distribution deti hai — ek Gaussian (bell curve). Network mean mu batata hai, aur
action uske aas-paas random sample hota hai, spread sigma ke saath. Yahi randomness exploration
hai — naye tareeke aazmana.

Evaluation me deterministic mode use karte hain — seedha mean wala action, koi random nahi.

Log-probability formula PPO ke math me chahiye; Gaussian ke liye yeh aasaan hai.
Trained square agent me sigma lagbhag 0.52 hai dx, dy ke liye. Theta matlab network ke saare
weights — 602,791 numbers. Seekhna = theta ko badalna.
""")


def values(prs):
    steps(prs, "02 · formal", "Value functions: how good is a situation?",
          "The critic's job — estimating future reward so the actor knows what was a good move.",
          [("V", "Vπ(s) = E[ Gₜ | sₜ = s ]",
            ["State value: expected return from state s if we follow π from here."]),
           ("Q", "Qπ(s, a) = E[ Gₜ | sₜ = s, aₜ = a ]",
            ["Action value: expected return if we take action a now, then follow π."]),
           ("A", "Aπ(s, a) = Qπ(s, a) − Vπ(s)",
            ["Advantage: how much BETTER action a is than the policy's average action. "
             "Positive → do it more often; negative → less often."]),
           ("Bellman", ["Vπ(s) = E [ r + γ · Vπ(s′) ]", "(expectation over a ∼ π and s′ ∼ P)"],
            ["Value now = reward now + discounted value of where you land. This recursion "
             "is what lets a network learn V from single steps."]),
           ("TD error", "δₜ = rₜ₊₁ + γ·V(sₜ₊₁) − V(sₜ)",
            ["'Surprise': how much better the step went than predicted. A one-step estimate "
             "of the advantage — the building block of GAE (Section 3)."])],
          notes="""
Value function batata hai koi situation kitni achhi hai. V(s) = is state se aage kitna reward
milne ki ummeed. Q(s, a) = yeh action lekar phir policy follow karo to kitna. Advantage A = Q − V
= yeh action average se kitna behtar hai. Advantage positive → yeh action zyada karo; negative →
kam karo.

Bellman equation: abhi ki value = abhi ka reward + agle state ki discounted value. Is recursion
ki wajah se network ek-ek step se V seekh sakta hai.

TD error delta = "surprise" — step umeed se kitna behtar gaya. Yeh advantage ka ek-step
andaaza hai, aur PPO ka GAE isi se banta hai.
""")


def explore(prs):
    concept(prs, "02 · rl basics", "Exploration vs exploitation",
            "The central dilemma: use what you know, or try something new?",
            ["Exploitation = pick the action you currently believe is best.",
             "Exploration = try something else, in case it is better.",
             "Too little exploration: stuck forever on the first thing that half-worked "
             "(we saw this — the 'draw nothing' and 'don't move' traps).",
             "Too much: never settles, wastes samples on random scribbles.",
             "Gaussian policy: σ controls exploration. PPO adds an entropy bonus "
             "(ent_coef = 0.02 in our runs) so σ does not collapse too early.",
             "A side effect we measured: the residual randomness makes the agent drift past "
             "the finished shape — part of the 'overshoot' story (Section 8)."],
            cards=[("ENTROPY", ["H(π) = −E[ log π(a|s) ]", "Gaussian: H = ½·log(2πe·σ²) per "
                                "dimension — bigger σ, more entropy.",
                                "Rewarding entropy = rewarding 'keep options open'."], VIOLET),
                   ("SAC TAKES IT FURTHER", ["SAC puts entropy directly into the objective "
                                             "and tunes its weight automatically (Section 4)."],
                    ACCENT)],
            analog="Choosing a restaurant: always going to your favourite is exploitation; "
                   "trying a new one sometimes is exploration — that is how you find a better favourite.",
            notes="""
Exploration vs exploitation RL ki sabse basic dilemma hai. Exploitation = jo abhi best lagta hai
wahi karo. Exploration = kuch naya aazmao, shayad behtar ho.

Kam exploration → pehli adhi-kaam-wali cheez par atak jaao. Hamare project me yeh hua tha —
agent ne seekha "kuch mat banao" ya "hilo mat" kyunki usse penalty nahi milti thi.
Zyada exploration → kabhi settle nahi hota.

Gaussian policy me sigma exploration control karta hai. PPO me entropy bonus (0.02) hai taaki
sigma jaldi zero na ho. Iska ek side effect hamne naapa: bachi hui randomness ki wajah se agent
shape poori hone ke baad bhi thoda aage nikal jaata hai — "overshoot" (Section 8).

Analogy: favourite restaurant hamesha jaana exploitation; kabhi naya try karna exploration.
""")


def families(prs):
    tabular(prs, "02 · rl basics", "The family tree of RL algorithms",
            "Where PPO and SAC sit — two answers to the same question.",
            ["family", "what it learns", "examples", "action type", "on / off-policy"],
            [["value-based", "Q(s,a); act = argmax Q", "Q-learning, DQN", "discrete", "off"],
             ["policy gradient", "π directly, from returns", "REINFORCE", "any", "on"],
             ["actor-critic (on-policy)", "π (actor) + V (critic)", "A2C, TRPO, PPO", "any", "on"],
             ["actor-critic (off-policy)", "π + Q, replay buffer", "DDPG, TD3, SAC", "continuous", "off"],
             ["model-based", "a model of P, then plans", "Dreamer, MBPO", "any", "either"]],
            colw=[2.6, 3.2, 2.6, 1.6, 1.8],
            cell_colors={(2, 2): VIOLET, (3, 2): ACCENT},
            below=["On-policy: learns only from data collected by the CURRENT policy, then "
                   "throws it away. Simple and stable, but sample-hungry.",
                   "Off-policy: stores all experience in a replay buffer and reuses it many "
                   "times. Far more sample-efficient, but more moving parts and hyperparameters.",
                   "Model-free (PPO, SAC): no attempt to learn the physics; just learn what to do."],
            take="PPO = on-policy actor-critic. SAC = off-policy actor-critic. Both handle our "
                 "continuous [dx, dy, pen] actions.", take_color=VIOLET,
            notes="""
RL algorithms ka family tree. Value-based (DQN): har action ki value seekho, sabse badi chuno —
discrete actions ke liye. Policy gradient (REINFORCE): seedha policy seekho. Actor-critic: dono —
actor policy hai, critic value function.

Do bade group: on-policy (PPO) — sirf abhi ki policy ka data use karta hai, phir phenk deta hai.
Simple aur stable par zyada samples chahiye. Off-policy (SAC) — saara anubhav ek replay buffer
me rakhta hai aur baar-baar use karta hai. Sample-efficient par zyada parts aur settings.

PPO aur SAC dono model-free hain: physics seekhne ki koshish nahi, sirf kya karna hai woh seekho.
Dono continuous actions sambhal lete hain.
""")


def nn_basics(prs):
    steps(prs, "02 · neural networks", "Neural networks in four equations",
          "The function approximator that turns an image into an action.",
          [("neuron", "y = f( w₁x₁ + w₂x₂ + … + wₙxₙ + b ) = f( wᵀx + b )",
            ["Weighted sum of inputs plus a bias, passed through a non-linearity f.",
             "ReLU: f(z) = max(0, z) — the one our network uses."]),
           ("layer", "h = f( W·x + b )   ·   network = layer ∘ layer ∘ … ∘ layer",
            ["Many neurons side by side form a layer; stacking layers lets the network "
             "represent complicated functions."]),
           ("loss", "L(θ) = how wrong the network is   (a single number)",
            ["In RL there is no 'right answer', so the loss is built from rewards — "
             "that is exactly what PPO's objective is (Section 3)."]),
           ("learning", "θ ← θ − η · ∇θ L(θ)",
            ["Gradient descent: nudge every weight slightly in the direction that reduces "
             "the loss. η = learning rate (3×10⁻⁴ for us). Backpropagation computes ∇θ L "
             "efficiently with the chain rule; Adam is the improved version we use."])],

          notes="""
Neural network chaar equations me. Ek neuron: inputs ka weighted sum + bias, phir ek
non-linearity (ReLU = negative ko zero kar do). Kai neurons = ek layer; kai layers = network.

Loss = network kitna galat hai, ek number. Supervised learning me sahi jawab se compare hota hai;
RL me sahi jawab nahi hota, isliye loss rewards se banta hai — yahi PPO ka objective hai.

Seekhna = gradient descent: har weight ko thoda us direction me khiskao jahan loss kam ho.
Learning rate 0.0003. Backpropagation chain rule se yeh gradient efficiently nikalta hai;
Adam iska behtar version hai jo hum use karte hain.
""")


def cnn(prs):
    s = slide(prs, "Convolutional neural networks — seeing the drawing",
              "02 · neural networks",
              "Our policy reads a 3 × 64 × 64 image. This is exactly the network that does it.")
    pts = ["A convolution slides a small filter (e.g. 8×8) over the image and responds where "
           "its pattern appears — edges, corners, ink near the pen.",
           "Same filter everywhere → a stroke is recognised wherever it is (and far fewer weights).",
           "Stride = how far the filter jumps; it shrinks the image layer by layer.",
           "This is SB3's 'NatureCNN' (from the DQN Atari paper), used unchanged via "
           "CnnPolicy. Actor and critic share it; only the last layers differ."]
    bullets(s, pts, M, 1.62, 4.6, 4.6, size=12.5)
    layers = [("input", "3 × 64 × 64", "target · drawing · pen", ACCENT),
              ("conv 8×8 /4", "32 × 15 × 15", "6,176 weights", VIOLET),
              ("conv 4×4 /2", "64 × 6 × 6", "32,832", VIOLET),
              ("conv 3×3 /1", "64 × 4 × 4", "36,928", VIOLET),
              ("dense", "512", "524,800", PRIMARY)]
    x0, gap = M + 4.85, 0.16
    bw = (CW - 4.85 - 4 * gap) / 5
    for i, (t, shp, sub, c) in enumerate(layers):
        x = x0 + i * (bw + gap)
        node(s, x, 1.70, bw, 1.60, t, shp + "\n" + sub, color=c, title_size=10.5, sub_size=9)
        if i < len(layers) - 1:
            arrow(s, x + bw + 0.01, 2.50, x + bw + gap - 0.01, 2.50, lw=1.4)
    # heads, right-aligned under the dense layer
    right = M + CW
    node(s, right - 1.55, 3.75, 1.55, 1.0, "value head", "512 → 1:  V(s)", color=GOOD,
         title_size=10.5, sub_size=9)
    node(s, right - 1.55 - 0.2 - 2.6, 3.75, 2.6, 1.0, "policy head",
         "512 → 3 means (dx, dy, pen)\n+ 3 learned log σ", color=VIOLET, title_size=10.5,
         sub_size=9)
    dx = x0 + 4 * (bw + gap) + bw / 2
    arrow(s, dx, 3.32, right - 1.55 - 0.2 - 1.3, 3.73, lw=1.3)
    arrow(s, dx, 3.32, right - 0.78, 3.73, lw=1.3)
    card(s, x0, 5.00, CW - 4.85, 1.25, "SIZE CHECK (loaded from models/ppo_square_kin.zip)",
         ["602,791 trainable numbers in total. 87% of them sit in the single dense layer. "
          "Small by modern standards — which is why a CPU is enough."], accent=GOOD,
         body_size=11.5)
    strip(s, "The image is the state; the CNN is how a 'picture of the paper' becomes a "
          "decision about where to move the pen.", PRIMARY)
    note(s, """
Agent ki observation ek image hai — 3 channels (target, ab tak ki drawing, pen ki jagah), 64x64.
Image padhne ke liye CNN use hota hai. Convolution ek chhota filter hai jo image par
khiskta hai aur jahan uska pattern mile wahan react karta hai — edge, corner, pen ke paas ink.
Ek hi filter poori image par → stroke kahin bhi ho, pehchaan liya jaata hai.

Yeh SB3 ka NatureCNN hai (DQN Atari paper wala), bina badlav. 3 conv layers image ko 64x64 se
4x4 tak chhota karti hain, phir 512 numbers ki dense layer. Uske baad do heads: policy head
(dx, dy, pen ka mean aur sigma) aur value head (V(s)). Actor aur critic ek hi CNN share karte hain.

Kul 602,791 parameters — maine trained model load karke gine. 87% ek hi dense layer me hain.
Modern standard se chhota, isliye CPU kaafi hai.
""")


def ours(prs):
    tabular(prs, "02 · mapping", "The RL vocabulary, mapped onto RoboSketch-RL",
            "Every abstract term from this section has a concrete counterpart in rl/draw_env.py.",
            ["RL term", "in RoboSketch-RL", "detail"],
            [["environment", "DrawEnv (Gymnasium)", "reset() and step(action); PyBullet arm optional"],
             ["observation sₜ", "3-channel 64×64 image", "target · drawn-so-far · pen marker (+ time, if O1)"],
             ["action aₜ", "[dx, dy, pen_down]", "dx, dy in [−1, 1] × 1.4 cm; pen kept down on the first rung"],
             ["reward rₜ", "10·ΔIoU + 0.4·Δφ − 0.02·|Δa|", "IoU gain + proximity shaping − jerkiness"],
             ["episode", "240 steps (max_steps)", "ends early only on IoU ≥ 0.60 (never reached)"],
             ["policy πθ", "CNN → Gaussian over actions", "602,791 weights, trained by PPO"],
             ["γ", "0.99", "≈ 100-step planning horizon"],
             ["evaluation", "true IoU of the real canvas", "always truth, whatever the agent saw"]],
            colw=[2.3, 3.6, 6.2], size=11.5, row_h=0.42,
            take="Scoring is ALWAYS the true IoU — a policy is never credited for a camera "
                 "that happens to flatter it.", take_color=GOOD,
            notes="""
Is section ke saare shabd hamare code me kahan hain: environment = DrawEnv. Observation = 3
channel 64x64 image. Action = dx, dy, pen_down (pehle task me pen hamesha neeche). Reward =
10 × IoU ka badlav + proximity shaping − jhatke wali movement ka penalty. Episode = 240 steps.
Policy = CNN jo Gaussian deta hai. Gamma = 0.99.

Sabse zaroori niyam: score hamesha asli canvas ka true IoU hota hai — agent ne camera se kuch
bhi dekha ho. Isse koi agent "camera ko bewakoof bana kar" achha score nahi le sakta.
""")


def build(prs):
    section(prs, 2, "Machine learning & RL basics",
            "From 'what is learning?' to the exact vocabulary RL uses — MDPs, returns, "
            "policies, values — and the neural network that holds the policy.",
            ["Three kinds of ML", "The RL loop", "MDP, return, discount",
             "Policy, value, advantage", "Neural networks & CNNs"])
    ml_kinds(prs)
    rl_loop(prs)
    mdp(prs)
    returns(prs)
    policy(prs)
    values(prs)
    explore(prs)
    families(prs)
    nn_basics(prs)
    cnn(prs)
    ours(prs)
