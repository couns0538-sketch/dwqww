"""pos_cycles.py - CPU cycles per position for two node-identical exes (A = lock, B = candidate).

For each position: ucinewgame, position fen, go depth D (or go nodes N). The engine process's cycle counter
(QueryProcessCycleTime) is read before and after each search. Arms run A B B A per block with a fresh engine
per arm (warm-up: bench 11). Every arm must report the same last info line (depth, score, nodes) and the
same best move for a position, else the run stops. Output per position: nodes, cycles per node of A and of
B (median over arms), and B's speed against A in percent (positive = B faster), then the same for the sum.
INDICATIVE, like every timing of this job: one shared CPU at Idle priority.

Unlike `bench`, which always builds its own 16 MB table, `go` uses the Hash option, so --hash varies the
size of the transposition table. Default positions: the eight positions of the engine's bench command.

--recopy DIR runs every arm from a new copy of its exe and alternates the block order (A B B A, B A A B),
as `spd_uci.py abba --recopy` does; the block ratios then carry the per-file effect as spread, not as bias.

usage: pos_cycles.py --a A.exe --b B.exe --out DIR [--depth 20 | --nodes N] [--net on|off] [--hash 16]
                     [--blocks 2] [--fens FILE --first 0 --count 8] [--recopy DIR]
"""
import argparse
import json
import os
import random
import shutil
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard  # noqa: E402
from spd_uci import Engine, now_vienna, read_fens, search_row, sha256_file  # noqa: E402

BENCH_FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
]


