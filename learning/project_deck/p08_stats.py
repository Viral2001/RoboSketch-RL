"""Section 8 - experimental method and statistics from scratch."""
from kit import *  # noqa: F401,F403
from teach_figs import TOY


def build(prs, toc):
    section(prs, 8, "Experimental method & statistics",
            "When is a difference real? Seeds, paired comparisons, the paired t-test, difference-in-"
            "differences, equivalence tests, pre-registration - and the mistakes that taught each rule.",
            ["Why many seeds", "Seed spacing (F6)", "Mean, sd, standard error", "Paired t-test",
             "'No detectable effect'", "Difference-in-differences", "TOST equivalence", "Pre-registration"],
            """
Section 8: statistics zero se. RL results bahut noisy hote hain - same setup, alag seed, alag result.
Is section ke baad aap samjhoge ki har result slide par n, mean +/- sd, paired difference, k/n aur t
kyun likhe hain, aur "no detectable effect" aur "no effect" me kya farak hai. Yeh project ki
"credibility" ka section hai.""", toc)

    concept(prs, "08 · seeds", "Why one training run proves nothing", None,
            ["A 'seed' fixes all the random choices of a run (network init, exploration noise, env streams). "
             "Different seed → a genuinely different training run.",
             "RL is noisy: in the H2 peak re-run the circle's truth-minus-camera gap swung from -0.127 "
             "(seed 0) to +0.159 (seed 2) - bigger than any effect we care about.",
             "Two 24-run H2 sweeps disagreed on WHICH arm was better (-0.028 vs +0.013) - both |t| < 1.5.",
             "Same seed is not even the same result: thread count changed one seeded cell from 0.175 to 0.195.",
             "So every claim here uses several seeds × shapes, paired, with a test fixed in advance."],
            cards=[("THE UNIT OF ANALYSIS", ["One (shape, seed) CELL. n = 8 means 4 shapes × 2 seeds, or 12 = 4 × 3."], PRIMARY),
                   ("WHAT ± MEANS HERE", ["Sample sd across cells (ddof = 1). Never across eval episodes of a "
                                          "fixed target - those are identical."], WARN)],
            notes="""
Seed: random number generator ka starting point. Seed fix = run ke saare random choices fix (network
ke shuruaati weights, exploration noise, environment streams). Alag seed = sach me alag training run.

RL bahut noisy hai. H2 ke ek re-run me circle par truth-minus-camera gap ek seed par -0.127 aur doosre
par +0.159 - jitna effect hum dhoondh rahe hain usse kahin bada. Do H2 sweeps ne yeh bhi tay nahi kiya
ki kaun aage hai (-0.028 vs +0.013).

Aur same seed bhi same result nahi: thread count badalne se ek hi seeded cell 0.175 se 0.195.

Isliye: unit of analysis = ek (shape, seed) cell; n = cells ki ginti; +/- = cells ke beech ka sample sd.
""", source="RESEARCH_LOG '### H2 PEAK-vs-FINAL RESULT' (per-cell swings, sign flip) and '### A reproducibility limit worth knowing'")

    figure(prs, "08 · seeds", "Seed spacing: the F6 lesson",
           "PPO(seed = k) re-seeds its 8 environments to k, k+1, …, k+7 - overwriting what the script passed.",
           "seed_streams.png",
           ["Seeds 0 and 1 then share 7 of 8 environment streams: the two 'independent' runs see mostly "
            "the same random episodes.",
            "Effect: between-seed spread is UNDERSTATED, and two sweeps on seeds 0, 1, 2 are not "
            "independent samples.",
            "Found 12 Sep 2026 - after both early H2 sweeps had used seeds 0, 1, 2.",
            "Rule since then: seeds 0, 100, 200, 300. The H2 re-run used 100/200/300 so no stream overlaps "
            "the old sweeps either."],
           fig_w=7.0, take="Interview line: 'adjacent seeds were not independent in this stack, so I re-ran "
                           "the main result on spaced seeds'.", take_color=WARN,
           notes="""
F6 lesson - bahut subtle bug. Hamari script har env ko seed + i deti thi. Par SB3 ka PPO(seed=k) khud
envs ko k, k+1, ..., k+7 se re-seed kar deta hai. To seed 0 ke streams 0-7, seed 1 ke 1-8: 8 me se 7 same!
Do "independent" runs asal me lagbhag same random episodes dekh rahe the.

Nateeja: seeds ke beech ka spread kam dikhta hai (understated), aur seeds 0,1,2 wale do sweeps
independent nahi.

Yeh 12 Sep ko pakda gaya - dono early H2 sweeps ke baad. Isliye H2 ko dobara spaced seeds 100/200/300
par chalaya (0 bhi nahi, taaki purane sweeps se bhi overlap na ho).

C5 (overshoot 4th arm) ko purane runs se pair karna tha, isliye wahan seeds 0/1 hi rahe - aur yeh limit
saaf likhi gayi hai.
""", source="RESEARCH_LOG '### Pre-run review of the perception model' (F6) and '### Found while drafting the paper "
            "(2026-10-19) - both H2 sweeps used overlapping seeds'; '## 2026-10-31 - H2 re-run with spaced seeds'")

    st = TOY["stats"]
    eq_slide(prs, "08 · basics", "Mean, standard deviation, standard error",
             "Three numbers that summarise n measurements - and how sure we are of their average.",
             r"\bar{d}=\frac{1}{n}\sum_{i=1}^{n}d_i,\qquad s=\sqrt{\frac{1}{n-1}\sum_{i=1}^{n}\left(d_i-\bar{d}\right)^2},\qquad \mathrm{SE}=\frac{s}{\sqrt{n}}",
             [(r"\bar{d}", "mean (average) of the n values"),
              (r"s", "sample standard deviation: typical spread of ONE value"),
              (r"n-1", "'ddof = 1': corrects the bias of estimating spread from few samples"),
              (r"\mathrm{SE}", "standard error: uncertainty of the MEAN; shrinks like 1/√n")],
             example=[f"Toy d = {st['d']}",
                      f"mean = {st['mean']:.4f}",
                      f"s (ddof 1) = {st['sd']:.4f};  ddof 0 would give {st['sd0']:.4f}",
                      f"SE = {st['se']:.4f}",
                      "(computed by teach_figs.py)"],
             why_text="With 2-3 seeds the n-1 matters (ddof 0 understates spread by ~18-29%); at n = 3 it even "
                      "flipped an 'error bars overlap?' verdict in this project.",
             label="Mean, sample sd, standard error", group="Statistics", eq_size=28,
             notes="""
Teen basic numbers:
- Mean: average.
- Standard deviation s: ek single value kitna phailta hai. n-1 se divide (ddof=1) - kyunki mean bhi
  usi data se nikala, isliye spread thoda kam dikhta hai; n-1 usko correct karta hai. 2-3 seeds par
  yeh 18-29% ka farak hai.
- Standard error SE = s/sqrt(n): MEAN kitna pakka hai. Zyada data -> SE chhota.

Toy (script se): d = [0.03, 0.05, -0.01, 0.04] -> mean 0.0275, s 0.0263 (ddof 0 dene par 0.0228), SE 0.0131.

Project story: n=3 par line aur triangle ke error bars ddof=0 se "disjoint" aur ddof=1 se "overlap"
dikhte the - verdict hi palat gaya. Sabak: "error bars overlap karte hain ya nahi" par claim mat banao;
paired test use karo.
""", source="rl/experiment.py _sd (ddof=1, '~18-29% at n=2-3'); RESEARCH_LOG '### Statistics housekeeping' (overlap flip); toy by teach_figs.py")

    concept(prs, "08 · pairing", "Paired comparisons: compare like with like", None,
            ["Both arms are trained on the SAME (shape, seed) cells. Compare them cell by cell: "
             "dᵢ = (arm A in cell i) - (arm B in cell i).",
             "Pairing cancels everything the two runs share: how hard the shape is, how lucky the seed was.",
             "The test then asks only: is the average dᵢ different from 0, given how much the dᵢ vary?",
             "Real mistake: O1's first analysis divided by the sd of ALL runs pooled (shape-to-shape spread "
             "included) and reported 'no measurable effect'; paired, it was +0.039, 9/12 pairs up, t = +2.17.",
             "Always also report k/n - in how many pairs arm A came out ahead."],
            cards=[("UNPAIRED", ["Big denominator (shape + seed + treatment noise). Real effects hide."], BAD),
                   ("PAIRED", ["Only the variation of the DIFFERENCES counts. Same data, much sharper."], GOOD)],
            take="Never compare two arms by whether their separate error bars overlap; test the paired differences.",
            take_color=VIOLET,
            notes="""
Pairing: dono arms same (shape, seed) cells par train hote hain. Har cell me farak nikalo: d_i = A - B.
Fayda: jo cheezen dono runs me common hain (shape kitna mushkil, seed kitna lucky) woh cancel ho jaati hain.

Real galti: O1 ke pehle analysis me sabhi runs ka pooled sd denominator tha - usme shapes ke beech ka
farak bhi tha (line 0.333 vs square 0.408). Result: "no measurable effect". Paired karne par: +0.039,
12 me se 9 pairs up, t = +2.17. Same data, alag (sahi) analysis.

k/n bhi hamesha batao: kitne pairs me A aage tha - ek simple, robust picture.
""", source="RESEARCH_LOG '### O1 RESULT' and '#### A bug in this entry's own analysis, found and fixed'")

    eq_fig_slide(prs, "08 · t-test", "The paired t-test",
                 "How many standard errors is the mean difference away from zero?",
                 r"t=\frac{\bar{d}}{s_d/\sqrt{n}},\qquad \mathrm{df}=n-1,\qquad |t|\geq t_{crit}\ \Rightarrow\ \mathrm{detectable}",
                 "t_dist.png",
                 [(r"\bar{d},\ s_d", "mean and sd of the paired differences"),
                  (r"\mathrm{df}", "degrees of freedom; n = 8 pairs → df = 7"),
                  (r"t_{crit}", "2.365 for df 7 (two-sided 5%); ~2.57 for n = 6; 2.13 for n = 16")],
                 after=[f"Toy (4 diffs above): t = {st['t']:.2f}",
                        "Under 'no true difference', |t| ≥ 2.365 happens only 5% of the time at df 7."],
                 why_text="t scales the effect by its own noise; the critical value is fixed BEFORE looking, "
                          "so a result cannot be argued into significance afterwards.",
                 label="Paired t statistic", group="Statistics", fig_w=7.0,
                 notes="""
Paired t-test: mean difference ko uske standard error se divide karo. t = d_bar / (s_d / sqrt(n)).
Matlab "farak, noise ke kitne guna hai". Agar sach me koi farak na ho, to t random hota hai aur
t-distribution follow karta hai (figure).

df = n - 1. n = 8 pairs -> df 7 -> critical value 2.365 (two-sided 5%). |t| >= 2.365 -> "detectable".
n=6 par ~2.57, n=16 par 2.13 (yeh values project scripts/log me use hui hain).

Figure: H4 v1 paper shift t = +0.24 (null, bell ke beech me) vs H4 replication t = +8.32 (bahut door,
clearly detectable).

Toy (script se): pichhle slide ke 4 differences par t = 2.09.

Critical value pehle se fix hota hai - baad me "thoda sa significant" bana ke nahi bech sakte.
""", source="RESEARCH_LOG pre-registered analyses (crit t(7)=2.365; RQ4 ~2.57 at df 5; pooled n=16 crit 2.13); "
            "'### H4 RESULT' (paper_shift t=+0.24); '### H4 v4 confirmation RESULT' (t=+8.32); toy by teach_figs.py")

    concept(prs, "08 · reporting", "'No detectable effect' is not 'no effect'", None,
            ["A null result (|t| below critical) means: at this n and this noise, we could not see a difference.",
             "It does NOT mean the difference is zero. H4 v1: standard errors 0.008-0.021 - an effect smaller "
             "than roughly 0.04 IoU could not have been seen.",
             "To claim 'the same', you need an EQUIVALENCE test (TOST, two slides ahead) with a margin fixed in advance.",
             "Every result here reports: n (seeds × shapes), mean ± sd, paired difference, pairs up k/n, t.",
             "'drop' and 'change' are opposites: drop = before - after. 'Fell from 0.393 to 0.379 (-0.014)' "
             "states the direction in words."],
            cards=[("ALLOWED WORDS", ["'no detectable difference', 'equivalent within ±0.05 IoU (TOST)', "
                                      "'consistent with', 'in simulation'."], GOOD),
                   ("FORBIDDEN WORDS", ["'no difference', 'the same', 'proves', 'significant' (when it is not), "
                                        "'novel', 'first'."], BAD)],
            notes="""
Null result ka matlab: is n aur is noise par farak dikh nahi saka. Iska matlab yeh NAHI ki farak zero hai.
H4 v1 me standard errors 0.008-0.021 the - 0.04 IoU se chhota effect dikh hi nahi sakta tha (power kam).

"Same" bolne ke liye equivalence test chahiye (TOST) - margin pehle se fix.

Reporting ke 5 cheezen: n, mean +/- sd, paired difference, k/n, t.

Direction ka dhyan: "drop" = pehle - baad. -0.003 ka drop asal me 0.003 ka GAIN hai. Ek baar kisi aur
tool ne "drop" ko "change" padh liya aur meaning palat gaya - isliye words me bolo: "0.393 se 0.379
tak gira (-0.014)".
""", source="RESEARCH_LOG '### The verdict, stated as pre-registered' (H4: SE 0.008-0.021, ~0.04); AGENTS.md section 6 "
            "rules 3 and 5; docs/PAPER_PLAN.md section 7")

    eq_fig_slide(prs, "08 · diff-in-diff", "Difference-in-differences: measure the LOSS, not the level",
                 "When two arms start at different levels, compare how much each one loses.",
                 r"\mathrm{DiD}=\left(y^{B}_{\mathrm{clean}}-y^{B}_{\mathrm{dist}}\right)-\left(y^{A}_{\mathrm{clean}}-y^{A}_{\mathrm{dist}}\right)",
                 "did.png",
                 [(r"y_{\mathrm{clean}}", "true IoU with no disturbance"),
                  (r"y_{\mathrm{dist}}", "true IoU under the disturbance"),
                  (r"A,\ B", "the two arms (e.g. A = camera_est, B = fk)"),
                  (r"\mathrm{DiD}>0", "A loses LESS than B: recovery")],
                 after=["Computed per (shape, seed) cell, then a paired t-test on the 8 DiDs."],
                 why_text="An arm that simply draws better everywhere is not 'recovering'. Only a smaller LOSS "
                          "from its own clean score counts as recovery.",
                 label="Difference-in-differences (recovery)", group="Statistics", fig_w=7.2,
                 notes="""
Difference-in-differences (DiD): har arm ka apna nuksaan naapo - clean score minus disturbed score - aur
phir dono nuksaanon ka farak lo. DiD > 0 matlab arm A ne KAM khoya - yeh recovery hai.

Left figure (toy): arm A shuru se upar hai, par dono 0.10 khote hain. Absolute farak disturbed me bhi
0.10 hai - lagta hai "A jeeta" - par DiD = 0. Koi recovery nahi, bas head start.

Right figure (real, H4 replication, paper shift): camera_est 0.375 -> 0.329 (0.046 khoya), fk 0.369 ->
0.203 (0.165 khoya). Clean gap sirf +0.006 - dono barabar shuru hue. DiD +0.119 - asli recovery.

Har (shape, seed) cell me DiD nikalte hain, phir 8 DiDs par paired t-test.
""", source="RESEARCH_LOG '### Pre-registered analysis (fixed before the remaining 14 runs)' (primary endpoint) and "
            "'### H4 v4 confirmation RESULT' (0.375/0.329, 0.369/0.203; losses 0.046, 0.165; DiD +0.119; clean gap +0.006)")

    tabular(prs, "08 · diff-in-diff", "The lesson that created the rule (19 Oct 2026)",
            "Interim H4 at 18/32 runs (n = 4 cells): the script declared 'camera recovers better'.",
            ["disturbance", "camera loses", "fk loses", "diff-in-diff (camera better if > 0)", "t (n = 4)"],
            [["slip", "+0.008", "-0.021", "-0.030", "-1.01"],
             ["paper_shift", "+0.041", "+0.049", "+0.007", "+0.30"],
             ["ink_failure", "+0.025", "+0.031", "+0.006", "+0.38"]],
            colw=[2.4, 2.0, 2.0, 3.6, 1.8], size=13, row_h=0.45,
            below=["The script's verdict used the ABSOLUTE gap on paper_shift: camera - fk = +0.061, t = 2.45.",
                   "But with NO disturbance camera already beat fk by +0.053 (0.386 vs 0.333): the 'win' was a head start.",
                   "Subtracting each arm's own clean score leaves +0.007, t = +0.30 - nothing. At n = 8 the clean gap "
                   "itself shrank to +0.016 (t = +0.52): the interim reading evaporated.",
                   "Rules adopted: diff-in-diff as the primary endpoint; no verdicts from interim data."],
            take="'A gap under disturbance that equals the clean gap is not recovery.' (AGENTS.md rule 4)",
            take_color=BAD,
            notes="""
Yeh woh galti hai jisse DiD rule bana. 19 Oct ko H4 ke 18/32 runs (n=4) par script ne bola "camera
recovers better" - paper shift par camera - fk = +0.061, t = 2.45.

Par bina disturbance ke bhi camera fk se +0.053 aage tha (0.386 vs 0.333). Matlab disturbed me jo farak
dikha woh lagbhag poora "head start" tha. Har arm ka apna nuksaan nikaalne par: camera 0.041 khoya, fk
0.049 - DiD +0.007, t = +0.30. Kuch nahi.

Aur n=8 par clean gap bhi +0.016 (t=0.52) reh gaya - interim reading poori tarah gayab.

Do rules bane: (1) DiD primary endpoint; (2) interim data par verdict nahi (no optional stopping).
Interview me yeh story bahut achhi lagti hai - dikhata hai ki aap apne result ko challenge karte ho.
""", source="RESEARCH_LOG '### Interim warning - the script's verdict was measuring the wrong thing' and "
            "'### H4 RESULT' / '### Honest limits' (clean gap +0.016 at n=8); AGENTS.md section 6 rule 4")

    eq_fig_slide(prs, "08 · equivalence", "TOST: how to show two arms are equivalent",
                 "Two one-sided tests: is the difference above -Δ AND below +Δ?",
                 r"t_{L}=\frac{\bar{d}+\Delta}{\mathrm{SE}},\qquad t_{U}=\frac{\bar{d}-\Delta}{\mathrm{SE}},\qquad \mathrm{equivalent}\Leftrightarrow \mathrm{90\%\ CI\ of}\ \bar{d}\subset(-\Delta,+\Delta)",
                 "tost.png",
                 [(r"\Delta", "equivalence margin, fixed BEFORE the run: 0.05 IoU (~13% of the ~0.38 level)"),
                  (r"t_L,\ t_U", "both one-sided tests must reject (α = 0.05 each)"),
                  (r"p_{\mathrm{TOST}}", "the larger of the two one-sided p-values")],
                 after=["H2 spaced: d = +0.004, 90% CI [-0.024, +0.033], p_TOST = 0.008 → equivalent.",
                        "Old overlapping seeds: CI [-0.007, +0.063] → not shown."],
                 why_text="A plain t-test can only fail to find a difference; TOST can positively support "
                          "'no difference bigger than Δ' - the claim H2 actually needs.",
                 label="TOST equivalence test", group="Statistics", eq_size=25, fig_w=6.6,
                 notes="""
TOST (two one-sided tests): "equivalent" claim karne ka sahi tareeka.
Margin Delta pehle se fix karo - kitna farak "practically koi farak nahi" maana jaye. H2 me 0.05 IoU
(~0.38 level ka ~13%), run se PEHLE chuna.

Do tests: (1) kya farak -Delta se upar hai? (2) kya +Delta se neeche hai? Dono reject ho to equivalent.
Simple picture: 90% confidence interval poora (-Delta, +Delta) ke andar ho.

H2 spaced sweep: d = +0.004, 90% CI [-0.024, +0.033], p_TOST = 0.008 -> equivalent within +/-0.05.
Purane overlapping seeds par CI [-0.007, +0.063] - +0.05 cross karta hai -> equivalence NOT shown. Dono
report kiye; naya (pre-registered) cite kiya; pool nahi kiya.

Limit: margin 0.03 hota to pass nahi hota (CI half-width ~0.03). Isliye margin pehle fix karna zaroori -
baad me chauda karke pass karwana cheating hai.
""", source="rl/h2_equivalence.py tost(); RESEARCH_LOG '### Pre-registered analysis (written before any run finished)' (margin 0.05) "
            "and '### H2 spaced RESULT' (d, CI, p_TOST; old-seed contrast; margin 0.03 would not pass)")

    concept(prs, "08 · pre-registration", "Pre-registration and no optional stopping", None,
            ["Pre-registration: write down - BEFORE the runs - the primary comparison, the test, the critical "
             "value, and what each possible outcome will mean. Here it is a dated entry in the research log.",
             "No optional stopping: do not peek, add runs until it looks significant, and stop. The only "
             "permitted follow-up was fixed in advance: if |t| landed in 1.5-2.365, add seeds 200/300 for ALL arms.",
             "Primary vs secondary: one primary endpoint per experiment; secondary results are reported but "
             "labelled, because many tests produce some 'significant' ones by chance.",
             "Exploratory vs confirmatory: the H4 series (v1, v2 null; v3 privileged; v4) was exploratory; the "
             "seeds-200/300 replication of v4 was the confirmatory test.",
             "Calibration is not tuning: the held-out camera missed its target range and was reported as is."],
            cards=[("WHY IT MATTERS", ["With 4 H4 designs tried, one positive could be luck. A fresh-seed, "
                                       "pre-registered replication is what makes it credible."], VIOLET),
                   ("EVEN THE FRAMING", ["PAPER_PLAN fixed how the paper's story changes for each H4 outcome "
                                         "before the result was read."], GOOD)],
            notes="""
Pre-registration: run se PEHLE likh do - primary comparison kya hai, kaunsa test, critical value, aur har
possible result ka matlab kya hoga. Yahan woh research log ki dated entry hai.

No optional stopping: baar-baar jhaank kar, runs badha-badha kar, "significant" dikhte hi ruk jaana -
mana hai. Ek hi follow-up allowed tha (pehle se likha): agar |t| 1.5 aur 2.365 ke beech ho, to SABHI arms
ke liye seeds 200/300 add karo.

Primary vs secondary: har experiment ka ek primary endpoint. Bahut saare tests me kuch chance se
significant aa jaate hain, isliye secondary ko label karke report karte hain.

Exploratory vs confirmatory: H4 ke 4 designs try hue - inme ek positive luck bhi ho sakta tha. Isliye
v4 ko fresh seeds 200/300 par, pre-registered, replicate kiya - yahi confirmatory hai.

PAPER_PLAN me result padhne se pehle hi likha tha ki har H4 outcome par paper ki kahani kaise badlegi.
""", source="RESEARCH_LOG pre-registration entries (2026-10-19, H4 v3/v4, '## 2026-11-07 - H4 v4 confirmation launched'); "
            "docs/PAPER_PLAN.md section 3; '### Calibration, measured rather than asserted'")

    grid(prs, "08 · reproducibility", "Reproducibility practices used in every sweep", None,
         [("APPEND-ONLY RESULTS", ["Each finished run appends one JSON line to results/*.jsonl; files are never "
                                   "edited or deleted."], PRIMARY),
          ("RESUMABLE", ["A crashed worker (exit code 4, power cuts) is relaunched with the same command; "
                         "finished runs are skipped. Resumed results were checked bit-identical."], GOOD),
          ("CONFIG-DRIFT WARNING", ["The resume key ignores settings, so a loud warning fires if recorded runs "
                                    "used different timesteps / episode length."], WARN),
          ("THREADS FIXED", ["OMP_NUM_THREADS = MKL_NUM_THREADS = 1 for every parallel sweep; thread count recorded."], WARN),
          ("ADDITIVE CODE CHANGES", ["New options are default-off, the old file is backed up, and old configs are "
                                     "checked bit-identical before any new run."], VIOLET),
          ("EVERY NUMBER SOURCED", ["The paper's lint script fails a draft if a decimal lacks a '% src:' pointer to "
                                    "the log; this deck names a source in every slide's notes."], ACCENT)],
         cols=3, notes="""
Reproducibility ke liye kya kiya:
- Results append-only JSONL - kabhi edit/delete nahi.
- Resumable sweeps - worker crash (unexplained exit code 4, power cut) hone par same command dobara;
  complete runs skip. Resume ke baad results bit-identical check hue (param200 3 restarts ke baad bhi).
- Config drift warning: agar file me purane runs alag settings ke hain to zor se warning.
- Threads 1 par fix aur record.
- Code changes additive, default off, backup, bit-identical check.
- Har number ka source: paper ka check_paper.py bina "% src:" wale decimal ko error deta hai.

Interview me: "Every number in my paper is traceable to a dated log entry and a script's printed output."
""", source="AGENTS.md section 5; rl/experiment.py warn_config_drift; RESEARCH_LOG '### Generalisation part 2 RESULT' "
            "(bit-identical after restarts); docs/paper/main.tex header rules")
