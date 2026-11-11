"""
Teaching figures and toy numbers for the learning deck.

Two kinds of content live here, and they must not be confused:
  * TOY  - small illustrative calculations (a 2-link arm, a 5-step return, a
           ring-shaped IoU example ...). They are COMPUTED here by numpy so no
           number on a slide is done "in the head" (AGENTS.md section 6, rule 1).
           They are NOT project results, and every slide that uses one says so.
  * real - the few plots that show project numbers (DiD, TOST, t-distribution
           markers) copy those numbers from docs/RESEARCH_LOG.md; the entry is
           named in the comment next to each number and in the slide notes.

Run directly to (re)generate every PNG into learning/project_deck/fig/.
"""
import math
import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "fig")
ROOT = os.path.dirname(os.path.dirname(HERE))
os.makedirs(FIG, exist_ok=True)

C = {"ink": "#0F172A", "body": "#334155", "muted": "#64748B", "grid": "#E5E9F0",
     "blue": "#2B4ACB", "orange": "#C27A0A", "green": "#0D8A5F", "red": "#C03535",
     "violet": "#6D45C7", "cyan": "#0E9CC4", "wash": "#F5F7FB"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 13, "axes.edgecolor": "#B8C2D3",
    "axes.labelcolor": C["body"], "xtick.color": C["muted"], "ytick.color": C["muted"],
    "axes.titlesize": 14, "axes.titleweight": "bold", "axes.titlecolor": C["ink"],
    "axes.grid": True, "grid.color": C["grid"], "grid.linewidth": 0.8,
    "axes.spines.top": False, "axes.spines.right": False, "mathtext.fontset": "cm",
    "savefig.dpi": 220, "savefig.bbox": "tight", "savefig.facecolor": "white",
})


def _save(fig, name):
    fig.savefig(os.path.join(FIG, name))
    plt.close(fig)


# ============================================================ TOY numbers ==
def _toy():
    T = {}
    # 2-link planar arm forward kinematics (illustrative lengths/angles)
    L1, L2, t1, t2 = 0.40, 0.30, 30.0, 45.0
    a1, a12 = math.radians(t1), math.radians(t1 + t2)
    T["fk"] = dict(L1=L1, L2=L2, t1=t1, t2=t2,
                   x=L1 * math.cos(a1) + L2 * math.cos(a12),
                   y=L1 * math.sin(a1) + L2 * math.sin(a12))
    # world -> pixel mapping of the project (draw_env.py constants), pen at sheet centre + 5 cm
    cx, cy, half, res = 0.55, 0.0, 0.10, 128
    x, y = 0.60, 0.05
    T["w2p"] = dict(x=x, y=y, col=(x - (cx - half)) / (2 * half) * (res - 1),
                    row=((cy + half) - y) / (2 * half) * (res - 1))
    # discounted return of a 5-reward toy episode
    rs, g = [1.0, 0.0, 0.0, 0.0, 1.0], 0.9
    T["ret"] = dict(r=rs, gamma=g, G=sum(g ** k * r for k, r in enumerate(rs)))
    T["horizon"] = {gm: 1.0 / (1.0 - gm) for gm in (0.9, 0.99)}
    T["g99_60"] = 0.99 ** 60
    T["g99_240"] = 0.99 ** 240
    # telescoping IoU-delta: rewards 10*dIoU over a toy IoU sequence
    ious = [0.0, 0.10, 0.25, 0.40, 0.38]
    T["tele"] = dict(ious=ious, sum=sum(10 * (b - a) for a, b in zip(ious, ious[1:])))
    # PPO ratio / clipping toy
    T["ppo"] = dict(eps=0.2, r_up=1.5, r_dn=0.6,
                    obj_up=min(1.5 * 1.0, max(min(1.5, 1.2), 0.8) * 1.0),
                    obj_dn=min(0.6 * -1.0, max(min(0.6, 1.2), 0.8) * -1.0))
    # CNN feature map sizes for a 64x64 input (SB3 NatureCNN kernels/strides)
    n = 64
    sizes = [n]
    for k, s in ((8, 4), (4, 2), (3, 1)):
        n = (n - k) // s + 1
        sizes.append(n)
    T["cnn"] = dict(sizes=sizes, flat=64 * sizes[-1] * sizes[-1])
    # PPO rollout bookkeeping from the settings in rl/experiment.py
    n_envs, n_steps, batch, epochs, total = 8, 512, 256, 6, 200_000
    roll = n_envs * n_steps
    T["ppo_book"] = dict(roll=roll, minib=roll // batch, grads=(roll // batch) * epochs,
                         rollouts=math.ceil(total / roll))
    # sample statistics of a toy set of 4 paired differences
    d = np.array([0.03, 0.05, -0.01, 0.04])
    sd = float(d.std(ddof=1))
    T["stats"] = dict(d=d.tolist(), mean=float(d.mean()), sd=sd, sd0=float(d.std(ddof=0)),
                      se=sd / math.sqrt(len(d)), t=float(d.mean()) / (sd / math.sqrt(len(d))))
    # relative threshold used in the threshold figure (same rule as rl/perception.py)
    T["thr"] = dict(ink=60.0, paper=235.0, frac=0.5, tau=60.0 + 0.5 * (235.0 - 60.0))
    # sheet and pen sizes from the constants in rl/draw_env.py
    half, res = 0.10, 128
    rad = max(2, int(0.0035 / (2 * half) * res))
    T["sheet"] = dict(side_m=2 * half, side_cm=round(2 * half * 100), canvas_res=res,
                      mm_per_px=2 * half * 1000 / (res - 1), pen_radius_px=rad,
                      line_px=max(2, 2 * rad), step_px=0.014 / (2 * half) * (res - 1))
    return T


