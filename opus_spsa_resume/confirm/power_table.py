"""power_table.py - operating characteristics of the confirmation SPRT, by simulation (SYNTHETIC; no Elo measured).

usage: python -I -B power_table.py <protocol.json> <out.json> [--runs 300] [--draw 0.6]
For each true model effect (normalized Elo of the simulated candidate; a property of the simulation, not a
measurement) it runs the protocol's sequential test (confirm_runner.gsprt/decide: bounds, alpha, beta, game cap,
minimum pairs) on independent games with the given draw rate and reports how often it ends in H1, H0 or the cap,
and the mean number of games used."""
import json
import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import confirm_runner as cr  # noqa: E402

EFFECTS = [-5.0, 0.0, 2.5, 5.0, 7.5, 10.0, 15.0, 20.0, 25.0]


def one(proto, true_nelo, draw, seed):
    rng = random.Random(seed)
    sd_g = math.sqrt((1 - draw) / 4)
    mu = 0.5 + true_nelo * math.log(10) / 800 * sd_g
    pw, pl = mu - draw / 2, 1 - mu - draw / 2
    pen = [0, 0, 0, 0, 0]
    s = proto["sprt"]
    for j in range(s["cap_games"] // 2):
        pts = 0.0
        for _ in range(2):
            x = rng.random()
            pts += 1.0 if x < pw else (0.0 if x < pw + pl else 0.5)
        pen[int(round(pts / 2 * 4))] += 1
        v = cr.decide(cr.gsprt(pen, s["nelo0"], s["nelo1"]), proto, 2 * (j + 1))
        if v:
            return v, 2 * (j + 1)
    return "cap, no decision (no claim)", s["cap_games"]


def main(argv):
    proto = json.loads(Path(argv[1]).read_text(encoding="utf-8-sig"))
    runs = int(argv[argv.index("--runs") + 1]) if "--runs" in argv else 300
    draw = float(argv[argv.index("--draw") + 1]) if "--draw" in argv else 0.6
    rows = []
    for e in EFFECTS:
        res = [one(proto, e, draw, f"power:{e}:{i}") for i in range(runs)]
        rows.append({"model_nelo": e, "runs": runs, "H1": sum(v == "H1 accepted" for v, _ in res) / runs,
                     "H0": sum(v == "H0 accepted" for v, _ in res) / runs,
                     "cap": sum(v.startswith("cap") for v, _ in res) / runs,
                     "mean_games": sum(g for _, g in res) / runs})
    out = {"label": "SYNTHETIC operating characteristics of the confirmation protocol; no Elo is measured",
           "sprt": proto["sprt"], "draw_rate": draw, "rows": rows}
    Path(argv[2]).write_text(json.dumps(out, indent=1) + "\n", encoding="ascii")
    for r in rows:
        print(f"model nElo {r['model_nelo']:5.1f}: H1 {r['H1']:.3f}  H0 {r['H0']:.3f}  cap {r['cap']:.3f}  "
              f"mean games {r['mean_games']:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
