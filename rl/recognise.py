"""
RoboSketch-RL  |  Stage 6 - recognisability metric (proposal 4.5)
-------------------------------------------------------------------
Recognisability = softmax probability that a small CNN assigns to the TARGET digit
when shown the drawn canvas (also top-1 correct). It is meant to complement IoU,
which rewards ink overlap, not legibility.

What this is NOT: the CNN is trained ONLY on augmented renders of my own schematic
skeletons (rl/glyphs.py) - no MNIST / handwriting data exists offline here (no
torchvision / sklearn). So it measures "looks like OUR template under jitter", not
human legibility. Report it as such.

    python rl/recognise.py --train        # trains + saves results/recognise_cnn.pt
    python rl/recognise.py --calibrate    # IoU vs recognisability on degraded perfect drawings
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np
import torch
import torch.nn as nn

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import glyphs as G            # noqa: E402
import metrics as M           # noqa: E402

ROOT = os.path.dirname(HERE)
MODEL = os.path.join(ROOT, "results", "recognise_cnn.pt")
CALIB = os.path.join(ROOT, "results", "recognise_calibration.json")
IN = 32          # classifier input size (px)
R = 128          # render res for augmentation
THREADS = 1


class Net(nn.Module):
    def __init__(self, n=10):
        super().__init__()
        c = lambda i, o: nn.Sequential(nn.Conv2d(i, o, 3, padding=1), nn.ReLU(), nn.MaxPool2d(2))
        self.f = nn.Sequential(c(1, 16), c(16, 32), c(32, 64))          # 32 -> 4
        self.h = nn.Sequential(nn.Flatten(), nn.Linear(64 * 16, 64), nn.ReLU(), nn.Dropout(0.2), nn.Linear(64, n))

    def forward(self, x):
        return self.h(self.f(x))


def to_input(mask):
    """255/0 (or any-res grey) canvas mask -> float32 (1,IN,IN) in [0,1]."""
    m = cv2.resize(mask, (IN, IN), interpolation=cv2.INTER_AREA).astype(np.float32) / 255.0
    return m[None]


def sample(rng, name):
    """One augmented render of digit `name` at R px -> classifier input."""
    st = G.strokes_px(name, scale=rng.uniform(0.6, 1.05), theta=rng.uniform(-20, 20),
                      shift=rng.uniform(-0.08, 0.08, 2), res=R, jitter=0.03, rng=rng)
    w = rng.uniform(8, 22)                                  # width in 512-px units; render() rescales
    return to_input(G.render(st, width=w, res=R))


def make_set(n_per_class, seed):
    rng = np.random.default_rng(seed)
    X, y = [], []
    for k, nm in enumerate(G.NAMES):
        for _ in range(n_per_class):
            X.append(sample(rng, nm))
            y.append(k)
    return torch.tensor(np.stack(X)), torch.tensor(y)


def train(epochs=12, seed=0):
    if os.path.exists(MODEL):
        sys.exit(f"{MODEL} exists - refusing to overwrite (rename it first)")
    torch.set_num_threads(THREADS)
    torch.manual_seed(seed)
    Xtr, ytr = make_set(1500, 1000)
    Xva, yva = make_set(200, 2000)
    Xte, yte = make_set(200, 3000)
    net = Net()
    opt = torch.optim.Adam(net.parameters(), 2e-3)
    g = torch.Generator().manual_seed(seed)
    for ep in range(epochs):
        net.train()
        perm = torch.randperm(len(Xtr), generator=g)
        for i in range(0, len(perm), 128):
            b = perm[i:i + 128]
            loss = nn.functional.cross_entropy(net(Xtr[b]), ytr[b])
            opt.zero_grad(); loss.backward(); opt.step()
        net.eval()
        with torch.no_grad():
            va = (net(Xva).argmax(1) == yva).float().mean().item()
        print(f"epoch {ep + 1:2d}  last-batch loss {loss.item():.3f}  val acc {va:.3f}")
    with torch.no_grad():
        te = (net(Xte).argmax(1) == yte).float().mean().item()
    print(f"TEST accuracy (200/class, seed 3000, same augmentation family as train): {te:.4f}")
    os.makedirs(os.path.dirname(MODEL), exist_ok=True)
    torch.save(net.state_dict(), MODEL)
    print("saved", MODEL)


_NET = None


def _net():
    global _NET
    if _NET is None:
        torch.set_num_threads(THREADS)
        _NET = Net()
        _NET.load_state_dict(torch.load(MODEL))
        _NET.eval()
    return _NET


def probs(canvas_mask):
    """Softmax over '0'..'9' for a drawn-ink mask (255 = ink, any resolution)."""
    with torch.no_grad():
        return torch.softmax(_net()(torch.tensor(to_input(canvas_mask))[None]), 1)[0].numpy()


def recognisability(canvas_mask, target_name):
    """(P(target), top-1 correct) for a drawn canvas mask."""
    p = probs(canvas_mask)
    k = G.NAMES.index(target_name)
    return float(p[k]), bool(p.argmax() == k)


# ---------------------------------------------------------------- calibration
def _degrade(name, kind, level, rng):
    """A perfect drawing of `name`, damaged in one controlled way (512 px)."""
    st = G.strokes_px(name)
    if kind == "shift":                       # whole drawing offset by `level` px (random direction)
        a = rng.uniform(0, 2 * np.pi)
        st = [s + level * np.array([np.cos(a), np.sin(a)]) for s in st]
    elif kind == "wobble":                    # smooth-ish per-vertex noise, sd in px
        st = [s + rng.normal(0, level, s.shape) for s in st]
    elif kind == "truncate":                  # only the first (1-level) of each stroke is inked
        st = [s[:max(2, int(round(len(s) * (1 - level))))] for s in st]
    elif kind == "stray":                     # perfect drawing + `level` random straight ink lines
        img = G.render(st)
        for _ in range(int(level)):
            p = rng.uniform(80, 432, (2, 2)).astype(np.int32)
            cv2.line(img, tuple(int(v) for v in p[0]), tuple(int(v) for v in p[1]), 255, G._stroke(512))
        return img
    return G.render(st)


def calibrate(n=40, seed=7):
    if os.path.exists(CALIB):
        sys.exit(f"{CALIB} exists - not overwriting")
    torch.set_num_threads(THREADS)
    rng = np.random.default_rng(seed)
    rows, out = [], {}
    grid = {"shift": [0, 10, 20, 40, 60], "wobble": [0, 3, 6, 10, 16],
            "truncate": [0.0, 0.2, 0.4, 0.6, 0.8], "stray": [0, 1, 2, 4]}
    for kind, levels in grid.items():
        for lv in levels:
            ious, ps, acc = [], [], []
            for nm in G.NAMES:
                tgt = G.make_glyph(nm)
                for _ in range(n // 10 if lv else 1):
                    d = _degrade(nm, kind, lv, rng)
                    p, ok = recognisability(d, nm)
                    ious.append(M.iou(d, tgt)); ps.append(p); acc.append(ok)
            rows.append((kind, lv, len(ious), np.mean(ious), np.mean(ps), np.mean(acc)))
            out[f"{kind}:{lv}"] = dict(n=len(ious), iou=float(np.mean(ious)),
                                       p_target=float(np.mean(ps)), top1=float(np.mean(acc)))
    print(f"{'degradation':10s} {'level':>6s} {'n':>4s} {'IoU':>6s} {'P(target)':>10s} {'top1':>6s}")
    for k, lv, nn_, i, p, a in rows:
        print(f"{k:10s} {lv:6} {nn_:4d} {i:6.3f} {p:10.3f} {a:6.2f}")
    # controls: things that are NOT digits
    ctl = {}
    from targets import make as make_shape
    for s in ("line", "circle", "square", "triangle"):
        pr = probs(make_shape(s))
        ctl[s] = dict(max_p=float(pr.max()), argmax=G.NAMES[int(pr.argmax())])
    pr = probs(np.zeros((512, 512), np.uint8))
    ctl["blank"] = dict(max_p=float(pr.max()), argmax=G.NAMES[int(pr.argmax())])
    sc = np.zeros((512, 512), np.uint8)
    for _ in range(25):
        q = rng.uniform(80, 432, (2, 2)).astype(np.int32)
        cv2.line(sc, tuple(int(v) for v in q[0]), tuple(int(v) for v in q[1]), 255, 14)
    pr = probs(sc)
    ctl["scribble25"] = dict(max_p=float(pr.max()), argmax=G.NAMES[int(pr.argmax())])
    print("controls (max softmax prob, argmax):", json.dumps(ctl))
    out["controls"] = ctl
    with open(CALIB, "w") as f:
        json.dump(out, f, indent=1)
    print("saved", CALIB)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", action="store_true")
    ap.add_argument("--calibrate", action="store_true")
    a = ap.parse_args()
    if a.train:
        train()
    if a.calibrate:
        calibrate()
