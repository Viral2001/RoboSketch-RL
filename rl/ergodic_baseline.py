"""
RoboSketch-RL  |  Stage 5 (proposal 4.7): a classical, non-learning comparator - spectral-multiscale (SMC) ergodic control.
-------------------------------------------------
Ergodic control (D04, Mathew & Mezic) drives a point so that the TIME it spends in each region matches a target density:
here the density is the target outline (normalised mask). Greedy SMC: at every step pick, among 16 unit directions (full
step length, as in the learned agents), the move that minimises the ergodic metric
    sum_k Lambda_k * (phi_k - c_k(t+1))^2 ,  Lambda_k = (1+|k|^2)^(-3/2),
over a cosine Fourier basis with K x K coefficients on the sheet, where phi_k are the target's coefficients and c_k(t) the
trajectory's running time-average. No learning and no camera: it reads the target mask (privileged, like the scripted
tracer of T1), and is run on the SAME eval targets as the learned agents (default / train / heldout / heldout_scale /
heldout_rot, reset seeds 20000+ep, 16 targets, 240 steps), scored with TRUE IoU by the same environment.

Deterministic, so there are no seeds: results are per shape (mean over 16 targets) and are compared with the learned
agents DESCRIPTIVELY (their per-shape means over seeds), not as paired runs.
  conda run -n robosketch --no-capture-output python rl/ergodic_baseline.py
"""
import argparse
import json
import os
import sys

import cv2
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from draw_env import PAPER_CX, PAPER_CY, PAPER_HALF
from gen_experiment import _make
import gen2_experiment as G2

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "results", "ergodic_baseline.json")
K = 10
G = 64
NDIR = 16


class Ergodic:
    def __init__(self, k=K, g=G):
        self.k, self.g = k, g
        ks = np.arange(k)
        self.kx, self.ky = np.meshgrid(ks, ks, indexing="ij")
        self.lam = (1.0 + self.kx ** 2 + self.ky ** 2) ** -1.5
        # normalisation h_k of the cosine basis on [0,1]^2
        self.h = np.sqrt(np.where(self.kx == 0, 1.0, 0.5) * np.where(self.ky == 0, 1.0, 0.5))
        cell = (np.arange(g) + 0.5) / g
        self.cell = cell
        self.bu = np.cos(np.pi * np.outer(ks, cell))          # (k, g): cos(k pi u) at cell centres

    def basis(self, u, v):
        fu = np.cos(np.pi * np.arange(self.k) * u)
        fv = np.cos(np.pi * np.arange(self.k) * v)
        return np.outer(fu, fv) / self.h

    def target_coeffs(self, mask512):
        m = cv2.resize(mask512, (self.g, self.g), interpolation=cv2.INTER_AREA).astype(np.float64)
        m /= max(m.sum(), 1e-9)                                # density over the g x g cells (u = column, v = row)
        return np.einsum("ic,jr,rc->ij", self.bu, self.bu, m) / self.h

    def run(self, env, steps):
        phi = self.target_coeffs(env.target)
        a, ang = np.zeros((self.k, self.k)), np.linspace(0, 2 * np.pi, NDIR, endpoint=False)
        dirs = np.stack([np.cos(ang), np.sin(ang)], 1)
        n = 0
        for t in range(steps):
            u0 = (env.pen_xy[0] - (PAPER_CX - PAPER_HALF)) / (2 * PAPER_HALF)
            v0 = ((PAPER_CY + PAPER_HALF) - env.pen_xy[1]) / (2 * PAPER_HALF)
            if t == 0:
                a += self.basis(u0, v0); n = 1
            best, bj = None, 0
            for j, (dx, dy) in enumerate(dirs):
                u = float(np.clip(u0 + dx * env.step_size / (2 * PAPER_HALF), 0, 1))
                v = float(np.clip(v0 - dy * env.step_size / (2 * PAPER_HALF), 0, 1))
                c = (a + self.basis(u, v)) / (n + 1)
                e = float((self.lam * (phi - c) ** 2).sum())
                if best is None or e < best:
                    best, bj = e, j
            _, _, term, trunc, info = env.step(np.array([dirs[bj, 0], dirs[bj, 1], 1.0], np.float32))
            n += 1
            a += self.basis((env.pen_xy[0] - (PAPER_CX - PAPER_HALF)) / (2 * PAPER_HALF),
                            ((PAPER_CY + PAPER_HALF) - env.pen_xy[1]) / (2 * PAPER_HALF))
            if term or trunc:
                break
        return info


def main(args):
    erg = Ergodic()
    out = {}
    for shape in G2.SHAPES:
        out[shape] = {}
        for name, es in G2.EVAL_SETS.items():
            env = _make(shape, es, 10_000, args.max_steps, args.step_size)()
            ious, peaks, paths = [], [], []
            for ep in range(args.eval_eps):
                env.reset(seed=20_000 + ep)
                info = erg.run(env, args.max_steps)
                ious.append(info["iou"]); peaks.append(info["peak_iou"]); paths.append(info["path_ratio"])
            env.close()
            out[shape][name] = {"iou": float(np.mean(ious)), "peak_iou": float(np.mean(peaks)),
                                "path_ratio": float(np.mean(paths)), "iou_eps": [round(float(x), 4) for x in ious]}
            print(f"{shape:9s} {name:14s} IoU {np.mean(ious):.3f}  peak {np.mean(peaks):.3f}  path_ratio {np.mean(paths):.2f}", flush=True)
    if not args.no_save:
        with open(OUT, "w", encoding="utf-8") as f:
            json.dump({"K": K, "grid": G, "ndir": NDIR, "max_steps": args.max_steps, "eval_eps": args.eval_eps, "result": out}, f)
    g2 = G2.load_done()
    print("\n=== ergodic (no learning, privileged target) vs PPO param200 (mean over seeds 0/100), TRUE IoU ===")
    print(f"{'set':<16}{'ergodic':>9}{'ppo':>8}")
    for name in G2.EVAL_SETS:
        e = np.mean([out[s][name]["iou"] for s in G2.SHAPES])
        p = np.mean([g2[(s, "param200", k)]["eval"][name]["iou"] for s in G2.SHAPES for k in (0, 100)])
        print(f"{name:<16}{e:>9.3f}{p:>8.3f}")
    print("per shape (default set): " + "  ".join(f"{s} {out[s]['default']['iou']:.3f}" for s in G2.SHAPES))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-steps", type=int, default=240)
    ap.add_argument("--step-size", type=float, default=0.014)
    ap.add_argument("--eval-eps", type=int, default=16)
    ap.add_argument("--no-save", action="store_true")
    main(ap.parse_args())