TOY = _toy()


def _ring(n=64, cx=32.0, cy=32.0, r=18.0, w=2.5):
    yy, xx = np.mgrid[0:n, 0:n]
    d = np.hypot(xx - cx, yy - cy)
    return np.abs(d - r) <= w / 2 + 0.5, np.abs(d - r)


def _iou_toy():
    tgt, _ = _ring()
    drw, _ = _ring(cx=35.0, cy=31.0)
    inter = np.logical_and(tgt, drw).sum()
    union = np.logical_or(tgt, drw).sum()
    blank = np.zeros_like(tgt)
    res = dict(target_px=int(tgt.sum()), drawn_px=int(drw.sum()), inter=int(inter),
               union=int(union), iou=inter / union,
               mse=float(np.mean(tgt != drw)), cov=inter / tgt.sum(), prec=inter / drw.sum(),
               blank_mse=float(np.mean(tgt != blank)), blank_iou=0.0)
    # chamfer distance by brute force (small sets)
    pa, pb = np.argwhere(drw), np.argwhere(tgt)
    dab = np.sqrt(((pa[:, None, :] - pb[None, :, :]) ** 2).sum(-1))
    res["chamfer"] = float((dab.min(1).mean() + dab.min(0).mean()) / 2)
    return tgt, drw, res


TGT, DRW, IOU = _iou_toy()
TOY["iou"] = IOU


# ================================================================ figures ==
def fig_two_link():
    f = TOY["fk"]
    a1, a12 = math.radians(f["t1"]), math.radians(f["t1"] + f["t2"])
    p1 = (f["L1"] * math.cos(a1), f["L1"] * math.sin(a1))
    p2 = (f["x"], f["y"])
    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    ax.plot([0, p1[0], p2[0]], [0, p1[1], p2[1]], "-", color=C["blue"], lw=6,
            solid_capstyle="round")
    for p, lab in ((((0, 0)), "joint 1"), (p1, "joint 2")):
        ax.plot(*p, "o", ms=14, color="white", mec=C["ink"], mew=2)
        ax.annotate(lab, p, xytext=(8, -18), textcoords="offset points", color=C["muted"])
    ax.plot(*p2, "o", ms=12, color=C["red"])
    ax.annotate("pen tip (x, y)", p2, xytext=(-30, 12), textcoords="offset points",
                color=C["red"], fontweight="bold")
    ax.annotate(r"$L_1$", (p1[0] / 2, p1[1] / 2), xytext=(4, -22), textcoords="offset points",
                fontsize=18, color=C["blue"])
    ax.annotate(r"$L_2$", ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2), xytext=(8, 2),
                textcoords="offset points", fontsize=18, color=C["blue"])
    th = np.linspace(0, a1, 30)
    ax.plot(0.12 * np.cos(th), 0.12 * np.sin(th), color=C["orange"], lw=2)
    ax.text(0.14, 0.02, r"$\theta_1$", fontsize=18, color=C["orange"])
    th2 = np.linspace(a1, a12, 30)
    ax.plot(p1[0] + 0.09 * np.cos(th2), p1[1] + 0.09 * np.sin(th2), color=C["orange"], lw=2)
    ax.plot([p1[0], p1[0] + 0.16 * math.cos(a1)], [p1[1], p1[1] + 0.16 * math.sin(a1)],
            ":", color=C["muted"])
    ax.text(p1[0] + 0.07, p1[1] + 0.10, r"$\theta_2$", fontsize=18, color=C["orange"])
    ax.set_aspect("equal")
    ax.set_xlim(-0.08, 0.62)
    ax.set_ylim(-0.08, 0.62)
    ax.set_xlabel("x (m)")
    ax.set_ylabel("y (m)")
    ax.set_title("A 2-link planar arm (toy numbers)")
    _save(fig, "two_link_arm.png")


