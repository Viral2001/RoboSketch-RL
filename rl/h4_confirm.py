"""
RoboSketch-RL  |  H4 v4 CONFIRMATION on fresh seeds {200, 300} (pre-registered in docs/RESEARCH_LOG.md "H4 v4 confirmation launched").
-------------------------------------------------
Runs the three unchanged H4 scripts, one after the other, for one shard, with --seeds 200 300 (resumable: each script skips rows it
already has). Shards c / d write results/h4_short_<s>.jsonl, h4_v3_<s>.jsonl, h4_v4_<s>.jsonl (append-only, keyed by seed).
  conda run -n robosketch --no-capture-output python rl/h4_confirm.py --shapes line circle     --shard c
  conda run -n robosketch --no-capture-output python rl/h4_confirm.py --shapes square triangle --shard d
  conda run -n robosketch --no-capture-output python rl/h4_confirm.py --aggregate                # seeds 200/300 ONLY (the confirmation)
  conda run -n robosketch --no-capture-output python rl/h4_confirm.py --aggregate --seeds 0 100 200 300   # pooled, secondary
The aggregate reuses h4_v4_experiment.aggregate() on rows filtered to the chosen seeds; its figure is NOT written (no overwrite of
output/h4_v4_disturbance_recovery.png).
"""
import argparse
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = ["rl/h4_short_experiment.py", "rl/h4_v3_experiment.py", "rl/h4_v4_experiment.py"]
SEEDS = [200, 300]


def run(args):
    for sc in SCRIPTS:
        cmd = [sys.executable, "-u", sc, "--seeds", *map(str, SEEDS), "--shapes", *args.shapes, "--shard", args.shard,
               "--timesteps", "200000", "--max-steps", "60"]
        print(">>", " ".join(cmd), flush=True)
        code = subprocess.call(cmd, cwd=ROOT)
        if code != 0:
            print(f"!! {sc} exited {code}", flush=True)
            sys.exit(code)


def aggregate(seeds, figure=False):
    import h4_v4_experiment as V4
    keep = set(seeds)
    orig = V4._rows
    V4._rows = lambda pattern: {k: v for k, v in orig(pattern).items() if k[2] in keep}
    if figure:   # NEW file name per seed set; never the original v4 figure
        tag = "_".join(map(str, sorted(keep)))
        out = os.path.join(ROOT, "output", f"h4_confirm_recovery_seeds{tag}.png")
        if os.path.exists(out):
            sys.exit(f"{out} exists - not overwriting")
        fig = V4._figure
        V4._figure = lambda rows, cells: fig(rows, cells, out=out,
                                             title=f"H4 v4 confirmation (seeds {', '.join(map(str, sorted(keep)))}): camera estimates the sheet offset")
    else:
        V4._figure = lambda rows, cells: print("\n(figure not written by h4_confirm)")
    print(f"### seeds used: {sorted(keep)}")
    V4.aggregate()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--shapes", nargs="+")
    ap.add_argument("--shard", default="")
    ap.add_argument("--seeds", type=int, nargs="+", default=SEEDS)
    ap.add_argument("--aggregate", action="store_true")
    ap.add_argument("--figure", action="store_true", help="with --aggregate: write output/h4_confirm_recovery_seeds<...>.png")
    a = ap.parse_args()
    aggregate(a.seeds, a.figure) if a.aggregate else run(a)
