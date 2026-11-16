#!/usr/bin/env python3
"""S02 AREA 2 job 1 — v3 driver (job 1's third and final harness; v1 withdrawn as invalid, v2 discarded).

Why v3 exists, in order:
  v1 wrote a whole sequence to stdin and closed it -> every bestmove came from the fabricated-bestmove path
     (seat 19's 19-F12; reproduced in ../harness_check/fabrication_quantified.txt). WITHDRAWN.
  v2 read each answer to completion, but left unbounded searches (`go`, `go infinite`, `go ponder ...`)
     to be collected by whatever `stop`/`ponderhit` the random sequence happened to contain. When the
     sequence contained none, the driver waited 25 s and recorded a "missing bestmove" that was really
     my harness's fault, not the engine's.

v3 rule, which removes that whole class: THE DRIVER OWNS SEARCH LENGTH. For any `go` that is unbounded
(bare `go`, `go infinite`, `go ponder`, or a ponder search with a depth/nodes limit, since a ponder search
does not answer until it is told to), the driver sends `stop` itself after 30 ms and then reads the
`bestmove`. Every search in every run therefore terminates because the driver said so, and a missing
`bestmove` is a genuine engine fault rather than a driver one.

Also recorded per search, and required: the number of `info depth` lines seen before that `bestmove`.
A fabricated bestmove (19-F12) has none. But 0 info lines is NOT proof: `go nodes 10` genuinely produces
none (budget exhausted before depth 1). So they are counted as `no_info_bestmoves`, never treated as a fault.

usage: run_sequences_v3.py <exe> <seqs.jsonl> <outdir> [workers]
"""
import json
import os
import re
import signal
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import chess

ANSWER_TIMEOUT = 20.0
STOP_AFTER_MS = 30
SAN_RE = re.compile(r"ERROR: AddressSanitizer|runtime error:|ERROR: LeakSanitizer|"
                    r"SUMMARY: (AddressSanitizer|UndefinedBehaviorSanitizer)")
BESTMOVE_RE = re.compile(r"^bestmove\s+(\S+)")


LIMIT_KEYWORDS = ("depth", "nodes", "movetime", "mate", "wtime", "btime", "movestogo")


def is_unbounded(parts, side_white):
    """True when the engine will not answer this `go` until it is stopped.

    Three separate reasons, each measured rather than assumed:
    1. a limit keyword must be followed by a parseable number: `go nodes` with the number missing bounds
       nothing (the engine leaves nodes_specified false);
    2. `go infinite` / `go ponder` never answer until told to;
    3. a CLOCK is only a limit for the side it belongs to. src/uci.cpp:118-121 reads `wtime` into
       limits.time_ms only when side == White and `btime` only when side == Black. So `go wtime 100` with
       BLACK to move leaves limits.time_ms at its unset value and the search runs until stopped — measured
       on both sides in ../finding_clock/repro.txt (wtime-only for White: answers; btime-only for White:
       runs until stopped; and the mirror images likewise). Nine of the first 2,000 sequences hit exactly
       this and were false "missing bestmove" flags until this was fixed."""
    if len(parts) < 2:
        return True
    if "infinite" in parts or "ponder" in parts:
        return True
    bounded = False
    clock_seen = False
    for idx, tok in enumerate(parts):
        if tok in ("depth", "nodes", "movetime", "mate", "movestogo"):
            if idx + 1 < len(parts):
                try:
                    int(parts[idx + 1])
                    bounded = True
                except ValueError:
                    pass
        elif tok in ("wtime", "btime", "winc", "binc"):
            clock_seen = True
            mine = (tok.startswith("w") and side_white) or (tok.startswith("b") and not side_white)
            if mine and idx + 1 < len(parts):
                try:
                    int(parts[idx + 1])
                    bounded = True
                except ValueError:
                    pass
    if clock_seen and not bounded:
        return True      # only the opponent's clock was given: no limit for the side to move
    return not bounded


class Engine:
    def __init__(self, exe):
        env = {k: v for k, v in os.environ.items()
               if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
        self.proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1, env=env,
                                     start_new_session=True)
        self.lines, self.lock, self.eof = [], threading.Lock(), False
        threading.Thread(target=self._read, daemon=True).start()

    def _read(self):
        for line in self.proc.stdout:
            with self.lock:
                self.lines.append(line.rstrip("\n"))
        with self.lock:
            self.eof = True

    def send(self, text):
        if self.proc.poll() is not None:
            return False
        try:
            self.proc.stdin.write(text + "\n")
            self.proc.stdin.flush()
            return True
        except Exception:
            return False

    def mark(self):
        with self.lock:
            return len(self.lines)

    def wait_for(self, prefix, start, timeout=ANSWER_TIMEOUT):
        deadline = time.monotonic() + timeout
        while True:
            with self.lock:
                for i in range(start, len(self.lines)):
                    if self.lines[i].startswith(prefix):
                        return i
                eof = self.eof
            if eof or self.proc.poll() is not None or time.monotonic() > deadline:
                with self.lock:
                    for i in range(start, len(self.lines)):
                        if self.lines[i].startswith(prefix):
                            return i
                return -1
            time.sleep(0.001)

    def kill(self):
        try:
            os.killpg(self.proc.pid, signal.SIGKILL)
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            pass


