"""Part 3 - the mathematics of PPO (derived step by step) and SAC, and the comparison."""
from gk import (ACCENT, BAD, BODY, CW, GOOD, INK, LINE, M, MUTED, PRIMARY, SLATE, VIOLET,
                WARN, WASH, WHITE, arrow, bullets, card, chip, code, concept, grid, node,
                note, rect, section, slide, steps, strip, tabular, txt, analogy)


# ------------------------------------------------------------------ PPO --------
def ppo(prs):
    section(prs, 3, "The mathematics of PPO",
            "Proximal Policy Optimisation — the algorithm that trains every agent in this "
            "project — derived from scratch, one step at a time, with nothing skipped.",
            ["The objective J(θ)", "Log-derivative trick", "REINFORCE & baselines",
             "Actor-critic & GAE", "Importance sampling", "The clipped objective",
             "Our hyperparameters"])

    steps(prs, "03 · ppo · step 0", "What we want: climb the hill of expected return",
          "We cannot differentiate through the simulator — so how do we get a gradient?",
          [("goal", "θ* = argmax_θ  J(θ),     J(θ) = E_τ∼πθ [ R(τ) ]",
            ["Find the network weights θ whose policy collects the most reward on average.",
             "R(τ) = total reward of one episode τ."]),
           ("ascent", "θ ← θ + α · ∇θ J(θ)",
            ["Gradient ascent: step uphill. We need ∇θ J — how J changes when θ changes."]),
           ("problem", "J(θ) = ∫ pθ(τ) · R(τ) dτ",
            ["R(τ) comes out of the simulator (physics, ink, IoU) — not a formula we can "
             "differentiate. And τ is sampled, which is not differentiable either.",
             "Trick needed: move the gradient onto something we DO control — the policy."])],
          take="The whole of policy-gradient RL is one idea: rewrite ∇J as an average we can "
               "estimate from episodes we have already played.",
          notes="""
Lakshya: aise weights theta dhoondo jinki policy average me sabse zyada reward laaye. Iske liye
gradient ascent — pahaadi par upar chadhna: theta ← theta + alpha × gradient.

Dikkat: J(theta) ke andar R(tau) simulator se aata hai — physics, ink, IoU. Iska derivative
seedha nahi le sakte. Aur episode random sample hota hai.

Isliye ek trick chahiye: gradient ko us cheez par le jao jo humare control me hai — policy.
Agle slides me wahi trick step by step.
""")

    steps(prs, "03 · ppo · step 1", "The log-derivative trick",
          "A one-line identity from calculus that makes the whole field work.",
          [("identity", "∇θ pθ(τ) = pθ(τ) · ∇θ log pθ(τ)",
            ["Because d/dx log f(x) = f′(x) / f(x). Multiply both sides by f(x)."]),
           ("apply", ["∇θ J = ∇θ ∫ pθ(τ) R(τ) dτ = ∫ ∇θ pθ(τ) · R(τ) dτ",
                      "= ∫ pθ(τ) · ∇θ log pθ(τ) · R(τ) dτ"],
            ["Move ∇ inside the integral (R does not depend on θ), then use the identity."]),
           ("result", "∇θ J = E_τ∼πθ [ ∇θ log pθ(τ) · R(τ) ]",
            ["An EXPECTATION again — so we can estimate it by playing N episodes and "
             "averaging. No derivative of the simulator needed."])],
          take="Read it as: 'make whole episodes more likely in proportion to how good they were'.",
          notes="""
Calculus ki ek line: log f ka derivative = f' / f. Dono taraf f se multiply karo to milta hai
∇p = p × ∇log p.

Isko J par lagao: gradient ko integral ke andar le jao, identity lagao, aur jo bachta hai woh
phir se ek average (expectation) hai. Average ko hum episodes khel kar estimate kar sakte hain —
simulator ka derivative kabhi nahi chahiye.

Matlab: jo episode achhe the, unhe zyada probable banao — jitne achhe, utna zyada.
""")

    steps(prs, "03 · ppo · step 2", "The environment drops out — 'model-free'",
          "Expand the probability of a trajectory and see what depends on θ.",
          [("trajectory", "pθ(τ) = ρ(s₀) · Πₜ πθ(aₜ | sₜ) · P(sₜ₊₁ | sₜ, aₜ)",
            ["Start state × (policy chooses action × physics gives next state) at every step."]),
           ("take log", "log pθ(τ) = log ρ(s₀) + Σₜ log πθ(aₜ|sₜ) + Σₜ log P(sₜ₊₁|sₜ,aₜ)",
            ["Log turns the product into a sum."]),
           ("differentiate", "∇θ log pθ(τ) = Σₜ ∇θ log πθ(aₜ | sₜ)",
            ["ρ and P (the physics) do not depend on θ, so their gradient is zero.",
             "We never need to know how the arm, ink or camera work — only our own network."]),
           ("so far", "∇θ J = E [ Σₜ ∇θ log πθ(aₜ|sₜ) · R(τ) ]",
            ["Computable: log π is the Gaussian log-prob from Section 2; autograd gives its "
             "gradient."])],
          take="This is why PPO and SAC are 'model-free': the simulator is a black box that only "
               "has to produce samples.",
          notes="""
Ek episode ki probability = shuruaati state × har step par (policy ka action chunna × physics ka
agla state dena). Log lene par product sum ban jaata hai.

Ab theta se derivative lo: physics (P) aur start (rho) theta par depend nahi karte, to unka
gradient zero. Bachta hai sirf policy ka log-probability gradient.

Isi wajah se PPO "model-free" hai — arm, ink, camera kaise kaam karte hain, yeh jaanna zaroori
nahi. Simulator sirf samples deta hai.
""")

    steps(prs, "03 · ppo · step 3", "Causality and REINFORCE",
          "An action cannot change rewards that already happened.",
          [("causality", "R(τ) → Gₜ = Σ_{k ≥ t} γ^(k−t) · rₖ₊₁",
            ["Action aₜ only influences rewards from t onwards. Replacing the full return by "
             "the reward-to-go Gₜ keeps the expectation the same and removes noise."]),
           ("estimator", "∇θ J ≈ (1/N) Σᵢ Σₜ ∇θ log πθ(aₜⁱ | sₜⁱ) · Gₜⁱ",
            ["REINFORCE (Williams, 1992): play N episodes, weight each action's log-prob "
             "gradient by what came after it."]),
           ("intuition", "Gₜ > 0 big → push π(aₜ|sₜ) up a lot;  Gₜ small → barely",
            ["Actions followed by good outcomes become more likely."]),
           ("the flaw", "Var[ Gₜ ] is huge",
            ["If every return is positive, EVERY action gets pushed up — only by different "
             "amounts. The signal is buried in noise; learning is slow and unstable."])],
          take="REINFORCE is correct but noisy. The next two steps exist only to reduce that noise.",
          notes="""
Causality: step t ka action pichhle rewards ko nahi badal sakta. Isliye poore episode ke reward
ki jagah sirf "aage ka reward" (reward-to-go G_t) use karo. Average wahi rehta hai, noise kam.

Isse REINFORCE algorithm milta hai: N episodes khelo, har action ke log-prob gradient ko uske
baad aaye reward se weight karo. Jo action achhe nateeje se pehle aaye, woh zyada probable.

Dikkat: variance bahut zyada. Agar saare returns positive hain to HAR action upar dhakela jaata
hai, bas alag-alag maatra me. Signal noise me dab jaata hai. Agle do steps sirf yeh noise kam
karne ke liye hain.
""")

    steps(prs, "03 · ppo · step 4", "Baselines and the advantage",
          "Subtract 'what we expected anyway' — the gradient stays correct, the noise drops.",
          [("claim", "E_{a∼πθ} [ ∇θ log πθ(a|s) · b(s) ] = 0   for any b(s)",
            ["A baseline that depends only on the state adds nothing on average."]),
           ("proof", ["= b(s) · Σₐ πθ(a|s) ∇θ log πθ(a|s) = b(s) · Σₐ ∇θ πθ(a|s)",
                      "= b(s) · ∇θ Σₐ πθ(a|s) = b(s) · ∇θ 1 = 0"],
            ["Log-derivative trick backwards, then: probabilities always sum to 1, and the "
             "derivative of a constant is 0."]),
           ("choice", "b(s) = V(s)   ⇒   Gₜ − V(sₜ) ≈ A(sₜ, aₜ)",
            ["The best simple baseline is the value function: 'how good did I expect this "
             "state to be?'. What remains is the advantage."]),
           ("gradient", "∇θ J = E [ Σₜ ∇θ log πθ(aₜ|sₜ) · Aₜ ]",
            ["Now only actions BETTER than expected are reinforced; worse ones are actively "
             "made less likely."])],
          take="Advantage = 'better or worse than usual?' — a far cleaner learning signal than "
               "'how much reward came after?'.",
          notes="""
Baseline trick: har return me se ek number b(s) ghata do jo sirf state par depend kare. Proof
slide par hai — probabilities ka sum hamesha 1 hai, aur constant ka derivative zero. Matlab
average gradient bilkul same rehta hai, par noise bahut kam ho jaata hai.

Sabse achha baseline value function V(s) hai — "is state se maine kitna expect kiya tha".
G − V = advantage: action umeed se behtar tha ya badtar. Ab sirf behtar actions badhaye jaate
hain aur badtar actions ghataye jaate hain. Bahut saaf signal.
""")

    steps(prs, "03 · ppo · step 5", "Actor-critic and Generalised Advantage Estimation (GAE)",
          "A second network (the critic) predicts V; GAE blends short and long look-ahead.",
          [("critic", "L_V(φ) = E [ ( Vφ(sₜ) − Ĝₜ )² ]",
            ["The critic is trained by plain regression to predict returns. (In our CnnPolicy "
             "it shares the CNN with the actor; only the last layer differs.)"]),
           ("n-step", ["Â⁽¹⁾ = δₜ,   Â⁽²⁾ = δₜ + γδₜ₊₁,   …,   Â⁽∞⁾ = Σₗ γˡ δₜ₊ₗ",
                       "with δₜ = rₜ₊₁ + γV(sₜ₊₁) − V(sₜ)"],
            ["Look 1 step ahead and trust the critic for the rest (low noise, but biased if V "
             "is wrong) … or look all the way to the end (unbiased, noisy)."]),
           ("GAE", "Âₜ^GAE(γ, λ) = Σₗ (γλ)ˡ · δₜ₊ₗ",
            ["An exponentially-weighted average of all n-step estimates (Schulman et al., 2016).",
             "λ = 0 → pure 1-step TD;  λ = 1 → full Monte-Carlo return."]),
           ("ours", "γ = 0.99,   λ = 0.95   (SB3 default)",
            ["Mostly long-horizon, slightly smoothed. Computed backwards over each 512-step "
             "rollout in one pass: Âₜ = δₜ + γλ·Âₜ₊₁."])],
          take="λ is a bias–variance dial. 0.95 is the standard setting and was not tuned here.",
          notes="""
Actor-critic: do hisse. Actor = policy (kya karna hai). Critic = value function (kitna achha
hai). Critic simple regression se seekhta hai — returns predict karo.

Advantage kaise nikaalein? Ek step aage dekho aur baaki critic par bharosa karo (kam noise, par
critic galat ho to bias). Ya episode ke ant tak dekho (bias nahi, par zyada noise). GAE dono ka
weighted average leta hai, lambda se control. Lambda 0 = sirf ek step; lambda 1 = poora episode.

Hamare runs me gamma 0.99, lambda 0.95 — SB3 ka default; humne ise tune nahi kiya. GAE ek hi
backward pass me nikal jaata hai: A_t = delta_t + gamma·lambda·A_{t+1}.
""")

    steps(prs, "03 · ppo · step 6", "Reusing data safely: importance sampling",
          "Plain policy gradient uses each batch once. To reuse it, correct for the policy having changed.",
          [("identity", "E_{x∼p} [ f(x) ] = E_{x∼q} [ (p(x) / q(x)) · f(x) ]",
            ["Average under one distribution using samples from another, by re-weighting."]),
           ("ratio", "rₜ(θ) = πθ(aₜ|sₜ) / πθ_old(aₜ|sₜ)",
            ["How much more (or less) likely the new policy makes the action the old one took. "
             "r = 1 means 'unchanged'."]),
           ("surrogate", "L^CPI(θ) = Eₜ [ rₜ(θ) · Âₜ ]",
            ["Its gradient at θ = θ_old equals the policy gradient of step 4 — so maximising it "
             "is a policy-gradient step that can use the same batch several times."]),
           ("danger", "max L^CPI  →  rₜ → ∞ for any Âₜ > 0",
            ["Nothing stops one huge update from destroying a good policy. TRPO fixed this with "
             "a hard KL-divergence constraint (complex, second-order maths). PPO does it with a clip."])],
          take="The surrogate is only trustworthy while the new policy stays close to the old one.",
          notes="""
Saadharan policy gradient har batch ko ek hi baar use karta hai — mehenga. Batch ko dobara use
karna hai to correction chahiye, kyunki policy badal chuki hai. Importance sampling: ek
distribution ka average doosre ke samples se, re-weight karke.

Ratio r = nayi policy / purani policy (us action ki probability). r = 1 matlab koi badlav nahi.
Surrogate objective = r × advantage. Iska gradient purane point par bilkul policy gradient hai.

Khatra: isko maximise karo to r anant tak badh sakta hai — ek bada update achhi policy barbaad kar
deta hai. TRPO ne KL constraint lagaya (bhaari math). PPO ek simple clip lagata hai — agla slide.
""")

    steps(prs, "03 · ppo · step 7", "The PPO clipped objective",
          "Take the more pessimistic of 'raw' and 'clipped' — so there is no reward for going too far.",
          [("objective", "L^CLIP(θ) = Eₜ [ min( rₜ(θ)·Âₜ ,  clip(rₜ(θ), 1−ε, 1+ε)·Âₜ ) ]",
            ["ε = 0.2 (SB3 default, used unchanged). Schulman et al., 2017."]),
           ("Â > 0", "good action:  objective stops rising once r > 1 + ε = 1.2",
            ["Make it more likely — but by at most 20% per update. Beyond that the gradient is 0."]),
           ("Â < 0", "bad action:  objective stops rising once r < 1 − ε = 0.8",
            ["Make it less likely — but by at most 20%. No incentive to over-correct."]),
           ("min", "min(·,·) ⇒ a lower bound on the unclipped objective",
            ["If the clipped term is the larger one, the raw term is chosen, so a move that "
             "makes things WORSE is still fully penalised. Only over-optimism is removed."])],
          take="Effect: a soft trust region with first-order maths — as simple as REINFORCE, "
               "almost as safe as TRPO.",
          notes="""
PPO ka dil yahi formula hai. Ratio r ko 0.8 aur 1.2 ke beech clip kar do (epsilon = 0.2), aur
clipped aur unclipped me se chhota (pessimistic) lo.

Achha action (advantage positive): use zyada probable banao, par ek update me 20% se zyada nahi.
Uske baad gradient zero — aur dhakka nahi.
Bura action (advantage negative): kam probable banao, par 20% se zyada nahi.

Min lene ka matlab: agar koi badlav cheezon ko BADTAR bana raha hai to uski poori saza milti hai;
sirf zyada-optimism hataya jaata hai. Nateeja: TRPO jaisi safety, REINFORCE jaisa simple math.
""")

    tabular(prs, "03 · ppo · worked example", "The clip in numbers",
            "ε = 0.2, so the 'trusted' ratio range is [0.8, 1.2]. Four cases.",
            ["case", "Â", "r", "r·Â", "clip(r)·Â", "min → used", "gradient?", "meaning"],
            [["good action, pushed too far", "+2", "1.5", "+3.0", "1.2 × 2 = +2.4", "+2.4",
              "0 (clipped)", "already 50% more likely — stop pushing"],
             ["good action, small change", "+2", "0.9", "+1.8", "0.9 × 2 = +1.8", "+1.8",
              "yes", "keep making it more likely"],
             ["bad action, already suppressed", "−1", "0.5", "−0.5", "0.8 × −1 = −0.8", "−0.8",
              "0 (clipped)", "already halved — stop pushing"],
             ["bad action, made MORE likely", "−1", "1.3", "−1.3", "1.2 × −1 = −1.2", "−1.3",
              "yes", "a harmful change — fully penalised"]],
            colw=[2.7, 0.6, 0.6, 0.8, 1.7, 1.1, 1.3, 3.4], size=10.5, row_h=0.55,
            cell_colors={(0, 6): WARN, (2, 6): WARN, (1, 6): GOOD, (3, 6): BAD},
            below=["Rows 1 and 3: the policy has already moved more than 20% in the right "
                   "direction for this sample, so this sample stops contributing.",
                   "Row 4 is why it is min and not just clip: moving the wrong way is never "
                   "excused."],
            take="PPO never forbids big changes outright — it just stops REWARDING them.",
            take_color=VIOLET,
            notes="""
Chaar case numbers ke saath. Epsilon 0.2, to 0.8 se 1.2 tak ratio "bharose wala" hai.

1) Achha action, ratio 1.5 — pehle hi 50% zyada probable. Clip 1.2 par → objective 2.4, gradient
   zero. Aur dhakka nahi.
2) Achha action, ratio 0.9 — range ke andar. Gradient chalta hai, aur badhao.
3) Bura action, ratio 0.5 — pehle hi aadha ho chuka. Clip 0.8 par, gradient zero.
4) Bura action jo galti se ZYADA probable ho gaya (1.3). Raw −1.3 aur clipped −1.2 me min = −1.3,
   yaani poori saza. Isi liye sirf clip nahi, min liya jaata hai.
""")

    steps(prs, "03 · ppo · full loss", "The complete loss PPO minimises",
          "Three terms trained together through the shared network.",
          [("total", "L(θ) = −L^CLIP(θ) + c₁ · L^VF(θ) − c₂ · S[πθ]",
            ["Minimised by Adam. The minus signs turn 'maximise' into 'minimise'."]),
           ("actor", "L^CLIP — the clipped surrogate",
            ["Improves the policy (previous slides)."]),
           ("critic", "L^VF = ( Vθ(sₜ) − V̂ₜ^target )²,   c₁ = 0.5",
            ["Teaches the critic to predict returns (target = Âₜ + V_old(sₜ))."]),
           ("entropy", "S[πθ] = entropy of the Gaussian,   c₂ = 0.02",
            ["Rewards keeping some randomness so exploration does not die early. 0.02 is "
             "our setting (SB3 default is 0)."]),
           ("safety", "‖∇θ L‖ clipped to 0.5;   learning rate 3 × 10⁻⁴",
            ["Gradient-norm clipping stops one weird batch producing a huge jump."])],
          notes="""
PPO teen cheezen ek saath seekhta hai: actor ka clipped objective, critic ka value loss (weight
0.5), aur entropy bonus (weight 0.02). Minus sign isliye ki optimizer minimise karta hai, aur
hum objective ko maximise karna chahte hain.

Entropy bonus 0.02 humne set kiya (SB3 default 0 hai) — taaki agent jaldi randomness na chhode.
Gradient-norm 0.5 par clip hota hai taaki ek ajeeb batch bada jhatka na de. Learning rate 0.0003.
""")

    s = slide(prs, "PPO, as it actually runs in our experiments", "03 · ppo · algorithm",
              "One training run = about 49 rounds of 'collect, then learn'.")
    code(s, M, 1.62, 6.6, 4.65, [
        "for update in 1 … ceil(200,000 / 4,096) = 49:",
        "",
        "    # 1. COLLECT  (policy frozen)",
        "    run 8 environments × 512 steps  = 4,096 transitions",
        "    store (s, a, r, log π_old(a|s), V(s)) for each",
        "",
        "    # 2. ESTIMATE",
        "    compute Â with GAE(γ=0.99, λ=0.95), backwards",
        "    value targets  V̂ = Â + V(s)",
        "",
        "    # 3. LEARN  (reuse the same data 6 times)",
        "    repeat 6 epochs:",
        "        shuffle 4,096 → 16 minibatches of 256",
        "        for each minibatch:",
        "            r = exp(log π_θ − log π_old)",
        "            loss = −L_clip + 0.5·L_vf − 0.02·entropy",
        "            Adam step (lr 3e-4, grad-norm ≤ 0.5)",
        "",
        "    # 4. throw the data away  (on-policy)"], size=11, title="ppo.learn()  — Stable-Baselines3")
    card(s, M + 6.85, 1.62, CW - 6.85, 2.15, "THE NUMBERS FOR ONE RUN",
         ["200,704 environment steps (49 × 4,096).",
          "49 × 6 × 16 = 4,704 gradient steps.",
          "≈ 830 episodes of 240 steps (H3 logged 832 per run)."], accent=VIOLET, body_size=12.5)
    card(s, M + 6.85, 3.92, CW - 6.85, 2.35, "WHY 8 PARALLEL ENVIRONMENTS",
         ["8 copies of DrawEnv step in lock-step (DummyVecEnv). One batch then contains 8 "
          "different episodes, so it is less correlated — steadier gradients.",
          "Seeds must be far apart (0, 100 — never 0, 1): SB3 seeds the 8 envs as k … k+7."],
         accent=PRIMARY, body_size=11.5)
    strip(s, "Same PPO settings in every experiment of the project — the algorithm is held "
          "fixed so only the variable under test changes.", GOOD)
    note(s, """
Ek training run asal me kaise chalta hai: 49 round. Har round me pehle 8 environments × 512
steps = 4,096 transitions collect karo (policy freeze). Phir GAE se advantage nikaalo. Phir usi
data ko 6 baar (6 epochs) use karo — har baar 256 ke 16 minibatch, har minibatch par ek Adam
step. Phir data phenk do (on-policy).

Ek run = 200,704 steps, 4,704 gradient steps, lagbhag 836 episodes.

8 parallel environments isliye ki ek batch me 8 alag episodes hon — gradient zyada steady.
Seeds door-door rakhne padte hain (0 aur 100), kyunki SB3 8 envs ko seed k se k+7 deta hai;
0 aur 1 lene par 7 streams same ho jaati.

Har experiment me PPO ki settings same hain — taaki sirf woh cheez badle jo test ho rahi hai.
""")

    tabular(prs, "03 · ppo · settings", "Every PPO hyperparameter, explained",
            "Source: rl/experiment.py, rl/h4_experiment.py (identical); defaults read from the installed SB3.",
            ["setting", "value", "what it controls", "set by"],
            [["n_envs", "8", "parallel environments per batch", "us"],
             ["n_steps", "512", "steps per env before each update (→ 4,096 per batch)", "us (default 2048)"],
             ["batch_size", "256", "minibatch size for each gradient step", "us (default 64)"],
             ["n_epochs", "6", "passes over each batch", "us (default 10)"],
             ["gamma γ", "0.99", "discount: ~100-step horizon", "default"],
             ["gae_lambda λ", "0.95", "bias–variance of the advantage", "default"],
             ["clip_range ε", "0.2", "trust region: ratio kept in [0.8, 1.2]", "default"],
             ["ent_coef c₂", "0.02", "exploration bonus", "us (default 0)"],
             ["vf_coef c₁", "0.5", "weight of the critic loss", "default"],
             ["learning_rate", "3 × 10⁻⁴", "Adam step size", "default"],
             ["max_grad_norm", "0.5", "gradient clipping", "default"],
             ["total timesteps", "200,000", "per run in every sweep (400k for single showcase runs)", "us"]],
            colw=[2.2, 1.4, 6.0, 2.5], size=10.5, row_h=0.355,
            take="None of these were tuned for a result — a deliberately standard setup, so "
                 "comparisons between arms are fair.", take_color=GOOD,
            notes="""
PPO ki har setting aur uska matlab. Kuch humne set ki (8 envs, 512 steps, batch 256, 6 epochs,
entropy 0.02, 200k steps), baaki SB3 ke default hain (gamma, lambda, clip 0.2, value weight 0.5,
learning rate, gradient clip).

Zaroori baat: koi bhi setting kisi result ko achha dikhane ke liye tune nahi ki gayi. Ek standard
setup jaan-boojh kar rakha, taaki arms ke beech comparison fair rahe.
""")

    concept(prs, "03 · ppo · intuition", "PPO without equations",
            "Everything on the last ten slides, in plain words.",
            ["Play the game for a while with the current policy and write everything down.",
             "For each move, ask the critic: was the outcome better or worse than usual? "
             "(the advantage)",
             "Make better-than-usual moves a bit more likely and worse-than-usual moves a bit "
             "less likely.",
             "'A bit' is enforced: no move's probability may be pushed more than 20% per round "
             "(the clip). That is the 'proximal' in the name.",
             "Squeeze the notes for all they are worth (6 passes), then throw them away and "
             "play again with the improved policy.",
             "Meanwhile the critic gets better at predicting, which makes the next round's "
             "'better or worse than usual' judgement sharper."],
            cards=[("WHY PPO IS SO POPULAR", ["Stable with default settings, simple to implement, "
                                               "works for discrete and continuous actions, "
                                               "parallelises easily."], GOOD),
                   ("ITS WEAKNESS", ["On-policy: every sample is used for one round only, so "
                                     "it needs many environment steps. Fine when the simulator "
                                     "is cheap — as ours is."], WARN)],
            analog="Learning a recipe by tasting: change each ingredient a little at a time, keep "
                   "what improved the taste, never change anything by more than 20% at once.",
            notes="""
Bina equations ke PPO: kuch der current policy se khelo aur sab likh lo. Har move ke liye
critic se poocho — umeed se behtar ya badtar? Behtar moves thode zyada probable, badtar thode
kam. "Thode" ka matlab: ek round me 20% se zyada nahi (yahi "proximal" hai). Notes ko 6 baar
nichodo, phir phenk kar naye policy se phir khelo. Saath me critic bhi behtar hota jaata hai.

PPO popular hai kyunki default settings par stable hai aur simple hai. Kamzori: har sample ek hi
round ke liye — zyada steps chahiye. Hamara simulator sasta hai, to yeh chalta hai.
Analogy: recipe chakh-chakh kar sudharna, har baar thoda sa badlav.
""")


