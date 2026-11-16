#!/usr/bin/env python3
"""go_stop_cycle.py EXE OUTDIR [ROUNDS]

The normal-play shape a GUI produces: `position ...`, `go infinite`, wait, `stop`,
`bestmove`, then the GUI plays the move and sends the next `position` + `go`.
This program does that for ROUNDS plies and asserts, per round:

  * a bestmove arrives within the timeout (a hang is a failure, recorded and the run stops);
  * the bestmove is legal in the position that was sent (python-chess), or is 0000 exactly when
    the position has no legal move;
  * after `stop`, the very next `go` still searches (a stale stop flag would make it
    answer instantly with 0 nodes, which is recorded rather than silently accepted).

It also interleaves one `go ponder` + `ponderhit` round and one `go depth 200` + `stop` round,
because those take different branches of uci.cpp's stop/quit handling.

Every failure is printed with the round number and the raw lines involved.
"""
import os
import queue
import re
import subprocess
import sys
import threading
import time

import chess


class Reader:
    def __init__(self, stream):
        self.q = queue.Queue()
        threading.Thread(target=self._pump, args=(stream,), daemon=True).start()

    def _pump(self, s):
        for line in s:
            self.q.put(line)
        self.q.put(None)

    def get(self, timeout):
        try:
            return self.q.get(timeout=timeout)
        except queue.Empty:
            return None


def main():
    exe, outdir = sys.argv[1], sys.argv[2]
    rounds = int(sys.argv[3]) if len(sys.argv) > 3 else 40
    os.makedirs(outdir, exist_ok=True)
    log = open(os.path.join(outdir, "transcript.txt"), "w", encoding="utf-8")

    proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE, text=True, bufsize=1)
    r = Reader(proc.stdout)
    failures = []

    def send(c):
        proc.stdin.write(c + "\n")
        proc.stdin.flush()
        log.write(">> " + c + "\n")
        log.flush()

    def drain(tag, timeout=120):
        deadline = time.monotonic() + timeout
        while True:
            line = r.get(max(0.01, deadline - time.monotonic()))
            if line is None:
                failures.append(f"{tag}: no readyok")
                return False
            log.write("<< " + line)
            if line.strip() == "readyok":
                return True

    def wait_bestmove(tag, timeout=60):
        deadline = time.monotonic() + timeout
        nodes = None
        while True:
            line = r.get(max(0.01, deadline - time.monotonic()))
            if line is None:
                failures.append(f"{tag}: NO bestmove within {timeout}s (hang)")
                return None, nodes
            log.write("<< " + line)
            if line.startswith("info depth") and " nodes " in line:
                m = re.search(r" nodes (\d+) ", line)
                if m:
                    nodes = int(m.group(1))
            if line.startswith("bestmove"):
                return line.split()[1], nodes

    send("uci")
    while True:
        line = r.get(30)
        if line is None or line.strip() == "uciok":
            break
        log.write("<< " + line)
    send("setoption name Hash value 16")
    send("isready")
    drain("setoption Hash")

    board = chess.Board()
    history = []
    for round_no in range(1, rounds + 1):
        fen = board.fen()
        send("position fen " + fen)
        send("isready")
        if not drain(f"round {round_no} position"):
            break
        # Round types: mostly infinite+stop (the normal GUI shape), one ponderhit, one deep+stop.
        if round_no == rounds // 2:
            send("go ponder depth 8")
            time.sleep(0.25)
            send("ponderhit")
            best, nodes = wait_bestmove(f"round {round_no} ponderhit", 60)
        elif round_no == rounds - 1:
            send("go depth 200")
            time.sleep(0.20)
            send("stop")
            best, nodes = wait_bestmove(f"round {round_no} deep+stop", 60)
        else:
            send("go infinite")
            time.sleep(0.10)
            send("stop")
            best, nodes = wait_bestmove(f"round {round_no} infinite+stop", 60)

        if best is None:
            break
        legal = [m.uci() for m in board.legal_moves]
        if best == "0000":
            if legal:
                failures.append(f"round {round_no}: bestmove 0000 but {len(legal)} legal moves in {fen}")
                break
        elif best not in legal:
            failures.append(f"round {round_no}: ILLEGAL bestmove {best} in {fen} (legal: {len(legal)})")
            break
        if nodes is None:
            # A missing nodes figure is NOT a pass (seat 19's rule): it means no depth line was
            # parsed, so this round measured nothing about whether the search really ran.
            failures.append(f"round {round_no}: no 'info depth ... nodes' line was parsed, so the "
                            f"round measured nothing (bestmove {best})")
            break
        if nodes == 0:
            failures.append(f"round {round_no}: search answered 0 nodes after a stop/ponderhit "
                            f"(stale stop flag?) bestmove {best}")
            break
        if round_no % 7 == 0:
            send("ucinewgame")
            send("isready")
            drain(f"round {round_no} ucinewgame")
        board.push(chess.Move.from_uci(best))
        history.append(best)

    # Final sanity: one plain search must still work after all that.
    send("position startpos")
    send("isready")
    drain("final position")
    send("go depth 6")
    final_best, final_nodes = wait_bestmove("final go depth 6", 60)
    send("quit")
    try:
        proc.wait(timeout=30)
    except subprocess.TimeoutExpired:
        proc.kill()
    log.close()

    print(f"rounds requested {rounds}, plies played {len(history)}")
    print(f"final search after the cycle: bestmove {final_best} nodes {final_nodes}")
    if final_nodes is None:
        failures.append("final go depth 6 produced no nodes line: the engine never searched")
    elif final_nodes == 0:
        failures.append("final go depth 6 produced 0 nodes: the engine never searched")
    for f in failures:
        print("  FAIL " + f)
    if failures:
        print(f"RESULT: {len(failures)} failure(s)")
        sys.exit(1)
    if len(history) < rounds - 2:
        print("RESULT: the cycle did not complete; see failures above")
        sys.exit(1)
    print("RESULT: every go/stop and go/ponderhit cycle returned a legal move with nodes > 0, "
          "and a plain search still worked afterwards")


if __name__ == "__main__":
    main()