def fig_pinhole():
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    ax.axis("off")
    ax.plot([0, 0], [-1.2, 1.2], color=C["ink"], lw=3)            # image plane
    ax.plot([2, 2], [-0.05, 0.05], color=C["ink"], lw=6)            # pinhole
    ax.plot([6, 6], [0, 1.6], color=C["blue"], lw=5)                # object
    ax.plot([0, 0], [0, -0.8], color=C["red"], lw=5)                # image of object
    ax.plot([6, 0], [1.6, -0.8], "--", color=C["muted"], lw=1.5)
    ax.plot([-0.3, 6.6], [0, 0], color=C["grid"], lw=1)
    ax.annotate("", xy=(0, -1.35), xytext=(2, -1.35), arrowprops=dict(arrowstyle="<->", color=C["orange"]))
    ax.text(1.0, -1.65, "f  (focal length)", ha="center", color=C["orange"], fontsize=13)
    ax.annotate("", xy=(2, -1.35), xytext=(6, -1.35), arrowprops=dict(arrowstyle="<->", color=C["green"]))
    ax.text(4.0, -1.65, "Z  (distance to the paper)", ha="center", color=C["green"], fontsize=13)
    ax.text(6.15, 0.8, "X  (size on\nthe paper)", color=C["blue"], fontsize=13, va="center")
    ax.text(-0.15, -0.4, "x  (size in\nthe image)", color=C["red"], fontsize=13, va="center", ha="right")
    ax.text(2, 0.25, "pinhole", ha="center", color=C["ink"], fontsize=12)
    ax.text(0, 1.35, "sensor", ha="center", color=C["ink"], fontsize=12)
    ax.set_xlim(-1.6, 7.6)
    ax.set_ylim(-1.9, 1.8)
    _save(fig, "pinhole.png")


def fig_iou():
    tgt, drw = TGT, DRW
    rgb = np.ones(tgt.shape + (3,))
    pink = np.array([1.0, 0.72, 0.72])
    rgb[tgt & ~drw] = pink
    rgb[drw & ~tgt] = np.array([0.55, 0.62, 0.75])
    rgb[tgt & drw] = np.array([0.05, 0.54, 0.37])
    fig, axs = plt.subplots(1, 3, figsize=(10.5, 3.7))
    axs[0].imshow(np.where(tgt[..., None], pink, 1.0))
    axs[0].set_title("B = target (pink)")
    axs[1].imshow(np.where(drw[..., None], 0.1, 1.0) * np.ones(3))
    axs[1].set_title("A = what was drawn")
    axs[2].imshow(rgb)
    axs[2].set_title("green = A∩B   grey/pink = rest of A∪B")
    for a in axs:
        a.set_xticks([])
        a.set_yticks([])
        a.grid(False)
    _save(fig, "iou_toy.png")


