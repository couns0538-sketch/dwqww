#!/usr/bin/env python3
"""seat 17: the moves-path guard validated on the SELF-PLAY path, with a deliberately corrupted list.

Same idiom as the owner's self-play: one process, `position startpos moves <accumulated>` before every move,
`go softnodes 2000`. At ply 40 the LAST accumulated token is corrupted, two ways:
  (a) a promotion token that is illegal in the position before it
  (b) a non-move token, "zzzz"

Then the question: does the engine emit `info string illegal move <token>`, and does the guard (treat that
line as fatal, do not apply the following bestmove) catch it?

The measurement is taken from a per-command line budget, not from a slice of a shared list: `mark()` returns
len(lines) and `since(mark)` returns the lines added after it. My previous two attempts miscounted this and
reported "no illegal line" when the line was there - recorded in FINDINGS as harness bug #5.

usage: selfplay_guard.py <exe> <outdir>
"""
import json
import os
import subprocess
import sys

import chess

S14 = [
    ("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
    ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
    ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
    ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
    ("IirDepth", "2"), ("NonPawnCorrection", "true"),
]
PC20_EXTRA = [
    ("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
    ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false"),
]
PC20 = S14 + PC20_EXTRA


class Engine:
    def __init__(self, exe):
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1)
        self.lines = []

    def send(self, line):
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def read_until(self, pred):
        while True:
            r = self.p.stdout.readline()
            if r == "":
                return None
            r = r.rstrip("\n")
            self.lines.append(r)
            if pred(r):
                return r

    def mark(self):
        return len(self.lines)

    def since(self, mark):
        return self.lines[mark:]

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=20)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            self.p.kill()
            self.p.wait()


def corrupt_token(board_after_prefix, mode):
    """A token that is definitely illegal in the position after the prefix."""
    legal = {m.uci() for m in board_after_prefix.legal_moves}
    if mode == "garbage":
        return "zzzz"
    for cand in ("a7a8q", "h7h8q", "e7e8q", "a2a1q", "a1a8q"):
        if cand not in legal:
            return cand
    raise SystemExit("could not find an illegal token")


def run_mode(exe, mode, outdir, corrupt_ply=40):
    eng = Engine(exe)
    eng.send("uci")
    eng.read_until(lambda l: l.strip() == "uciok")
    for k, v in PC20:
        eng.send("setoption name %s value %s" % (k, v))
        eng.send("isready")
        eng.read_until(lambda l: l.strip() == "readyok")

    board = chess.Board()
    moves = []
    for ply in range(corrupt_ply + 1):
        if board.is_game_over():
            return {"mode": mode, "error": "game ended at ply %d before the corruption" % ply}
        sent = list(moves)
        corrupted = None
        if ply == corrupt_ply:
            probe = chess.Board()
            for tok in sent[:-1]:
                probe.push_uci(tok)
            corrupted = corrupt_token(probe, mode)
            sent[-1] = corrupted

        # Mark BEFORE the position command: the `info string illegal move` line is emitted in
        # response to `position`, not to `go`, so a window that starts after `readyok` misses it
        # entirely. That is the mistake that made my first two runs report a false HAZARD.
        mark = eng.mark()
        eng.send("position startpos" + (" moves " + " ".join(sent) if sent else ""))
        eng.send("isready")
        eng.read_until(lambda l: l.strip() == "readyok")
        eng.send("go softnodes 2000")
        best = eng.read_until(lambda l: l.startswith("bestmove"))
        window = eng.since(mark)

        if ply == corrupt_ply:
            ill = [l for l in window if "illegal move" in l]
            returned = best.split()[1] if best else None
            # Is the returned move legal in the requested position? It cannot be, because the
            # requested position does not exist; check it against the LEGAL PREFIX instead.
            prefix = chess.Board()
            for tok in sent[:-1]:
                prefix.push_uci(tok)
            legal_in_prefix = returned in {m.uci() for m in prefix.legal_moves} if returned else None
            return {
                "mode": mode,
                "ply": ply,
                "corrupted_token": corrupted,
                "engine_emitted_illegal_line": bool(ill),
                "engine_line": ill[0] if ill else None,
                "engine_returned": returned,
                "returned_move_legal_in_legal_prefix": legal_in_prefix,
                "guard_decision": "REFUSE (fatal for this game)" if ill else "WOULD APPLY - HAZARD",
                "guard_worked": bool(ill),
            }

        if not best:
            return {"mode": mode, "error": "no bestmove at ply %d" % ply}
        tok = best.split()[1]
        if tok not in {m.uci() for m in board.legal_moves}:
            return {"mode": mode, "error": "engine returned an illegal move at ply %d: %s" % (ply, tok)}
        moves.append(tok)
        board.push_uci(tok)
    return {"mode": mode, "error": "never reached the corrupt ply"}


def main():
    exe, outdir = sys.argv[1:3]
    os.makedirs(outdir, exist_ok=True)
    results = {}
    for mode in ("illegal_promotion", "garbage"):
        results[mode] = run_mode(exe, mode, outdir)
        json.dump(results, open(os.path.join(outdir, "guard_selfplay.json"), "w"), indent=1)
        print(json.dumps(results[mode]), flush=True)
    ok = all(r.get("guard_worked") for r in results.values())
    print("GUARD WORKED ON THE SELF-PLAY PATH:", ok)


if __name__ == "__main__":
    main()
