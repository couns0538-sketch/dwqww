"""R9: tests of r9_spsa.py without games (no engine, no CPU load): fastchess is replaced by a simulated match whose
true Elo is known, Elo(values) = -K * sum(((value - opt) / scale)^2), with 50% draws; the governor always allows 4.
Checks: (1) a parameter started far from its optimum moves toward it (the sign of the update is right),
(2) a parameter started at its optimum stays within its noise level, (3) a run stopped half way and resumed gives
the same theta after every batch as one uninterrupted run, (4) the report runs and calls the far parameter real.
usage: python -I -B test_r9_spsa_sim.py <scratch dir>"""
import importlib.util
import json
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("r9_spsa", HERE / "r9_spsa.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
scratch = Path(sys.argv[1]) / time.strftime("sim_%H%M%S")
scratch.mkdir(parents=True)
OPT = {"Far": 220.0, "AtOpt": 100.0, "FarHigh": 200.0}
SCALE = {"Far": 60.0, "AtOpt": 30.0, "FarHigh": 60.0}
K = 20.0


def elo(vals):
    return -K * sum(((vals[n] - OPT[n]) / SCALE[n]) ** 2 for n in OPT)


def fake_fastchess(run, plus, minus, pairs, conc, start, base):
    rng = random.Random(f"sim:{start}")
    p = 1 / (1 + 10 ** (-(elo(plus) - elo(minus)) / 400))
    draw = 0.5
    wp, lp = (1 - draw + 2 * p - 1) / 2, (1 - draw - (2 * p - 1)) / 2
    w = l = d = 0
    for _ in range(2 * pairs):
        x = rng.random()
        if x < wp:
            w += 1
        elif x < wp + lp:
            l += 1
        else:
            d += 1
    with open(base + ".out", "x") as f:
        f.write("simulated\n")
    return 0, w, l, d, {"normal": 2 * pairs}, 0.0


m.fastchess = fake_fastchess
m.governor = lambda run: (4, 10.0, 20.0)
cfg = {"name": "sim", "engine": "none", "fastchess": "none", "book": "none", "tc": "sim", "pairs_planned": 3000,
       "pairs_per_batch": 2, "seed": 77, "book_openings": 1000000,
       "governor": {"cap_percent": 70, "max_concurrency": 4, "min_free_gb": 8},
       "params": [{"name": "Far", "start": 120, "min": 0, "max": 500, "c_end": 15, "r_end": 0.004},
                  {"name": "AtOpt", "start": 100, "min": 0, "max": 300, "c_end": 10, "r_end": 0.004},
                  {"name": "FarHigh", "start": 300, "min": 0, "max": 500, "c_end": 15, "r_end": 0.004}]}
cfg_path = scratch / "sim.json"
cfg_path.write_text(json.dumps(cfg), encoding="ascii")
m.cmd_run(str(cfg_path), str(scratch / "whole"), False, 3000, None, None)
m.cmd_run(str(cfg_path), str(scratch / "split"), False, 1500, None, None)
m.cmd_run(str(cfg_path), str(scratch / "split"), True, 1500, None, None)


def thetas(d):
    return [json.loads(x)["theta_after"] for x in (d / "iterations.jsonl").read_text().splitlines() if x.strip()]


whole, split = thetas(scratch / "whole"), thetas(scratch / "split")
end = whole[-1]
rep = subprocess.run([sys.executable, "-I", "-B", str(HERE / "r9_spsa_report.py"), str(scratch / "whole"), "--out",
                      str(scratch / "report")], capture_output=True, text=True)
params = json.loads((scratch / "report" / "r9_params.json").read_text())["params"]
far, at, high = (next(p for p in params if p["name"] == n) for n in ("Far", "AtOpt", "FarHigh"))
checks = [
    # the speed depends on r_end (expected drift here about 55 units); the property under test is the direction
    ("far parameter moves up toward its optimum", end["Far"] > 120 + 0.25 * (220 - 120) and far["z"] >= 3,
     f"Far 120 -> {end['Far']:.1f} (optimum 220), z {far['z']}"),
    ("high parameter moves down toward its optimum", end["FarHigh"] < 300 - 0.25 * (300 - 200) and high["z"] <= -3,
     f"FarHigh 300 -> {end['FarHigh']:.1f} (optimum 200), z {high['z']}"),
    ("parameter at its optimum stays within 3 sigma", abs(end["AtOpt"] - 100) < 3 * at["sigma"],
     f"AtOpt 100 -> {end['AtOpt']:.1f}, sigma {at['sigma']:.1f}"),
    ("resumed run == uninterrupted run", whole == split, f"{len(whole)} batches each"),
    ("report: far parameter likely real", rep.returncode == 0 and far["likely_real"], f"z {far['z']}"),
]
for name, ok, detail in checks:
    print(f"{'PASS' if ok else 'FAIL'} {name}: {detail}")
print("SIM TESTS OK" if all(ok for _, ok, _ in checks) else "SIM TESTS FAILED")
sys.exit(0 if all(ok for _, ok, _ in checks) else 1)
