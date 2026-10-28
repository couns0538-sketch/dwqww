#!/usr/bin/env python3
"""Fault-injecting UCI proxy for the self-test of opus_selfplay_check.py (selftest_faults.py).

usage: fault_proxy.py <engine exe> <fault> [k]

Forwards every line between the harness and a real engine and breaks the protocol once, at the k-th event of
the fault's kind in this process (default k = 10), so the self-test can show the harness reports it:
  none               forward only (control: must give 0 errors)
  illegal_bestmove   k-th bestmove -> "bestmove a1a1"
  illegal_ponder     first bestmove with a ponder move from the k-th on -> ponder move a1a1
  double_bestmove    k-th bestmove printed twice
  late_double        k-th bestmove printed again 30 ms later (a racing second sender)
  unsolicited        "bestmove e2e4" right after the k-th position command (engine idle)
  early_infinite     first "go infinite" from the k-th go on is sent as "go depth 1" (answers before stop)
  hang               k-th bestmove never delivered
  crash              at the k-th go the proxy kills the engine and exits with status 5
  exit_code          exit status 3 at quit
  bad_info           a malformed "info depth x" line after the k-th go
  illegal_pv         " a1a1" appended to the pv of the first info line after the k-th go
  illegal_currmove   "info currmove a1a1" after the k-th go
  stderr             a line on stderr at the k-th go
  no_readyok         the k-th isready is not forwarded (no readyok)
  error_string       "info string ERROR simulated failure" at the k-th go
  option_missing     "option name CuckooRep ..." removed from the uci answer
  reject_move        "info string illegal move e2e4" after the k-th position command
  late_info          an "info depth 1 ..." line right after the k-th bestmove
"""
import os
import subprocess
import sys
import threading


def main():
    exe, fault = sys.argv[1], sys.argv[2]
    k = int(sys.argv[3]) if len(sys.argv) > 3 else 10
    eng = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE, bufsize=0)
    lock = threading.Lock()
    st = dict(bestmoves=0, gos=0, positions=0, isready=0, fired=False)

    def emit(line):
        with lock:
            sys.stdout.buffer.write((line + "\n").encode())
            sys.stdout.buffer.flush()

    def fire():
        if st["fired"]:
            return False
        st["fired"] = True
        return True

    def from_engine():
        for raw in iter(eng.stdout.readline, b""):
            line = raw.decode("utf-8", "replace").rstrip("\r\n")
            if fault == "option_missing" and line.startswith("option name CuckooRep "):
                continue
            if line.startswith("info") and not line.startswith("info string") and st["gos"] >= k:
                if fault == "bad_info" and fire():
                    emit("info depth x nodes 5")
                elif fault == "illegal_pv" and " pv " in line and fire():
                    line += " a1a1"
                elif fault == "illegal_currmove" and fire():
                    emit("info currmove a1a1 currmovenumber 1")
            if line.startswith("bestmove"):
                st["bestmoves"] += 1
                n = st["bestmoves"]
                if fault == "illegal_bestmove" and n == k:
                    line = "bestmove a1a1"
                elif fault == "illegal_ponder" and n >= k and " ponder " in line and fire():
                    line = line.split(" ponder ")[0] + " ponder a1a1"
                elif fault == "hang" and n == k:
                    continue
                elif fault == "double_bestmove" and n == k:
                    emit(line)
                elif fault == "late_double" and n == k:
                    threading.Timer(0.03, emit, [line]).start()
                elif fault == "late_info" and n == k:
                    emit(line)
                    line = "info depth 1 seldepth 1 score cp 0 nodes 1 nps 1 hashfull 0 time 0 pv"
            emit(line)

    threading.Thread(target=from_engine, daemon=True).start()
    for raw in iter(sys.stdin.buffer.readline, b""):
        line = raw.decode("utf-8", "replace").rstrip("\r\n")
        words = line.split()
        cmd = words[0] if words else ""
        if cmd == "go":
            st["gos"] += 1
            if st["gos"] == k:
                if fault == "crash":
                    eng.kill()
                    os._exit(5)
                if fault == "error_string":
                    emit("info string ERROR simulated failure")
                if fault == "stderr":
                    sys.stderr.write("simulated diagnostic on stderr\n")
                    sys.stderr.flush()
            if fault == "early_infinite" and st["gos"] >= k and "infinite" in words and fire():
                line = "go depth 1"
        elif cmd == "position":
            st["positions"] += 1
            if st["positions"] == k and fault in ("unsolicited", "reject_move"):
                eng.stdin.write((line + "\n").encode())
                eng.stdin.flush()
                emit("bestmove e2e4" if fault == "unsolicited" else "info string illegal move e2e4")
                continue
        elif cmd == "isready":
            st["isready"] += 1
            if fault == "no_readyok" and st["isready"] == k:
                continue
        try:
            eng.stdin.write((line + "\n").encode())
            eng.stdin.flush()
        except OSError:
            break
        if cmd == "quit":
            code = eng.wait()
            sys.stdout.flush()
            os._exit(3 if fault == "exit_code" else code)
    eng.kill()
    os._exit(0)


if __name__ == "__main__":
    main()