def board_after(lines, upto):
    """python-chess's view of the board after lines[0..upto], following the engine's own rules:
    a refused FEN drops the whole line (moves too); `ucinewgame` resets to startpos; an illegal move
    keeps the legal prefix."""
    board = chess.Board()
    for line in lines[:upto + 1]:
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "ucinewgame":
            board = chess.Board()
            continue
        if parts[0] != "position":
            continue
        new_board, mv_start, refused = board, None, False
        if len(parts) >= 2 and parts[1] == "startpos":
            new_board, mv_start = chess.Board(), 2
        elif len(parts) >= 3 and parts[1] == "fen":
            try:
                cut = parts.index("moves")
            except ValueError:
                cut = len(parts)
            try:
                cand = chess.Board(" ".join(parts[2:cut]))
                ok = cand.is_valid()
            except Exception:
                cand, ok = None, False
            if ok:
                new_board = cand
                mv_start = cut + 1 if cut < len(parts) else None
            else:
                refused = True
        if refused:
            continue
        if mv_start is not None and len(parts) > mv_start and parts[mv_start] == "moves":
            mv_start += 1
        if mv_start is not None:
            b = new_board.copy()
            for tok in parts[mv_start:]:
                try:
                    mv = chess.Move.from_uci(tok)
                except Exception:
                    break
                if mv not in b.legal_moves:
                    break
                b.push(mv)
            new_board = b
        board = new_board
    return board


def run_one(exe, rec, outdir):
    sid, lines = rec["id"], rec["lines"]
    o = {"id": sid, "crashed": False, "hung": False, "sanitizer_lines": 0, "sanitizer_first": [],
         "illegal": [], "bestmoves": [], "missing_bestmove": [], "readyok_missing": 0,
         "uciok_missing": 0, "zero_no_sm": 0, "zero_sm": 0, "n_go": 0, "n_bestmove": 0,
         "no_info_bestmoves": 0, "driver_stopped_go": 0, "info_depth_total": 0,
         "book_answers": 0, "steps": []}
    eng = Engine(exe)
    t0 = time.monotonic()
    try:
        if not eng.send("uci") or eng.wait_for("uciok", 0) < 0:
            o["uciok_missing"] += 1
        for i, line in enumerate(lines):
            parts = line.split()
            cmd = parts[0] if parts else ""
            start = eng.mark()
            if not eng.send(line):
                o["crashed"] = True
                o["steps"].append({"i": i, "line": line, "answer": "process gone"})
                break
            if cmd == "uci":
                if eng.wait_for("uciok", start) < 0:
                    o["uciok_missing"] += 1
                o["steps"].append({"i": i, "line": line, "answer": "uciok"})
            elif cmd == "isready":
                if eng.wait_for("readyok", start) < 0:
                    o["readyok_missing"] += 1
                o["steps"].append({"i": i, "line": line, "answer": "readyok"})
            elif cmd == "go":
                o["n_go"] += 1
                side_white = board_after(lines, i).turn
                if is_unbounded(parts, side_white):
                    time.sleep(STOP_AFTER_MS / 1000.0)
                    eng.send("stop")
                    o["driver_stopped_go"] += 1
                at = eng.wait_for("bestmove", start)
                if at < 0:
                    o["missing_bestmove"].append({"i": i, "go": line})
                    o["steps"].append({"i": i, "line": line, "answer": "NO BESTMOVE"})
                    continue
                o["n_bestmove"] += 1
                with eng.lock:
                    bm_line, seg = eng.lines[at], eng.lines[start:at]
                info = [l for l in seg if l.startswith("info depth")]
                book = [l for l in seg if "book move" in l]
                o["info_depth_total"] += len(info)
                if book:
                    o["book_answers"] += 1
                elif not info:
                    # A bestmove with no `info depth` line. This is the SIGNATURE of 19-F12's fabrication,
                    # but it is NOT proof of it: `go nodes 10` on startpos genuinely exhausts the node
                    # budget before depth 1 completes and prints `bestmove a2a3` with no info line
                    # (measured: nodes 10 -> 0 info lines, nodes 100 -> 2, nodes 1000 -> 4). So these are
                    # counted and listed, NOT called faults. The real discriminator for 19-F12 is an
                    # interruption by quit/EOF, which this driver never causes.
                    o["no_info_bestmoves"] += 1
                bm = (BESTMOVE_RE.match(bm_line) or [None, "?"])[1] if BESTMOVE_RE.match(bm_line) else "?"
                board = board_after(lines, i)
                legal = {m.uci() for m in board.legal_moves}
                if bm == "0000" and legal:
                    if "searchmoves" in parts:
                        o["zero_sm"] += 1
                    else:
                        o["zero_no_sm"] += 1
                        o["illegal"].append({"i": i, "bestmove": bm, "fen": board.fen(), "go": line,
                                             "kind": "0000 on a board with legal moves"})
                elif bm != "0000" and bm not in legal:
                    o["illegal"].append({"i": i, "bestmove": bm, "fen": board.fen(), "go": line,
                                         "legal_sample": sorted(legal)[:12],
                                         "kind": "move not legal in the engine's board"})
                o["bestmoves"].append({"i": i, "bestmove": bm, "go": line, "info_depth": len(info)})
                o["steps"].append({"i": i, "line": line, "answer": bm_line})
            else:
                time.sleep(0.002)
                o["steps"].append({"i": i, "line": line, "answer": "(none owed)"})
        eng.send("quit")
        try:
            eng.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            eng.kill()
            o["hung"] = True
        rc = eng.proc.returncode
        if rc is not None and rc < 0:
            o["crashed"] = True
            o["signal"] = -rc
        elif rc not in (0, None):
            o["crashed"] = True
            o["exit_code"] = rc
    finally:
        if eng.proc.poll() is None:
            eng.kill()
            o["hung"] = True
        with eng.lock:
            text = list(eng.lines)
        san = [l for l in text if SAN_RE.search(l)]
        o["sanitizer_lines"] = len(san)
        o["sanitizer_first"] = san[:2]
        o["output_lines"] = len(text)
        o["wall_s"] = round(time.monotonic() - t0, 3)
        o["bad"] = bool(o["crashed"] or o["hung"] or san or o["illegal"] or o["missing_bestmove"]
                        or o["readyok_missing"] or o["uciok_missing"] or o["zero_no_sm"])
        if o["bad"]:
            d = os.path.join(outdir, "bad")
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "seq%04d.txt" % sid), "w") as fh:
                fh.write("# lines (driver sends one, reads its answer, then the next)\n")
                for l in lines:
                    fh.write(repr(l) + "\n")
                fh.write("# verdict\n%s\n" % json.dumps(
                    {k: o[k] for k in ("crashed", "hung", "sanitizer_lines", "illegal", "missing_bestmove",
                                       "readyok_missing", "uciok_missing", "zero_no_sm",
                                       "no_info_bestmoves", "driver_stopped_go")}))
                fh.write("# engine output\n")
                for l in text:
                    fh.write(l + "\n")
    return o