def fig_threshold():
    rng = np.random.default_rng(3)
    n = 64
    img = np.full((n, n), 235.0)
    yy, xx = np.mgrid[0:n, 0:n]
    stroke = np.abs(yy - (0.55 * xx + 10)) < 2.2
    img[stroke] = 60.0
    # 3x3 box blur + noise (illustrative camera)
    pad = np.pad(img, 1, mode="edge")
    img = sum(pad[i:i + n, j:j + n] for i in range(3) for j in range(3)) / 9.0
    img = np.clip(img + rng.normal(0, 12, img.shape), 0, 255)
    ink, paper, frac = 60.0, 235.0, 0.5
    thr = ink + frac * (paper - ink)
    mask = img < thr
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.6), gridspec_kw={"width_ratios": [1, 1.25, 1]})
    axs[0].imshow(img, cmap="gray", vmin=0, vmax=255)
    axs[0].set_title("grey photo (0-255)")
    axs[1].hist(img.ravel(), bins=40, color=C["blue"])
    axs[1].axvline(thr, color=C["red"], lw=2)
    axs[1].text(thr + 4, axs[1].get_ylim()[1] * 0.8, "threshold", color=C["red"])
    axs[1].set_title("histogram of grey levels")
    axs[1].set_xlabel("grey level")
    axs[2].imshow(~mask, cmap="gray")
    axs[2].set_title("binary mask: ink = black")
    for a in (axs[0], axs[2]):
        a.set_xticks([])
        a.set_yticks([])
        a.grid(False)
    _save(fig, "threshold_toy.png")


def fig_downsample():
    big = np.zeros((512, 512))
    big[249:263, 100:412] = 1.0                       # a 14-px band, like targets.py STROKE_PX

    def area(img, k):
        n = img.shape[0] // k
        return img[:n * k, :n * k].reshape(n, k, n, k).mean(axis=(1, 3))

    a128, a64 = area(big, 4), area(big, 8)
    fig, axs = plt.subplots(1, 3, figsize=(11, 3.5))
    for a, im, t in ((axs[0], big, "512 px: 14-px stroke"), (axs[1], a128, "128 px: ~3.5 px"),
                     (axs[2], a64, "64 px (observation): ~1.75 px")):
        a.imshow(1 - im, cmap="gray", vmin=0, vmax=1, interpolation="nearest")
        a.set_title(t)
        a.set_xticks([])
        a.set_yticks([])
        a.grid(False)
        h = im.shape[0]
        a.set_ylim(h * 0.6, h * 0.4)
    _save(fig, "downsample_toy.png")


def fig_activations():
    x = np.linspace(-3, 3, 200)
    fig, ax = plt.subplots(figsize=(6, 3.6))
    ax.plot(x, np.maximum(0, x), color=C["blue"], lw=2.5)
    ax.plot(x, np.tanh(x), "--", color=C["orange"], lw=2.5)
    ax.text(1.6, 2.0, "ReLU", color=C["blue"], fontweight="bold")
    ax.text(1.8, 0.75, "tanh", color=C["orange"], fontweight="bold")
    ax.set_xlabel("input z")
    ax.set_ylabel("output")
    ax.set_title("Two activation functions")
    _save(fig, "activations.png")


def fig_grad_descent():
    w = np.linspace(-1.5, 4.5, 200)
    f = lambda v: (v - 2.0) ** 2  # noqa: E731
    lr, v, pts = 0.3, -1.0, []
    for _ in range(7):
        pts.append(v)
        v = v - lr * 2 * (v - 2.0)
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    ax.plot(w, f(w), color=C["muted"], lw=2)
    ax.plot(pts, [f(p) for p in pts], "o-", color=C["red"], lw=1.5, ms=8)
    for i, p in enumerate(pts[:4]):
        ax.annotate(f"step {i}", (p, f(p)), xytext=(6, 6), textcoords="offset points",
                    fontsize=11, color=C["body"])
    ax.set_xlabel(r"parameter $\theta$")
    ax.set_ylabel(r"loss $L(\theta)=(\theta-2)^2$")
    ax.set_title(r"Gradient descent, learning rate $\alpha=0.3$ (toy)")
    _save(fig, "grad_descent.png")
    TOY["gd"] = [round(p, 3) for p in pts]


def fig_conv():
    img = np.zeros((7, 7))
    img[:, 4:] = 1.0
    k = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]], float)
    out = np.array([[(img[i:i + 3, j:j + 3] * k).sum() for j in range(5)] for i in range(5)])
    fig, axs = plt.subplots(1, 3, figsize=(10.5, 3.6), gridspec_kw={"width_ratios": [7, 3, 5]})
    for a, m, t in ((axs[0], img, "input image 7x7"), (axs[1], k, "kernel 3x3"),
                    (axs[2], out, "output (feature map) 5x5")):
        a.imshow(m, cmap="coolwarm", vmin=-3, vmax=3)
        for (i, j), v in np.ndenumerate(m):
            a.text(j, i, f"{v:g}", ha="center", va="center", fontsize=11, color=C["ink"])
        a.set_title(t)
        a.set_xticks([])
        a.set_yticks([])
        a.grid(False)
    _save(fig, "conv_toy.png")


