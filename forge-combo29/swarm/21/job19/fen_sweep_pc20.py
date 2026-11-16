#!/usr/bin/env python3
"""fen_sweep_pc20.py EXE MUT_TSV OUTDIR LABEL [N]

The 20,000-mutation FEN sweep on the PC build under PC20, Threads 1.

Differences from job6/fen_rerun.py (which is for the base tree, default options):
  - the 14 S14 settings + the six PC20 options are sent ONCE per engine process, each followed
    by isready/readyok and checked for unknown option / invalid value / ERROR;
  - Threads 1 and Hash 16 explicitly; OwnBook false.
Everything else is the same discipline: one fresh process per 500 FENs, `position fen` answered
to readyok, `go depth 2` read to bestmove (19-F12), a dead process counted as a crash and the
batch restarted, and every bestmove checked for legality on the FEN the ENGINE was given.

[N] (optional) truncates the input for a quick smoke run; the report always states how many
FENs the table covers.
"""
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "job6"))
from safe_engine import SafeEngine, Timeout, bestmove_of  # noqa: E402

import chess

S14 = [("LmrQuietBase", "93"), ("LmrQuietDivisor", "205"), ("LmrNoisyBase", "13"),
       ("LmrNoisyDivisor", "333"), ("LmrHistoryDivisor", "5643"), ("NullMoveBase", "5"),
       ("LmpBase", "8"), ("HistoryPruneMultiplier", "2220"), ("HistoryBonusQuadratic", "24"),
       ("HistoryBonusLinear", "54"), ("HistoryBonusMax", "2212"), ("SingularDepth", "6"),
       ("IirDepth", "2"), ("NonPawnCorrection", "true")]
PC20_EXTRA = [("CuckooRep", "true"), ("HistRework", "2"), ("TtPruneV2", "true"),
              ("CorrHistV2", "true"), ("MateAlphaGuard", "true"), ("OwnBook", "false")]
BAD = ("unknown option", "invalid value", "ERROR")
SAN = ("__asan_", "__ubsan_", "AddressSanitizer", "Sanitizer", "runtime error",
       "SUMMARY: UndefinedBehavior", "SEGV", "heap-buffer-overflow")
BATCH = 500


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def main():
    exe, mut_tsv, outdir, label = sys.argv[1:5]
    limit = int(sys.argv[5]) if len(sys.argv) > 5 else None
    os.makedirs(outdir, exist_ok=True)
    rows = []
    for ln in open(mut_tsv):
        p = ln.rstrip("\n").split("\t")
        if len(p) >= 5:
            rows.append(p)
    if limit:
        rows = rows[:limit]

    stats = dict(total=0, refused=0, accepted=0, acc_pyvalid=0, acc_pyinvalid=0,
                 crash=0, hang=0, san=0, illegal_best=0, empty_bestmove=0, option_reject=0)
    acc_invalid = []
    engine = None
    batch_idx = -1
    res = open(os.path.join(outdir, label + "_results.tsv"), "w")
    stamps = open(os.path.join(outdir, label + "_stamps.txt"), "w")

    def start_batch():
        nonlocal engine, batch_idx
        batch_idx += 1
        engine = SafeEngine(exe, os.path.join(outdir, "%s_raw_%03d.txt" % (label, batch_idx)),
                            hash_mb=16, threads=1)
        for n, v in S14 + PC20_EXTRA:
            engine.send("setoption name %s value %s" % (n, v))
            engine.send("isready")
            lines = engine.wait_for("readyok")
            bad = [l for l in lines if any(b in l for b in BAD)]
            if bad:
                stats["option_reject"] += 1
                raise SystemExit("option %s=%s rejected: %s" % (n, v, bad))
        engine.send("ucinewgame")
        engine.send("isready")
        engine.wait_for("readyok")

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
                res.write("\t".join([idx, src, kind, desc, fen, pych, "HANG"] ) + "\n")
                engine.close()
                start_batch()
                continue
            if any("invalid FEN" in l for l in ans):
                stats["refused"] += 1
                res.write("\t".join([idx, src, kind, desc, fen, pych, "REFUSED",
                                     "", "", next((l for l in ans if "info string" in l), "")]) + "\n")
                continue
            stats["accepted"] += 1
            try:
                gl = engine.go("go depth 2", timeout=120)
            except (Timeout, EOFError):
                stats["hang"] += 1
                res.write("\t".join([idx, src, kind, desc, fen, pych, "HANG_IN_GO"]) + "\n")
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
                legal = "n/a"
            if legal == "ILLEGAL":
                stats["illegal_best"] += 1
            res.write("\t".join([idx, src, kind, desc, fen, pych, "ACCEPTED", best, legal]) + "\n")
            if stats["total"] % 2500 == 0:
                stamps.write("%s after %d\n" % (__import__("datetime").datetime.now(
                    __import__("datetime").timezone.utc).isoformat(), stats["total"]))
                stamps.flush()
    finally:
        try:
            engine.close()
        except Exception:
            pass
        res.close()
        stamps.close()

    with open(os.path.join(outdir, label + "_summary.txt"), "w") as fh:
        fh.write("exe: %s\nsha256: %s\noptions: Hash 16, Threads 1, S14, PC20 extras\n"
                 % (os.path.abspath(exe), sha256(exe)))
        for k, v in stats.items():
            fh.write("%s %d\n" % (k, v))
    with open(os.path.join(outdir, label + "_accepted_pyinvalid.txt"), "w") as fh:
        fh.write("\n".join(acc_invalid) + "\n")
    print(open(os.path.join(outdir, label + "_summary.txt")).read())


if __name__ == "__main__":
    main()