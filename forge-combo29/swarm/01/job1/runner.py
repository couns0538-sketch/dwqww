#!/usr/bin/env python3
"""swarm seat 01, job 1 runner: FEN input under ASan+UBSan.

For every mutated FEN in mutants.tsv:
    position fen <FEN>
    isready                      -> read every line up to readyok, record them
    go depth 2                   -> read every line up to bestmove, record them
One engine process per 500 FENs. A process that dies (crash) is counted and restarted;
its unfinished FEN is recorded as crash at that index.

Usage: runner.py <exe> <mutants.tsv> <outdir> [--chunk 500]
Writes outdir/results.jsonl (one record per FEN), outdir/chunks.txt, outdir/raw/*.log
Writes outdir/meta.txt: exe path it STARTED, sha256, id name, every option line sent,
and the nm -C sanitizer symbol counts.

Refusal detection: the engine answers a refused FEN with a line starting
"info string invalid FEN" (see src/uci.cpp apply_position).
"""
import hashlib
import json
import os
import select
import signal
import subprocess
import sys
import time
from pathlib import Path

import chess

FEN_TIMEOUT = 20.0
CHUNK = 500


def nm_count(exe, sym):
    try:
        out = subprocess.run(["nm", "-C", exe], capture_output=True, text=True, timeout=120).stdout
    except Exception:
        return -1
    return sum(1 for line in out.splitlines() if sym in line)


class LineReader:
    """Raw-fd line reader: os.read + own buffer, so select() never lies about pending lines."""

    def __init__(self, fd):
        self.fd = fd
        self.buf = b""
        self.eof = False

    def readline(self, deadline):
        while b"\n" not in self.buf:
            if self.eof:
                return None
            remain = deadline - time.monotonic()
            if remain <= 0:
                return None
            r, _, _ = select.select([self.fd], [], [], remain)
            if not r:
                return None
            try:
                chunk = os.read(self.fd, 65536)
            except OSError:
                chunk = b""
            if not chunk:
                self.eof = True
                return None
            self.buf += chunk
        line, _, self.buf = self.buf.partition(b"\n")
        return line.decode("utf-8", "replace")


def send(proc, line):
    proc.stdin.write((line + "\n").encode())
    proc.stdin.flush()


def read_until(reader, want_prefixes, deadline, lines):
    """Read lines until any of want_prefixes is seen. Returns the matched line or None."""
    while True:
        line = reader.readline(deadline)
        if line is None:
            return None
        lines.append(line)
        for p in want_prefixes:
            if line.startswith(p):
                return line