def fig_discount():
    k = np.arange(0, 241)
    fig, ax = plt.subplots(figsize=(7, 3.8))
    ax.plot(k, 0.99 ** k, color=C["blue"], lw=2.5)
    ax.plot(k, 0.9 ** k, "--", color=C["orange"], lw=2.5)
    ax.axvline(60, color=C["muted"], lw=1, ls=":")
    ax.axvline(240, color=C["muted"], lw=1, ls=":")
    ax.text(62, 0.9, "60-step H4\nepisode", color=C["muted"], fontsize=11)
    ax.text(170, 0.9, "240-step\nepisode", color=C["muted"], fontsize=11)
    ax.text(120, 0.36, r"$\gamma=0.99$ (used)", color=C["blue"], fontweight="bold")
    ax.text(14, 0.12, r"$\gamma=0.9$", color=C["orange"], fontweight="bold")
    ax.set_xlabel("steps into the future, k")
    ax.set_ylabel(r"weight $\gamma^k$")
    ax.set_title("How much a future reward counts")
    _save(fig, "discount.png")


def fig_gae():
    l = np.arange(0, 61)
    fig, ax = plt.subplots(figsize=(7, 3.8))
    for lam, col, ls in ((0.95, C["blue"], "-"), (0.5, C["orange"], "--")):
        ax.plot(l, (0.99 * lam) ** l, ls, color=col, lw=2.5)
    ax.text(25, 0.42, r"$\lambda=0.95$ (SB3 default, used)", color=C["blue"], fontweight="bold")
    ax.text(4, 0.10, r"$\lambda=0.5$", color=C["orange"], fontweight="bold")
    ax.set_xlabel(r"how far ahead, $l$ steps")
    ax.set_ylabel(r"weight $(\gamma\lambda)^l$ on $\delta_{t+l}$")
    ax.set_title(r"GAE weights ($\gamma=0.99$)")
    _save(fig, "gae_weights.png")


def fig_gauss():
    a = np.linspace(-3.5, 3.5, 400)
    mu, sd = 0.3, 1.0
    p = np.exp(-0.5 * ((a - mu) / sd) ** 2) / (sd * math.sqrt(2 * math.pi))
    fig, ax = plt.subplots(figsize=(7, 3.6))
    ax.plot(a, p, color=C["blue"], lw=2.5)
    ax.fill_between(a, p, where=(a < -1) | (a > 1), color=C["orange"], alpha=0.35)
    ax.axvline(mu, color=C["red"], lw=2)
    ax.set_ylim(0, 0.52)
    ax.text(mu + 0.08, 0.45, r"mean $\mu_\theta(s)$ = action used at test time", color=C["red"])
    ax.text(2.05, 0.28, "shaded: outside [-1, 1],\nclipped by the bounds", color=C["orange"], fontsize=11)
    ax.set_xlabel("action value (e.g. dx before scaling)")
    ax.set_ylabel("probability density")
    ax.set_title(r"Gaussian policy: sample $a\sim\mathcal{N}(\mu,\sigma^2)$ (toy $\mu=0.3$, $\sigma=1$)")
    _save(fig, "gauss_policy.png")


def fig_ppo_clip():
    r = np.linspace(0.0, 2.0, 400)
    eps = 0.2
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4))
    fig.subplots_adjust(wspace=0.35)
    for ax, A, t in ((axs[0], 1.0, r"advantage $\hat A>0$ (good action)"),
                     (axs[1], -1.0, r"advantage $\hat A<0$ (bad action)")):
        unc = r * A
        cl = np.clip(r, 1 - eps, 1 + eps) * A
        ax.plot(r, unc, ":", color=C["muted"], lw=2)
        ax.plot(r, np.minimum(unc, cl), color=C["blue"], lw=3)
        ax.axvspan(1 - eps, 1 + eps, color=C["grid"], alpha=0.8)
        ax.axvline(1, color=C["muted"], lw=1)
        ax.set_xlabel(r"probability ratio $r_t(\theta)=\pi_\theta/\pi_{old}$")
        ax.set_ylabel(r"$L^{CLIP}$ contribution")
        ax.set_title(t)
    axs[0].text(0.05, 0.92, "blue = clipped objective\ndotted = unclipped", transform=axs[0].transAxes,
                fontsize=11, color=C["body"], va="top")
    axs[1].text(0.95, 0.92, "blue = clipped objective\ndotted = unclipped", transform=axs[1].transAxes,
                fontsize=11, color=C["body"], va="top", ha="right")
    axs[0].text(1.25, 0.75, "flat: no extra gain\nabove r = 1.2", color=C["blue"], fontsize=11)
    axs[1].text(0.05, -1.25, "flat: no extra gain\nbelow r = 0.8", color=C["blue"], fontsize=11)
    _save(fig, "ppo_clip.png")


