"""nodes: monotonicity and worker accounting, and multipv/pv legality.

The `nodes` field is `total_nodes()`, which sums `local_nodes_` with every other
worker's published `nodes_` atomic. That sum is read without a barrier while
helpers are still running, so it is only guaranteed to be a lower bound at any
instant. This probe tests what a client actually receives:

  * is the sequence non-decreasing at Threads 1, 2 and 4?
  * at Threads 1 does the final line equal the bench-pin node count exactly?
  * at MultiPV 3 does the node field fall between depths (the override
    `shown_nodes` accumulates the alternate workers' nodes on top)?

And for `pv`: is `pv[0] == bestmove` on every searching path, and is every pv a
legal line under python-chess?
"""

import json
import os

import chess

import uci

ENGINE = os.environ.get("FORGE_BIN", "/agent/repos/work-infofields/build/forge")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
SET = {"build": "g++ -DFORGE_MARCH=x86-64-v4 Release NDEBUG", "base_commit": "6b98f217",
       "own_book": False}


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


def probe_nodes_threads():
    out = {"by_threads": [], "multipv_nodes": []}
    fen = None
    for threads in (1, 2, 4):
        e = engine(Threads=threads)
        e.position(fen)
        lines, bm = e.search("depth 16", timeout=300)
        rows = parse(lines)
        seq = [int(r["nodes"]) for r in rows]
        out["by_threads"].append({
            "threads": threads, "depth": 16,
            "sequence": seq, "final_nodes": seq[-1],
            "monotone_non_decreasing": all(b >= a for a, b in zip(seq, seq[1:])),
            "final_line": rows[-1]["_line"], "bestmove": bm})
        e.quit()

    for mp in (1, 2, 3):
        e = engine(MultiPV=mp)
        e.position(fen)
        lines, bm = e.search("depth 12", timeout=300)
        rows = parse(lines)
        # nodes must not fall between one depth's last line and the next depth's first
        drops = []
        for i in range(1, len(rows)):
            if int(rows[i]["nodes"]) < int(rows[i - 1]["nodes"]):
                drops.append({"prev_line": rows[i - 1]["_line"],
                              "cur_line": rows[i]["_line"],
                              "prev_depth": int(rows[i - 1]["depth"]),
                              "cur_depth": int(rows[i]["depth"]),
                              "drop": int(rows[i - 1]["nodes"]) - int(rows[i]["nodes"])})
        out["multipv_nodes"].append({
            "multipv": mp, "drops": drops, "n_drops": len(drops),
            "drop_fraction": len(drops) / max(1, len(rows) - 1),
            "rows": [(int(r["depth"]), int(r.get("multipv", 1)), int(r["nodes"]))
                     for r in rows]})
        e.quit()

    dump("nodes_threads", {"settings": SET, **out})
    for r in out["by_threads"]:
        print("Threads %d: final %d monotone %s" % (r["threads"], r["final_nodes"],
                                                    r["monotone_non_decreasing"]))
    for r in out["multipv_nodes"]:
        print("MultiPV %d: %d node drops over %d transitions (%.0f%%)" % (
            r["multipv"], r["n_drops"], len(r["rows"]) - 1, 100 * r["drop_fraction"]))


def probe_pv_all():
    """pv[0] == bestmove and legality, at MultiPV 1 and 3, plus an abort."""
    out = {"cases": []}
    fens = [
        (None, "startpos"),
        ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", "kiwipete"),
        ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", "rook-ending"),
        ("r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9", "italian"),
        ("2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1", "mate-in-2"),
        ("6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1", "black-to-move"),
        ("4k3/8/8/8/8/8/8/4K2R b - - 0 1", "black-down-a-rook"),
    ]

    def check(name, fen, go, stop_after=None, multipv=1):
        e = engine(MultiPV=multipv)
        e.position(fen)
        lines, bm = e.search(go, timeout=300, stop_after=stop_after)
        e.quit()
        rows = parse(lines)
        rec = {"case": name, "fen": fen, "go": go, "multipv_setting": multipv,
               "stop_after_s": stop_after, "bestmove": bm,
               "n_depth_lines": len(rows), "violations": []}
        best = bm.split()[1] if len(bm.split()) > 1 else None
        for r in rows:
            pv = r["pv_moves"]
            if not pv:
                rec.setdefault("empty_pv_lines", []).append(r["_line"])
                continue
            if pv[0] != best and int(r.get("multipv", 1)) == 1:
                rec["violations"].append({"kind": "pv0 != bestmove", "line": r["_line"],
                                          "pv0": pv[0], "bestmove": best})
            board = chess.Board(fen if fen else chess.STARTING_FEN)
            for i, tok in enumerate(pv):
                mv = chess.Move.from_uci(tok)
                if mv not in board.legal_moves:
                    rec["violations"].append(
                        {"kind": "illegal pv move", "line": r["_line"],
                         "index": i, "move": tok})
                    break
                board.push(mv)
        out["cases"].append(rec)

    for fen, name in fens:
        if fen:
            chess.Board(fen)
        check(name, fen, "depth 14")

    # MultiPV 3: does pv[0] of line 1 still equal bestmove?
    check("startpos multipv3", None, "depth 12", multipv=3)
    check("kiwipete multipv3",
          "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
          "depth 12", multipv=3)

    # aborted search: is pv[0] == bestmove after a mid-iteration stop?
    check("startpos aborted at 0.8s", None, "depth 40", stop_after=0.8)
    check("italian aborted at 1.0s",
          "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
          "depth 40", stop_after=1.0)

    dump("pv_all", {"settings": SET, **out})
    for c in out["cases"]:
        print("%-26s lines=%-3d violations=%-2d empty_pv=%d bm=%s" % (
            c["case"], c["n_depth_lines"], len(c["violations"]),
            len(c.get("empty_pv_lines", [])), c["bestmove"]))


if __name__ == "__main__":
    import sys
    fns = {"nodes_threads": probe_nodes_threads, "pv_all": probe_pv_all}
    for n in (sys.argv[1:] or list(fns)):
        print("==", n)
        fns[n]()
