"""Does the final `nodes` on the wire equal the bench-pin node count?

`bench N` builds its own single-threaded searcher over eight positions and prints
one total. This script reproduces that total from ORDINARY UCI searches, so the
`nodes` field is checked against an independent number rather than against
itself.

The subtlety that made a first attempt wrong: `bench` constructs a FRESH
Searcher(16) and calls clear() per position, so each position starts with a cold
16 MB table and cold histories. A single engine process reusing one table gives
343,222 instead of the pin -- the difference is warm history, not a node-field
defect. Each position therefore gets its own process here, and the control that
proves the setup matters is included.
"""

import json
import os

import uci

ENGINE = os.environ.get("FORGE_BIN", "/agent/repos/work-infofields/build/forge")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
SET = {"build": "g++ -DFORGE_MARCH=x86-64-v4 Release NDEBUG", "base_commit": "6b98f217",
       "threads": 1, "hash_mb": 16, "own_book": False, "depth": 11}

FENS = [
    "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
]

PIN = 312866


def bench_on_stdin():
    """The gate itself: bench is a UCI command, never an argv."""
    e = uci.Engine(ENGINE)
    e.handshake()
    e.send("bench %d" % SET["depth"])
    lines = e.read_until(lambda l: l.startswith("info string bench"), timeout=600)
    e.quit()
    return lines[-1]


def fresh_per_fen(depth, hash_mb):
    rows = []
    for fen in FENS:
        e = uci.Engine(ENGINE)
        e.handshake()
        e.setoption("OwnBook", "false")
        e.setoption("Hash", str(hash_mb))
        e.position(fen)
        lines, bm = e.search("depth %d" % depth, timeout=300)
        e.quit()
        dl = [l for l in lines if l.startswith("info depth")]
        f, _ = uci.parse_info(dl[-1])
        rows.append({"fen": fen, "nodes": int(f["nodes"]), "line": dl[-1]})
    return rows


def reused_table(depth, hash_mb):
    """Control: one process for all eight, which must NOT reproduce the pin."""
    e = uci.Engine(ENGINE)
    e.handshake()
    e.setoption("OwnBook", "false")
    rows = []
    for fen in FENS:
        e.setoption("Hash", str(hash_mb))
        e.position(fen)
        lines, bm = e.search("depth %d" % depth, timeout=300)
        dl = [l for l in lines if l.startswith("info depth")]
        f, _ = uci.parse_info(dl[-1])
        rows.append({"fen": fen, "nodes": int(f["nodes"])})
    e.quit()
    return rows


def main():
    gate = bench_on_stdin()
    fresh = fresh_per_fen(SET["depth"], 16)
    reused = reused_table(SET["depth"], 16)
    out = {
        "settings": SET, "bench_pin": PIN,
        "bench_line": gate,
        "fresh_process_per_fen": fresh,
        "fresh_process_sum": sum(r["nodes"] for r in fresh),
        "reused_table_control": reused,
        "reused_table_sum": sum(r["nodes"] for r in reused),
        "matches_pin": sum(r["nodes"] for r in fresh) == PIN,
        "control_does_not_match_pin": sum(r["nodes"] for r in reused) != PIN,
    }
    with open(os.path.join(OUT, "nodes_bench.json"), "w") as fh:
        json.dump(out, fh, indent=1)

    print("bench line:", gate)
    print("fresh process per FEN, Hash 16, depth %d:" % SET["depth"])
    for r in fresh:
        print("  %-8d %s" % (r["nodes"], r["fen"][:60]))
    print("  SUM %d vs pin %d -> %s" % (out["fresh_process_sum"], PIN,
                                        "MATCH" if out["matches_pin"] else "DIFF"))
    print("control, one reused table: SUM %d -> %s the pin" % (
        out["reused_table_sum"],
        "also matches" if not out["control_does_not_match_pin"] else "does NOT match"))


if __name__ == "__main__":
    main()
