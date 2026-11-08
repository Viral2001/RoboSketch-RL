"""
RoboSketch-RL  |  Stage 6 step 2b(i) - recognisability metric v2 WITH a reject class
------------------------------------------------------------------------------------
v1 (rl/recognise.py, results/recognise_cnn.pt) has 10 classes and no way to say "this is not a
digit": a scribble was read as '8' with P=1.00. v2 adds an 11th class `reject` trained on:
blank canvas, random-line scribbles (1-30 lines), the four non-digit shapes (line/circle/square/
triangle at random size/rotation/shift), and random curvy strokes. v1 is NOT touched; v2 is a NEW
model file (results/recognise_cnn_v2.pt) and a NEW calibration file.

Legible(target) := top-1 == target digit AND P(target) >= 0.5 (so P(reject) < 0.5).
Same limits as v1: trained only on my own schematic skeletons, so "looks like our template",
not human legibility. Note a vertical line / tall ellipse can be genuinely close to '1' / '0'.

    python rl/recognise11.py --train
    python rl/recognise11.py --calibrate
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
import targets as T           # noqa: E402
import recognise as R1        # noqa: E402  (reuse Net, to_input, sample, _degrade; v1 files untouched)

ROOT = os.path.dirname(HERE)
MODEL = os.path.join(ROOT, "results", "recognise_cnn_v2.pt")
CALIB = os.path.join(ROOT, "results", "recognise_calibration_v2.json")
CLASSES = list(G.NAMES) + ["reject"]          # 11
REJ = 10
R = R1.R
THREADS = 1


def _lines(rng, k, res=R, w=None):
    img = np.zeros((res, res), np.uint8)
    for _ in range(k):
        p = (rng.uniform(0.15, 0.85, (2, 2)) * res).astype(np.int32)
        cv2.line(img, tuple(int(v) for v in p[0]), tuple(int(v) for v in p[1]), 255,
                 max(1, int(round((w or rng.uniform(8, 22)) * res / 512))))
    return img


def reject_sample(rng):
    kind = rng.choice(["blank", "scribble", "shape", "curve"], p=[0.1, 0.3, 0.4, 0.2])
    if kind == "blank":
        img = np.zeros((R, R), np.uint8)
        if rng.random() < 0.5:                                   # a few specks of ink
            img = _lines(rng, 1, w=rng.uniform(3, 8)) if rng.random() < 0.5 else img
    elif kind == "scribble":
        img = _lines(rng, int(rng.integers(3, 31)))
    elif kind == "shape":
        name = str(rng.choice(["line", "circle", "square", "triangle"]))
        m = T.make_param(name, rng.uniform(0.6, 1.05), rng.uniform(-30, 30), res=512)
        sh = rng.uniform(-0.08, 0.08, 2)
        M_ = np.float32([[1, 0, sh[0] * 512], [0, 1, sh[1] * 512]])
        m = cv2.warpAffine(m, M_, (512, 512))
        img = cv2.resize(m, (R, R), interpolation=cv2.INTER_AREA)
    else:                                                        # random smooth wiggly stroke(s)
        img = np.zeros((R, R), np.uint8)
        for _ in range(int(rng.integers(1, 4))):
            t = np.linspace(0, 1, 40)
            pts = np.stack([rng.uniform(0.2, 0.8) + 0.3 * np.sin(rng.uniform(2, 9) * t + rng.uniform(0, 6)),
                            rng.uniform(0.2, 0.8) + 0.3 * np.sin(rng.uniform(2, 9) * t + rng.uniform(0, 6))], 1)
            cv2.polylines(img, [np.round(pts * R).astype(np.int32)], False, 255,
                          max(1, int(round(rng.uniform(8, 22) * R / 512))))
    return R1.to_input(img)


def make_set(n_digit, n_rej, seed):
    rng = np.random.default_rng(seed)
    X, y = [], []
    for k, nm in enumerate(G.NAMES):
        for _ in range(n_digit):
            X.append(R1.sample(rng, nm)); y.append(k)
    for _ in range(n_rej):
        X.append(reject_sample(rng)); y.append(REJ)
    return torch.tensor(np.stack(X)), torch.tensor(y)


def train(epochs=12, seed=0):
    if os.path.exists(MODEL):
        sys.exit(f"{MODEL} exists - refusing to overwrite (rename it first)")
    torch.set_num_threads(THREADS)
    torch.manual_seed(seed)
    Xtr, ytr = make_set(1500, 3000, 1000)
    Xva, yva = make_set(200, 400, 2000)
    Xte, yte = make_set(200, 400, 3000)
    net = R1.Net(n=11)
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
        pred = net(Xte).argmax(1)
    print(f"TEST accuracy all 11 classes (digits 200/class + reject 400, seed 3000, same augmentation family): {(pred == yte).float().mean().item():.4f}")
    print(f"  digits only: {(pred[yte < 10] == yte[yte < 10]).float().mean().item():.4f}   reject recall: {(pred[yte == REJ] == REJ).float().mean().item():.4f}")
    os.makedirs(os.path.dirname(MODEL), exist_ok=True)
    torch.save(net.state_dict(), MODEL)
    print("saved", MODEL)


_NET = None


def _net():
    global _NET
    if _NET is None:
        torch.set_num_threads(THREADS)
        _NET = R1.Net(n=11)
        _NET.load_state_dict(torch.load(MODEL))
        _NET.eval()
    return _NET


def probs(canvas_mask):
    """Softmax over '0'..'9','reject' for a drawn-ink mask (255 = ink, any resolution)."""
    with torch.no_grad():
        return torch.softmax(_net()(torch.tensor(R1.to_input(canvas_mask))[None]), 1)[0].numpy()


def recognisability(canvas_mask, target_name):
    """(P(target), legible) ; legible = top-1 is the target AND P(target) >= 0.5."""
    p = probs(canvas_mask)
    k = G.NAMES.index(target_name)
    return float(p[k]), bool(p.argmax() == k and p[k] >= 0.5)


def calibrate(n=40, seed=7):
    if os.path.exists(CALIB):
        sys.exit(f"{CALIB} exists - not overwriting")
    torch.set_num_threads(THREADS)
    rng = np.random.default_rng(seed)
    out, rows = {}, []
    grid = {"shift": [0, 10, 20, 40, 60], "wobble": [0, 3, 6, 10, 16],
            "truncate": [0.0, 0.2, 0.4, 0.6, 0.8], "stray": [0, 1, 2, 4]}
    for kind, levels in grid.items():
        for lv in levels:
            ious, ps, leg, rj = [], [], [], []
            for nm in G.NAMES:
                tgt = G.make_glyph(nm)
                for _ in range(n // 10 if lv else 1):
                    d = R1._degrade(nm, kind, lv, rng)
                    p, ok = recognisability(d, nm)
                    ious.append(M.iou(d, tgt)); ps.append(p); leg.append(ok); rj.append(probs(d)[REJ])
            rows.append((kind, lv, len(ious), np.mean(ious), np.mean(ps), np.mean(leg), np.mean(rj)))
            out[f"{kind}:{lv}"] = dict(n=len(ious), iou=float(np.mean(ious)), p_target=float(np.mean(ps)),
                                       legible=float(np.mean(leg)), p_reject=float(np.mean(rj)))
    print(f"{'degradation':10s} {'level':>6s} {'n':>4s} {'IoU':>6s} {'P(target)':>10s} {'legible':>8s} {'P(rej)':>7s}")
    for k, lv, nn_, i, p, a, r in rows:
        print(f"{k:10s} {lv:6} {nn_:4d} {i:6.3f} {p:10.3f} {a:8.2f} {r:7.3f}")
    # controls, with FRESH seeds not used in training (seed 7 here vs 1000/2000/3000 in training)
    ctl = {}
    for s in ("line", "circle", "square", "triangle"):
        pr = probs(T.make(s))
        ctl[s] = dict(p_reject=float(pr[REJ]), argmax=CLASSES[int(pr.argmax())])
    pr = probs(np.zeros((512, 512), np.uint8))
    ctl["blank"] = dict(p_reject=float(pr[REJ]), argmax=CLASSES[int(pr.argmax())])
    for k in (10, 25, 40):
        sc = _lines(rng, k, res=512, w=14)
        pr = probs(sc)
        ctl[f"scribble{k}"] = dict(p_reject=float(pr[REJ]), argmax=CLASSES[int(pr.argmax())])
    print("controls (P(reject), argmax):", json.dumps(ctl))
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