def _tpdf(x, df):
    c = math.gamma((df + 1) / 2) / (math.sqrt(df * math.pi) * math.gamma(df / 2))
    return c * (1 + x * x / df) ** (-(df + 1) / 2)


def fig_tdist():
    x = np.linspace(-9.5, 9.5, 800)
    y = np.array([_tpdf(v, 7) for v in x])
    crit = 2.365                       # RESEARCH_LOG: critical t(7)=2.365 (two-sided 5%)
    fig, ax = plt.subplots(figsize=(10, 3.9))
    ax.plot(x, y, color=C["ink"], lw=2)
    ax.fill_between(x, y, where=np.abs(x) >= crit, color=C["red"], alpha=0.35)
    for v in (-crit, crit):
        ax.axvline(v, color=C["red"], lw=1.2, ls="--")
    ax.text(crit + 0.15, 0.30, "critical\n|t| = 2.365", color=C["red"], fontsize=11)
    # real t values from the log, both n = 8 pairs (df 7)
    marks = [(0.24, "H4 v1 paper shift\nt = +0.24 (null)", C["blue"]),   # "### H4 RESULT"
             (8.32, "H4 replication\nt = +8.32", C["green"])]           # "### H4 v4 confirmation RESULT"
    for v, lab, col in marks:
        ax.axvline(v, color=col, lw=2.5)
        ax.text(v + (0.2 if v < 5 else -0.2), 0.36, lab, color=col, fontsize=11,
                ha="left" if v < 5 else "right", fontweight="bold")
    ax.set_xlabel("t statistic")
    ax.set_ylabel("density")
    ax.set_title("Student t distribution, df = 7 (n = 8 pairs): where 'detectable' starts")
    ax.set_ylim(0, 0.45)
    _save(fig, "t_dist.png")


def fig_did():
    fig, axs = plt.subplots(1, 2, figsize=(11.5, 4.1))
    # left: TOY - a head start, no recovery
    ax = axs[0]
    ax.plot([0, 1], [0.45, 0.35], "o-", color=C["blue"], lw=2.5, ms=8)
    ax.plot([0, 1], [0.35, 0.25], "s--", color=C["orange"], lw=2.5, ms=8)
    ax.text(1.03, 0.35, "arm A", color=C["blue"], fontweight="bold", va="center")
    ax.text(1.03, 0.25, "arm B", color=C["orange"], fontweight="bold", va="center")
    ax.set_title("TOY: A ends higher, but both lose 0.10\n-> diff-in-diff = 0, no recovery")
    # right: REAL - H4 confirmation, seeds 200/300 (RESEARCH_LOG "### H4 v4 confirmation RESULT")
    ax = axs[1]
    fk = (0.369, 0.203)
    ce = (0.375, 0.329)
    ax.plot([0, 1], ce, "o-", color=C["blue"], lw=2.5, ms=8)
    ax.plot([0, 1], fk, "s--", color=C["orange"], lw=2.5, ms=8)
    ax.text(1.03, ce[1], "camera_est\nloses 0.046", color=C["blue"], fontweight="bold", va="center")
    ax.text(1.03, fk[1], "fk\nloses 0.165", color=C["orange"], fontweight="bold", va="center")
    ax.set_title("REAL: H4 replication, paper shift\nclean gap +0.006, diff-in-diff +0.119")
    for a in axs:
        a.set_xticks([0, 1])
        a.set_xticklabels(["no disturbance", "disturbed"])
        a.set_xlim(-0.2, 1.45)
        a.set_ylabel("true IoU")
    axs[0].set_ylim(0.15, 0.5)
    axs[1].set_ylim(0.15, 0.45)
    _save(fig, "did.png")


