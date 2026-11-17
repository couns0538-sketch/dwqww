"""Probes for `time`, `hashfull`, `score` sign, and the no-info paths.

Each measurement is paired with the control that makes it meaningful.
"""

import json
import os
import time

import chess

import uci

ENGINE = os.environ.get("FORGE_BIN", "/agent/repos/work-infofields/build/forge")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
SET = {"build": "g++ -DFORGE_MARCH=x86-64-v4 Release NDEBUG", "base_commit": "6b98f217",
       "threads": 1, "hash_mb": "default 32 unless stated", "own_book": False}


def engine(**opts):
    e = uci.Engine(ENGINE)
    e.handshake()
    e.setoption("OwnBook", "false")
    for k, v in opts.items():
        e.setoption(k.replace("_", " "), v)
    return e


def parse(lines):
    out = []
    for l in lines:
        f, pv = uci.parse_info(l)
        if f and "depth" in f:
            out.append({**f, "pv_moves": pv, "_line": l})
    return out


def dump(name, payload):
    with open(os.path.join(OUT, name + ".json"), "w") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)
    print("wrote", name + ".json")


# --------------------------------------------------------------------------
# time: ordinary movetime, then ponder with the SAME finite budget
# --------------------------------------------------------------------------

def probe_time_ponder():
    """The budget starts at ponderhit; does the `time` field?"""
    e = engine()
    e.position()

    # Control: ordinary movetime, no ponder. time should track ~budget.
    t0 = time.monotonic()
    lines, bm = e.search("movetime 1000", timeout=120)
    wall = time.monotonic() - t0
    ordinary = {"wall_s": round(wall, 3), "last": parse(lines)[-1]["_line"],
                "last_time_ms": int(parse(lines)[-1]["time"]), "budget_ms": 990}
    e.quit()

    # Ponder, then a finite budget measured from ponderhit.
    e = engine()
    e.position()
    wait = 3.0
    t_go = time.monotonic()
    e.send("go ponder movetime 1000")
    time.sleep(wait)
    t_hit = time.monotonic()
    e.send("ponderhit")
    lines = e.read_until(lambda l: l.startswith("bestmove"), timeout=180)
    t_end = time.monotonic()
    parsed = parse(lines)
    e.quit()

    ponder = {
        "go": "go ponder movetime 1000",
        "ponder_wait_s": round(t_hit - t_go, 3),
        "wall_after_hit_s": round(t_end - t_hit, 3),
        "budget_after_hit_ms": 990,
        "first_line_after_hit": parsed[0]["_line"] if parsed else None,
        "last_line": parsed[-1]["_line"] if parsed else None,
        "last_time_ms": int(parsed[-1]["time"]) if parsed else None,
        "predicted_time_if_counted_from_go": round((t_end - t_go) * 1000),
        "predicted_time_if_counted_from_hit": round((t_end - t_hit) * 1000),
    }
    dump("time_ponder", {"settings": SET, "ordinary": ordinary, "ponder": ponder})
    print("ordinary last time:", ordinary["last_time_ms"], "ms of", ordinary["budget_ms"])
    print("ponder: wall after hit %.3fs, last `time` %s ms, from-go would be %s" % (
        ponder["wall_after_hit_s"], ponder["last_time_ms"],
        ponder["predicted_time_if_counted_from_go"]))


# --------------------------------------------------------------------------
# hashfull bounds and what it samples
# --------------------------------------------------------------------------

def probe_hashfull_bounds():
    out = {"runs": []}
    for depth, hash_mb in ((24, 32), (20, 1), (16, 64)):
        e = engine(Hash=hash_mb)
        e.position()
        lines, bm = e.search("depth %d" % depth, timeout=300)
        rows = parse(lines)
        vals = [int(r["hashfull"]) for r in rows]
        out["runs"].append({
            "depth": depth, "hash_mb": hash_mb,
            "series": vals, "max": max(vals), "min": min(vals),
            "in_0_1000": all(0 <= v <= 1000 for v in vals),
            "monotone_non_decreasing": all(b >= a for a, b in zip(vals, vals[1:])),
            "final_line": rows[-1]["_line"],
        })
        e.quit()
    dump("hashfull_bounds", {"settings": SET, **out})
    for r in out["runs"]:
        print("depth %-2d hash %-3d MB -> max %d, in-range %s, monotone %s" % (
            r["depth"], r["hash_mb"], r["max"], r["in_0_1000"],
            r["monotone_non_decreasing"]))


