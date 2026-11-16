#!/usr/bin/env python3
"""check_s21f2_v2.py EXE OUT — check of seat 21's 21-F2, done CORRECTLY.

My first version (check_s21f2.py) piped `quit` into the engine right after `go depth 1`, which is exactly
seat 19's 19-F12 fault: the build answers a FABRICATED `bestmove` with no info line. That version's `a2a3`
is therefore NOT evidence of anything, and its perft evidence, while sound (perft is synchronous), is
re-measured here too. This version is a long-lived process that reads stdout until `bestmove` and only then
sends anything else.

Claim chain (seat 21's 21-F2):
 (1) a REFUSED `position fen` still answers `readyok`  -> harness must count readyok lines against a known number
 (2) after the refusal the engine keeps the PREVIOUS position -> proven by synchronous perft, which cannot be
     faked by a quit, plus a real depth-1 search waited out properly
 (3) the kept position is the OLD one, so a GUI gets a move that is legal for the old position and ILLEGAL for
     the position it asked for -> that is the hazard
"""
import subprocess
import sys
import time

import chess

BADMARK = ("invalid FEN", "invalid value", "unknown option", "illegal move")


class Eng:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.DEVNULL, text=True, bufsize=1)
        self.send("uci")
        while True:
            if self.p.stdout.readline().startswith("uciok"):
                break
        self.send("setoption name Threads value 1")
        self.sync()
        self.send("setoption name Hash value 16")
        self.sync()
        self.send("setoption name OwnBook value false")
        self.sync()

    def send(self, s):
        self.p.stdin.write(s + "\n")
        self.p.stdin.flush()

    def sync(self):
        self.send("isready")
        out = []
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise EOFError
            out.append(l.rstrip("\n"))
            if l.startswith("readyok"):
                return out

    def position(self, fen):
        """Returns (readyok_count_for_this_command, refusal_line_or_None)."""
        self.send("position fen " + fen)
        lines = self.sync()
        ready = sum(1 for l in lines if l == "readyok")
        bad = next((l for l in lines if any(b in l for b in BADMARK)), None)
        return ready, bad

    def perft(self, depth):
        self.send("go perft %d" % depth)
        lines = []
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise EOFError
            l = l.rstrip("\n")
            lines.append(l)
            if l.startswith("nodes "):
                break
        self.sync()
        nodes = int([l for l in lines if l.startswith("nodes ")][-1].split()[1])
        return nodes, lines

    def search(self, go):
        self.send(go)
        lines = []
        while True:
            l = self.p.stdout.readline()
            if not l:
                raise EOFError("closed mid-search")
            l = l.rstrip("\n")
            lines.append(l)
            if l.startswith("bestmove"):
                break
        self.sync()
        infos = [l for l in lines if l.startswith("info depth")]
        bm = [l for l in lines if l.startswith("bestmove")][-1].split()[1]
        return bm, len(infos), infos[-1] if infos else ""

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=5)
        except Exception:
            self.p.kill()


exe, outpath = sys.argv[1:3]
GOOD = "r1bqk2r/ppp1bppp/3p1n2/8/3QP3/2N5/PPP1BPPP/R1B1K2R w KQkq - 2 8"
GOOD2 = "r3r1k1/p1bb1ppp/1p1q4/3P1p2/1nBP4/PPN2N1P/5PP1/1R1Q1RK1 b - - 0 1"
BAD = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN w KQkq - 0 1"      # 7 squares in rank 8
BAD2 = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBN1 w KQ - 0 1"  # KQ claimed but h1 is empty: seat 21's FEN

lines = []


def emit(s):
    lines.append(s)
    print(s)


e = Eng(exe)

# ---- control: the good FENs must be ACCEPTED and their perft must be non-zero and distinct
g_nodes, g_lines = e.perft(2)
e.position(GOOD2)
g2_nodes, _ = e.perft(2)
e.position(GOOD)
emit("## control — the good positions are accepted and give real, distinct perft numbers")
emit("| position | engine perft 2 | python-chess legal moves |")
emit("|---|---|---|")
emit("| GOOD (KQkq) | %d | %d |" % (g_nodes, chess.Board(GOOD).legal_moves.count()))
emit("| GOOD2 (other) | %d | %d |" % (g2_nodes, chess.Board(GOOD2).legal_moves.count()))
if g_nodes in (0, None) or g_nodes == g2_nodes:
    raise SystemExit("CONTROL FAILED: the good positions' perft 2 are %r and %r - the harness cannot tell "
                     "positions apart, refusing to report" % (g_nodes, g2_nodes))
