#!/usr/bin/env python3
"""uciprobe.py -- the twelve UCI robustness cases of long 46, one fresh process per case.
Feeds each case's lines (with sleeps where the case needs timing), reads EVERY answer line,
records: the answer lines, the bestmove (checked legal by python-chess where a position exists),
sanitizer lines from stderr, and the exit code."""
import chess
import subprocess
import sys
import threading
import time

exe = sys.argv[1]
outdir = sys.argv[2]

def run_case(name, feed, wait_best=True, check_pos=None):
    """feed: list of (delay, line). Reads everything until the process exits."""
    p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                         stderr=subprocess.PIPE, text=True, bufsize=1)
    out_lines = []
    err_lines = []
    def rdo():
        try:
            for l in p.stdout:
                out_lines.append(l.rstrip("\n"))
        except Exception:
            pass
    def rde():
        try:
            for l in p.stderr:
                err_lines.append(l.rstrip("\n"))
        except Exception:
            pass
    threading.Thread(target=rdo, daemon=True).start()
    threading.Thread(target=rde, daemon=True).start()
    for delay, line in feed:
        time.sleep(delay)
        try:
            p.stdin.write(line + "\n")
            p.stdin.flush()
        except Exception:
            break
    try:
        p.wait(timeout=120)
    except subprocess.TimeoutExpired:
        p.kill()
        p.wait()
    san = [l for l in err_lines if "AddressSanitizer" in l or "LeakSanitizer" in l or
           "SUMMARY" in l or "runtime error" in l or "UndefinedBehaviorSanitizer" in l]
    best = next((l for l in reversed(out_lines) if l.startswith("bestmove ")), None)
    bm_legal = None
    if best and check_pos:
        mv = best.split()[1]
        if mv != "0000" and check_pos is not True:
            b = chess.Board(check_pos)
            bm_legal = mv in [m.uci() for m in b.legal_moves]
        else:
            bm_legal = "n/a"
    with open(f"{outdir}/{name}.txt", "w") as f:
        f.write("== stdout ==\n" + "\n".join(out_lines) + "\n== stderr sanitizer lines ==\n" +
                ("\n".join(san) if san else "(none)") + f"\n== exit {p.returncode} ==\n")
    print(f"== {name}: exit {p.returncode}, san lines {len(san)}, bestmove: {best if best else 'NONE'}"
          + (f" legal={bm_legal}" if bm_legal is not None else ""))

SP = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
base = [(0.0, "uci"), (0.05, "setoption name Threads value 1"), (0.05, "setoption name Hash value 16"),
        (0.05, "setoption name OwnBook value false"), (0.05, "isready")]

run_case("c1_illegal_move", base + [(0.05, "position startpos moves e2e4 e7e5 e1e3"),
                                    (0.05, "isready"), (0.05, "go perft 1"), (0.3, "quit")],
         check_pos=SP)
run_case("c2_hash_zero", base + [(0.05, "setoption name Hash value 0"), (0.05, "isready"),
                                 (0.05, "position startpos"), (0.05, "go depth 1"), (0.5, "quit")],
         check_pos=SP)
run_case("c3_go_stop", base + [(0.05, "position startpos"), (0.05, "go"), (0.7, "stop"), (0.5, "quit")],
         check_pos=SP)
run_case("c4_setoption_no_value", base + [(0.05, "setoption name LmpBase"), (0.05, "isready"),
                                          (0.3, "quit")])
run_case("c5_go_depth_0", base + [(0.05, "position startpos"), (0.05, "go depth 0"), (0.5, "quit")],
         check_pos=SP)
run_case("c6_unknown_command", base + [(0.05, "foo bar"), (0.05, "isready"), (0.3, "quit")])
# case 7: a 600-ply random game from python-chess (seed 46)
import random
random.seed(46)
b = chess.Board()
moves = []
while len(moves) < 600 and not b.is_game_over():
    m = random.choice(list(b.legal_moves))
    moves.append(m.uci())
    b.push(m)
final_fen = b.fen()
run_case("c7_600_ply_game", base + [(0.02, "position startpos moves " + " ".join(moves)),
                                    (0.3, "isready"), (0.05, "go depth 6"), (2.0, "quit")],
         check_pos=final_fen)
run_case("c8_go_infinite_stop", base + [(0.05, "position startpos"), (0.05, "go infinite"),
                                        (1.0, "stop"), (0.5, "quit")], check_pos=SP)
run_case("c9_go_ponder_ponderhit", base + [(0.05, "position startpos"), (0.05, "go ponder"),
                                           (0.5, "ponderhit"), (1.0, "stop"), (0.5, "quit")],
         check_pos=SP)
run_case("c10_ucinewgame_during_search", base + [(0.05, "position startpos"), (0.05, "go depth 30"),
                                                 (0.5, "ucinewgame"), (0.3, "stop"), (0.8, "quit")],
         check_pos=SP)
run_case("c11_hash_between_searches", base + [(0.05, "position startpos"), (0.05, "go depth 6"),
                                              (1.2, "setoption name Hash value 64"), (0.3, "isready"),
                                              (0.05, "position startpos moves e2e4 e7e5"),
                                              (0.05, "go depth 6"), (1.5, "quit")],
         check_pos="rnbqkbnr/pppp1ppp/8/4p3/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 3")
run_case("c12_garbage_fen", base + [(0.05, "position fen " + "x" * 2000), (0.05, "isready"),
                                    (0.05, "go perft 2"), (0.5, "quit")])
print("done")
