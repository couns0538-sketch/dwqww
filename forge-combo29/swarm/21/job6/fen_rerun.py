#!/usr/bin/env python3
"""fen_rerun.py EXE MUT_TSV OUTDIR LABEL

Re-runs the job1 measurement (20,000 mutated FENs) with the 19-F12-safe driver:
  - stdout is always read to `bestmove` (or to the `readyok` after a `position`) before
    the next command is sent;
  - stdin is never closed or sent `quit` while a search is outstanding.
Each FEN: `position fen` + `isready` (answer lines kept), then `go depth 2` read to
`bestmove`. One process per 500 FENs; a dead process is a CRASH and the batch restarts.

Writes: <LABEL>_results.tsv, <LABEL>_raw_<k>.txt, <LABEL>_meta.txt, <LABEL>_stamps.txt,
        <LABEL>_summary.txt, <LABEL>_accepted_pyinvalid.txt
"""
import hashlib
import os
import sys
import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from safe_engine import SafeEngine, Timeout, bestmove_of  # noqa: E402

import chess

BATCH = 500
GO_TIMEOUT = 60.0
SAN = ("__asan_", "__ubsan_", "AddressSanitizer", "Sanitizer", "runtime error",
       "SUMMARY: UndefinedBehavior", "SEGV", "heap-buffer-overflow")


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    exe, mut_tsv, outdir, label = sys.argv[1:5]
    os.makedirs(outdir, exist_ok=True)
    rows = []
    for ln in open(mut_tsv):
        p = ln.rstrip("\n").split("\t")
        if len(p) >= 5:
            rows.append(p)

    meta = dict(exe=os.path.abspath(exe), sha256=sha256(exe))
    idout = os.popen("%s <<'EOF'\nuci\nquit\nEOF" % exe).read()
    meta["id_name"] = next((l for l in idout.splitlines() if l.startswith("id name")), "?")
    meta["options_sent"] = "Hash 16, Threads 1, OwnBook false"
    for sym in ("__asan_", "__ubsan_"):
        meta["nm_" + sym] = os.popen("nm -C %s | grep -c %s || true" % (exe, sym)).read().strip()

    stats = dict(total=0, refused=0, accepted=0, acc_pyvalid=0, acc_pyinvalid=0,
                 crash=0, hang=0, san=0, illegal_best=0, empty_bestmove=0)
    acc_invalid = []
    engine = None
    batch_idx = -1
    res = open(os.path.join(outdir, label + "_results.tsv"), "w")
    stamps = open(os.path.join(outdir, label + "_stamps.txt"), "w")

    def start_batch():
        nonlocal engine, batch_idx
        batch_idx += 1
        engine = SafeEngine(exe, os.path.join(outdir, "%s_raw_%03d.txt" % (label, batch_idx)))

    start_batch()
    try:
        for i, parts in enumerate(rows):
            idx, src, kind, desc, fen = parts[:5]
            pych = parts[5] if len(parts) > 5 else "?"
            if i and i % BATCH == 0:
                engine.close()
                start_batch()
            stats["total"] += 1
            try:
                ans = engine.position("position fen " + fen)
            except (Timeout, EOFError):
                stats["hang"] += 1
                res.write("\t".join([idx, src, kind, desc, fen, pych, "HANG_IN_POSITION", "", "?"]) + "\n")
                engine.close()
                start_batch()
                continue
            ans_txt = " | ".join(ans)
            if "invalid FEN" in ans_txt:
                stats["refused"] += 1
                res.write("\t".join([idx, src, kind, desc, fen, pych, "REFUSED", "", "-"]) + "\n")
                continue
            stats["accepted"] += 1
            try:
                gl = engine.go("go depth 2", timeout=GO_TIMEOUT)
            except (Timeout, EOFError):
                stats["hang"] += 1
                res.write("\t".join([idx, src, kind, desc, fen, pych, "HANG_IN_GO", "", "?"]) + "\n")
                engine.close()
                start_batch()
                continue
            gtxt = " | ".join(gl)
            if any(m in gtxt for m in SAN):
                stats["san"] += 1
            best = bestmove_of(gl)
            if not best:
                stats["empty_bestmove"] += 1
            if pych == "1":
                stats["acc_pyvalid"] += 1
            else:
                stats["acc_pyinvalid"] += 1
                acc_invalid.append("\t".join([idx, src, kind, desc, fen, pych, best]))
            try:
                lm = {m.uci() for m in chess.Board(fen).legal_moves}
                legal = "legal" if best in lm else ("legal" if best == "0000" and not lm else "ILLEGAL")
            except Exception:
                lm = None
                legal = "n/a"
            if legal == "ILLEGAL":
                stats["illegal_best"] += 1
            res.write("\t".join([idx, src, kind, desc, fen, pych, "ACCEPTED", best, legal]) + "\n")
            if stats["total"] % 2500 == 0:
                stamps.write("%s after %d FENs %s\n" %
                             (datetime.datetime.now(datetime.timezone.utc).isoformat(),
                              stats["total"], dict(stats)))
                stamps.flush()
    finally:
        try:
            engine.close()
        except Exception:
            pass
        res.close()
        stamps.write("%s END %s\n" % (datetime.datetime.now(datetime.timezone.utc).isoformat(),
                                      dict(stats)))
        stamps.close()

    with open(os.path.join(outdir, label + "_summary.txt"), "w") as fh:
        for k, v in stats.items():
            fh.write("%s %d\n" % (k, v))
    with open(os.path.join(outdir, label + "_accepted_pyinvalid.txt"), "w") as fh:
        fh.write("\n".join(acc_invalid) + "\n")
    with open(os.path.join(outdir, label + "_meta.txt"), "w") as fh:
        for k, v in meta.items():
            fh.write("%s: %s\n" % (k, v))
    print(open(os.path.join(outdir, label + "_summary.txt")).read())


if __name__ == "__main__":
    main()