def run_arm(exe, fens, go, net, hash_mb):
    eng = Engine(exe)
    eng.handshake(["OwnBook=false", f"UseNNUE={'true' if net == 'on' else 'false'}"] +
                  ([f"Hash={hash_mb}"] if hash_mb != 16 else []))
    eng.bench(11)
    rows = []
    for fen in fens:
        eng.send("ucinewgame")
        eng.sync()
        c0 = eng.cpu_seconds()
        d, sc, n, best = search_row(eng, fen, go, 7200, False)
        rows.append({"sig": f"{d}/{sc}/{n}/{best}", "nodes": int(n or 0), "gcycles": eng.cpu_seconds() - c0})
    eng.close()
    return rows


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--a", required=True)
    p.add_argument("--b", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--depth", type=int, default=20)
    p.add_argument("--nodes", type=int, default=0)
    p.add_argument("--net", choices=["on", "off"], default="on")
    p.add_argument("--hash", type=int, default=16)
    p.add_argument("--blocks", type=int, default=2)
    p.add_argument("--fens", default=None)
    p.add_argument("--first", type=int, default=0)
    p.add_argument("--count", type=int, default=8)
    p.add_argument("--recopy", default="")
    a = p.parse_args()
    pin = pinguard.ensure()
    print(pin, flush=True)
    os.makedirs(a.out, exist_ok=False)
    fens = BENCH_FENS if not a.fens else read_fens(a.fens)[a.first:a.first + a.count]
    go = f"nodes {a.nodes}" if a.nodes > 0 else f"depth {a.depth}"
    arms = []
    sig = None
    leftovers = []
    if a.recopy:
        os.makedirs(a.recopy, exist_ok=True)
    block_ratios = []
    for block in range(a.blocks):
        order = "BAAB" if (a.recopy and block % 2 == 1) else "ABBA"
        tot = {"A": [], "B": []}
        for idx, letter in enumerate(order):
            exe = a.a if letter == "A" else a.b
            if a.recopy:                      # a new copy of the exe for every arm (see spd_uci.py abba --recopy)
                dst = os.path.join(a.recopy, f"pos_{os.getpid()}_{block}_{idx}.exe")
                shutil.copyfile(exe, dst)
                leftovers.append(dst)
                exe = dst
            rows = run_arm(exe, fens, go, a.net, a.hash)
            s = [r["sig"] for r in rows]
            if sig is None:
                sig = s
            if s != sig:
                bad = [i for i, (x, y) in enumerate(zip(s, sig)) if x != y]
                raise SystemExit(f"arm {letter} of block {block} differs at positions {bad}: {s} vs {sig}")
            arms.append({"block": block, "letter": letter, "rows": rows})
            tot[letter].append(sum(r["gcycles"] for r in rows))
        ratio = ((tot["A"][0] * tot["A"][1]) / (tot["B"][0] * tot["B"][1])) ** 0.5       # B speed against A
        block_ratios.append(ratio)
        print(f"block {block} ({order}): A {tot['A'][0]:.3f} {tot['A'][1]:.3f}  B {tot['B'][0]:.3f} {tot['B'][1]:.3f} Gcycles, "
              f"B speed {100 * (ratio - 1):+.2f} %", flush=True)
        for path in list(leftovers):
            try:
                os.remove(path)
                leftovers.remove(path)
            except OSError:
                pass
    time.sleep(1.0)
    for path in leftovers:
        try:
            os.remove(path)
        except OSError:
            print(f"left behind (own temporary copy): {path}", flush=True)

    def med(letter, i):
        return statistics.median(x["rows"][i]["gcycles"] for x in arms if x["letter"] == letter)

    table = []
    for i, fen in enumerate(fens):
        ca, cb, n = med("A", i), med("B", i), arms[0]["rows"][i]["nodes"]
        table.append({"i": i, "fen": fen, "sig": sig[i], "nodes_last_info": n, "a_gcycles": ca, "b_gcycles": cb,
                      "b_speed_pct": 100.0 * (ca / cb - 1.0) if cb > 0 else None})
    ta = statistics.median(sum(r["gcycles"] for r in x["rows"]) for x in arms if x["letter"] == "A")
    tb = statistics.median(sum(r["gcycles"] for r in x["rows"]) for x in arms if x["letter"] == "B")
    br = [r - 1 for r in block_ratios]
    rng = random.Random(20261110)
    boot = sorted(statistics.median(rng.choices(br, k=len(br))) for _ in range(10000))
    res = {"label": "INDICATIVE - not the QA quiet ABBA", "a": a.a, "b": a.b, "a_sha256": sha256_file(a.a),
           "b_sha256": sha256_file(a.b), "pin": pin, "go": go, "net": a.net, "hash": a.hash, "blocks": a.blocks,
           "recopy": "a new copy of the exe for every arm, odd blocks B A A B" if a.recopy else "none: the same two files",
           "finished": now_vienna(), "positions": table, "total_a_gcycles": ta, "total_b_gcycles": tb,
           "total_b_speed_pct": 100.0 * (ta / tb - 1.0), "block_speed_pct": [100 * x for x in br],
           "block_median_pct": 100 * statistics.median(br), "block_median_boot95_pct": [100 * boot[249], 100 * boot[9749]],
           "block_mean_pct": 100 * statistics.mean(br),
           "block_se_pct": 100 * (statistics.pstdev(br) / len(br) ** 0.5 if len(br) > 1 else 0.0)}
    with open(os.path.join(a.out, "POS_CYCLES.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(res, f, indent=1)
    with open(os.path.join(a.out, "ARMS.json"), "w", encoding="utf-8", newline="\n") as f:
        json.dump(arms, f, indent=1)
    print(f"POS_CYCLES go {go} net {a.net} Hash {a.hash}, {a.blocks} blocks (positive = B faster)", flush=True)
    for r in table:
        share = 100.0 * r["a_gcycles"] / ta
        print(f"  pos {r['i']}: last info {r['sig']:<34} A {r['a_gcycles']:8.3f} Gc ({share:4.1f} % of A)  "
              f"B {r['b_gcycles']:8.3f} Gc  B speed {r['b_speed_pct']:+6.2f} %", flush=True)
    print(f"POS_CYCLES TOTAL: A {ta:.3f} Gc, B {tb:.3f} Gc, B speed {res['total_b_speed_pct']:+.2f} %", flush=True)
    print(f"POS_CYCLES BLOCKS go {go} net {a.net} Hash {a.hash}: median {res['block_median_pct']:+.2f} % "
          f"[boot95 {res['block_median_boot95_pct'][0]:+.2f} .. {res['block_median_boot95_pct'][1]:+.2f}], "
          f"mean {res['block_mean_pct']:+.2f} +/- {res['block_se_pct']:.2f} over {len(br)} blocks", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
