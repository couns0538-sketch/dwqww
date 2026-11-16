#!/usr/bin/env python3
"""seat 17: is the small budget's different move a DEPTH effect or a SELECTION effect?

Position 6 changed its move between go nodes 20000 and 50000/250000. Two candidate explanations:
  DEPTH effect     - the small budget simply stops at a shallower depth; at EQUAL depth it would agree.
  SELECTION effect - the budget changes WHICH move the search settles on, not only how deep it looks,
                     so the small-budget move is worse even at the same depth.

Design: for position 6 and its near neighbours (the other G positions at the same game phase),
run `go depth D` with D fixed at 12 and 16 (depth-fixed = the "equal depth" control), and the three
node budgets. Then evaluate every distinct move the engine chose with an INDEPENDENT shallow search
at a common depth, so the moves are ranked by one yardstick rather than by the search under test.

usage: selection_vs_depth.py <exe> <epd> <outdir> [positions]
"""
import json
import os
import subprocess
import sys

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

BUDGETS = ["go nodes 20000", "go nodes 50000", "go nodes 250000"]
DEPTHS = ["go depth 12", "go depth 16"]
# The yardstick: how good is each chosen move? Search the position AFTER the move at a fixed depth with
# the same engine, from the opponent's side (so a higher score for the opponent means our move was worse).
YARDSTICK_DEPTH = 14


def run(exe, fen, go, timeout=300):
    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT, text=True, bufsize=1)
    out = []

    def send(line):
        proc.stdin.write(line + "\n")
        proc.stdin.flush()

    def read_until(pred):
        while True:
            reply = proc.stdout.readline()
            if reply == "":
                return None
            out.append(reply.rstrip("\n"))
            if pred(reply):
                return reply

    try:
        send("uci")
        read_until(lambda l: l.strip() == "uciok")
        for name, value in PC20:
            send("setoption name %s value %s" % (name, value))
            send("isready")
            read_until(lambda l: l.strip() == "readyok")
        send("position fen " + fen)
        send("isready")
        read_until(lambda l: l.strip() == "readyok")
        send(go)
        read_until(lambda l: l.startswith("bestmove"))
    finally:
        try:
            send("quit")
            proc.wait(timeout=20)
        except (BrokenPipeError, subprocess.TimeoutExpired):
            proc.kill()
            proc.wait()
    depths = [l for l in out if l.startswith("info depth")]
    last = depths[-1] if depths else ""
    best = [l for l in out if l.startswith("bestmove")]
    score = None
    if " score " in last:
        score = last.split(" score ")[1].split(" pv")[0]
    depth_reached = None
    if " depth " in last:
        try:
            depth_reached = int(last.split(" depth ")[1].split()[0])
        except (IndexError, ValueError):
            depth_reached = None
    return (best[-1].split()[1] if best else None), score, depth_reached, "\n".join(out)


def yardstick(exe, fen, move):
    """Score the position after `move` from the OPPONENT's point of view at a fixed depth.

    Negate it: a larger returned number means our move was worse for us.
    """
    import chess
    board = chess.Board(fen)
    try:
        board.push_uci(move)
    except ValueError:
        return None
    after = board.fen()
    _, score, _, _ = run(exe, after, "go depth %d" % YARDSTICK_DEPTH)
    if score is None:
        return None
    kind, value = score.split()[0], int(score.split()[1])
    if kind == "cp":
        return -value          # opponent score negated = our result
    return None                # mate scores handled separately by the caller


def main():
    exe, epd, outdir = sys.argv[1:4]
    count = int(sys.argv[4]) if len(sys.argv) > 4 else 10
    os.makedirs(outdir, exist_ok=True)
    fens = [line.split(";")[0].strip() for line in open(epd) if line.strip()][:count]
    rows = []
    for index, fen in enumerate(fens):
        record = {"index": index, "fen": fen, "runs": {}}
        moves = set()
        for go in BUDGETS + DEPTHS:
            move, score, depth_reached, text = run(exe, fen, go)
            record["runs"][go] = {"move": move, "score": score, "depth_reached": depth_reached}
            open(os.path.join(outdir, "p%d_%s.log" % (index, go.replace(" ", "_"))), "w").write(text)
            if move:
                moves.add(move)
        record["distinct_moves"] = sorted(moves)
        # the interesting split: do the depth-fixed runs agree with each other and with the big budget?
        d12 = record["runs"]["go depth 12"]["move"]
        d16 = record["runs"]["go depth 16"]["move"]
        b20 = record["runs"]["go nodes 20000"]["move"]
        b50 = record["runs"]["go nodes 50000"]["move"]
        b250 = record["runs"]["go nodes 250000"]["move"]
        record["depth_fixed_12_eq_16"] = d12 == d16
        record["small_budget_matches_depth12"] = b20 == d12
        record["small_budget_matches_depth16"] = b20 == d16
        record["big_budget_matches_depth16"] = b250 == d16
        record["depth_seen_at_20000"] = record["runs"]["go nodes 20000"]["depth_reached"]
        record["depth_seen_at_250000"] = record["runs"]["go nodes 250000"]["depth_reached"]

        # yardstick every distinct move so the answer does not come from the search under test
        scores = {}
        for move in sorted(moves):
            scores[move] = yardstick(exe, fen, move)
        record["yardstick_our_result_cp"] = scores
        rows.append(record)
        print(json.dumps(record), flush=True)
    differing = [r for r in rows if len(r["distinct_moves"]) > 1]
    summary = {
        "positions": len(rows),
        "positions_with_more_than_one_move": len(differing),
        "detail": [
            {"index": r["index"], "fen": r["fen"], "moves": r["runs"], "yardstick": r["yardstick_our_result_cp"],
             "depth_fixed_agree": r["depth_fixed_12_eq_16"],
             "small_matches_d12": r["small_budget_matches_depth12"],
             "small_matches_d16": r["small_budget_matches_depth16"]}
            for r in differing
        ],
        "yardstick_depth": YARDSTICK_DEPTH,
    }
    json.dump({"summary": summary, "rows": rows}, open(os.path.join(outdir, "selection.json"), "w"), indent=1)
    print(json.dumps(summary, indent=1))


if __name__ == "__main__":
    main()
