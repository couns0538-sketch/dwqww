#!/usr/bin/env python3
"""analyze.py RESULTS_TSV OUTREPORT

Reads the raw per-FEN result table written by run_fen.py and produces every table
that goes into the report. Nothing in the tables is typed by hand.

Reclassification rule for bestmove legality (applied here, not in the runner):
a bestmove of "0000" counts as LEGAL exactly when python-chess says the position has
zero legal moves and the position parses; otherwise "0000" is ILLEGAL. Any other
bestmove counts as LEGAL only when it is a python-chess legal move.
"""
import sys
from collections import Counter, defaultdict

import chess


def classify(fen, best):
    try:
        b = chess.Board(fen)
    except Exception:
        return "n/a"
    if not fen.strip():
        return "n/a"
    moves = {m.uci() for m in b.legal_moves}
    if best == "0000":
        return "legal" if not moves else "ILLEGAL_mate_claim_with_moves"
    return "legal" if best in moves else "ILLEGAL"


def main():
    path, out = sys.argv[1], sys.argv[2]
    rows = []
    with open(path) as fh:
        for ln in fh:
            p = ln.rstrip("\n").split("\t")
            if len(p) >= 9:
                rows.append(p)

    verdict = Counter(r[6] for r in rows)
    kind_acc = defaultdict(Counter)
    for r in rows:
        kind_acc[r[2]][r[6]] += 1

    accepted = [r for r in rows if r[6] == "ACCEPTED"]
    acc_valid = [r for r in accepted if r[5] == "1"]
    acc_invalid = [r for r in accepted if r[5] != "1"]

    legal_recheck = Counter()
    illegal_rows = []
    for r in accepted:
        c = classify(r[4], r[7])
        legal_recheck[c] += 1
        if c.startswith("ILLEGAL"):
            illegal_rows.append((r, c))

    lines = []
    w = lines.append
    w("### counts (as recorded by the runner)")
    for k, v in sorted(verdict.items()):
        w("| %s | %d |" % (k, v))
    w("")
    w("### per mutation kind")
    w("| kind | " + " | ".join(sorted(verdict)) + " |")
    for kind in sorted(kind_acc):
        w("| %s | %s |" % (kind, " | ".join(str(kind_acc[kind][v]) for v in sorted(verdict))))
    w("")
    w("### accepted FENs")
    w("| measure | count |")
    w("| accepted | %d |" % len(accepted))
    w("| ... python-chess also valid | %d |" % len(acc_valid))
    w("| ... python-chess INVALID | %d |" % len(acc_invalid))
    w("| refused | %d |" % verdict.get("REFUSED", 0))
    w("")
    w("### bestmove legality, reclassified")
    for k, v in sorted(legal_recheck.items()):
        w("| %s | %d |" % (k, v))
    w("")
    w("### accepted-but-python-invalid FENs (all, with the mutation)")
    w("| idx | src | kind | mutation | FEN | engine bestmove |")
    for r in acc_invalid:
        w("| %s | %s | %s | %s | `%s` | %s |" % (r[0], r[1], r[2], r[3], r[4], r[7]))
    w("")
    w("### genuinely illegal bestmoves after reclassification")
    if not illegal_rows:
        w("none")
    for r, c in illegal_rows:
        w("| %s | `%s` | bestmove %s | %s |" % (r[0], r[4], r[7], c))
    w("")
    with open(out, "w") as fh:
        fh.write("\n".join(lines) + "\n")
    sys.stdout.write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
