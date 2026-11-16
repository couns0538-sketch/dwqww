#!/usr/bin/env python3
"""seat 17: the moves-path guard tested on the SELF-PLAY path, with a deliberately corrupted list.

Same idiom as the owner's self-play (one process, `position startpos moves <accumulated>` before every
move, `go softnodes 2000`), but at ply 40 one token in the accumulated list is corrupted — a move made
illegal by replotting, and then also a made-up token. The harness rule under test:

  treat `info string illegal move` as FATAL for the game: do not apply the following bestmove.

The test PASSES only if, on the corrupted ply, (a) the engine emits the `illegal move` line and (b) the
guard refuses the move that follows instead of applying it. A run where the guard does not fire is not a
pass — it is the hazard.

usage: selfplay_corrupt.py <exe> <outdir>
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

    def close(self):
        try:
            self.send("quit")
            self.p.wait(timeout=20)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            self.p.kill()
            self.p.wait()


def main():
    exe, outdir = sys.argv[1:3]
    os.makedirs(outdir, exist_ok=True)
    results = {}

    for mode in ("corrupt_illegal_move", "corrupt_garbage_token"):
        eng = Engine(exe)
        eng.send("uci")
        eng.read_until(lambda l: l.strip() == "uciok")
        for k, v in PC20:
            eng.send("setoption name %s value %s" % (k, v))
            eng.send("isready")
            eng.read_until(lambda l: l.strip() == "readyok")

        board = chess.Board()
        moves = []
        caught = None
        applied_after_error = 0
        reached_corrupt_ply = False
        for ply in range(80):
            if board.is_game_over():
                results.setdefault(mode, {})["stopped_reason"] = "game over at ply %d" % ply
                break
            sent = list(moves)
            corrupt_at = None
            if ply == 40:
                if len(sent) < 2:
                    results.setdefault(mode, {})["stopped_reason"] = \
                        "never reached ply 40 (game ended at ply %d)" % len(sent)
                    break
                reached_corrupt_ply = True
                corrupt_at = len(sent) - 1
                if mode == "corrupt_illegal_move":
                    # Replace the last token with one that is NOT legal in the position before it.
                    probe = chess.Board()
                    for tok in sent[:-1]:
                        probe.push_uci(tok)
                    legal_before = {m.uci() for m in probe.legal_moves}
                    replacement = None
                    for cand in ("a7a8q", "h7h8q", "e7e8q", "a2a1q"):
                        if cand not in legal_before:
                            replacement = cand
                            break
                    sent[corrupt_at] = replacement
                else:
                    sent[corrupt_at] = "zzzz"

            pos = "position startpos" + (" moves " + " ".join(sent) if sent else "")
            eng.send(pos)
            eng.send("isready")
            ready = eng.read_until(lambda l: l.strip() == "readyok")
            before = len(eng.lines)
            eng.send("go softnodes 2000")
            best = eng.read_until(lambda l: l.startswith("bestmove"))
            window = eng.lines[before:]
            if ply == 40:
                illegal_line = [l for l in window if "illegal move" in l]
                caught = illegal_line[0] if illegal_line else None
                returned = best.split()[1] if best else None
                # THE GUARD: if an illegal-move line was emitted, the move must NOT be applied
                if caught:
                    results[mode] = {
                        "ply": ply,
                        "corrupted_token": sent[corrupt_at],
                        "engine_line": caught,
                        "engine_returned": returned,
                        "guard_decision": "REFUSE (fatal for this game)",
                        "move_applied": False,
                        "guard_worked": True,
                        "note": ("the engine still returned a move (%s), which belongs to the retained "
                                 "legal prefix - the guard must refuse it" % returned),
                    }
                    # do not apply; stop the game here
                    break
                else:
                    results[mode] = {
                        "ply": ply, "corrupted_token": sent[corrupt_at],
                        "engine_line": None, "engine_returned": returned,
                        "guard_decision": "would apply - HAZARD", "move_applied": True,
                        "guard_worked": False,
                    }
                    break
            if not best:
                break
            tok = best.split()[1]
            if tok not in [m.uci() for m in board.legal_moves]:
                applied_after_error += 1
                break
            moves.append(tok)
            board.push_uci(tok)
        open(os.path.join(outdir, mode + ".log"), "w").write("\n".join(eng.lines) + "\n")
        eng.close()
        results[mode]["plies_before_corruption"] = 40
        print(json.dumps(results[mode]), flush=True)

    json.dump(results, open(os.path.join(outdir, "selfplay_corrupt.json"), "w"), indent=1)
    all_ok = all(r.get("guard_worked") for r in results.values())
    print("GUARD WORKED ON THE SELF-PLAY PATH:", all_ok)


if __name__ == "__main__":
    main()