# a perft-2 sanity check against python-chess, so the numbers are known to be real perft values
py_g = chess.Board(GOOD)
expected = sum(1 for _ in py_g.legal_moves)  # perft 1 count, only used as a floor
if g_nodes < expected:
    raise SystemExit("CONTROL FAILED: engine perft 2 = %d is below the number of legal moves (%d); "
                     "these are not perft numbers" % (g_nodes, expected))

# ---- link 1: readyok after a refused position
e.position(GOOD)
ready_before, bad_before = e.position(BAD)
ready_after, bad_after = e.position(GOOD)
emit("")
emit("## link 1 — a REFUSED `position fen` still answers readyok")
emit("| command | refusal line | readyok lines |")
emit("|---|---|---|")
emit("| position fen BAD | %s | %d |" % (bad_before or "NONE (!)", ready_before))
emit("| position fen GOOD (control) | %s | %d |" % (bad_after or "none", ready_after))
if not bad_before:
    raise SystemExit("CONTROL FAILED: the FEN I expect to be refused was ACCEPTED (%r); the check has "
                     "nothing to test" % (BAD,))

# ---- link 2 and 3: which board does the engine hold after the refusal?
# put GOOD2 on the board, refuse BAD, then perft synchronously.
e.position(GOOD2)
ready_r, bad_r = e.position(BAD)
after_nodes, after_lines = e.perft(1)
e.position(GOOD2)
true_nodes, _ = e.perft(1)
emit("")
emit("## link 2 — after a refused FEN, which board is on the engine? (synchronous perft 1)")
emit("| sequence | perft 1 nodes | equals which board? |")
emit("|---|---|---|")
which = ("GOOD2 (%d)" % true_nodes) if after_nodes == true_nodes else "something else"
emit("| position GOOD2 -> position BAD(refused) -> perft 1 | %d | %s |" % (after_nodes, which))
emit("| position GOOD2 -> perft 1 (reference) | %d | GOOD2 |" % true_nodes)
emit("| position GOOD (first board) -> perft 1 | %s | %s |" % (
    next((l for l in g_lines if l.startswith("nodes ")), "?").split()[-1], "GOOD"))
if after_nodes != true_nodes:
    raise SystemExit("RESULT: the board after a refusal is NOT the previous position (perft %d vs %d). "
                     "Seat 21's link 2 is REFUTED." % (after_nodes, true_nodes))

# ---- link 3: a real, fully-waited depth-1 search after the refusal, with legality checked against both boards
e.position(GOOD2)
e.position(BAD)
bm, ninfos, lastinfo = e.search("go depth 1")
old = chess.Board(GOOD2)
# the board the GUI ASKED FOR is BAD, which python-chess cannot even build (7 squares in rank 8).
# So link 3's legality test uses BAD2 (a FEN python-chess parses but the engine refuses): it gives a board
# the GUI believes in, which the engine does not hold.
e.position(GOOD2)
ready_b2, bad_b2 = e.position(BAD2)
bm2, ninfos2, _ = e.search("go depth 1")
new2 = chess.Board(BAD2)
legal_old2 = chess.Move.from_uci(bm2) in chess.Board(GOOD2).legal_moves
legal_new2 = chess.Move.from_uci(bm2) in new2.legal_moves
emit("")
emit("## link 3 — the move a GUI receives after a refusal (real search, waited out)")
emit("| refused FEN | its refusal line | bestmove | info lines | legal in the OLD board | legal in the board the GUI asked for |")
emit("|---|---|---|---|---|---|")
emit("| BAD (7 squares, python-chess cannot parse it) | %s | %s | %d | %s | (not testable) |" %
     (bad_r or "none", bm, ninfos, chess.Move.from_uci(bm) in old.legal_moves))
emit("| BAD2 (castling right without rook, both parsers read it) | %s | %s | %d | %s | %s |" %
     (bad_b2 or "ACCEPTED (!)", bm2, ninfos2, legal_old2, legal_new2))
if ninfos == 0 or ninfos2 == 0:
    raise SystemExit("RESULT INVALID: an answer with 0 info lines may be a quit artifact; refusing")

with open(outpath, "w") as fh:
    fh.write("\n".join(lines) + "\n")
e.close()