def fig_tost():
    fig, ax = plt.subplots(figsize=(9.5, 3.4))
    m = 0.05                                            # pre-registered margin
    ax.axvspan(-m, m, color=C["green"], alpha=0.10)
    for v in (-m, m):
        ax.axvline(v, color=C["green"], ls="--", lw=1.5)
    ax.axvline(0, color=C["muted"], lw=1)
    rows = [  # RESEARCH_LOG "### H2 spaced RESULT" (new sweep and the old-seed contrast)
        (1, +0.004, -0.024, +0.033, "seeds 100/200/300 (pre-registered): CI inside -> EQUIVALENT", C["blue"]),
        (0, +0.028, -0.007, +0.063, "old seeds 0/1/2 (overlapping): CI crosses +0.05 -> NOT shown", C["orange"])]
    for y, d, lo, hi, lab, col in rows:
        ax.plot([lo, hi], [y, y], color=col, lw=4, solid_capstyle="round")
        ax.plot(d, y, "o", color=col, ms=10)
        ax.text(-0.095, y + 0.22, lab, color=col, fontsize=11, fontweight="bold")
    ax.text(m + 0.002, -0.55, "+0.05 margin", color=C["green"], fontsize=11)
    ax.text(-m - 0.002, -0.55, "-0.05 margin", color=C["green"], fontsize=11, ha="right")
    ax.set_yticks([])
    ax.set_ylim(-0.7, 1.6)
    ax.set_xlim(-0.1, 0.1)
    ax.set_xlabel("d = truth IoU - camera IoU (90% confidence interval)")
    ax.set_title("TOST: equivalence = the whole 90% CI sits inside the margin")
    _save(fig, "tost.png")


def fig_seeds():
    fig, axs = plt.subplots(2, 1, figsize=(11, 5.6))
    fig.subplots_adjust(hspace=0.45)
    for ax, seeds, t in ((axs[0], [0, 1, 2], "adjacent seeds 0, 1, 2: red = env stream shared with another run"),
                         (axs[1], [0, 100, 200], "spaced seeds 0, 100, 200: every stream unique (blue)")):
        streams = sorted({k + i for k in seeds for i in range(8)})
        if seeds[1] - seeds[0] > 8:
            idx = {k + i: b * 9 + i for b, k in enumerate(seeds) for i in range(8)}
        else:
            idx = {s: j for j, s in enumerate(streams)}
        for r, k in enumerate(seeds):
            for i in range(8):
                shared = sum((k + i) in range(k2, k2 + 8) for k2 in seeds) > 1
                ax.add_patch(plt.Rectangle((idx[k + i], r), 0.9, 0.8,
                                           color=C["red"] if shared else C["blue"], alpha=0.85))
                ax.text(idx[k + i] + 0.45, r + 0.4, str(k + i), ha="center", va="center",
                        color="white", fontsize=9)
        ax.set_xlim(0, max(idx.values()) + 1)
        ax.set_ylim(len(seeds), 0)
        ax.set_yticks([r + 0.4 for r in range(len(seeds))])
        ax.set_yticklabels([f"PPO seed {k}" for k in seeds])
        ax.set_xticks([])
        ax.grid(False)
        ax.set_title(t)
    _save(fig, "seed_streams.png")
    TOY["streams_shared"] = len(set(range(0, 8)) & set(range(1, 9)))


