"""Section 3 - computer vision from scratch."""
from kit import *  # noqa: F401,F403
from teach_figs import TOY


def build(prs, toc):
    section(prs, 3, "Computer vision from scratch",
            "How a picture becomes numbers, how a camera loses information, how we score a drawing "
            "(IoU and friends), how the simulated camera is built, and how a photo can reveal that "
            "the paper moved.",
            ["Images are arrays", "Pinhole camera", "Thresholding & masks", "IoU, MSE, chamfer",
             "The simulated camera (8 parameters)", "Domain randomisation", "Phase correlation"],
            """
Section 3: computer vision. Yahan teen baatein sabse zaroori hain: (1) image sirf numbers ki
grid hai; (2) camera information khota hai - resolution, blur, noise; (3) drawing ko score karne
ke liye IoU kyun chuna. End me phase correlation - woh trick jisse camera paper ka khisakna
pakadta hai (H4 v4 ka dil).""", toc)

    sh = TOY["sheet"]
    concept(prs, "03 · images", "An image is just a grid of numbers", None,
            ["Greyscale image = a matrix of H × W numbers, each 0 (black) to 255 (white): one byte (uint8).",
             "Colour image = H × W × 3 (red, green, blue planes).",
             "Binary mask = every pixel is either 'on' or 'off'. Our convention: 255 = ink / target, 0 = blank.",
             f"The canvas (true ink) is a {sh['canvas_res']}×{sh['canvas_res']} mask; targets are made at 512 px and "
             "resized to it.",
             "The agent's observation is 64 × 64 × 3: three masks stacked as 'channels' - target, "
             "what has been drawn, and a dot at the pen position.",
             "Resizing loses detail: a 14-px stroke at 512 px becomes ~3.5 px at 128 and ~1.75 px at 64."],
            cards=[("WHY SMALL IMAGES", ["Every training step renders and feeds an image to a neural net. "
                                         "64 × 64 keeps ~200k steps per run feasible on a laptop CPU."], PRIMARY),
                   ("WHY CHANNELS", ["Stacking target / drawn / pen lets one convolutional network compare "
                                     "them pixel by pixel at the same location."], VIOLET)],
            notes="""
Computer ke liye image sirf numbers ki table hai. Greyscale me har pixel 0 (kala) se 255 (safed)
tak - ek byte. Colour me teen tables (R, G, B). Binary mask me pixel ya to "on" hai ya "off" -
hamare code me 255 matlab ink/target, 0 matlab khaali.

Hamara canvas 128x128 mask hai. Agent ko 64x64x3 image milti hai: teen masks ek ke upar ek
(channels): channel 0 target, channel 1 ab tak kya draw hua, channel 2 pen kahan hai (ek dot).

Chhoti images kyun? Har step par image banti hai aur neural network me jaati hai - 200k steps
per run laptop CPU par tabhi possible hai jab image chhoti ho. Keemat: detail kho jaati hai -
14 px ki line 64 px par ~1.75 px reh jaati hai (agla figure).

Channels kyun stack kiye? CNN ek hi location par teeno ko saath dekhta hai - "target yahan hai,
ink yahan nahi hai" - yahi comparison drawing ke liye chahiye.
""", source="rl/draw_env.py docstring and _obs (obs_res 64, channels target/drawn/pen); rl/targets.py "
            "(RES 512, STROKE_PX 14); downsampled widths from rl/perception.py calibration note")

    s = slide(prs, "The pinhole camera: how 3-D becomes 2-D", "03 · camera",
              "Similar triangles: the farther the paper, the smaller its image.")
    top = s._top + 0.05
    rect(s, M, top, 5.6, 1.25, fill=WASH, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    place_eq(s, r"x = f\,\frac{X}{Z}", M + 0.2, top + 0.08, 5.2, 1.1, size=40)
    formula("Vision", "Pinhole projection", r"x = f\,\frac{X}{Z}")
    pic(s, "pinhole.png", M, top + 1.4, 5.8, 3.4)
    bullets(s, ["X = size on the paper, Z = distance to the camera, f = focal length, x = size on the "
                "sensor. (Real cameras add lens distortion; ignored here.)",
                "Our simulated camera looks straight down at the sheet ('top-down', 'near-fixed'), so the "
                "sheet maps to the image by a simple scale - no perspective tricks needed.",
                "Then the continuous image is sampled by a pixel grid: resolution loss.",
                "Real B6 render: a 480×480 virtual RGB camera above the paper (sim/04_camera_capture.py).",
                "A tilted camera gives a perspective warp; we model only a small RESIDUAL warp (corners "
                "registered), see the camera model slide."],
            M + 6.1, top, CW - 6.1, 4.85, start=15)
    why(s, "A top-down, registered camera makes 'paper pixel ↔ image pixel' almost one-to-one, so the "
           "experiment tests learning from perception, not camera calibration.")
    note(s, """
Pinhole camera: ek chhota sa ched, peeche sensor. Similar triangles se: image me size x = f * X/Z.
Physics wala ray optics hi hai. Paper jitna door (Z bada), image utni chhoti.

Hamara camera paper ke bilkul upar se neeche dekhta hai (top-down). Isliye paper ka har point
image me ek simple scale se map hota hai - perspective ka jhanjhat almost nahi. Real B6 pipeline
me PyBullet ka 480x480 virtual camera paper ke upar tha.

Kyun aisa? Hum "camera calibration" test nahi kar rahe; hum test kar rahe hain ki perception se
seekhna kitna mehnga hai. Isliye geometry simple rakhi, aur imperfection (blur, noise, resolution,
chhota residual warp) alag se controlled tareeke se daala.

Asli camera me lens distortion bhi hota hai - yahan ignore kiya, hardware par calibrate karna padega.
""", "standard pinhole model; RESEARCH_LOG '### B6 - the robot sees its own drawing'; rl/perception.py "
       "(warp_px is a residual registration error)")

    figure(prs, "03 · camera", "The real camera pipeline (B6): render → extract → compare",
           "A PyBullet camera photographs the paper; OpenCV pulls the ink out; IoU against the truth.",
           "fig_vision_pipeline.png",
           ["1. Park the arm first: it occluded the paper (first capture: ~40% visible, ink ≈ 0).",
            "2. Threshold: Otsu was fooled by the dark arm; with the arm parked a fixed threshold (128) "
            "on paper pixels works.",
            "3. Validated: perceived vs true IoU 0.871 (line) and 0.882 (square); perceived strokes "
            "~14% thicker.",
            "4. Orientation calibrated, not assumed: of 8 flips/rotations the identity won at IoU 0.998."],
           fig_w=7.4, take="The camera recovers ~0.87-0.88 of a drawing: good, but NOT the truth - "
                           "exactly the imperfection the study is about.", take_color=ACCENT,
           notes="""
Yeh asli simulated camera pipeline hai (B6). Teen problems measurement se pakde gaye:
1) Arm paper ko dhak raha tha - photo se pehle arm ko "park" karo (seedha upar). Asli drawing
   robots bhi yahi karte hain.
2) Otsu threshold (automatic) dark arm ki wajah se galat split kar raha tha; arm hatane ke baad
   fixed threshold 128 kaafi.
3) Texture cache bug (pichhle section me).

Result: camera drawing ka ~87-88% sahi pakadta hai (IoU 0.871 line, 0.882 square), strokes ~14%
mote dikhte hain. Orientation bhi check ki - 8 possible flip/rotation me se identity sabse sahi
(IoU 0.998).

Key point: camera achha hai par perfect nahi. Yahi gap - "perceived" vs "true" - poore project
ka subject hai.
""", source="RESEARCH_LOG '### B6 - the robot sees its own drawing (virtual camera + OpenCV) (2026-07-24)'")

    t = TOY["thr"]
    eq_fig_slide(prs, "03 · thresholding", "Thresholding: grey photo → binary ink mask",
                 "Every pixel darker than a threshold τ is called 'ink'.",
                 r"B(u,v)=\mathbf{1}\left[I(u,v)<\tau\right],\qquad \tau = I_{ink}+f\,(I_{paper}-I_{ink})",
                 "threshold_toy.png",
                 [(r"I(u,v)", "grey level of pixel (u, v), 0-255"),
                  (r"\mathbf{1}[\cdot]", "indicator: 1 if true, else 0"),
                  (r"I_{ink},\ I_{paper}", "grey level of ink and of paper as the sensor sees them"),
                  (r"f", "where τ sits between them (0 = on the ink, 1 = on the paper)")],
                 after=[f"Toy: ink {t['ink']:.0f}, paper {t['paper']:.0f}, f = {t['frac']} → τ = {t['tau']:.1f}",
                        "Fixed project camera: f = 195/255 ≈ 0.765"],
                 why_text="A RELATIVE threshold keeps working when exposure or paper tone changes; an "
                          "absolute grey level (the first version) sat below faint ink and detected nothing.",
                 label="Relative threshold (binarisation)", group="Vision",
                 notes="""
Thresholding: har pixel ko poochho "kya yeh threshold se gehra hai?" Haan -> ink (1), nahi ->
paper (0). Histogram me do pahaad dikhte hain - ink ka aur paper ka - threshold beech me.

Kahan rakhein? Pehle version me threshold ek fixed grey level tha (45-90). Problem: agar ink
halki ho (grey 64) aur threshold 45, to threshold ink se bhi neeche - kuch detect hi nahi hoga.
Isliye perception.py me threshold RELATIVE hai: ink level aur paper level ke beech ek fraction f
par, aur woh levels gain ke BAAD (sensor jaise dekhta hai) liye jaate hain. Asli auto-threshold
pipelines aise hi kaam karti hain.

Toy example (script ne compute kiya): ink 60, paper 235, f=0.5 -> tau 147.5. Project ke fixed
camera me f = 195/255 ~0.765 (purane ">60" rule ke barabar).
""", source="rl/perception.py (thresh_frac, step 7 'binarise'); RESEARCH_LOG 2026-09-12 Stage 2 'The threshold "
            "cannot be an absolute grey level'; toy numbers by teach_figs.py")

    figure(prs, "03 · resolution", "Resolution loss - and the fast camera used for training",
           "Downsampling averages pixels; thin strokes get thinner, then thresholding can break them.",
           "downsample_toy.png",
           ["The fast proxy camera (DrawEnv._perceive): shrink the canvas to 150 px, threshold > 60, "
            "enlarge back to 128, threshold > 50.",
            "Calibrated: perceived-vs-true IoU ~0.83 (real B6 render ~0.88).",
            "Validated against the real render on trained agents: mean reward gap 0.010.",
            "Real render in the loop: 8.6 steps/s vs 2296 for the proxy (~270× slower)."],
           fig_w=7.2, take="Why a proxy: the same reward signal ~270× faster - so the full multi-seed "
                           "study is possible; the real render is the confirmation.", take_color=VIOLET,
           notes="""
Resolution loss: jab image chhoti karte hain to pixels ka average hota hai. Moti line patli ho
jaati hai; aur threshold lagane par kahin-kahin toot bhi sakti hai.

Training me har step par asli 3-D camera render bahut slow tha. Isliye ek fast "proxy" camera
banaya (_perceive): canvas ko 150 px tak chhota karo, threshold, wapas 128 px. Isse perceived-vs-
true IoU ~0.83 aata hai (asli render ~0.88 tha).

Kya proxy theek hai? Validate kiya: trained agents ke canvases par proxy aur asli render dono se
reward nikala - mean gap sirf 0.010. Aur speed: asli render 8.6 steps/second, proxy 2296 -
~270 guna tez. Asli render se poora training ~6.5 ghante per run hota.

Interview me: "I used a validated proxy camera for training and confirmed it against a real render."
""", source="rl/draw_env.py _perceive; RESEARCH_LOG '### H2 experiment - VISION reward' (proxy ~0.83) and "
            "'### Real camera-in-the-loop' (gap 0.010, 8.6 vs 2296 steps/s); figure = toy (teach_figs.py)")

    i = TOY["iou"]
    eq_fig_slide(prs, "03 · metrics", "IoU: the score of a drawing",
                 "Intersection over Union - how much of the ink and the target overlap, out of all ink + target.",
                 r"\mathrm{IoU}(A,B)=\frac{|A\cap B|}{|A\cup B|}",
                 "iou_toy.png",
                 [(r"A", "set of inked pixels (what was drawn)"),
                  (r"B", "set of target pixels"),
                  (r"|A\cap B|", "pixels that are both ink and target"),
                  (r"|A\cup B|", "pixels that are ink or target (or both)")],
                 after=[f"Toy ring shifted 3 px: |A∩B| = {i['inter']}, |A∪B| = {i['union']} → IoU = {i['iou']:.3f}",
                        "1 = perfect overlap, 0 = none. Stray ink grows the union, so it LOWERS IoU."],
                 why_text="IoU punishes both missing ink and stray ink, so it cannot be gamed by scribbling; "
                          "D03 and D09 also score geometric drawing with IoU.",
                 label="Intersection over Union", group="Vision",
                 notes="""
IoU = intersection / union. Intersection: woh pixels jo ink bhi hain aur target bhi. Union: woh
pixels jo ink ya target (ya dono) hain. Perfect drawing -> 1. Bilkul alag -> 0.

Toy example (script se): ek ring target, aur drawing wahi ring 3 px khiski hui. Overlap 168 px,
union 624 px -> IoU ~0.269. Dekho - sirf 3 pixel khiskane se IoU 0.27 par aa gaya. IoU bahut
sakht hai thin shapes ke liye, isliye targets mote rakhe.

Kyun IoU? (1) Agar agent zyada ink bikhere (scribble), union badhta hai aur IoU girta hai - to
cheating nahi ho sakti. (2) Agar ink kam ho, intersection kam -> IoU girta hai. (3) Literature
(D03 "pixel accuracy", D09 terminal 80*IoU) bhi yahi use karta hai.

Fairness rule yaad rakho: evaluation me IoU hamesha TRUE canvas par naapa jaata hai.
""", source="rl/metrics.py iou(); docs/PROJECT_PROPOSAL_v2.md section 7 (D03, D09 use IoU); toy numbers by teach_figs.py")

    steps_slide(prs, "03 · metrics", "The other metrics, and what each one catches",
                "All take two binary masks; all are in rl/metrics.py.",
                [("MSE", r"\mathrm{MSE}=\frac{1}{N}\sum_{p}\left(A_p-B_p\right)^2",
                  "Fraction of pixels that disagree (masks as 0/1). Dominated by the empty background.",
                  "Mean squared error (masks)"),
                 ("coverage", r"\mathrm{cov}=\frac{|A\cap B|}{|B|},\qquad \mathrm{prec}=\frac{|A\cap B|}{|A|}",
                  "Coverage (recall): how much of the target is inked. Precision: how much ink is on target.",
                  "Coverage and precision"),
                 ("chamfer", r"d_{ch}=\frac{1}{2}\left(\frac{1}{|A|}\sum_{a\in A}\min_{b\in B}\|a-b\|+\frac{1}{|B|}\sum_{b\in B}\min_{a\in A}\|b-a\|\right)",
                  "Average distance (px) from each ink pixel to the nearest target pixel and back. Soft: "
                  "'close but not overlapping' still scores well.", "Chamfer distance"),
                 ("path ratio", r"\mathrm{path\ ratio}=\frac{\mathrm{distance\ travelled}}{\mathrm{target\ outline\ length}},\quad \mathrm{SNR}=\frac{\#\mathrm{strokes\ drawn}}{\#\mathrm{strokes\ target}}",
                  "Path ratio > 1 = wasted travel (zig-zag, spurs). SNR > 1 = fragmented ink (D09's metric).",
                  "Path ratio and stroke-number ratio")],
                take="IoU alone is blind to zig-zag and fragmentation; path_ratio and SNR were added for that.",
                eq_w=6.6, eq_size=24, group="Vision",
                notes="""
IoU ke alawa aur metrics bhi log hote hain:
- MSE: kitne pixels match nahi karte. Problem: zyada-tar image khaali background hai, to khaali
  canvas ka MSE bhi chhota aata hai (agla slide).
- Coverage (recall) aur precision: target ka kitna hissa dhaka, aur ink ka kitna hissa target par.
  IoU in dono ka combination jaisa hai.
- Chamfer distance: har ink pixel se nearest target pixel ki doori ka average (aur ulta) -
  "soft" metric, thoda khiska hua stroke bhi achha score karta hai.
- path_ratio: pen kitna chala / target ki outline kitni lambi. 1 = ek baar perfectly trace.
  Bada = zig-zag ya faltu ghoomna.
- SNR (stroke number ratio, D09 se): kitne alag strokes bane / target me kitne chahiye. Jab tak
  pen hamesha neeche hai, SNR ~1 by construction; pen-up/down (A2) ke baad informative hua.

Bug story: path_ratio ka denominator (target perimeter) closed shapes par ~1.9x kam naapa ja raha
tha (RETR_EXTERNAL annulus ka sirf bahar wala kinara leta tha). RETR_LIST se fix - square ka
"pen ne 3x travel kiya" asli me 1.59x tha. Section 7 me detail.
""", source="rl/metrics.py (mse, coverage, precision, chamfer, snr, path_ratio); RESEARCH_LOG "
            "'### BUG 2 - target_perimeter_px under-measured every closed shape by ~1.9x'")

    concept(prs, "03 · metrics", "Why IoU and not MSE - a worked example", "Same toy ring as before (computed by teach_figs.py).",
            [f"Target ring vs a drawing shifted by 3 px: IoU = {i['iou']:.3f}, MSE = {i['mse']:.3f}.",
             f"Target ring vs a BLANK canvas: IoU = {i['blank_iou']:.0f}, MSE = {i['blank_mse']:.3f}.",
             "So by MSE, drawing nothing scores BETTER than a decent attempt - because most pixels are "
             "background and blank agrees with background everywhere.",
             f"Chamfer for the shifted ring is only {i['chamfer']:.2f} px: a soft metric that forgives near misses.",
             "IoU ignores the background entirely: it only counts ink and target pixels."],
            cards=[("REWARD CONSEQUENCE", ["An MSE-based reward would make 'draw nothing' a strong "
                                           "local optimum - the trap the first PPO runs fell into anyway."], BAD),
                   ("WHERE THE OTHERS ARE USED", ["MSE, chamfer, coverage, precision are logged for "
                                                  "analysis; only IoU drives reward and scoring."], PRIMARY)],
            take="Choose the metric that cannot be satisfied by doing nothing.", take_color=VIOLET,
            notes="""
Yeh slide interview ke liye gold hai. Same toy ring: 3 px khiski drawing ka IoU ~0.27 aur MSE
~0.111. Khaali canvas ka IoU 0 par MSE ~0.097 - yaani MSE ke hisaab se KUCH NA BANANA ek theek
attempt se BEHTAR hai! Kyun? Image ka zyada-tar hissa background hai, aur khaali canvas background
se har jagah match karta hai.

IoU background ko ignore karta hai - sirf ink aur target pixels ginta hai. Isliye "kuch mat karo"
IoU me 0 hai.

Reward design me yeh bahut zaroori hai: agar reward MSE hota, to "draw nothing" ek bahut strong
trap hota. (Waise bhi pehle PPO runs "draw nothing" trap me phase the - Section 7.)

Chamfer ~0.98 px - soft metric, near misses maaf kar deta hai. Analysis ke liye achha, par reward
ke liye IoU chuna.
""", source="toy numbers computed by learning/project_deck/teach_figs.py (not project results); "
            "rl/metrics.py; RESEARCH_LOG '### Reward shaping - two local optima found and fixed'")

    s = slide(prs, "The simulated camera: an 8-parameter imaging chain", "03 · camera model",
              "rl/perception.py applies the steps in the order a real camera does.")
    pipeline(s, [("paper tone", "sheet not\npure white"), ("ink contrast", "how dark\nink reads"),
                 ("warp", "residual pose\nerror (px)"), ("resolution", "sensor\npixels"),
                 ("blur", "defocus σ"), ("gain + noise", "exposure,\nsensor noise"),
                 ("threshold", "relative\nfraction f")],
             M, s._top + 0.1, CW, 1.15, colors=[ACCENT], gap=0.22, title_size=12, sub_size=10.5)
    rect(s, M, s._top + 1.45, CW, 1.0, fill=WASH, line=LINE, shape=MSO_SHAPE.ROUNDED_RECTANGLE, radius=0.06)
    lat = r"I=\mathrm{clip}\left(g\cdot\mathrm{blur}_{\sigma}\left(\mathrm{resize}_{s}\left(\mathrm{warp}(I_0)\right)\right)+n,\ 0,\ 255\right),\quad n\sim\mathcal{N}(0,\sigma_n^2)"
    place_eq(s, lat, M + 0.2, s._top + 1.5, CW - 0.4, 0.9, size=26)
    formula("Vision", "Camera imaging chain", lat)
    bullets(s, ["I₀ = clean grey image of the sheet (paper tone, ink contrast applied); g = gain; "
                "σ = blur width; s = sensor size; n = Gaussian noise; then binarise with the relative τ.",
                "Clipping to [0, 255] matters: without it a gain above 1 would IMPROVE the signal-to-noise "
                "ratio, the opposite of an over-exposed photo.",
                "Outside the sheet the warp fills with PAPER, not by copying edge pixels (that created "
                "+34-39% phantom ink - a bug fixed before the sweep)."],
            M, s._top + 2.65, CW, 2.0, start=15)
    why(s, "Each step is a physical way a real camera loses ink; making them explicit lets us make "
           "the camera worse on purpose and measure the effect.")
    note(s, """
Asli camera kaise information khota hai - perception.py usko 8 steps me model karta hai, usi
order me jaise asli camera me hota hai: paper ka rang (poora safed nahi), ink kitni gehri,
camera ka thoda tedha hona (residual warp), sensor resolution, blur (focus), gain (exposure) aur
noise, aur end me threshold.

Equation: I = clip(g * blur(resize(warp(I0))) + noise, 0, 255). Phir relative threshold se mask.

Do bugs jo pehle hi pakad liye (sweep se pehle review):
- Clip na karne par gain > 1 se signal-to-noise BEHTAR ho jaata - ulta physics. Asli sensor
  saturate hota hai, isliye clip.
- Warp ke baad sheet ke bahar ka area edge pixels copy karke bhara ja raha tha - ek ink pixel
  edge par ho to poori border par phantom ink (+34-39%). Fix: bahar paper ka rang.

Kyun itna detail? Taaki hum camera ko jaan-boojh kar kharab kar sakein aur naap sakein (domain
randomisation, agla slide).
""", source="rl/perception.py Camera.perceive (steps 1-8); RESEARCH_LOG '### Pre-run review of the perception "
            "model - six fixes' (F7 border, F11 saturation)")

    tabular(prs, "03 · domain randomisation", "Domain randomisation: train on many cameras, test on a worse one",
            "Camera parameters are drawn once per EPISODE from a range (Tobin et al., IROS 2017).",
            ["parameter", "TRAIN range", "HELD-OUT range (outside train on every axis)"],
            [["paper tone", "0.90 – 1.00", "0.78 – 0.88 (dingier)"],
             ["ink contrast", "0.75 – 1.00", "0.55 – 0.72 (fainter)"],
             ["residual warp (px)", "0 – 1.5", "2.0 – 3.0"],
             ["sensor resolution (px)", "96 – 128", "76 – 92 (coarser)"],
             ["blur σ", "0 – 1.2", "1.3 – 1.8 (softer)"],
             ["gain / noise sd", "0.85–1.20 / 0–8", "0.60–0.78 / 10–16"],
             ["threshold fraction f", "0.45 – 0.85", "0.28 – 0.43"]],
            colw=[3.2, 3.2, 5.4], size=12.5, row_h=0.37,
            below=["Ink recovered from a PERFECT drawing: fixed camera 0.834, train 0.756, held-out 0.394 "
                   "(criterion set in advance was 0.45-0.60; missed, reported as measured, not re-tuned).",
                   "Per episode, not per step: reward = IoU(t) - IoU(t-1), so a camera changing between steps "
                   "would put camera noise into the reward."],
            take="Only resolution, blur and warp actually move the result; gain, tone, contrast cancel by "
                 "construction (relative threshold).", take_color=WARN,
            notes="""
Domain randomisation (Tobin et al. 2017): training ke dauraan camera ke parameters har episode
naye random values se lo. Agar policy kai cameras par kaam kare, to woh "drawing" seekh rahi hai,
kisi ek camera ki aadat nahi.

Do distributions: TRAIN (jisme seekhta hai) aur HELD-OUT (har axis par TRAIN se bahar - aur kharab).
Held-out camera ek perfect drawing ka sirf 0.394 hissa pakadta hai (fixed camera 0.834). Pehle
se criterion 0.45-0.60 tha - miss hua, aur parameters ko aur ghuma ke target me laane ke bajaye
jo mila woh report kiya. Yeh honesty ka example hai: "knob ghumate raho jab tak number sahi na
aaye" - aise calibration result ban jaata hai.

Per episode kyun, per step kyun nahi? Reward = IoU(t) - IoU(t-1). Agar beech me camera badla to
reward me camera ka noise aa jayega - agent ko us cheez ka reward/saza milegi jo usne kiya hi nahi.

Honest scope: 8 me se sirf 3 axes (resolution, blur, warp) asar karte hain; gain/tone/contrast
relative threshold ki wajah se cancel ho jaate hain - "8-axis" bolna overstatement hoga.
""", source="rl/perception.py TRAIN / HELDOUT; RESEARCH_LOG '### Calibration, measured rather than asserted' "
            "and '### Which axes actually do anything'")

    pc = TOY["pc"]
    eq_fig_slide(prs, "03 · phase correlation", "Phase correlation: find how far a picture has slid",
                 "Used by the camera_est arm (H4 v4) to estimate the sheet offset from its own photo.",
                 r"R=\frac{\mathcal{F}\{b\}\ \overline{\mathcal{F}\{a\}}}{\left|\mathcal{F}\{b\}\ \overline{\mathcal{F}\{a\}}\right|},\qquad (\Delta r,\Delta c)=\arg\max\ \mathcal{F}^{-1}\{R\}",
                 "phase_corr_toy.png",
                 [(r"a,\ b", "belief canvas (what kinematics expects) and the photo"),
                  (r"\mathcal{F}\{\cdot\}", "2-D Fourier transform"),
                  (r"\overline{z}", "complex conjugate"),
                  (r"R", "cross-power spectrum, normalised to unit magnitude")],
                 extra=[r"b(x)=a(x-x_0)\ \Rightarrow\ \mathcal{F}\{b\}=e^{-2\pi i\,k\cdot x_0}\,\mathcal{F}\{a\}"],
                 after=[f"Toy: true shift (row, col) = {pc['true']}, recovered = {pc['est']}"],
                 why_text="A shift is invisible to kinematics but is a clean phase ramp in Fourier space - "
                          "so one FFT finds it, even with camera noise.",
                 label="Phase correlation", group="Vision", fig_w=6.6,
                 notes="""
Phase correlation - H4 v4 ka dil. Sawaal: photo me drawing, belief (jo kinematics sochta hai)
se kitni khiski hui hai?

Physics wala intuition (Fourier shift theorem): agar ek signal x0 se shift ho, to uske Fourier
transform ka magnitude same rehta hai, sirf phase me ek ramp aata hai: exp(-2 pi i k.x0). To
dono transforms ko multiply karo (ek ka conjugate), magnitude se divide karo -> sirf phase ramp
bachta hai. Uska inverse Fourier transform ek sharp peak (delta) deta hai - bilkul shift ki
jagah par. argmax = shift.

Toy (script se): belief me ek circle + line, photo me woh (4, -3) pixel khiski + noise. Phase
correlation ne exactly (4, -3) wapas diya.

Project me: OpenCV cv2.phaseCorrelate(belief, photo). Agar response < 0.05 (peak kamzor) ya
koi ink hi nahi, to offset 0 maan lo.
""", source="rl/draw_env.py _estimate_offset (cv2.phaseCorrelate, min_response 0.05); Fourier shift theorem; "
            "toy numbers by teach_figs.py")

    concept(prs, "03 · phase correlation", "How camera_est uses it - and its limits", None,
            ["The camera_est arm keeps a 'belief canvas' (where kinematics says ink went) next to the photo.",
             "Each step: phase-correlate belief vs photo → estimated sheet offset → draw the pen marker "
             "where the pen is ON THE SHEET. The simulator's true offset is never read.",
             "Accuracy check (random actions, steps 40-59, 24 episodes): mean error 0.48 px against a "
             "mean true shift of 7.6 px.",
             "Weak peak (response < 0.05) or no ink yet → offset assumed 0."],
            cards=[("LIMIT: EASY CASE", ["The photo is a pure translation of the belief, from a near-fixed "
                                         "simulated camera. Written knowing that shift model. A real camera "
                                         "adds perspective, lighting, a hand in view."], WARN),
                   ("LIMIT: MEASURED COST", ["When ink is missing or displaced (ink failure, slip) the "
                                             "correlation can mislead: camera_est loses more than a plain "
                                             "camera arm there (H4 replication)."], BAD)],
            take="It is a feasibility demonstration in simulation, not a real-world estimator.",
            take_color=WARN,
            notes="""
camera_est arm ke paas do cheezen hain: belief canvas (kinematics ke hisaab se ink kahan gayi)
aur camera ki photo. Har step par dono ka phase correlation -> sheet ka estimated offset -> pen
ka marker wahan banao jahan pen SHEET par hai. Simulator ka asli offset kabhi nahi padha jaata -
yahi isse "camera result" banata hai (v3 me asli offset diya gaya tha, isliye woh camera result
nahi tha).

Accuracy (random actions, steps 40-59): mean error 0.48 px, jabki asli shift ~7.6 px. Bahut achha.

Limits jo hamesha saath bolni hain:
1) Easy case: photo belief ka pure translation hai, camera almost fixed, aur estimator yeh jaante
   hue likha gaya. Asli duniya me perspective, roshni, haath beech me.
2) Measured cost: jab ink missing ya displaced ho (ink failure, slip) to correlation galat offset
   de sakta hai - replication me camera_est ne in disturbances par plain camera arm se zyada
   khoya. Cause untested.
""", source="RESEARCH_LOG '## 2026-10-30 - H4 v4 launched' (0.48 px vs 7.6 px; honest limits) and "
            "'### H4 v4 confirmation RESULT' (estimator cost); rl/draw_env.py _estimate_offset")
