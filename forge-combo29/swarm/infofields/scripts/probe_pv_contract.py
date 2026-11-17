"""The `pv` claim, stated the only way UCI makes it testable.

UCI does not say pv[0] of EVERY info line equals bestmove -- deeper iterations
legitimately change the best move, and bestmove is the LAST iteration's choice.
The contract a client can rely on is:

    the FINAL depth line's pv[0] == bestmove          (on a searching path)

plus: every pv on the wire is a legal line from the position given.

Both are tested here, separately from the "empty pv" bail (which is a known
defect, reported elsewhere). Intermediate-depth disagreement is recorded as
expected behaviour, not as a violation, and the count is reported so the
distinction is visible rather than hidden.
"""

import json
import os

import chess

import uci

ENGINE = os.environ.get("FORGE_BIN", "/agent/repos/work-infofields/build/forge")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "evidence")
SET = {"build": "g++ -DFORGE_MARCH=x86-64-v4 Release NDEBUG", "base_commit": "6b98f217",
       "threads": 1, "own_book": False}

FENS = [
    (None, "startpos"),
    ("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", "kiwipete"),
    ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", "rook-ending"),
    ("r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9", "italian"),
    ("2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1", "mate-in-2"),
    ("6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1", "black-to-move"),
    ("4k3/8/8/8/8/8/8/4K2R b - - 0 1", "black-down-a-rook"),
    ("rnbqkbnr/ppp2ppp/4p3/3pP3/3P4/8/PPP2PPP/RNBQKBNR b KQkq - 0 3", "french"),
]


def parse(lines):
    out = []
    for l in lines:
        f, pv = uci.parse_info(l)
        if f and "depth" in f:
            out.append({**f, "pv_moves": pv, "_line": l})
    return out


def legal_line(fen, pv):
    board = chess.Board(fen if fen else chess.STARTING_FEN)
    for i, tok in enumerate(pv):
        mv = chess.Move.from_uci(tok)
        if mv not in board.legal_moves:
            return False, i, tok
        board.push(mv)
    return True, None, None


def run_case(fen, name, go, stop_after=None, multipv=1):
    e = uci.Engine(ENGINE)
    e.handshake()
    e.setoption("OwnBook", "false")
    e.setoption("MultiPV", str(multipv))
    e.position(fen)
    lines, bm = e.search(go, timeout=300, stop_after=stop_after)
    e.quit()
    rows = parse(lines)
    best = bm.split()[1] if len(bm.split()) > 1 else None

    # pv[0] of line 1 at each depth (MultiPV>1 splits one depth into m lines)
    line1 = [r for r in rows if int(r.get("multipv", 1)) == 1]
    intermediate = [r for r in line1[:-1] if r["pv_moves"] and r["pv_moves"][0] != best]
    last = line1[-1] if line1 else None

    illegal = []
    for r in rows:
        ok, idx, tok = legal_line(fen, r["pv_moves"])
        if not ok:
            illegal.append({"line": r["_line"], "index": idx, "move": tok})

    return {
        "case": name, "fen": fen, "go": go, "multipv": multipv,
        "stop_after_s": stop_after, "bestmove": best,
        "n_lines": len(rows), "n_depth_levels": len(line1),
        "final_line": last["_line"] if last else None,
        "final_pv0": last["pv_moves"][0] if last and last["pv_moves"] else None,
        "final_pv0_matches_bestmove": bool(last and last["pv_moves"] and last["pv_moves"][0] == best),
        "intermediate_disagreements": len(intermediate),
        "illegal_pv_lines": illegal,
        "empty_final_pv": bool(last) and not last["pv_moves"],
    }


def main():
    cases = []
    for fen, name in FENS:
        if fen:
            chess.Board(fen)
        cases.append(run_case(fen, name, "depth 14"))

    cases.append(run_case(None, "startpos multipv3", "depth 12", multipv=3))
    cases.append(run_case("r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
                          "kiwipete multipv3", "depth 12", multipv=3))

    # aborted searches: the abort branch can publish a *different* pv head, so
    # this is where a final-line mismatch would actually appear.
    for t in (0.5, 0.8, 1.1, 1.5):
        cases.append(run_case(None, "startpos abort %.1fs" % t, "depth 40", stop_after=t))
    for t in (0.8, 1.0, 1.3):
        cases.append(run_case("r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
                              "italian abort %.1fs" % t, "depth 40", stop_after=t))

    payload = {"settings": SET, "cases": cases}
    with open(os.path.join(OUT, "pv_contract.json"), "w") as fh:
        json.dump(payload, fh, indent=1, sort_keys=True)

    print("%-24s final_pv0==bm  illegal  intermed  empty_final" % "case")
    for c in cases:
        print("%-24s %-13s %-8d %-9d %s" % (
            c["case"], c["final_pv0_matches_bestmove"], len(c["illegal_pv_lines"]),
            c["intermediate_disagreements"], c["empty_final_pv"]))
    bad = [c for c in cases if not c["final_pv0_matches_bestmove"]]
    ill = [c for c in cases if c["illegal_pv_lines"]]
    print("\nfinal-line mismatches:", len(bad), "cases with illegal pv:", len(ill))
    for c in bad:
        print("  MISMATCH", c["case"], "bestmove", c["bestmove"], "final_pv0", c["final_pv0"])
        print("    ", (c["final_line"] or "")[:220])


if __name__ == "__main__":
    main()
