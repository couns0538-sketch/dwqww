#!/usr/bin/env python3
"""S02 AREA 2 job 1 — RE-RUN with an interactive harness (job1 v2, after 19-F12).

WHY THIS FILE EXISTS: the first version of run_sequences.py wrote all of a sequence's lines to the engine's
stdin at once and then closed stdin. Per seat 19's finding 19-F12 (broadcast to every seat), this build then
answers a FABRICATED `bestmove` with no `info` lines: `printf 'position startpos\ngo depth 12\nquit\n'`
gives `bestmove a2a3` and zero info lines, where an uninterrupted search gives `e2e4` at 56,720 nodes.
I reproduced that on my own build (file ../harness_check/fabrication_quantified.txt: 0 info lines and
`bestmove a2a3` piped, 12 info lines and `bestmove e2e4` when the search is allowed to finish).
So every bestmove my first job-1 run recorded was measured through the fabrication path. Those numbers are
WITHDRAWN and re-measured here.

THE FIX: this runner is a real UCI driver. It sends one line, then reads the engine's stdout until the
answer that line must produce is complete — `bestmove` for a `go`, `readyok` for an `isready`, `uciok` for a
`uci` — and only then sends the next line. stdin is never closed while a search is running; the closing
`quit` is sent only after the last answer arrived.

usage: run_sequences_v2.py <exe> <seqs.jsonl> <outdir> [workers]
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

TIMEOUT_S = 25.0
SAN_RE = re.compile(r"ERROR: AddressSanitizer|runtime error:|ERROR: LeakSanitizer|"
                    r"SUMMARY: (AddressSanitizer|UndefinedBehaviorSanitizer)")
BESTMOVE_RE = re.compile(r"^bestmove\s+(\S+)(?:\s+ponder\s+(\S+))?\s*$")


class Engine:
    """One engine process, driven strictly question/answer."""

    def __init__(self, exe):
        env = {k: v for k, v in os.environ.items()
               if k not in ("ASAN_OPTIONS", "UBSAN_OPTIONS", "TSAN_OPTIONS")}
        self.proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.STDOUT, text=True, bufsize=1, env=env,
                                     start_new_session=True)
        self.lines = []
        self.lock = threading.Lock()
        self.closed = False
        self.reader = threading.Thread(target=self._read, daemon=True)
        self.reader.start()

    def _read(self):
        for line in self.proc.stdout:
            with self.lock:
                self.lines.append(line.rstrip("\n"))
        with self.lock:
            self.closed = True

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

    def wait_for(self, prefixes, start, timeout=TIMEOUT_S):
        """Wait for a line starting with any of `prefixes` at index >= start. Returns (index or -1)."""
        if isinstance(prefixes, str):
            prefixes = (prefixes,)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            with self.lock:
                for i in range(start, len(self.lines)):
                    if any(self.lines[i].startswith(p) for p in prefixes):
                        return i
                eof = self.closed
            if eof or self.proc.poll() is not None:
                with self.lock:
                    for i in range(start, len(self.lines)):
                        if any(self.lines[i].startswith(p) for p in prefixes):
                            return i
                return -1
            time.sleep(0.001)
        return -1

    def kill(self):
        try:
            os.killpg(self.proc.pid, signal.SIGKILL)
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except Exception:
            pass

    def close(self):
        self.send("quit")
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.kill()


def board_after(lines, upto):
    """The board python-chess believes after lines[0..upto]. Mirrors the engine's own rules:
    a refused FEN leaves the previous board AND ignores that line's moves (invalid FEN -> whole line dropped);
    `ucinewgame` resets to the start position; an illegal move keeps the legal prefix."""
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
            fen = " ".join(parts[2:cut])
            try:
                cand = chess.Board(fen)
                ok = cand.is_valid()
            except Exception:
                ok = False
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


def _judge_go(out, eng, lines, i, line):
    """Count, record and judge the bestmove that answered the `go` at lines[i]."""
    parts = line.split()
    with eng.lock:
        # the bestmove is the newest one in the buffer
        at = max(idx for idx, l in enumerate(eng.lines) if l.startswith("bestmove"))
        bm_line = eng.lines[at]
    out["n_bestmove"] += 1
    m = BESTMOVE_RE.match(bm_line)
    bm = m.group(1) if m else "?"
    board = board_after(lines, i)
    legal = {mv.uci() for mv in board.legal_moves}
    has_sm = "searchmoves" in parts
    if bm == "0000" and legal:
        if has_sm:
            out["zero_with_searchmoves"] += 1
        else:
            out["zero_no_searchmoves"] += 1
            out["illegal_bestmoves"].append({"i": i, "bestmove": bm, "fen": board.fen(),
                                             "go": line, "kind": "0000 on a board with legal moves"})
    elif bm != "0000" and bm not in legal:
        out["illegal_bestmoves"].append({"i": i, "bestmove": bm, "fen": board.fen(), "go": line,
                                         "legal_sample": sorted(legal)[:12],
                                         "kind": "move not legal in the engine's board"})
    out["bestmoves"].append({"i": i, "bestmove": bm, "go": line})
    out["steps"].append({"i": i, "line": line, "answer": bm_line})
    return bm_line


def run_one(exe, rec):
    sid, lines = rec["id"], rec["lines"]
    out = {"id": sid, "steps": [], "crashed": False, "hung": False, "sanitizer_lines": 0,
           "sanitizer_first": [], "illegal_bestmoves": [], "readyok_missing": 0, "uciok_missing": 0,
           "zero_no_searchmoves": 0, "zero_with_searchmoves": 0, "bestmoves": [], "n_go": 0,
           "outstanding_go": None, "go_without_info_depth": 0,
           "n_bestmove": 0, "go_without_bestmove": 0, "timeouts": []}
    eng = Engine(exe)
    t0 = time.monotonic()
    try:
        for i, line in enumerate(lines):
            parts = line.split()
            cmd = parts[0] if parts else ""
            start = eng.mark()
            if not eng.send(line):
                out["crashed"] = True
                out["steps"].append({"i": i, "line": line, "result": "process already gone"})
                break
            if cmd == "uci":
                at = eng.wait_for("uciok", start)
                if at < 0:
                    out["uciok_missing"] += 1
                    out["timeouts"].append({"i": i, "line": line, "waiting_for": "uciok"})
                out["steps"].append({"i": i, "line": line, "answer": "uciok" if at >= 0 else "NONE"})
            elif cmd == "isready":
                at = eng.wait_for("readyok", start)
                if at < 0:
                    out["readyok_missing"] += 1
                    out["timeouts"].append({"i": i, "line": line, "waiting_for": "readyok"})
                out["steps"].append({"i": i, "line": line, "answer": "readyok" if at >= 0 else "NONE"})
            elif cmd == "go":
                out["n_go"] += 1
                # A `go infinite` (or `go ponder`) owes no bestmove until a `stop`/`ponderhit` arrives, so it
                # must NOT be waited on here: doing so is a harness hang, not an engine fault. Record it as
                # outstanding and let the sequence's own `stop` collect the answer.
                if parts.count("infinite") or parts.count("ponder"):
                    out["outstanding_go"] = {"i": i, "line": line, "start": start}
                    out["steps"].append({"i": i, "line": line,
                                         "answer": "(no answer owed: unbounded search)"})
                    continue
                at = eng.wait_for("bestmove", start)
                if at < 0:
                    out["go_without_bestmove"] += 1
                    out["timeouts"].append({"i": i, "line": line, "waiting_for": "bestmove"})
                    out["steps"].append({"i": i, "line": line, "answer": "NONE"})
                    continue
                _judge_go(out, eng, lines, i, line)
            elif cmd in ("stop", "ponderhit", "ucinewgame", "setoption", "position", ""):
                og = out.get("outstanding_go")
                if og is not None and cmd in ("stop", "ponderhit", "ucinewgame"):
                    at = eng.wait_for("bestmove", og["start"])
                    if at < 0:
                        out["go_without_bestmove"] += 1
                        out["timeouts"].append({"i": og["i"], "line": og["line"],
                                                "waiting_for": "bestmove after %s" % cmd})
                    else:
                        _judge_go(out, eng, lines, og["i"], og["line"])
                    out.pop("outstanding_go", None)
                time.sleep(0.004)
                out["steps"].append({"i": i, "line": line, "answer": "(no answer owed)"})
            else:
                time.sleep(0.002)
                out["steps"].append({"i": i, "line": line, "answer": "(unknown command)"})
        eng.close()
        rc = eng.proc.returncode
        if rc is not None and rc < 0:
            out["crashed"] = True
            out["exit_signal"] = -rc
        elif rc not in (0, None):
            out["crashed"] = True
            out["exit_code"] = rc
    finally:
        if eng.proc.poll() is None:
            eng.kill()
            out["hung"] = True
        with eng.lock:
            text = list(eng.lines)
        san = [l for l in text if SAN_RE.search(l)]
        out["sanitizer_lines"] = len(san)
        out["sanitizer_first"] = san[:2]
        out["output_lines"] = len(text)
        # 19-F12 detector: a fabricated bestmove comes with no `info depth` line at all for that search.
        # Counted per sequence: bestmoves whose search produced no info line before them is measured below.
        out["info_depth_lines"] = sum(1 for l in text if l.startswith("info depth"))
        out["wall_s"] = round(time.monotonic() - t0, 3)
        # a sequence that got bestmoves but produced no `info depth` line at all is the fabrication signature
        out["fabrication_suspected"] = bool(out["n_bestmove"] and out["info_depth_lines"] == 0)
        bad = (out["crashed"] or out["hung"] or san or out["illegal_bestmoves"] or out["fabrication_suspected"]
               or out["readyok_missing"] or out["uciok_missing"] or out["zero_no_searchmoves"]
               or out["go_without_bestmove"])
        out["bad"] = bool(bad)
        if bad:
            d = os.path.join(OUTDIR, "bad")
            os.makedirs(d, exist_ok=True)
            with open(os.path.join(d, "seq%04d.txt" % sid), "w") as fh:
                fh.write("# lines sent (one at a time, each answered before the next)\n")
                for l in lines:
                    fh.write(repr(l) + "\n")
                fh.write("# verdict %s\n" % json.dumps(
                    {k: out[k] for k in ("crashed", "hung", "sanitizer_lines", "illegal_bestmoves",
                                         "readyok_missing", "uciok_missing", "go_without_bestmove")}))
                fh.write("# engine output\n")
                for l in text:
                    fh.write(l + "\n")
    return out


OUTDIR = "."


def main():
    global OUTDIR
    exe, seqs_path, outdir = sys.argv[1], sys.argv[2], sys.argv[3]
    workers = int(sys.argv[4]) if len(sys.argv) > 4 else 4
    OUTDIR = outdir
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
        fh.write("driver interactive: one line sent, its answer read to completion, then the next line\n")
        fh.write("stdin is closed only after the last answer; timeout per answer %s s\n" % TIMEOUT_S)
        fh.write("started_utc %s\n" % time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()))
        fh.write("options sent: whatever seqs.jsonl holds for each sequence, one line at a time\n")
        for line in idout.splitlines():
            if line.startswith("id name"):
                fh.write("id answer: %s\n" % line)
    results = []
    with ThreadPoolExecutor(max_workers=workers) as pool:
        for r in pool.map(lambda rec: run_one(exe, rec), recs):
            results.append(r)
    with open(os.path.join(outdir, "results.jsonl"), "w") as fh:
        for r in results:
            fh.write(json.dumps(r) + "\n")
    print("done %d sequences" % len(results))


if __name__ == "__main__":
    main()
