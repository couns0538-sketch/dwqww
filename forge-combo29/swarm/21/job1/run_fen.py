#!/usr/bin/env python3
"""run_fen.py EXE MUT_TSV OUTDIR LABEL

Drives the engine over every mutated FEN in MUT_TSV.
Per FEN: `position fen <FEN>` + `isready` (all answer lines up to readyok are kept),
then `go depth 2`, wait for bestmove (20 s limit -> HANG).
One engine process per 500 FENs; a dead process is a CRASH, counted, and the batch
continues with a fresh process at the next FEN.

Writes into OUTDIR:
  <LABEL>_results.tsv   one line per FEN: idx src kind desc fen pych_valid answer verdict bestmove legal
  <LABEL>_raw_<k>.txt   raw engine output of batch k
  <LABEL>_meta.txt      exe path, sha256, id name, options sent, ASan/UBSan symbol counts
  <LABEL>_stamps.txt    `date -u` after every 2500 FENs
"""
import hashlib
import os
import subprocess
import sys
import time
import datetime

import chess

BATCH = 500
GO_TIMEOUT = 20.0
BAD_MARKERS = ("unknown option", "invalid value", "invalid FEN", "illegal move")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


class Engine:
    def __init__(self, exe, raw_path):
        self.raw = open(raw_path, "w")
        env = dict(os.environ)
        env.pop("ASAN_OPTIONS", None)
        env.pop("UBSAN_OPTIONS", None)
        env.pop("TSAN_OPTIONS", None)
        self.p = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                  stderr=subprocess.STDOUT, text=True, bufsize=1, env=env)
        self.send("uci")
        self.until("uciok")
        self.opt_lines = []
        for name, val in (("Hash", "16"), ("Threads", "1")):
            self.send("setoption name %s value %s" % (name, val))
            self.opt_lines.append("setoption name %s value %s" % (name, val))
            self.send("isready")
            self.until("readyok")
        self.send("ucinewgame")
        self.send("isready")
        self.until("readyok")

    def send(self, line):
        self.raw.write(">>> " + line + "\n")
        self.raw.flush()
        self.p.stdin.write(line + "\n")
        self.p.stdin.flush()

    def readline(self, timeout):
        end = time.time() + timeout
        while True:
            if time.time() > end:
                return None
            line = self.p.stdout.readline()
            if line == "":
                return ""  # EOF: process died
            self.raw.write(line)
            self.raw.flush()
            return line.rstrip("\n")

    def until(self, token, timeout=GO_TIMEOUT):
        lines = []
        while True:
            line = self.readline(timeout)
            if line is None or line == "":
                return None, lines
            lines.append(line)
            if line.strip() == token or line.strip().startswith(token + " "):
                return True, lines

    def kill(self):
        try:
            self.p.kill()
        except Exception:
            pass
        try:
            self.p.wait(timeout=5)
        except Exception:
            pass
        self.raw.close()


def legal_moves(fen):
    try:
        b = chess.Board(fen)
    except Exception:
        return None
    return {m.uci() for m in b.legal_moves}


