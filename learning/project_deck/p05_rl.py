"""Section 5 - reinforcement learning from scratch."""
from kit import *  # noqa: F401,F403
from teach_figs import TOY


def build(prs, toc):
    section(prs, 5, "Reinforcement learning from scratch",
            "Learning by trial and error: an agent acts, the world answers with a new situation and a "
            "reward, and the agent changes its behaviour to collect more reward over time.",
            ["The agent-environment loop", "Episodes, MDPs, partial observability", "Return & discount",
             "Policies", "Value functions & Bellman", "Exploration & entropy", "Reward shaping"],
            """
Section 5: reinforcement learning (RL) zero se. Supervised learning me "sahi jawab" diya jaata hai;
RL me sirf ek reward milta hai - "achha tha / bura tha" - aur woh bhi der se. Agent ko khud
pata lagana padta hai ki kaunse actions ne reward dilaya. Is section ke concepts (return, value,
advantage) seedhe PPO (Section 6) me use hote hain.""", toc)

    s = slide(prs, "The agent-environment loop", "05 · RL", "At every step t: observe, act, receive a reward and the next observation.")
    top = s._top + 0.2
    node(s, M + 0.2, top + 0.9, 2.6, 1.4, "AGENT", "policy πθ\n(the CNN)", color=VIOLET, title_size=16, sub_size=12)
    node(s, M + 5.0, top + 0.9, 2.8, 1.4, "ENVIRONMENT", "DrawEnv: pen, paper,\ntarget, camera", color=PRIMARY, title_size=16, sub_size=12)
    elbow(s, [(M + 1.5, top + 0.88), (M + 1.5, top + 0.25), (M + 6.4, top + 0.25), (M + 6.4, top + 0.88)], color=VIOLET, lw=2)
    place_eq(s, r"\mathrm{action}\ \ a_t=(dx,\ dy,\ \mathrm{pen})", M + 2.0, top - 0.2, 4.2, 0.42, size=18, color=HEX["violet"])
    elbow(s, [(M + 6.4, top + 2.32), (M + 6.4, top + 2.95), (M + 1.5, top + 2.95), (M + 1.5, top + 2.32)], color=GOOD, lw=2)
    place_eq(s, r"\mathrm{next\ observation}\ \ s_{t+1},\ \ \mathrm{reward}\ \ r_{t+1}", M + 1.2, top + 3.03, 5.5, 0.45, size=18, color=HEX["good"])
    table(s, ["RL word", "in RoboSketch-RL"],
          [["state / observation", "64×64×3 image: target, drawn-so-far, pen"],
           ["action", "dx, dy in [-1, 1] (× 0.014 m), pen in [0, 1]"],
           ["reward", "IoU gain + closeness bonus - jerkiness (equation: Section 7)"],
           ["episode", "240 steps (60 in H4), pen starts on the target"],
           ["policy", "CNN → Gaussian over actions"],
           ["learning algorithm", "PPO (Stable-Baselines3), 200k steps"]],
          M + 8.2, top - 0.1, CW - 8.2, colw=[1.6, 2.6], size=11.5, row_h=0.62, align="left")
    why(s, "RL fits drawing-by-trial-and-error: there is no 'correct next move' label, only a score of "
           "how the drawing turned out.")
    note(s, """
RL ka loop: har step t par agent observation dekhta hai, action leta hai, environment ek naya
observation aur ek reward deta hai. Yahi baar-baar.

Hamare project me: observation = 64x64x3 image (target, ab tak ki drawing, pen). Action = pen ka
(dx, dy) aur pen neeche/upar. Reward = IoU kitna badha + chhota shaping (Section 7 me pura formula).
Episode = 240 steps (H4 me 60). Policy = CNN jo actions par ek Gaussian deta hai. Algorithm = PPO.

RL kyun, supervised kyun nahi? Supervised ke liye har step ka "sahi move" chahiye - woh kisi ke
paas nahi hai (bina demonstrations ke seekhna hi H1 hai). RL ko sirf ek score chahiye.
""", source="rl/draw_env.py (spaces, _reward, step); rl/experiment.py (PPO, 200k); docs/paper/main.tex Setup")

    concept(prs, "05 · RL", "Steps, episodes and the two ways an episode ends", None,
            ["Step: one action and its consequence. Episode: one full attempt at the drawing, from reset "
             "to end. Trajectory: the sequence s₀, a₀, r₁, s₁, a₁, r₂, …",
             "TERMINATED: the task itself ended (success: reward IoU ≥ 0.60, or the agent chose to stop "
             "in the stop-action ablation). No future after it.",
             "TRUNCATED: we cut the episode for practical reasons (step limit 240, or the plateau stop). "
             "The future still existed, so the value estimate should 'bootstrap' through it.",
             "Mixing them up teaches the agent wrong values; the code keeps them separate on purpose.",
             "Fact: no agent ever reached IoU 0.60 (best peak on record 0.516), so in practice every "
             "episode is truncated at the step limit."],
            cards=[("WHY IT MATTERS HERE", ["The stop-action bug: pressing 'stop' set terminated=True AND "
                                            "collected the +2 success bonus - on a blank canvas. Fixed by "
                                            "separating 'reached' from 'terminated'."], BAD)],
            notes="""
Step = ek action. Episode = ek poori koshish (reset se end tak). Trajectory = states, actions,
rewards ki series.

Episode do tarah khatam hota hai:
- Terminated: task khud khatam - success (IoU >= 0.60) ya agent ne khud "stop" dabaya (ablation me).
  Iske baad koi future nahi.
- Truncated: humne practical wajah se kaata - 240 step limit ya plateau stop. Future tha, bas humne
  dekha nahi - isliye value estimate ko aage "bootstrap" karna chahiye.

Gymnasium dono ko alag flags deta hai, aur code me dono alag rakhe gaye.

Bug story: stop-action ablation me "stop" dabane par terminated=True ho jaata tha aur +2 success
bonus bhi mil jaata tha - khaali canvas par! (step 1 par reward +1.99). Fix: "reached" (success)
aur "terminated" alag. Waise 0.60 kabhi kisi agent ne nahi chhua (best peak 0.516) - to normal
episodes sab truncated hote hain.
""", source="rl/draw_env.py step() (reached / terminated / truncated); RESEARCH_LOG '### BUG 1 (critical) - "
            "the stop action was being paid the success bonus'")

    eq_slide(prs, "05 · MDP", "The Markov decision process (MDP)",
             "The mathematical model behind RL: states, actions, transitions, rewards, discount.",
             r"\mathcal{M}=(\mathcal{S},\ \mathcal{A},\ P,\ R,\ \gamma),\qquad P(s_{t+1}\mid s_t,a_t)",
             [(r"\mathcal{S},\ \mathcal{A}", "set of states, set of actions"),
              (r"P(s'\mid s,a)", "transition: probability of the next state given state and action"),
              (r"R(s,a)", "reward function"),
              (r"\gamma\in[0,1)", "discount factor (ours 0.99)"),
              (r"\mathrm{Markov}", "the next state depends only on the CURRENT state and action, not the history")],
             example=["State here = canvas + pen position + target (+ step count, + sheet offset in H4).",
                      "Transitions are deterministic except the H4 disturbances and the random camera.",
                      "The agent does not see the full state (next slide): it sees a 64-px picture."],
             example_title="IN OUR TASK", example_color=PRIMARY,
             why_text="Writing the task as an MDP tells you exactly what the agent must be able to observe "
                      "to act well - which is where several of our findings came from.",
             label="Markov decision process", group="Reinforcement learning",
             notes="""
MDP = RL problem ka math model: states S, actions A, transition probability P (is state me yeh
action liya to agla state kya hoga), reward R, aur discount gamma.

Markov property: agla state sirf ABHI ke state aur action par depend karta hai, poore itihaas par
nahi. Physics analogy: classical mechanics me position + velocity pata ho to future tay - poora
past nahi chahiye.

Hamare task me state = canvas + pen position + target (H4 me sheet offset bhi). Agent ko poora
state nahi dikhta - sirf 64 px ki picture. Yahi "partial observability" agle slide ka topic hai,
aur kai findings (O1 time channel, H4 ka world-frame marker) isi se aayi.
""", source="standard RL (Sutton & Barto); rl/draw_env.py; gamma 0.99 from rl/experiment.py")

    concept(prs, "05 · partial observability", "When the agent cannot see the whole state", None,
            ["The episode is cut at 240 steps, but the picture does not show how many steps are left: "
             "two identical canvases with 5 or 100 steps left look the same yet need different actions.",
             "That makes the task PARTIALLY observable. Fix O1: a 4th channel filled with the elapsed "
             "fraction of the episode (D02 puts the step count in its state for this reason).",
             "O1 result: +0.039 IoU, 9/12 pairs up, t = +2.17 - modest, shape-dependent; default left OFF.",
             "O1 did NOT reduce the overshoot (+0.001, t = 0.11) - the predicted mechanism was wrong.",
             "The same idea returns in H4: after the sheet slides, the pen marker drawn in WORLD "
             "coordinates hides where the pen is on the sheet - the agent must infer it."],
            cards=[("LESSON", ["When an agent fails, first ask: could it even SEE what it needed? "
                               "Two of the project's biggest changes (O1, the H4 sheet marker) came from this question."], VIOLET)],
            notes="""
Partial observability: jab agent ko poora state nahi dikhta. Example: episode 240 step par kat jaata
hai, par image me yeh nahi dikhta ki kitne steps bache. Do bilkul same canvas - ek me 5 step bache,
ek me 100 - alag action chahiye, par agent ko farak dikhta hi nahi.

Fix O1: ek 4th channel jisme "episode ka kitna hissa beet gaya" likha hai (0 se 255). D02 bhi step
number state me daalta hai isi wajah se.

Result: +0.039 IoU, 12 me se 9 pairs me better, t = +2.17 - chhota, shape-dependent fayda (square/
triangle me, circle me nahi). Default OFF rakha kyunki observation shape badalta hai.

Imandari wala hissa: prediction tha ki O1 overshoot kam karega - nahi kiya (t=0.11). Galat
prediction log me likhi gayi.

H4 me same lesson wapas aaya: paper khisakne ke baad pen marker world coordinates me tha, sheet par
pen kahan hai yeh agent ko dikhta nahi tha. Sawaal hamesha: "kya agent woh dekh sakta tha jo use
chahiye tha?"
""", source="RESEARCH_LOG '### O1 RESULT - remaining-time in the observation'; rl/draw_env.py time_in_obs comment; "
            "RESEARCH_LOG '## 2026-10-29 - H4 oracle check'")

    r = TOY["ret"]
    hz = TOY["horizon"]
    eq_fig_slide(prs, "05 · return", "Return and discount: what the agent maximises",
                 "Not the next reward - the (discounted) sum of all future rewards.",
                 r"G_t=\sum_{k=0}^{\infty}\gamma^{k}\,r_{t+k+1}=r_{t+1}+\gamma\,G_{t+1}",
                 "discount.png",
                 [(r"G_t", "return from step t onwards"),
                  (r"r_{t+k+1}", "reward k steps later"),
                  (r"\gamma", "discount 0.99: a reward k steps away counts γᵏ"),
                  (r"1/(1-\gamma)", f"rough 'horizon': {hz[0.99]:.0f} steps for γ = 0.99")],
                 after=[f"Toy: rewards {r['r']}, γ = {r['gamma']} → G₀ = {r['G']:.4f}",
                        f"γ = 0.99: 60 steps away counts {TOY['g99_60']:.2f}; 240 steps away {TOY['g99_240']:.2f}"],
                 why_text="γ = 0.99 makes the agent care about the whole ~60-240-step drawing, not just the "
                          "next move; and a sum (not a max) is what makes IoU-delta rewards telescope.",
                 label="Discounted return", group="Reinforcement learning",
                 notes="""
Agent agla reward nahi, balki aage ke saare rewards ka sum maximize karta hai - "return" G_t. Discount
gamma: k step door wala reward gamma^k se multiply hota hai. Recursion: G_t = r_(t+1) + gamma*G_(t+1)
- yeh Bellman equation ka beej hai.

Discount kyun? (1) Math: infinite sum finite rehta hai. (2) Intuition: jaldi milne wala reward thoda
zyada keemti. Rough horizon = 1/(1-gamma) = 100 steps for 0.99 (script ne compute kiya).

Toy (script se): rewards [1,0,0,0,1], gamma 0.9 -> G0 = 1.6561.

Hamare liye: gamma 0.99 par 60 step door ka reward ~0.55 aur 240 step door ka ~0.09 weight paata hai.
Drawing ~30-40 steps me trace hoti hai (overrun finding), to 0.99 poori drawing ko cover karta hai.

Ek aur cheez: reward = 10 * delta IoU. Sum karne par yeh telescope hota hai (Section 7) - return
lagbhag final IoU ban jaata hai.
""", source="rl/experiment.py gamma=0.99; toy numbers by teach_figs.py")

    eq_fig_slide(prs, "05 · policy", "The policy: a probability distribution over actions",
                 "Continuous actions → the network outputs a mean; the action is sampled around it.",
                 r"\pi_\theta(a\mid s)=\mathcal{N}\left(\mu_\theta(s),\ \mathrm{diag}(\sigma^2)\right)",
                 "gauss_policy.png",
                 [(r"\pi_\theta(a\mid s)", "probability (density) of action a in state s"),
                  (r"\mu_\theta(s)", "mean action from the CNN's policy head"),
                  (r"\sigma", "spread; a learned parameter, starts at 1 (log σ = 0)"),
                  (r"\theta", "network weights")],
                 after=["Training: SAMPLE actions (exploration). Evaluation: use the MEAN (deterministic=True).",
                        "Samples outside [-1, 1] are clipped by the action bounds."],
                 why_text="A stochastic policy explores by itself and has a smooth log-probability - "
                          "exactly what policy-gradient methods (PPO) need.",
                 label="Gaussian policy", group="Reinforcement learning",
                 notes="""
Policy = agent ka "dimaag": state dekh kar action ka probability distribution. Continuous actions ke
liye Gaussian: network mean mu deta hai, aur sigma (spread) ek alag learned parameter hai (SB3 me
state-independent), jo log(sigma) = 0, yaani sigma = 1 se shuru hota hai.

Training me action SAMPLE hota hai - isse exploration apne aap hoti hai. Evaluation me mean use hota
hai (deterministic=True) - isliye hamara evaluation poori tarah deterministic hai (fixed targets par
8 eval episodes = ek hi episode 8 baar! - Section 7 ka protocol finding).

Ek side effect jo log me hai: sigma = 1 par "stop" head jaisa 0.5 threshold wala output ~31% samples
me trigger hota tha - isliye stop ablation me bias -2.0 rakhna pada.

Stochastic policy kyun? PPO ko log pi(a|s) ka gradient chahiye - Gaussian ka log-probability smooth
aur aasaan hai.
""", source="stable_baselines3 2.9.0 policies (log_std_init 0.0); rl/experiment.py (model.predict deterministic=True); "
            "RESEARCH_LOG 'Why the stop arm also needed a policy-side fix' and 'Protocol finding - eval_eps=8'")

    eq_slide(prs, "05 · value", "Value functions: how good is this situation?",
             "The critic's job: predict the return, so the actor knows whether an outcome was better than expected.",
             r"V^{\pi}(s)=\mathbb{E}_{\pi}\left[G_t\mid s_t=s\right],\qquad Q^{\pi}(s,a)=\mathbb{E}_{\pi}\left[G_t\mid s_t=s,\ a_t=a\right]",
             [(r"V^{\pi}(s)", "expected return from state s if we follow policy π"),
              (r"Q^{\pi}(s,a)", "expected return if we take action a first, then follow π"),
              (r"\mathbb{E}_{\pi}[\cdot]", "average over the randomness of the policy and the world"),
              (r"A^{\pi}=Q^{\pi}-V^{\pi}", "advantage: how much better a is than the policy's average")],
             example=["Mid-drawing, half the circle done: V is high (more IoU to collect).",
                      "Pen far off the target with little time left: V is low.",
                      "PPO's network has a VALUE head that learns V(s) by regression on observed returns."],
             example_title="INTUITION", example_color=PRIMARY,
             extra=[r"A^{\pi}(s,a)=Q^{\pi}(s,a)-V^{\pi}(s)"],
             why_text="Rewards are noisy; comparing an outcome with V(s) ('better or worse than usual?') "
                      "turns noisy rewards into a usable learning signal.",
             label="State value and action value", group="Reinforcement learning",
             notes="""
Value function V(s): is state se, current policy follow karke, average kitna return milega. Q(s,a):
pehle action a lo, phir policy follow karo - average return.

Advantage A = Q - V: yeh action average se kitna behtar tha. Positive -> is action ki probability
badhao; negative -> ghatao. PPO isi advantage par chalta hai.

Intuition: aadha circle ban chuka hai -> V zyada (abhi aur IoU milega). Pen target se door aur time
kam -> V kam.

PPO ke network me ek "value head" (critic) hota hai jo V(s) seekhta hai - observed returns par simple
regression (MSE loss). Policy head = actor. Isliye ise actor-critic kehte hain.

Note: T1 experiment me BC warm start ke waqt value head train nahi hua tha - ek untested candidate
reason ki PPO ne achhi starting policy ko "unlearn" kyun kiya.
""", source="standard RL; RESEARCH_LOG '### T1 BC warm start RESULT' honest limits (value head untrained)")

    steps_slide(prs, "05 · Bellman", "The Bellman equation and the TD error",
                "Value today = reward now + discounted value tomorrow. The mismatch is the learning signal.",
                [("Bellman", r"V^{\pi}(s)=\mathbb{E}_{\pi}\left[r_{t+1}+\gamma\,V^{\pi}(s_{t+1})\mid s_t=s\right]",
                  "Follows from the return recursion (previous slides): the value is self-consistent over one step.",
                  "Bellman expectation equation"),
                 ("TD error", r"\delta_t=r_{t+1}+\gamma\,V(s_{t+1})-V(s_t)",
                  "If the value estimate were perfect, δ would average to zero. δ > 0: things went better "
                  "than expected.", "Temporal-difference (TD) error"),
                 ("use", r"\hat{A}_t\approx\delta_t\quad(\mathrm{one\ step})",
                  "δ is a one-step estimate of the advantage. GAE (Section 6) blends many steps of δ.")],
                take="The Bellman equation turns 'predict the whole future' into 'be consistent with the "
                     "next step' - learnable from single transitions.", group="Reinforcement learning",
                notes="""
Bellman equation: V(s) = average[ abhi ka reward + gamma * agle state ka V ]. Yeh G_t = r + gamma*G_(t+1)
se seedha aata hai. Matlab: poora future predict karne ke bajaye, bas ek step ke saath consistent raho.

TD error delta = r + gamma*V(s') - V(s). Agar value estimate perfect hota to delta average me zero.
delta positive = umeed se behtar hua. Yahi signal critic ko train karta hai aur actor ko advantage
deta hai.

Ek-step advantage ~ delta. PPO GAE use karta hai jo kai steps ke delta ko mila ke better estimate
banata hai (agla section).
""", source="standard RL (Sutton & Barto, Bellman 1957)")

    eq_slide(prs, "05 · exploration", "Exploration vs exploitation, and the entropy bonus",
             "To find better drawings the agent must sometimes try moves it is unsure about.",
             r"\mathcal{H}\left[\pi_\theta(\cdot\mid s)\right]=-\int \pi_\theta(a\mid s)\,\log\pi_\theta(a\mid s)\,da",
             [(r"\mathcal{H}", "entropy: how spread-out (uncertain) the action distribution is"),
              (r"\mathcal{H}_{\mathcal{N}}", "for a Gaussian: ½ log(2πeσ²) per action dimension - grows with σ"),
              (r"c_2", "entropy coefficient ('ent_coef'): ours 0.02 (SB3 default is 0)")],
             example=["Exploitation: repeat what worked. Exploration: try something new.",
                      "PPO adds +c₂·H to the objective, so σ does not collapse too early.",
                      "Side effect seen here: with ent_coef 0.02 the Gaussian rarely lands on 'stand still' "
                      "exactly, so after finishing the agent drifts past the outline (overshoot)."],
             example_title="IN THIS PROJECT", example_color=WARN,
             extra=[r"\mathcal{H}_{\mathcal{N}(\mu,\sigma^2)}=\frac{1}{2}\log\left(2\pi e\,\sigma^2\right)"],
             why_text="Without exploration the 'draw nothing' and 'don't move' traps are never escaped; "
                      "with too much, the policy never settles.",
             label="Entropy of a policy", group="Reinforcement learning",
             notes="""
Exploration vs exploitation: jo kaam karta hai wahi dohrao (exploit) ya naya try karo (explore)?
Bina exploration ke agent pehle mile "theek-thaak" solution par atak jaata hai.

Entropy H = distribution kitna phaila hua hai. Gaussian ke liye 1/2 log(2 pi e sigma^2) - sigma badha
to entropy badhi. PPO objective me +c2*H jodta hai taaki sigma jaldi se zero na ho jaye. Hamara c2 =
0.02 (SB3 ka default 0 hai - humne exploration badhai).

Project me side effect: Gaussian policy ke saath "bilkul ruk jaana" (dx=dy=0) ek single point hai jis
par sample kabhi exactly nahi girta - isliye shape poori hone ke baad pen thoda aage phisalta hai
(overshoot, H6). Log yahi explanation deta hai.
""", source="rl/experiment.py ent_coef=0.02; stable_baselines3 2.9.0 ppo.py (ent_coef default 0.0); "
            "RESEARCH_LOG 'UNEXPECTED FINDING - agents finish early' ('Why it happens')")

    grid(prs, "05 · families", "The map of RL algorithms - where PPO and SAC sit", None,
         [("MODEL-FREE vs MODEL-BASED", ["Model-free: learn the policy/value directly from experience "
                                         "(PPO, SAC). Model-based: learn how the world works, then plan. "
                                         "We are model-free."], PRIMARY),
          ("ON-POLICY (PPO)", ["Learns only from data collected by the CURRENT policy; throws it away after "
                               "each update. Simple and stable, but needs lots of samples."], VIOLET),
          ("OFF-POLICY (SAC)", ["Stores past experience in a replay buffer and reuses it many times. "
                                "Sample-efficient, but many more gradient updates per step."], ACCENT),
          ("VALUE-BASED (DQN)", ["Learn Q(s, a), act greedily. Natural for discrete actions; our actions "
                                 "are continuous."], SLATE),
          ("POLICY-GRADIENT / ACTOR-CRITIC", ["Learn the policy directly (actor) with a value "
                                              "estimate as a baseline (critic). PPO and SAC are both actor-critic."], GOOD),
          ("OUR CHOICE", ["PPO first: stable, standard in SB3, cheap per update on a CPU. SAC (RQ3) was run "
                          "later at ~7.6 h per run and ended far behind PPO (0.051 vs 0.292)."], WARN)],
         cols=3, notes="""
RL algorithms ka naksha:
- Model-free vs model-based: hum model-free hain - duniya ka model nahi seekhte, seedha policy/value.
- On-policy (PPO): sirf current policy ka data use karta hai, update ke baad phek deta hai. Stable,
  simple, par samples zyada chahiye. Simulation me samples sasté hain - isliye theek.
- Off-policy (SAC): purana data replay buffer me rakhta hai, baar-baar use karta hai. Sample-efficient,
  par har step par zyada gradient updates - CPU par mehnga.
- Value-based (DQN): discrete actions ke liye; hamare actions continuous hain.
- Actor-critic: policy (actor) + value (critic). PPO aur SAC dono actor-critic.

Choice: PPO pehle. SAC (RQ3) baad me chalaya: ~7.6 ghante per run (CPU par mehnga), aur result me SAC
bahut peeche (0.051 vs 0.292 IoU) - low update ratio ke saath, isliye "is budget par".
""", source="RESEARCH_LOG '### RQ3 PPO vs SAC RESULT'; rl/train.py docstring (PPO first)")

    eq_fig_slide(prs, "05 · shaping", "Reward shaping with a potential: guidance without changing the goal",
                 "Add a bonus for getting closer to the target - in a way that provably keeps the best policy the same.",
                 r"F(s,s')=\gamma\,\Phi(s')-\Phi(s),\qquad \Phi(s)=-\,d\left(\mathrm{pen},\ \mathrm{nearest\ target\ pixel}\right)",
                 "potential_toy.png",
                 [(r"\Phi(s)", "potential: higher when the pen is closer to the target"),
                  (r"F", "shaping reward added each step"),
                  (r"d", "distance (from a distance transform), / canvas size")],
                 after=["Ng et al. (1999): potential-based shaping leaves the optimal policy unchanged - "
                        "the bonuses telescope away over an episode.",
                        "Our code adds 0.4·(Φ(s') - Φ(s)), i.e. without the γ factor - the usual "
                        "approximation; the exact guarantee is for γΦ(s') - Φ(s)."],
                 why_text="The first agents found 'draw nothing' optimal: a sparse coverage reward was too "
                          "hard to discover. The potential pulls the pen toward the shape from step 1.",
                 label="Potential-based reward shaping", group="Reinforcement learning", fig_w=4.8,
                 notes="""
Reward shaping: agent ko extra "hint" reward dena taaki seekhna aasaan ho. Khatra: galat hint se
agent galat cheez seekh leta hai. Ng et al. (1999) ne dikhaya: agar bonus F = gamma*Phi(s') - Phi(s)
form ka ho (potential ka difference), to best policy nahi badalti - kyunki episode par yeh sum
telescope hoke sirf start aur end ke potential par depend karta hai.

Hamara potential Phi = -(pen se nearest target pixel ki doori). Pen target ke paas -> Phi zyada.
Figure me ek ring target ke liye Phi ka heatmap.

Kyun chahiye tha? Pehle PPO runs "draw nothing" trap me phase - patla target random exploration me
kabhi hit hi nahi hota tha. Potential ne pen ko step 1 se shape ki taraf kheencha.

Honest nuance (interview me pooch sakte hain): code 0.4*(Phi' - Phi) use karta hai, gamma factor ke
bina. gamma = 0.99 par yeh common approximation hai; exact theoretical guarantee gamma*Phi' - Phi
ke liye hai.
""", source="rl/draw_env.py _potential and _reward (prox_weight 0.4); RESEARCH_LOG '### Reward shaping - two local "
            "optima found and fixed'; Ng, Harada & Russell 1999 (potential-based shaping); figure = toy")