# --------------------------------------------------------------------------
# score sign from both sides of the same board
# --------------------------------------------------------------------------

def probe_score_sign():
    e = engine()
    out = []
    cases = [
        ("white up a rook, White to move", "4k3/8/8/8/8/8/8/4K2R w - - 0 1"),
        ("white up a rook, Black to move", "4k3/8/8/8/8/8/8/4K2R b - - 0 1"),
        ("white up a queen, White to move", "4k3/8/8/8/8/8/8/3QK3 w - - 0 1"),
        ("white up a queen, Black to move", "4k3/8/8/8/8/8/8/3QK3 b - - 0 1"),
        ("black up a queen, Black to move", "3qk3/8/8/8/8/8/8/4K3 b - - 0 1"),
        ("black up a queen, White to move", "3qk3/8/8/8/8/8/8/4K3 w - - 0 1"),
    ]
    for name, fen in cases:
        chess.Board(fen)
        e.position(fen)
        lines, bm = e.search("depth 12", timeout=120)
        rows = parse(lines)
        out.append({"case": name, "fen": fen, "score": rows[-1]["score"],
                    "stm": "white" if " w " in fen else "black",
                    "line": rows[-1]["_line"], "bestmove": bm})
    e.quit()

    # mate sign from the side that DELIVERS it
    e = engine()
    mate_white = "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1"
    mirrored = chess.Board(mate_white).mirror().fen(en_passant="fen")
    for name, fen in (("White mates (White to move)", mate_white),
                      ("Black mates (mirrored, Black to move)", mirrored)):
        chess.Board(fen)
        e.position(fen)
        lines, bm = e.search("depth 12", timeout=120)
        rows = parse(lines)
        out.append({"case": name, "fen": fen, "score": rows[-1]["score"],
                    "stm": "white" if " w " in fen else "black",
                    "line": rows[-1]["_line"], "bestmove": bm})
    e.quit()
    dump("score_sign", {"settings": SET, "cases": out})
    for c in out:
        print("%-42s %-10s %s" % (c["case"], c["score"], c["stm"]))


# --------------------------------------------------------------------------
# paths that emit no depth line at all
# --------------------------------------------------------------------------

def probe_noinfo():
    out = {"cases": []}

    def note(name, e, go, **kw):
        e.position(**kw) if kw else e.position()
        lines, bm = e.search(go, timeout=120, **({"stop_after": kw["stop_after"]} if "stop_after" in kw else {}))
        depths = [l for l in lines if l.startswith("info depth")]
        out["cases"].append({
            "case": name, "go": go, "info_depth_lines": len(depths),
            "all_info_lines": [l for l in lines if l.startswith("info")],
            "bestmove": bm})

    e = engine()
    note("book path (OwnBook on, startpos)", engine() if False else e, "movetime 300")
    e.quit()

    e = engine(OwnBook="true")
    e.position()
    lines, bm = e.search("movetime 300", timeout=60)
    out["cases"].append({"case": "book path (OwnBook true)", "go": "movetime 300",
                         "info_depth_lines": len([l for l in lines if l.startswith("info depth")]),
                         "all_info_lines": [l for l in lines if l.startswith("info")],
                         "bestmove": bm})
    e.quit()

    e = engine()
    e.position()
    lines, bm = e.search("nodes 0", timeout=60)
    out["cases"].append({"case": "go nodes 0", "go": "nodes 0",
                         "info_depth_lines": 0,
                         "all_info_lines": [l for l in lines if l.startswith("info")],
                         "bestmove": bm})
    e.quit()

    # empty clock reserve: emergency path
    e = engine()
    e.position()
    lines, bm = e.search("wtime 1 btime 1", timeout=60)
    out["cases"].append({"case": "empty clock reserve (wtime 1)", "go": "wtime 1 btime 1",
                         "info_depth_lines": len([l for l in lines if l.startswith("info depth")]),
                         "all_info_lines": [l for l in lines if l.startswith("info")],
                         "bestmove": bm})
    e.quit()

    dump("noinfo", {"settings": SET, **out})
    for c in out["cases"]:
        print("%-34s depth-lines=%d bm=%s info=%r" % (
            c["case"], c["info_depth_lines"], c["bestmove"], c["all_info_lines"]))


if __name__ == "__main__":
    import sys
    fns = {"time_ponder": probe_time_ponder, "hashfull_bounds": probe_hashfull_bounds,
           "score_sign": probe_score_sign, "noinfo": probe_noinfo}
    for n in (sys.argv[1:] or list(fns)):
        print("==", n)
        fns[n]()
