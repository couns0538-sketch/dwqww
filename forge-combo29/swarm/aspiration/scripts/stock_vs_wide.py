"""The headline measurement, on the pinned stock build only.

Question: does the engine ever publish an aspiration BOUND as if it were a value?

The traced build answers that from the inside (see measure_aspiration.py). This
script answers it on the PINNED stock binary, which is the artifact anyone else
will run, and it does so without needing any instrumentation:

  For a fixed position and depth, the score published by the stock build must
  match the score published by the never-narrow build. If the stock build ever
  published a fail-high bound, its score would sit at the window edge and would
  differ from the true value the wide search reports.

Both builds are pinned first (bench 11/13/16 + perft 5). The never-narrow build
is a compilation of the SAME commit with one line changed (`narrow = false`), so
it is the same engine with aspiration removed -- the only difference allowed to
explain a score difference is aspiration itself.

This also measures the COST/BENEFIT: nodes and time with and without aspiration,
which is what tells us whether aspiration is a speed optimisation here at all.
"""
import json
import pathlib
import statistics
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))

from uci import Engine  # noqa: E402

EVIDENCE = pathlib.Path("/tmp/asp/evidence")
STOCK = "/tmp/asp/build-stock/forge"
NOASP = "/tmp/asp/build-noasp/forge"
BASE = {"OwnBook": "false"}
PINS = {"bench11": 312866, "bench13": 862329, "bench16": 3024920, "perft5": 4865609}


def bench(binary, n):
    p = subprocess.run([binary], input=f"uci\nsetoption name OwnBook value false\nisready\nbench {n}\nquit\n",
                       capture_output=True, text=True, timeout=1200)
    for line in p.stdout.splitlines():
        if line.startswith(f"info string bench depth {n} nodes "):
            # Line ends `... nodes <n> time <t> nps <r>`; take the token after
            # `nodes`, not the last field (rsplit grabbed nps and reported a
            # bogus pin mismatch on the first run of this script).
            toks = line.split()
            return int(toks[toks.index("nodes") + 1])
    return None


def perft5(binary):
    p = subprocess.run([binary], input="uci\nsetoption name OwnBook value false\nisready\nposition startpos\ngo perft 5\nquit\n",
                       capture_output=True, text=True, timeout=600)
    for line in p.stdout.splitlines():
        if line.startswith("nodes "):
            return int(line.split()[1])
    return None


def pin(binary, label):
    got = {"bench11": bench(binary, 11), "bench13": bench(binary, 13),
           "bench16": bench(binary, 16), "perft5": perft5(binary)}
    ok = {k: got[k] == PINS[k] for k in PINS}
    print(f"{label}: " + " ".join(f"{k}={got[k]}{'' if ok[k] else ' MISMATCH'}" for k in PINS))
    return got, ok


def top(res):
    rows = {r["depth"]: r for r in res["info"] if r["depth"] is not None}
    return rows[max(rows)] if rows else None


def main():
    pins = {}
    pins["stock"], ok_stock = pin(STOCK, "stock   ")
    pins["noasp"], ok_noasp = pin(NOASP, "noasp   ")
    # The never-narrow build must still match perft (movegen untouched) but its
    # bench node counts MUST differ, or the flag did nothing.
    aspiration_active = pins["noasp"]["bench16"] != PINS["bench16"]
    print(f"never-narrow build changes bench16: {aspiration_active} "
          f"({PINS['bench16']} -> {pins['noasp']['bench16']})")
    print(f"never-narrow perft5 correct: {ok_noasp['perft5']}")

    corpus = json.loads((EVIDENCE / "corpus.json").read_text())
    positions = corpus["depth_positions"]
    rows = []
    for depth in (8, 10, 12):
        n_same = n_diff = 0
        node_ratios = []
        time_ratios = []
        for pos in positions:
            fen = pos["fen"]
            a = None
            b = None
            with Engine(STOCK, BASE) as e:
                e.newgame(); e.position(fen)
                a = e.search(f"go depth {depth}")
            with Engine(NOASP, BASE) as e:
                e.newgame(); e.position(fen)
                b = e.search(f"go depth {depth}")
            ta, tb = top(a), top(b)
            if ta is None or tb is None:
                continue
            same = (ta["score_kind"], ta["score"]) == (tb["score_kind"], tb["score"])
            n_same += same
            n_diff += (not same)
            if tb["nodes"] and ta["nodes"]:
                node_ratios.append(ta["nodes"] / tb["nodes"])
            if tb["time"] and ta["time"]:
                time_ratios.append(ta["time"] / tb["time"])
            rows.append({
                "depth": depth, "label": pos["label"], "fen": fen,
                "stock": {"score_kind": ta["score_kind"], "score": ta["score"],
                          "depth": ta["depth"], "nodes": ta["nodes"],
                          "time": ta["time"], "bestmove": a["bestmove"],
                          "pv": ta["pv"]},
                "noasp": {"score_kind": tb["score_kind"], "score": tb["score"],
                          "depth": tb["depth"], "nodes": tb["nodes"],
                          "time": tb["time"], "bestmove": b["bestmove"],
                          "pv": tb["pv"]},
                "score_agrees": same,
                "move_agrees": a["bestmove"] == b["bestmove"],
            })
        print(f"depth {depth}: score agrees {n_same}/{n_same + n_diff}  "
              f"median node ratio asp/wide {statistics.median(node_ratios):.3f}  "
              f"median time ratio {statistics.median(time_ratios):.3f}")

    payload = {"pins": pins, "aspiration_active": aspiration_active,
               "rows": rows,
               "note": "stock = audit base as committed; noasp = same commit with "
                       "narrow disabled; both pinned before recording"}
    (EVIDENCE / "stock_vs_wide.json").write_text(json.dumps(payload, indent=2) + "\n")

    for depth in (8, 10, 12):
        sub = [r for r in rows if r["depth"] == depth]
        nr = [r["stock"]["nodes"] / r["noasp"]["nodes"] for r in sub
              if r["stock"]["nodes"] and r["noasp"]["nodes"]]
        print(f"  d{depth} node ratio: min {min(nr):.3f} median {statistics.median(nr):.3f} "
              f"max {max(nr):.3f}  (aspiration cheaper on {sum(x < 1 for x in nr)}/{len(nr)})")


if __name__ == "__main__":
    main()
