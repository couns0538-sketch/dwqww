"""Cross-build correctness sweep.

Three independent checks, because a node-count match alone does not prove the
builds agree on what they *are*:

1. bench pins (already run separately) -- fixed corpus, fixed depth.
2. perft at several depths on several positions -- pure movegen, no eval, no
   search, so it isolates the bitboard/PEXT path.
3. a 120-position `go depth 12` sweep compared field by field: bestmove, score
   kind, score, depths reached, AND node count. Node equality is the strong
   one: a search whose evaluation differed by 1 cp would diverge somewhere.
"""

import json
import sys

sys.path.insert(0, "/tmp/build")
from harness import Engine, parse_info

BUILDS = {
    "native": "/tmp/build/native/forge",
    "v2": "/tmp/build/v2/forge",
    "v3": "/tmp/build/v3/forge",
}

PERTF_POSITIONS = [
    ("startpos", "position startpos"),
    ("kiwipete", "position fen r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1"),
    ("pos3", "position fen 8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"),
    ("pos4", "position fen r3k2r/Pppp1ppp/1b3nbN/nP6/BBP1P3/q4N2/Pp1P2PP/R2Q1RK1 w kq - 0 1"),
    ("pos5", "position fen rnbq1k1r/pp1Pbppp/2p5/8/2B5/8/PPP1NnPP/RNBQK2R w KQ - 1 8"),
    ("ep-heavy", "position fen 8/8/8/8/1k1Pp2r/8/8/4K3 b - d3 0 1"),
]


def perft(eng, pos_cmd, depth):
    eng.send(pos_cmd)
    text = eng.command(f"go perft {depth}", wait_for="nodes", timeout=600)
    for line in text.splitlines():
        if line.startswith("nodes "):
            return int(line.split()[1])
    raise RuntimeError(f"no perft total in {text!r}")


def main():
    out = {"perft": {}, "sweep": {}}

    print("=== perft across builds ===")
    engines = {k: Engine(v, hash_mb=16, threads=1, nnue=True, book=False) for k, v in BUILDS.items()}
    for name, cmd in PERTF_POSITIONS:
        depths = [5] if name == "startpos" else [4]
        for d in depths:
            got = {b: perft(e, cmd, d) for b, e in engines.items()}
            agree = len(set(got.values())) == 1
            out["perft"][f"{name}/d{d}"] = got
            print(f"  {name:10s} d{d}  " + "  ".join(f"{b}={v}" for b, v in got.items())
                  + ("  AGREE" if agree else "  *** DISAGREE ***"))
    for e in engines.values():
        e.close()

    fens = [l.strip() for l in open("/tmp/build/corpus/pos120.fens") if l.strip()]
    print(f"\n=== go depth 12 sweep, {len(fens)} positions ===")
    engines = {k: Engine(v, hash_mb=16, threads=1, nnue=True, book=False) for k, v in BUILDS.items()}
    mismatches = []
    try:
        for i, fen in enumerate(fens, 1):
            res = {}
            for b, e in engines.items():
                e.send("ucinewgame")
                e.isready()
                e.send(f"position fen {fen}")
                text = e.command("go depth 12", timeout=600)
                info, best = parse_info(text)
                res[b] = {"best": best, "nodes": info.get("nodes"),
                          "score": info.get("score"), "kind": info.get("score_kind"),
                          "depth": info.get("depth")}
            keys = ("best", "nodes", "score", "kind", "depth")
            bad = [k for k in keys if len({json.dumps(res[b][k]) for b in res}) != 1]
            if bad:
                mismatches.append({"i": i, "fen": fen, "fields": bad, "rows": res})
                print(f"  {i:3d} MISMATCH on {bad}: {fen}")
            out["sweep"][i] = res
            if i % 20 == 0:
                print(f"  ... {i}/{len(fens)}, mismatches so far {len(mismatches)}", flush=True)
    finally:
        for e in engines.values():
            e.close()

    print(f"\npositions compared: {len(fens)}; fields compared per position: 5 "
          f"(bestmove, nodes, score, score-kind, depth)")
    print(f"positions with any mismatch: {len(mismatches)}")
    out["mismatches"] = mismatches
    json.dump(out, open("/tmp/build/identity-sweep.json", "w"), indent=1)


if __name__ == "__main__":
    main()
