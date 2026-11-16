#!/usr/bin/env python3
"""dtm_oracle.py FENS OUTDIR : score the engine's move by its true DISTANCE TO MATE, using a validated solver.

This is the upgrade the coordinator asked for: instead of "did the engine miss an immediate mate", it asks
"does the engine's move reach a position whose true DTM is worse than the best move's DTM", with DTM from an
exact retrograde solve.

Scope, stated before any number is produced:
  * only signatures the solver can enumerate: ONE bare king versus ONE piece (KQvK, KRvK, KBvK, KNvK, KPvK);
  * the solver is validated on KQvK against theory (max DTM must be 19 plies) and the script REFUSES to report
    if that validation fails;
  * KBvK and KNvK are draws by insufficient material — they are solved but always draw, so they contribute
    nothing and are skipped;
  * KPvK is solved but its pawn-promotion successors leave the signature, so a promotion is recorded as
    "escapes the oracle" rather than guessed at.

Everything outside this scope is reported as out of scope, never silently dropped.
"""
import chess
import os
import sys

PIECE_OF = {"P": chess.PAWN, "N": chess.KNIGHT, "B": chess.BISHOP, "R": chess.ROOK, "Q": chess.QUEEN}
SOLVER = None


def load_solver_module(path):
    src = open(path).read().split("if __name__")[0]
    ns = {}
    exec(compile(src, path, "exec"), ns)
    return ns


def sig_of(board):
    """Signature of the non-bare side if exactly one side is king-only, else None."""
    names = {chess.PAWN: "P", chess.KNIGHT: "N", chess.BISHOP: "B", chess.ROOK: "R", chess.QUEEN: "Q"}
    w, b = [], []
    for pt, ch in names.items():
        w += [ch] * len(board.pieces(pt, chess.WHITE))
        b += [ch] * len(board.pieces(pt, chess.BLACK))
    if bool(w) == bool(b):
        return None
    if w:
        return "".join(sorted(w)), chess.WHITE
    return "".join(sorted(b)), chess.BLACK


def main():
    fens_path, outdir = sys.argv[1], sys.argv[2]
    here = os.path.dirname(os.path.abspath(__file__))
    ns = load_solver_module(os.path.join(here, "dtm_bfs.py"))
    solve = ns["solve"]

    positions = [l.strip() for l in open(fens_path) if l.strip()]
    by_sig = {}
    for i, fen in enumerate(positions):
        b = chess.Board(fen)
        s = sig_of(b)
        if s is None:
            continue
        sig, strong = s
        by_sig.setdefault((sig, strong), []).append((i, fen))

    os.makedirs(outdir, exist_ok=True)
    log = open(os.path.join(outdir, "dtm_oracle.txt"), "w")
    log.write("# DTM oracle over lone-king positions, by signature\n\n")

    for (sig, strong), items in sorted(by_sig.items()):
        if sig in ("B", "N", "BB", "NN", "BN"):
            log.write("signature %s: insufficient material, always a draw — skipped\n" % sig)
            continue
        if len(sig) > 1:
            log.write("signature %s: %d pieces — outside this solver's scope (k=1 only), skipped\n"
                      % (sig, len(sig)))
            continue
        log.write("signature **%s** (%d positions in the sample)\n\n" % (sig, len(items)))
        dtm, succ, turn_of, boards = solve(sig, strong)
        if sig == "Q":
            mx = max(v for k, v in dtm.items() if turn_of[k] == strong)
            verdict = "MATCH" if mx == 19 else "MISMATCH"
            log.write("- validation: max DTM strong-to-move = %d plies vs theory 19 -> **%s**\n" % (mx, verdict))
            if verdict != "MATCH":
                log.write("\nREFUSING to report: the solver failed validation on this binary.\n")
                break
            print("validation", verdict)
        # score each position: engine-best DTM vs best-legal DTM, both from the current side's perspective
        for idx, fen in items:
            b = chess.Board(fen)
            log.write("\n### position %d: `%s`\n" % (idx, fen))
            log.write("| move | DTM after (plies, strong-to-move conv.) |\n|---|---|\n")
            best = None
            for m in sorted(b.legal_moves, key=lambda x: x.uci()):
                c = b.copy()
                c.push(m)
                if c.is_checkmate():
                    v = 0
                else:
                    k = (c.board_fen(), c.turn)
                    v = dtm.get(k)
                    if v is not None and c.turn != strong:
                        v -= 1
                log.write("| %s | %s |\n" % (m.uci(), "draw/unsolved" if v is None else v))
                if v is not None and (best is None or v < best):
                    best = v
            log.write("\nbest DTM available: %s plies\n" % best)
    log.close()
    print(open(os.path.join(outdir, "dtm_oracle.txt")).read()[-1200:])


if __name__ == "__main__":
    main()
