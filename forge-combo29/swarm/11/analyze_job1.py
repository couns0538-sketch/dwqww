#!/usr/bin/env python3
"""analyze_job1.py RESULTS_JSONL OUTDIR : python-chess cross-check of the runner's raw results.

Reads only the raw results file. Writes:
  refused.txt            one line per refused FEN: id, answer line
  accepted_pyvalid.txt   accepted + python-chess Board(fen) OK
  accepted_pyinv.txt     accepted + python-chess REJECTED (the interesting ones)
  illegal_best.txt       accepted + bestmove not legal per python-chess
  summary.txt            the counts the report table quotes
"""
import json, sys, chess

res_path, outdir = sys.argv[1], sys.argv[2]
rows = [json.loads(l) for l in open(res_path)]
refused, acc_valid, acc_inv, illegal, unknown_bm = [], [], [], [], []
bm_missing = 0

for r in rows:
    if r["refused"]:
        refused.append((r["id"], r["refused"], r["fen"]))
        continue
    fen = r["fen"]
    try:
        b = chess.Board(fen)
    except Exception as e:
        acc_inv.append((r["id"], str(e), fen))
        continue
    if not b.is_valid():
        acc_inv.append((r["id"], "python-chess is_valid() False", fen))
        continue
    acc_valid.append(r["id"])
    bm = r.get("bestmove")
    if bm in (None, "refused", "EOF", "TIMEOUT") or str(bm).startswith("CRASH"):
        bm_missing += 1
        continue
    if bm in ("(none)", "0000"):
        unknown_bm.append((r["id"], bm, fen))
        continue
    try:
        mv = chess.Move.from_uci(bm)
    except Exception:
        illegal.append((r["id"], bm, fen, "unparseable"))
        continue
    if mv not in b.legal_moves:
        illegal.append((r["id"], bm, fen, "not legal"))

lines = {
    "refused.txt": [f"{i}\t{a}\t{f}" for i, a, f in refused],
    "accepted_pyvalid.txt": [str(i) for i in acc_valid],
    "accepted_pyinv.txt": [f"{i}\t{why}\t{f}" for i, why, f in acc_inv],
    "illegal_best.txt": [f"{i}\t{bm}\t{f}\t{why}" for i, bm, f, why in illegal],
}
for name, ls in lines.items():
    with open(f"{outdir}/{name}", "w") as g:
        g.write("\n".join(ls) + ("\n" if ls else ""))

total = len(rows)
summary = [
    f"cases            {total}",
    f"refused          {len(refused)}  ({100.0*len(refused)/total:.2f} %)",
    f"accepted         {len(acc_valid)+len(acc_inv)}  ({100.0*len(acc_valid+[(0,0,0)]*len(acc_inv))/total:.2f} %)",
    f"  py valid       {len(acc_valid)}",
    f"  py INVALID     {len(acc_inv)}",
    f"agreement among accepted  {100.0*len(acc_valid)/max(1,(len(acc_valid)+len(acc_inv))):.3f} %",
    f"no bestmove      {bm_missing}",
    f"no-move bestmove {len(unknown_bm)}",
    f"illegal bestmove {len(illegal)}",
    f"sanitizer lines  {sum(len(r.get('san') or []) for r in rows)}",
]
with open(f"{outdir}/summary.txt", "w") as g:
    g.write("\n".join(summary) + "\n")
print("\n".join(summary))