class Engine:
    def __init__(self, exe):
        self.exe = exe
        self.proc = None
        self.start()

    def start(self):
        self.proc = subprocess.Popen(
            [self.exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, text=False, bufsize=0, cwd="/tmp")
        self.reader = LineReader(self.proc.stdout.fileno())

    def alive(self):
        return self.proc is not None and self.proc.poll() is None

    def kill(self):
        if self.proc is not None and self.proc.poll() is None:
            try:
                self.proc.kill()
            except Exception:
                pass
        if self.proc is not None:
            try:
                self.proc.wait(timeout=20)
            except Exception:
                pass


def check_fen(exe, fens):
    """Return (records, crashed_at_index or None, chunk_log_lines)."""
    eng = Engine(exe)
    records = []
    log = []
    log.append("PID %d started for chunk of %d" % (eng.proc.pid, len(fens)))
    for i, fen in enumerate(fens):
        lines = []
        send(eng.proc, "position fen " + fen)
        send(eng.proc, "isready")
        deadline = time.monotonic() + FEN_TIMEOUT
        ready = read_until(eng.reader, ("readyok",), deadline, lines)
        if ready is None:
            log.append("index %d: no readyok (dead/deadline)" % i)
            log.extend("RAW: " + l for l in lines)
            eng.kill()
            return records, i, log
        refusal = [l for l in lines if l.startswith("info string invalid FEN")]
        refused = bool(refusal)
        answer = [l for l in lines if not l.startswith("info string invalid FEN")]
        send(eng.proc, "go depth 2")
        deadline = time.monotonic() + FEN_TIMEOUT
        bm_line = read_until(eng.reader, ("bestmove",), deadline, lines)
        if bm_line is None:
            log.append("index %d: no bestmove (dead/deadline)" % i)
            log.extend("RAW: " + l for l in lines)
            eng.kill()
            return records, i, log
        bestmove = bm_line.split()[1] if len(bm_line.split()) > 1 else ""
        search_lines = [l for l in lines if l.startswith("info ") and "invalid FEN" not in l]
        rec = {
            "i": i,
            "fen": fen,
            "refused": refused,
            "refusal_line": refusal[0] if refusal else "",
            "answer_position": answer,
            "bestmove": bestmove,
            "search_infos": search_lines[-3:],
            "sanitizer": [l for l in lines if ("AddressSanitizer" in l or "runtime error" in l
                                               or "SUMMARY:" in l or "UndefinedBehaviorSanitizer" in l)],
        }
        records.append(rec)
    eng.kill()
    log.append("chunk finished clean, %d records" % len(records))
    return records, None, log


def main():
    exe = sys.argv[1]
    mutants = sys.argv[2]
    outdir = Path(sys.argv[3])
    chunk = CHUNK
    if "--chunk" in sys.argv:
        chunk = int(sys.argv[sys.argv.index("--chunk") + 1])
    raw = outdir / "raw"
    raw.mkdir(parents=True, exist_ok=True)

    rows = []
    with open(mutants) as fh:
        header = fh.readline()
        for line in fh:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 5:
                continue
            rows.append(parts)

    sha = hashlib.sha256(Path(exe).read_bytes()).hexdigest()
    idprobe = subprocess.run([exe], input="uci\nquit\n", capture_output=True, text=True, timeout=120)
    idname = [l for l in idprobe.stdout.splitlines() if l.startswith("id name")]
    meta = [
        "exe_started: %s" % exe,
        "sha256: %s" % sha,
        "id name line: %s" % (idname[0] if idname else "MISSING"),
        "nm -C grep -c __asan_ : %d" % nm_count(exe, "__asan_"),
        "nm -C grep -c __ubsan_ : %d" % nm_count(exe, "__ubsan_"),
        "option lines sent: NONE (no setoption in this job)",
        "position lines sent: 'position fen <mutated fen>' then 'isready' then 'go depth 2'",
        "chunk size: %d" % chunk,
        "fen timeout seconds: %g" % FEN_TIMEOUT,
        "uci and quit sent once before the run for the id probe only",
    ]
    (outdir / "meta.txt").write_text("\n".join(meta) + "\n")

    all_records = []
    crashes = []
    chunk_lines = []
    for start in range(0, len(rows), chunk):
        block = rows[start:start + chunk]
        fens = [r[4] for r in block]
        recs, crashed_at, log = check_fen(exe, fens)
        logname = raw / ("chunk_%05d.log" % start)
        logname.write_text("\n".join(log) + "\n")
        chunk_lines.append("chunk start %d size %d records %d crashed_at %s"
                           % (start, len(block), len(recs), crashed_at))
        for j, rec in enumerate(recs):
            idx = start + j
            rec["i"] = idx
            rec["base_set"] = block[j][1]
            rec["mutation_kind"] = block[j][2]
            rec["mutation_detail"] = block[j][3]
            all_records.append(rec)
        if crashed_at is not None:
            j = len(recs)
            san = [l for l in log if ("AddressSanitizer" in l or "runtime error" in l
                                      or "SUMMARY:" in l or "UndefinedBehaviorSanitizer" in l)]
            crashes.append({"chunk_start": start, "index_in_chunk": crashed_at, "idx": start + j,
                            "chunk_log": str(logname), "sanitizer_lines_in_log": san})
            all_records.append({"i": start + j, "fen": block[j][4], "crash": True,
                                "base_set": block[j][1], "mutation_kind": block[j][2],
                                "mutation_detail": block[j][3]})
            print("CRASH at chunk %d index %d; restarting" % (start, crashed_at), flush=True)
        print("done chunks up to %d" % (start + len(block)), flush=True)

    with open(outdir / "results.jsonl", "w") as fh:
        for rec in all_records:
            fh.write(json.dumps(rec) + "\n")
    (outdir / "chunks.txt").write_text("\n".join(chunk_lines) + "\n")
    (outdir / "crashes.json").write_text(json.dumps(crashes, indent=1) + "\n")
    print("records %d crashes %d" % (len(all_records), len(crashes)))


if __name__ == "__main__":
    main()
