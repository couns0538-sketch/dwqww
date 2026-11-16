#!/usr/bin/env python3
"""swarm seat 01, job 1 analysis: read results.jsonl + mutants.tsv, cross-check with python-chess.

Outputs (all in the directory given):
  table.txt            the job's table
  invalid_list.txt     every FEN accepted by the engine but INVALID per python-chess (one per line, with reason)
  illegal_bestmoves.txt every bestmove not legal per python-chess on the position the engine kept
  sanitizer_lines.txt  every sanitizer line seen
  by_mutation.txt      refusal rate per mutation kind
Everything here is computed from the committed raw files, never typed by hand.
"""
import json
import sys
from collections import Counter, defaultdict

import chess


def main(outdir):
    rows = []
    with open(outdir + "/results.jsonl") as fh:
        for line in fh:
            rows.append(json.loads(line))
    mutants = []
    with open(outdir + "/mutants.tsv") as fh:
        fh.readline()
        for line in fh:
            p = line.rstrip("\n").split("\t")
            if len(p) == 5:
                mutants.append(p)
    fen_by_idx = {int(m[0]): m[4] for m in mutants}

    refused = 0
    accepted = 0
    accepted_valid = 0
    accepted_invalid = []
    crashes = 0
    sanitizer = []
    illegal = []
    illegal_checked = 0
    illegal_skipped = 0

    for rec in rows:
        idx = rec["i"]
        if rec.get("crash"):
            crashes += 1
            continue
        if rec.get("refused"):
            refused += 1
            continue
        accepted += 1
        fen = fen_by_idx[idx]
        # python-chess view of THIS exact FEN. "valid" means parseable AND chess.Board.is_valid(),
        # because python-chess's constructor happily parses boards with no king, two kings, pawns on
        # rank 1/8 and impossible checkers; is_valid() is the judgement the job asks for.
        board = None
        try:
            board = chess.Board(fen)
            py_ok = board.is_valid()
            py_reason = "" if py_ok else "python-chess status %d" % board.status()
        except Exception as exc:  # noqa: BLE001
            py_ok = False
            py_reason = str(exc).split("\n")[0]
        if py_ok:
            accepted_valid += 1
        else:
            accepted_invalid.append((idx, rec.get("base_set", ""), rec.get("mutation_kind", ""),
                                     fen, py_reason))
        if rec.get("sanitizer"):
            sanitizer.append((idx, rec["sanitizer"]))
        bm = rec.get("bestmove", "")
        if rec.get("mutated_fen") is None and "fen" not in rec:
            pass
        # legality: if python-chess accepts the FEN, the engine's position is that board;
        # if it does not, we cannot judge from python-chess, so skip and count the skip.
        if board is not None and py_ok and bm and bm != "0000":
            illegal_checked += 1
            try:
                mv = chess.Move.from_uci(bm)
            except Exception:  # noqa: BLE001
                illegal.append((idx, fen, bm, "unparsable uci"))
                continue
            if mv not in board.legal_moves:
                illegal.append((idx, fen, bm, "not legal in python-chess board"))
        elif board is not None and py_ok and bm == "0000":
            if list(board.legal_moves):
                illegal.append((idx, fen, bm, "0000 but python-chess has legal moves"))
            illegal_checked += 1
        else:
            illegal_skipped += 1

    total = len(rows)
    lines = []
    lines.append("swarm seat 01, area 1, job 1: 20,000 mutated FENs, ASan+UBSan build")
    lines.append("total FENs: %d" % total)
    lines.append("refused by the engine: %d (%.2f %%)" % (refused, 100.0 * refused / total))
    lines.append("accepted by the engine: %d" % accepted)
    lines.append("python-chess validity rule used: chess.Board(fen) parses AND board.is_valid() is true")
    lines.append("accepted and python-chess valid: %d" % accepted_valid)
    lines.append("accepted and python-chess INVALID: %d" % len(accepted_invalid))
    lines.append("crashes: %d" % crashes)
    lines.append("sanitizer lines (ASan/UBSan) recorded in engine output: %d" % len(sanitizer))
    lines.append("illegal bestmoves (engine-kept position judged by python-chess): %d of %d judged"
                 % (len(illegal), illegal_checked))
    lines.append("bestmoves not judgeable here (python-chess rejected the FEN the engine accepted): %d"
                 % illegal_skipped)
    table = "\n".join(lines) + "\n"
    with open(outdir + "/table.txt", "w") as fh:
        fh.write(table)

    with open(outdir + "/invalid_list.txt", "w") as fh:
        for idx, base, kind, fen, reason in accepted_invalid:
            fh.write("%d\t%s\t%s\t%s\t%s\n" % (idx, base, kind, fen, reason))
    with open(outdir + "/illegal_bestmoves.txt", "w") as fh:
        for idx, fen, bm, why in illegal:
            fh.write("%d\t%s\t%s\t%s\n" % (idx, fen, bm, why))
    with open(outdir + "/sanitizer_lines.txt", "w") as fh:
        for idx, sl in sanitizer:
            fh.write("%d\t%s\n" % (idx, " | ".join(sl[:5])))

    # refusal rate per mutation kind
    counts = defaultdict(lambda: [0, 0])  # kind -> [refused, total]
    for rec in rows:
        k = rec.get("mutation_kind", "?")
        counts[k][1] += 1
        if rec.get("refused"):
            counts[k][0] += 1
        elif rec.get("crash"):
            pass
    with open(outdir + "/by_mutation.txt", "w") as fh:
        fh.write("mutation_kind\trefused\ttotal\trefused_pct\n")
        for k in sorted(counts):
            r, t = counts[k]
            fh.write("%s\t%d\t%d\t%.2f\n" % (k, r, t, 100.0 * r / t))
    # refusal reasons, engine side
    reasons = Counter()
    with open(outdir + "/refusal_reasons.txt", "w") as fh:
        for rec in rows:
            if rec.get("refused") and rec.get("refusal_line"):
                reasons[rec["refusal_line"][len("info string invalid FEN: "):]] += 1
        for reason, n in reasons.most_common():
            fh.write("%d\t%s\n" % (n, reason))

    print(table)


if __name__ == "__main__":
    main(sys.argv[1])