def fig_phase_corr():
    n = 64
    rng = np.random.default_rng(7)
    t, _ = _ring(n=n, cx=30, cy=32, r=16, w=2.5)
    belief = t.astype(float)
    belief[10:13, 8:40] = 1.0
    sh = (4, -3)                                   # (rows, cols) shift of the "sheet"
    photo = np.roll(np.roll(belief, sh[0], axis=0), sh[1], axis=1)
    photo = np.clip(photo + rng.normal(0, 0.15, photo.shape), 0, 1)
    Fa, Fb = np.fft.fft2(belief), np.fft.fft2(photo)
    R = Fb * np.conj(Fa)
    R /= np.abs(R) + 1e-9
    corr = np.real(np.fft.ifft2(R))
    pk = np.unravel_index(np.argmax(corr), corr.shape)
    est = tuple(int(v if v <= n // 2 else v - n) for v in pk)
    TOY["pc"] = dict(true=sh, est=est, peak=float(corr.max()))
    fig, axs = plt.subplots(1, 3, figsize=(12, 4.0))
    fig.subplots_adjust(wspace=0.25)
    axs[0].imshow(1 - belief, cmap="gray")
    axs[0].set_title("1. belief: what kinematics\nthinks was drawn")
    axs[1].imshow(1 - photo, cmap="gray")
    axs[1].set_title("2. photo: sheet slid\n(+ camera noise)")
    shifted = np.fft.fftshift(corr)
    axs[2].imshow(shifted, cmap="magma")
    c0 = n // 2
    axs[2].plot(c0 + est[1], c0 + est[0], "o", mfc="none", mec="cyan", ms=16, mew=2)
    axs[2].set_title(f"3. correlation: one peak\nat (row {est[0]:+d}, col {est[1]:+d})")
    for a in axs:
        a.set_xticks([])
        a.set_yticks([])
        a.grid(False)
    _save(fig, "phase_corr_toy.png")


def fig_potential():
    n = 64
    tgt, dist = _ring(n=n, r=20, w=2.5)
    phi = -dist / n
    fig, ax = plt.subplots(figsize=(5.4, 4.4))
    im = ax.imshow(phi, cmap="viridis")
    ax.contour(tgt.astype(float), levels=[0.5], colors="white", linewidths=1.5)
    ax.set_title(r"potential $\Phi$ = -(distance to target)")
    ax.set_xticks([])
    ax.set_yticks([])
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.046)
    cb.set_label(r"$\Phi$ (higher = closer)")
    _save(fig, "potential_toy.png")


def fig_ego():
    n = 128
    sq = np.zeros((n, n), bool)
    lo, hi, w = 26, 102, 2
    sq[lo:hi, lo - w:lo + w] = sq[lo:hi, hi - w:hi + w] = True
    sq[lo - w:lo + w, lo:hi] = sq[hi - w:hi + w, lo:hi] = True
    pen = (lo, 70)                      # (row, col) on the top edge
    glob = sq.reshape(64, 2, 64, 2).mean(axis=(1, 3))
    pad = np.pad(sq, 32)
    ego = pad[pen[0]:pen[0] + 64, pen[1]:pen[1] + 64]
    fig, axs = plt.subplots(1, 2, figsize=(9.2, 4.3))
    axs[0].imshow(1 - glob, cmap="gray", vmin=0, vmax=1)
    axs[0].plot(pen[1] / 2, pen[0] / 2, "o", color=C["red"], ms=10)
    axs[0].add_patch(plt.Rectangle((pen[1] / 2 - 16, pen[0] / 2 - 16), 32, 32, fill=False,
                                   ec=C["red"], lw=2, ls="--"))
    axs[0].set_title("global view: whole sheet, 64 px\n(pen = red dot)")
    axs[1].imshow(1 - ego, cmap="gray", vmin=0, vmax=1)
    axs[1].plot(32, 32, "+", color=C["red"], ms=22, mew=3)
    axs[1].set_title("ego view: 64 canvas px around the pen\n(pen always at the centre)")
    for a in axs:
        a.set_xticks([])
        a.set_yticks([])
        a.grid(False)
    _save(fig, "ego_toy.png")


def crop_project_figs():
    """Cropped copies of project figures (white space removed); originals untouched."""
    jobs = [("results_h2_spaced.png", (0, 0, 880, 460), "h2_spaced_crop.png"),
            ("h5_error_growth.png", (0, 0, 1500, 700), "h5_crop.png"),
            ("results_overshoot.png", (0, 0, 860, 500), "overshoot_crop.png")]
    for src, box, dst in jobs:
        p = os.path.join(ROOT, "output", src)
        Image.open(p).crop(box).save(os.path.join(FIG, dst))


def make_all():
    for fn in (fig_two_link, fig_pinhole, fig_iou, fig_threshold, fig_downsample,
               fig_activations, fig_grad_descent, fig_conv, fig_discount, fig_gae, fig_gauss,
               fig_ppo_clip, fig_tdist, fig_did, fig_tost, fig_seeds, fig_phase_corr,
               fig_potential, fig_ego, crop_project_figs):
        fn()


if __name__ == "__main__":
    make_all()
    for k, v in TOY.items():
        print(k, v)
