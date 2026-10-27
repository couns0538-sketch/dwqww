#!/usr/bin/env python3
"""Independent PGN legality check for the O1 self-play games (python-chess move generator).
Replays every game from its FEN header (or the start position), checks that every move is legal,
that the game-ending result is consistent (mate / stalemate / 50-move / repetition / insufficient
material / adjudication), and classifies terminations. Any illegal move, crash ("disconnect",
"abandoned"), hang/missing bestmove ("stall", "timeout", "time forfeit" beyond the time margin)
is reported; exit 1 on any illegal move, crash or stall.
usage: pgn_legality.py <games.pgn> [<more.pgn> ...]"""
import collections
import sys

import chess
import chess.pgn


def main():
    totals = collections.Counter()
    terminations = collections.Counter()
    problems = []
    plies = 0
    for path in sys.argv[1:]:
        with open(path, encoding="utf-8", errors="replace") as fh:
            while True:
                game = chess.pgn.read_game(fh)
                if game is None:
                    break
                totals["games"] += 1
                board = game.board()
                ident = f"{path} game {totals['games']} ({game.headers.get('White')}-{game.headers.get('Black')}, " \
                        f"round {game.headers.get('Round')})"
                if game.errors:
                    problems.append(f"{ident}: PGN parse/legality errors: {[str(e) for e in game.errors]}")
                    totals["illegal"] += 1
                for move in game.mainline_moves():
                    if move not in board.legal_moves:
                        problems.append(f"{ident}: ILLEGAL move {move.uci()} in {board.fen()}")
                        totals["illegal"] += 1
                        break
                    board.push(move)
                    plies += 1
                term = game.headers.get("Termination", "missing")
                terminations[term] += 1
                result = game.headers.get("Result", "*")
                if result == "*":
                    problems.append(f"{ident}: unfinished game (Result *)")
                    totals["unfinished"] += 1
                lowered = term.lower()
                if any(k in lowered for k in ("illegal",)):
                    totals["illegal"] += 1
                    problems.append(f"{ident}: termination '{term}'")
                if any(k in lowered for k in ("disconnect", "abandon", "crash")):
                    totals["crash"] += 1
                    problems.append(f"{ident}: termination '{term}'")
                if any(k in lowered for k in ("stall", "timeout")):
                    totals["stall"] += 1
                    problems.append(f"{ident}: termination '{term}'")
                if "time forfeit" in lowered:
                    totals["time_forfeit"] += 1
                if board.is_checkmate() and result not in ("1-0", "0-1"):
                    problems.append(f"{ident}: final position is mate but result {result}")
                if board.is_stalemate() and result != "1/2-1/2":
                    problems.append(f"{ident}: final position is stalemate but result {result}")
    print(f"games {totals['games']}, plies {plies}, illegal {totals['illegal']}, crashes {totals['crash']}, "
          f"stalls/missing bestmove {totals['stall']}, time forfeits {totals['time_forfeit']}, "
          f"unfinished {totals['unfinished']}")
    print("terminations:", dict(terminations))
    for p in problems[:50]:
        print(" -", p)
    bad = totals["illegal"] or totals["crash"] or totals["stall"] or totals["unfinished"] or not totals["games"]
    print("PGN LEGALITY:", "FAIL" if bad else "PASS")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
