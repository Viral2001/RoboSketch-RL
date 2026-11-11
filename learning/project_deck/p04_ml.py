"""Section 4 - machine-learning basics."""
from kit import *  # noqa: F401,F403
from teach_figs import TOY


def build(prs, toc):
    section(prs, 4, "Machine-learning basics",
            "The agent's 'brain' is a neural network. Here: what a network is, how it learns by "
            "gradient descent, and why a convolutional network is the right tool for image observations.",
            ["Function approximation", "Neurons and layers", "Loss and gradient descent",
             "Backpropagation", "Convolution and CNNs", "Generalisation"],
            """
Section 4: machine learning ki basics - sirf utna jitna RL samajhne ke liye chahiye. Neural network
ek bada function hai jiske parameters (weights) gradient descent se adjust hote hain. Images ke
liye convolutional network (CNN) kyun - yeh is section ka main "why" hai.""", toc)

    concept(prs, "04 · ML", "Function approximation: why a neural network at all", None,
            ["The agent must map an observation (a 64×64×3 image) to an action (dx, dy, pen).",
             "A lookup table is hopeless: the number of possible images is astronomically large, and "
             "the agent will almost never see the exact same image twice.",
             "Instead we learn a function f_θ(observation) with parameters θ (weights) that "
             "GENERALISES: similar images → similar actions.",
             "A neural network is a flexible family of such functions; training = choosing θ.",
             "In PPO the network has two outputs ('heads'): the policy (which action) and the value "
             "(how good this situation is). Section 6 explains both."],
            cards=[("PHYSICS ANALOGY", ["Like fitting a curve to data - but with ~a million "
                                        "parameters and an image as the input."], PRIMARY),
                   ("WHAT IT CANNOT DO", ["Generalise far outside what it was trained on: Section 9 "
                                          "shows our agents lose most accuracy on resized/rotated shapes."], WARN)],
            notes="""
Agent ko image dekh kar action dena hai. Table bana do (har image -> action)? Possible images
itni zyada hain ki koi table nahi ban sakti, aur same image dobara milegi bhi nahi. Isliye ek
function seekhte hain f_theta(image) -> action, jiske parameters theta hain. Achha function
"generalise" karta hai: milti-julti images par milte-julte actions.

Neural network functions ka ek bahut flexible family hai. Training = theta chunna.

Physics analogy: data par curve fit karna (least squares) - bas yahan parameters laakhon hain aur
input ek image hai.

Limit (aage aayega): network wahi tak achha hai jahan tak usne dekha hai. Hamare agents naye size/
rotation wale shapes par kaafi accuracy kho dete hain - Section 9 me generalisation result.
""", source="rl/draw_env.py observation/action spaces; RESEARCH_LOG '### Generalisation RESULT'")

    eq_fig_slide(prs, "04 · networks", "A neuron, a layer, a network",
                 "Each layer: multiply by weights, add a bias, apply a simple non-linear function.",
                 r"h = \sigma\left(Wx+b\right),\qquad f_\theta(x)=W_L\,\sigma\left(\cdots\sigma\left(W_1x+b_1\right)\cdots\right)+b_L",
                 "activations.png",
                 [(r"x", "input vector (e.g. image pixels, flattened)"),
                  (r"W,\ b", "weight matrix and bias vector - the learned parameters θ"),
                  (r"\sigma", "activation: ReLU max(0, z) or tanh"),
                  (r"h", "the layer's output, fed to the next layer")],
                 after=["Without σ, stacked layers collapse into one linear map - no curves.",
                        "SB3's CNN uses ReLU after every layer."],
                 why_text="Layers of 'linear + bend' can approximate very complex maps - here, "
                          "'what I see' → 'where to move the pen'.",
                 label="Neural-network layer", group="Machine learning", fig_w=5.6,
                 notes="""
Ek neuron: inputs ka weighted sum + bias, phir ek non-linear function (activation). Ek layer =
bahut saare neurons ek saath = matrix W se multiply + b add + sigma. Network = kai layers ek ke
baad ek.

Non-linearity kyun? Agar sigma na ho, to kitni bhi linear layers milao, result ek hi linear map
hoga - seedhi lines ke alawa kuch nahi seekh sakta. ReLU (max(0,z)) ya tanh "mod" (bend) dete
hain; inko jodkar complex shapes ban jaati hain.

SB3 ka CNN har layer ke baad ReLU use karta hai. Weights W aur biases b hi "theta" hain jo
training me badalte hain.
""", source="stable_baselines3 2.9.0 torch_layers.NatureCNN (ReLU after each layer); figure = toy")

    gd = TOY["gd"]
    eq_fig_slide(prs, "04 · learning", "Loss and gradient descent: how a network learns",
                 "Define a number that is small when the network is right; walk downhill on it.",
                 r"\theta \leftarrow \theta - \alpha\,\nabla_\theta L(\theta)",
                 "grad_descent.png",
                 [(r"L(\theta)", "loss: how wrong the network is (lower is better)"),
                  (r"\nabla_\theta L", "gradient: direction of steepest increase of L"),
                  (r"\alpha", "learning rate: step size (ours: 3e-4)"),
                  (r"\theta", "all weights and biases")],
                 after=[f"Toy: L = (θ-2)², α = 0.3, start θ = -1 → {gd[1]}, {gd[2]}, {gd[3]} … → 2",
                        "In practice: Adam (an adaptive version), on mini-batches of data."],
                 why_text="Every learning method in this project - PPO's policy and value, the BC warm start, "
                          "the digit recogniser - is this one update rule with a different loss.",
                 label="Gradient descent", group="Machine learning", fig_w=6.0,
                 notes="""
Loss = ek number jo batata hai network kitna galat hai. Gradient = woh direction jidhar loss
sabse tezi se badhta hai. To ulti direction me chhota sa step lo: theta <- theta - alpha * grad.
Pahaad se neeche utarna, aankhon par patti bandh ke, sirf dhalan mehsoos karke.

Learning rate alpha: bahut bada -> overshoot/oscillate; bahut chhota -> bahut slow. Hamare PPO me
3e-4 (0.0003), SB3 ka standard.

Toy (script se): L = (theta-2)^2, alpha 0.3, theta -1 se shuru -> 0.8 -> 1.52 -> 1.808 ... -> 2.

Asli me "Adam" optimizer use hota hai (har parameter ka apna adaptive step) aur data ke chhote
hisson (mini-batches) par gradient nikalte hain - isliye "stochastic" gradient descent.

Yaad rakho: PPO, BC warm start, digit recogniser - sab isi rule ko alag loss ke saath use karte hain.
""", source="rl/experiment.py PPO(learning_rate=3e-4); toy numbers by teach_figs.py")

    steps_slide(prs, "04 · learning", "Backpropagation: the chain rule, applied layer by layer",
                "How the gradient of the loss reaches every weight, even deep inside the network.",
                [("forward", r"h_1=\sigma(W_1x),\quad h_2=\sigma(W_2h_1),\quad L=\ell(h_2)",
                  "Run the input through the layers and compute the loss; remember the intermediate values."),
                 ("chain rule", r"\frac{\partial L}{\partial W_1}=\frac{\partial L}{\partial h_2}\,\frac{\partial h_2}{\partial h_1}\,\frac{\partial h_1}{\partial W_1}",
                  "The effect of an early weight on the loss = product of local effects along the path.",
                  "Chain rule (backpropagation)"),
                 ("backward", r"\delta_{k}=\left(W_{k+1}^{\mathrm{T}}\,\delta_{k+1}\right)\odot\sigma'(z_k)",
                  "Pass the error signal δ backwards, one layer at a time - each layer reuses the "
                  "next layer's δ. PyTorch does all of this automatically ('autograd').")],
                take="You never write gradients by hand here: PyTorch computes them; the design choices "
                     "are the LOSS and the ARCHITECTURE.", group="Machine learning",
                notes="""
Backpropagation = chain rule, bas. Forward pass me input layers se guzarta hai aur loss nikalta
hai. Backward pass me hum poochhte hain: pehli layer ka weight thoda badle to loss kitna badlega?
Jawab = raste ke saare local derivatives ka product (chain rule).

Efficient trick: error signal delta ko peeche ki taraf bhejo; har layer agle wali layer ka delta
reuse karti hai - isliye poora gradient ek hi backward pass me mil jaata hai.

Practically: PyTorch (jis par SB3 bana hai) yeh automatically karta hai ("autograd"). Hamara kaam
sirf loss define karna aur architecture chunna hai. Interview me itna bolna kaafi hai.
""", source="standard backpropagation; stable_baselines3 is built on PyTorch")

    c = TOY["cnn"]
    eq_fig_slide(prs, "04 · CNN", "Convolution: one small filter slid over the whole image",
                 "The same 3×3 (or 8×8) weights are reused at every position: weight sharing.",
                 r"S(i,j)=\sum_{m}\sum_{n} I(i+m,\,j+n)\,K(m,n)",
                 "conv_toy.png",
                 [(r"I", "input image (or previous feature map)"),
                  (r"K", "kernel / filter: a small learned weight grid"),
                  (r"S", "output feature map: where the pattern is found"),
                  (r"(i,j)", "output position")],
                 after=["Toy: a vertical-edge kernel lights up exactly where the edge is.",
                        "A CNN learns its kernels: edges, corners, 'ink near target' …"],
                 why_text="Drawing is about local spatial patterns (is there ink on the target HERE?). "
                          "Convolution detects a pattern anywhere with few weights.",
                 label="2-D convolution", group="Machine learning", fig_w=6.6,
                 notes="""
Convolution: ek chhota filter (kernel), jaise 3x3 numbers, poori image par slide karo; har jagah
filter aur image ke patch ka element-wise product jodo -> output ka ek pixel. Output ko feature
map kehte hain - batata hai pattern kahan mila.

Toy (script se): image me ek vertical edge hai (left 0, right 1). Kernel [-1 0 1] har row me -
yeh horizontal change detect karta hai. Output exactly edge ki jagah par bada hai.

CNN kyun? (1) Weight sharing: wahi chhota filter har jagah - kam parameters, aur pattern kahin bhi
ho pakda jaata hai. (2) Locality: drawing me sawaal local hai - "yahan target hai, kya yahan ink
hai?" Ek fully-connected network ko 12288 pixel inputs ke liye bahut zyada weights chahiye honge
aur woh spatial structure nahi samjhega.

CNN apne kernels khud seekhta hai - edges, corners, "target ke paas ink" jaise patterns.
""", source="standard convolution; toy numbers by teach_figs.py")

    steps_slide(prs, "04 · CNN", "The network inside our agent (SB3 'CnnPolicy')",
                "Stable-Baselines3 NatureCNN, fed our 64 × 64 × 3 observation (pixels scaled to 0-1).",
                [("size rule", r"n_{out}=\left\lfloor\frac{n_{in}-k}{s}\right\rfloor+1",
                  "k = kernel size, s = stride (step of the slide), no padding.", "Conv output size"),
                 ("3 conv layers", r"64\ \rightarrow\ %d\ \rightarrow\ %d\ \rightarrow\ %d" % tuple(c["sizes"][1:]),
                  ["Filters: 32 of 8×8 stride 4, then 64 of 4×4 stride 2, then 64 of 3×3 stride 1.",
                   f"Feature maps shrink {c['sizes'][0]} → {c['sizes'][1]} → {c['sizes'][2]} → {c['sizes'][3]} (computed with the rule).",
                   f"Flatten: 64 × {c['sizes'][3]} × {c['sizes'][3]} = {c['flat']} numbers."]),
                 ("heads", r"\mathrm{features}\in\mathbb{R}^{512}\ \rightarrow\ \mu_\theta(s)\in\mathbb{R}^{3},\ \ V_\phi(s)\in\mathbb{R}",
                  ["A linear layer + ReLU gives 512 features.",
                   "Policy head: the mean of each action dim. Value head: one number."])],
                take="We did not design a network: we used SB3's standard image policy, so results reflect "
                     "the reward/observation, not a tuned architecture.", group="Machine learning",
                notes="""
Hamare agent ka network SB3 ka "NatureCNN" hai (DQN Atari paper wala). Teen conv layers:
32 filters 8x8 stride 4, 64 filters 4x4 stride 2, 64 filters 3x3 stride 1, har ek ke baad ReLU.
Phir flatten aur ek linear layer -> 512 features. Uske upar do chhoti linear "heads": policy
(teen action dims ka mean) aur value (ek number).

Size formula: n_out = floor((n_in - k)/s) + 1. 64x64 input par: 64 -> 15 -> 6 -> 4 (script ne
calculate kiya). Flatten = 64*4*4 = 1024.

Design choice ka "why": humne network design nahi kiya - standard SB3 CnnPolicy use kiya. Isse
results reward/observation ke baare me hain, kisi tuned architecture ke baare me nahi. Aur
"CnnPolicy" se pixels automatically 0-1 me scale hote hain.

(O3 experiment me 5 channels - coordinate planes - diye gaye; SB3 ne 5-channel NatureCNN banaya.)
""", source="stable_baselines3 2.9.0 common/torch_layers.py NatureCNN (32@8 s4, 64@4 s2, 64@3 s1, features_dim 512); "
            "rl/experiment.py PPO('CnnPolicy'); sizes computed by teach_figs.py")

    concept(prs, "04 · generalisation", "Training data vs new data: generalisation", None,
            ["A model is judged on data it did NOT train on. Fitting the training set well is not enough.",
             "Overfitting / memorising: great on what it saw, poor on anything new.",
             "In our project 'data' = the targets the agent practised on. Most experiments use ONE fixed "
             "picture per shape - so they test drawing THAT picture.",
             "Section 9 measures it: agents trained on one picture lose a lot on resized / rotated "
             "versions; training on a family helps a little; a pen-centred view helps a lot.",
             "Same logic for cameras: test on a held-out camera, never only the training camera."],
            cards=[("HELD-OUT SETS USED", ["Targets: size 0.6-0.8 and rotation 15-45° (outside the "
                                          "training range). Cameras: the HELDOUT distribution."], ACCENT),
                   ("WORDING", ["Claims hold 'for the fixed-picture setting'. Never write 'the agent "
                                "draws arbitrary shapes'."], WARN)],
            notes="""
ML ka sabse bada sawaal: jo data model ne nahi dekha, us par kaisa karta hai? Training data par
achha hona kaafi nahi - woh "ratta" (memorisation) bhi ho sakta hai.

Hamare project me "data" = woh targets jin par agent practice karta hai. Zyada-tar experiments me
har shape ki EK fixed picture hai. To woh results "us picture ko draw karna" test karte hain.

Section 9 me naapa: ek picture par trained agent thoda bade/chhote ya ghoome hue shape par bahut
accuracy kho deta hai. Family (size/rotation range) par training thoda help karti hai; pen-centred
(ego) view bahut help karta hai.

Cameras ke liye bhi wahi logic: held-out camera par test karo.

Interview wording: "claims hold for the fixed-picture setting" - "arbitrary shapes" kabhi mat bolna.
""", source="rl/targets.py PARAM_RANGES; docs/PAPER_PLAN.md section 4 item 4; RESEARCH_LOG '### Generalisation RESULT'")