# ------------------------------------------------------------------ SAC --------
def sac(prs):
    section(prs, 4, "SAC and the PPO-vs-SAC comparison",
            "Soft Actor-Critic: the leading off-policy alternative. Its maths, how it differs "
            "from PPO, and why PPO was the right first choice for this project.",
            ["Maximum-entropy RL", "Soft Q and soft value", "Critic, actor and temperature losses",
             "The algorithm", "Side-by-side comparison", "Status of RQ3"])

    steps(prs, "04 · sac", "Maximum-entropy RL: reward + randomness",
          "SAC changes the goal itself, not just the optimiser.",
          [("standard", "J(π) = Σₜ E [ r(sₜ, aₜ) ]",
            ["What PPO maximises (entropy appears only as a small bonus in its loss)."]),
           ("max-ent", "J(π) = Σₜ E [ r(sₜ, aₜ) + α · H( π(· | sₜ) ) ]",
            ["Be rewarded AND stay as random as possible while doing so. α (temperature) sets "
             "the trade-off."]),
           ("why", "H(π(·|s)) = −E_{a∼π} [ log π(a|s) ]",
            ["Keeps exploring all good options instead of committing early; learns several "
             "ways to succeed; tends to be robust to disturbances."]),
           ("origin", "Haarnoja et al., 2018 (ICML) · 2018/19 automatic-α version",
            ["Built on soft Q-learning; uses the twin-critic idea of TD3 (Fujimoto et al., 2018)."])],
          take="In SAC, randomness is part of what is being optimised — not a side-effect to tolerate.",
          notes="""
SAC lakshya hi badal deta hai. PPO sirf reward maximise karta hai (entropy chhota bonus hai).
SAC reward + entropy dono maximise karta hai: "kaam achha karo, aur jitna ho sake random raho".
Alpha (temperature) dono ke beech balance rakhta hai.

Fayda: jaldi kisi ek tareeke par atakta nahi, kai tareeke seekhta hai, aur disturbance ke
saamne zyada robust hota hai. Haarnoja et al. 2018. Twin critic ka idea TD3 se liya.
""")

    steps(prs, "04 · sac", "Soft value functions and the soft Bellman backup",
          "The value functions change to include the entropy bonus.",
          [("soft Q", "Q(sₜ, aₜ) = r(sₜ, aₜ) + γ · E_{sₜ₊₁} [ V(sₜ₊₁) ]",
            ["Same shape as before…"]),
           ("soft V", "V(sₜ) = E_{aₜ∼π} [ Q(sₜ, aₜ) − α · log π(aₜ | sₜ) ]",
            ["…but the value of a state now includes the bonus for how random the policy is "
             "there (−α log π is large when π spreads its probability)."]),
           ("improvement", "π_new = argmin_π  KL( π(·|s)  ‖  exp(Q(s,·)/α) / Z(s) )",
            ["Policy improvement step: move the policy towards a Boltzmann distribution over Q. "
             "High-Q actions get high probability, but never all of it."]),
           ("guarantee", "soft policy iteration converges to the optimal max-entropy policy",
            ["Proven for the tabular case; SAC is its practical neural-network approximation."])],
          notes="""
SAC me value functions entropy shamil karti hain. Soft V = Q − alpha × log pi ka average —
matlab jahan policy zyada spread hai, wahan state ki value zyada.

Policy improvement: policy ko us distribution ki taraf le jao jo exp(Q/alpha) ke proportional hai
(Boltzmann). Zyada Q wale actions zyada probable, par kabhi 100% nahi. Tabular case me yeh
proven hai ki optimal max-entropy policy tak converge karta hai; SAC iska neural network version
hai.
""")

    steps(prs, "04 · sac", "The three SAC losses",
          "Critics, actor and temperature — all trained from a replay buffer D.",
          [("critic", ["J_Q(φᵢ) = E_D [ ( Q_φᵢ(s, a) − y )² ],   i = 1, 2",
                       "y = r + γ(1 − d) · ( minⱼ Q_φ̄ⱼ(s′, ã′) − α log π(ã′|s′) ),   ã′ ∼ π(·|s′)"],
            ["Two Q-networks, use the smaller → curbs over-estimation. φ̄ = slowly-moving "
             "target copies: φ̄ ← τφ + (1 − τ)φ̄, τ = 0.005."]),
           ("actor", ["ã = tanh( μθ(s) + σθ(s) ⊙ ξ ),   ξ ∼ 𝒩(0, I)",
                      "J_π(θ) = E_{s∼D, ξ} [ α log πθ(ã|s) − minⱼ Q_φⱼ(s, ã) ]"],
            ["Reparameterisation trick: noise ξ is outside the network, so gradients flow "
             "through the action into Q. tanh keeps actions in [−1, 1] (with a log-prob correction)."]),
           ("temperature", "J(α) = E_{a∼π} [ −α · ( log π(a|s) + H̄ ) ],   H̄ = −dim(A) = −3",
            ["α is tuned automatically: if entropy falls below the target H̄, α rises and "
             "rewards randomness more."])],
          eq_w=7.0,
          notes="""
SAC ke teen loss. Critic: do Q networks, target y me dono ka minimum — taaki value
over-estimate na ho. Target networks dheere-dheere update hote hain (tau 0.005).

Actor: reparameterisation trick — noise bahar se aata hai, isliye gradient action se hote hue
Q tak jaata hai. tanh action ko −1 se 1 me rakhta hai.

Temperature alpha khud tune hota hai: entropy target (−3, kyunki 3 action dimensions) se neeche
gayi to alpha badhta hai aur randomness ko zyada reward milta hai.
""")

    s = slide(prs, "SAC, as it would run", "04 · sac · algorithm",
              "One gradient update per environment step, from a large memory of old experience.")
    code(s, M, 1.62, 6.6, 4.65, [
        "initialise actor πθ, critics Qφ1, Qφ2, targets φ̄1, φ̄2,",
        "replay buffer D (capacity 1,000,000), α = auto",
        "",
        "for every environment step:",
        "    a ∼ πθ(·|s);   step env → r, s′, done",
        "    D ← D ∪ {(s, a, r, s′, done)}",
        "",
        "    sample minibatch of 256 from D   (old data OK)",
        "    update Qφ1, Qφ2   with J_Q",
        "    update πθ         with J_π",
        "    update α          with J(α)",
        "    φ̄ ← 0.005·φ + 0.995·φ̄",
        "",
        "# nothing is ever thrown away until D is full"], size=11,
         title="SAC  — Stable-Baselines3 defaults")
    card(s, M + 6.85, 1.62, CW - 6.85, 2.25, "THE KEY DIFFERENCE FROM PPO",
         ["PPO: collect 4,096 fresh steps, learn, discard.",
          "SAC: every step is stored and can be replayed thousands of times. That is where "
          "its sample efficiency comes from."], accent=ACCENT, body_size=12)
    card(s, M + 6.85, 4.02, CW - 6.85, 2.25, "A COST SPECIFIC TO OUR TASK",
         ["Our observation is a 3 × 64 × 64 image = 12,288 bytes.",
          "A default 1,000,000-step buffer holds s and s′: ≈ 24.6 GB — far more than this "
          "laptop's RAM. SAC here would need a much smaller buffer."], accent=WARN, body_size=11.5)
    strip(s, "Off-policy = learns from experience gathered by older versions of itself.", ACCENT)
    note(s, """
SAC kaise chalta: har environment step ke baad experience ek replay buffer (10 lakh capacity)
me daalo, buffer se 256 random samples lo, dono critics, actor aur alpha update karo, target
networks thoda sa update karo. Kuch bhi phenka nahi jaata jab tak buffer bhar na jaye.

PPO se bada farak: PPO 4,096 naye steps leta hai, seekhta hai, phenk deta hai. SAC har step ko
hazaaron baar dobara use kar sakta hai — isliye kam steps me seekhta hai.

Hamare task ki ek khaas dikkat: observation ek image hai (12,288 bytes). 10 lakh steps ka
default buffer, s aur s' dono ke saath, ~24.6 GB banta hai — is laptop ki RAM se bahut zyada.
SAC chalana ho to buffer bahut chhota rakhna padega.
""")

    tabular(prs, "04 · comparison", "PPO vs SAC, side by side",
            "Neither is 'better' in general — they trade different resources.",
            ["dimension", "PPO (used)", "SAC (planned, RQ3)"],
            [["data use", "on-policy: each batch used for one round (6 epochs), then discarded",
              "off-policy: replay buffer, every sample reused many times"],
             ["sample efficiency", "lower — needs more environment steps",
              "higher — often several times fewer steps on continuous control"],
             ["compute per env step", "low (one update per 4,096 steps)",
              "high (a gradient update every step)"],
             ["stability", "very stable with defaults; clip limits each change",
              "stable for an off-policy method; twin critics + target nets"],
             ["exploration", "Gaussian noise + small entropy bonus (0.02)",
              "entropy is part of the objective, α auto-tuned"],
             ["memory", "one batch (4,096 steps)", "replay buffer — large with image observations"],
             ["action spaces", "discrete and continuous", "continuous only"],
             ["parallel envs", "natural (8 here)", "possible, less natural"],
             ["best when", "the simulator is cheap and fast", "real-world samples are expensive"]],
            colw=[2.4, 4.9, 4.9], size=10.5, row_h=0.43,
            take="For hardware, SAC's sample efficiency matters a lot; in a cheap simulator, "
                 "PPO's simplicity and stability win.", take_color=VIOLET,
            notes="""
Dono algorithms ko aamne-saamne. PPO: on-policy, kam sample-efficient, par har step par compute
kam, bahut stable, parallel envs aasaan, memory kam. SAC: off-policy, replay buffer, zyada
sample-efficient, har step par gradient update (zyada compute), entropy objective ka hissa, sirf
continuous actions, aur image observations ke saath memory bhaari.

Saar: asli hardware par, jahan har sample mehenga hai, SAC ka fayda bada hai. Saste simulator
me PPO ki simplicity aur stability jeet-ti hai.
""")

    concept(prs, "04 · decision", "Why PPO first — and what RQ3 will do",
            "An honest status: SAC is planned, not yet run. No PPO-vs-SAC result exists.",
            ["The research question is about WHERE the learning signal comes from (truth vs "
             "camera) — so the algorithm is held fixed. Swapping it mid-study would confound "
             "every comparison.",
             "Our simulator is cheap (≈ 2,300 steps/s with the fast camera model), so PPO's "
             "appetite for samples costs minutes, not days.",
             "PPO has stable defaults: no result in this project depends on algorithm tuning.",
             "Image observations make SAC's replay buffer expensive on this machine (≈ 24.6 GB "
             "at default size).",
             "SAC becomes important later: on hardware, every sample costs real time and wear."],
            cards=[("RQ3 — THE FAIR PROTOCOL (PROPOSAL §5.5)",
                    ["Compare at equal environment steps AND equal wall-clock time.",
                     "At least 5 seeds per arm, paired by seed.",
                     "Same reward, observation, shapes and scoring (true IoU)."], VIOLET),
                   ("STATUS", ["Stage 5 of the plan. Not started. The paper does not need it; "
                               "PAPER_PLAN marks it 'nice to have'."], WARN)],
            take="Any slide or paper text that claims 'PPO beats SAC' (or the reverse) would be "
                 "unsupported today.", take_color=BAD,
            notes="""
Saaf baat: SAC abhi plan me hai, chalaya nahi gaya. PPO vs SAC ka koi result abhi nahi hai.

PPO pehle kyun: hamara research sawaal yeh hai ki seekhne ka signal kahan se aaye (truth ya
camera) — isliye algorithm fix rakha. Beech me algorithm badalna har comparison bigaad deta.
Simulator sasta hai, to PPO ki zyada samples ki bhookh minutes ki baat hai. PPO ke defaults
stable hain. Aur SAC ka replay buffer images ke saath is laptop par bahut bhaari hota.

RQ3 ka fair tareeka: same environment steps aur same wall-clock time par compare karo, kam se
kam 5 seeds. Yeh Stage 5 hai; paper ke liye zaroori nahi. Agar koi "PPO SAC se behtar hai" bole,
to woh abhi bina saboot ki baat hogi.
""")


def build(prs):
    ppo(prs)
    sac(prs)