def main():
    exe, mut_tsv, outdir, label = sys.argv[1:5]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    with open(mut_tsv) as fh:
        for ln in fh:
            parts = ln.rstrip("\n").split("\t")
            if len(parts) >= 5:
                rows.append(parts)

    nm = subprocess.run("nm -C %s | grep -c __sanitizer || true" % exe, shell=True,
                        capture_output=True, text=True).stdout.strip()
    nm_asan = subprocess.run("nm -C %s | grep -c __asan_ || true" % exe, shell=True,
                             capture_output=True, text=True).stdout.strip()
    nm_ubsan = subprocess.run("nm -C %s | grep -c __ubsan_ || true" % exe, shell=True,
                              capture_output=True, text=True).stdout.strip()
    meta_path = os.path.join(outdir, label + "_meta.txt")
    stamps_path = os.path.join(outdir, label + "_stamps.txt")
    results_path = os.path.join(outdir, label + "_results.tsv")

    stats = dict(total=0, refused=0, accepted=0, acc_pyvalid=0, acc_pyinvalid=0,
                 crash=0, hang=0, san=0, illegal_best=0, badline=0)
    acc_pyinvalid_rows = []

    engine = None
    batch_idx = -1
    with open(results_path, "w") as res, open(stamps_path, "w") as stamps:
        def start_batch():
            nonlocal engine, batch_idx
            batch_idx += 1
            raw_path = os.path.join(outdir, "%s_raw_%03d.txt" % (label, batch_idx))
            engine = Engine(exe, raw_path)
            if batch_idx == 0:
                with open(meta_path, "w") as meta:
                    meta.write("exe: %s\n" % os.path.abspath(exe))
                    meta.write("sha256: %s\n" % sha256(exe))
                    idline = subprocess.run([exe], input="uci\nquit\n", text=True,
                                            capture_output=True).stdout
                    for ln in idline.splitlines():
                        if ln.startswith("id name"):
                            meta.write("id_name: %s\n" % ln)
                    for ln in engine.opt_lines:
                        meta.write("option_sent: %s\n" % ln)
                    meta.write("nm_sanitizer_syms: %s\n" % nm)
                    meta.write("nm_asan_syms: %s\n" % nm_asan)
                    meta.write("nm_ubsan_syms: %s\n" % nm_ubsan)
                    meta.write("env: ASAN_OPTIONS/UBSAN_OPTIONS/TSAN_OPTIONS unset before spawn\n")
                    meta.write("batch_size: %d go_timeout_s: %.1f\n" % (BATCH, GO_TIMEOUT))

        start_batch()
        for i, parts in enumerate(rows):
            idx, src, kind, desc, fen = parts[0], parts[1], parts[2], parts[3], parts[4]
            pych = parts[5] if len(parts) > 5 else "?"
            stats["total"] += 1
            if i and i % BATCH == 0:
                engine.kill()
                start_batch()

            engine.send("position fen " + fen)
            engine.send("isready")
            ok, lines = engine.until("readyok")
            if ok is None:
                if lines and lines[-1] == "":
                    stats["crash"] += 1
                    verdict = "CRASH"
                else:
                    stats["hang"] += 1
                    verdict = "HANG"
                res.write("\t".join([idx, src, kind, desc, fen, pych, verdict, "", "?", "?"]) + "\n")
                res.flush()
                engine.kill()
                start_batch()
                continue
            ans = " | ".join(lines)
            if any(m in ans for m in ("__asan_", "__ubsan_", "Sanitizer", "runtime error")):
                stats["san"] += 1

            if "invalid FEN" in ans:
                stats["refused"] += 1
                verdict = "REFUSED"
                best = ""
                legal = "-"
                engine.send("ucinewgame")
                engine.send("isready")
                engine.until("readyok")
            else:
                stats["accepted"] += 1
                verdict = "ACCEPTED"
                engine.send("go depth 2")
                gok, glines = engine.until("bestmove")
                if gok is None:
                    if glines and glines[-1] == "":
                        stats["crash"] += 1
                        verdict = "CRASH_IN_GO"
                    else:
                        stats["hang"] += 1
                        verdict = "HANG_IN_GO"
                    res.write("\t".join([idx, src, kind, desc, fen, pych, verdict, "", "?", "?"]) + "\n")
                    res.flush()
                    engine.kill()
                    start_batch()
                    continue
                if any(m in ln for ln in glines for m in ("__asan_", "__ubsan_", "Sanitizer", "runtime error")):
                    stats["san"] += 1
                best = ""
                for ln in glines:
                    if ln.startswith("bestmove"):
                        best = ln.split()[1] if len(ln.split()) > 1 else ""
                if pych == "1":
                    stats["acc_pyvalid"] += 1
                else:
                    stats["acc_pyinvalid"] += 1
                    acc_pyinvalid_rows.append("\t".join([idx, src, kind, desc, fen, pych, best]))
                lm = legal_moves(fen)
                if lm is None:
                    legal = "n/a"
                elif best in lm:
                    legal = "legal"
                else:
                    legal = "ILLEGAL"
                    stats["illegal_best"] += 1
                engine.send("ucinewgame")
                engine.send("isready")
                engine.until("readyok")
            res.write("\t".join([idx, src, kind, desc, fen, pych, verdict, best, legal, ans[:300]]) + "\n")
            res.flush()
            if stats["total"] % 2500 == 0:
                stamps.write("%s after %d FENs\n" % (datetime.datetime.utcnow().isoformat() + "Z",
                                                     stats["total"]))
                stamps.flush()
        engine.kill()
        stamps.write("%s END\n" % (datetime.datetime.utcnow().isoformat() + "Z"))

    with open(os.path.join(outdir, label + "_summary.txt"), "w") as fh:
        for k in ("total", "refused", "accepted", "acc_pyvalid", "acc_pyinvalid",
                  "crash", "hang", "san", "illegal_best"):
            fh.write("%s %d\n" % (k, stats[k]))
    with open(os.path.join(outdir, label + "_accepted_pyinvalid.txt"), "w") as fh:
        for r in acc_pyinvalid_rows:
            fh.write(r + "\n")
    print(open(os.path.join(outdir, label + "_summary.txt")).read())


if __name__ == "__main__":
    main()