def main():
    exe, seqs_path, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    os.makedirs(outdir, exist_ok=True)
    recs = [json.loads(l) for l in open(seqs_path)]
    env = {k: v for k, v in os.environ.items()
           if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
    idout = subprocess.run([exe], input="uci\nquit\n", capture_output=True, text=True, env=env).stdout
    with open(os.path.join(outdir, "meta.txt"), "w") as fh:
        fh.write("exe %s\n" % exe)
        fh.write("sha256 %s\n" % subprocess.run(["sha256sum", exe], capture_output=True,
                                               text=True).stdout.split()[0])
        fh.write("nm -C grep -c __asan_ %s\n" % subprocess.run(
            "nm -C %s | grep -c __asan_" % exe, shell=True, capture_output=True, text=True).stdout.strip())
        fh.write("nm -C grep -c __ubsan_ %s\n" % subprocess.run(
            "nm -C %s | grep -c __ubsan_" % exe, shell=True, capture_output=True, text=True).stdout.strip())
        fh.write("driver: v3 interactive; one line sent, its answer read to completion, then the next\n")
        fh.write("driver OWNS search length: unbounded or ponder `go` gets `stop` after %d ms\n" % STOP_AFTER_MS)
        fh.write("stdin closed only after the last answer; per-answer timeout %s s\n" % ANSWER_TIMEOUT)
        fh.write("detector: bestmoves with 0 preceding `info depth` lines are COUNTED (no_info_bestmoves), not faulted:\n"
                 "  `go nodes 10` legitimately gives 0 info lines and `bestmove a2a3`. 19-F12 needs an interruption.\n")
        fh.write("started_utc %s\n" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        for line in idout.splitlines():
            if line.startswith("id name"):
                fh.write("id answer: %s\n" % line)
    res = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for r in pool.map(lambda rec: run_one(exe, rec, outdir), recs):
            res.append(r)
    with open(os.path.join(outdir, "results.jsonl"), "w") as fh:
        for r in res:
            fh.write(json.dumps(r) + "\n")
    print("done %d sequences" % len(res))


if __name__ == "__main__":
    main()
