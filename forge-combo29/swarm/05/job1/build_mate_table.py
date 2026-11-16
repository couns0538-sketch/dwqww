#!/usr/bin/env python3
"""build_mate_table.py -- builds the mate table of REPORT_job1.md from the committed raw files ONLY.
Every row is derived here from out/rows.jsonl (engine's own claim) and out/sf_authority*.txt (Stockfish 16,
the outside authority). Nothing is typed by hand.
"""
import json
import re

rows = {f"{r['set']}/{r['pos']}": r for r in (json.loads(l) for l in open("out/rows.jsonl"))}

sf = {}
for fn in ("out/sf_authority.txt", "out/sf_authority2.txt"):
    fen = None
    for line in open(fn):
        m = re.match(r"### pos fen=(.+?) go=", line)
        if m:
            fen = m.group(1)
            continue
        m = re.match(r"score: (mate|cp) (-?\d+)", line)
        if m and fen:
            sf[fen] = (m.group(1), int(m.group(2)))
            # do NOT clear fen here: the score line comes before the bestmove line

# The rows store the full FEN; the sf file stores it too (the `go=` anchor captures the whole FEN).
def sf_lookup(fen):
    if fen in sf:
        return sf[fen]
    # tolerate FENs whose trailing fields differ only in whitespace
    norm = " ".join(fen.split())
    for k, v in sf.items():
        if " ".join(k.split()) == norm:
            return v
    return None

print("| position | engine d12 score | engine pv plies | pv ends in checkmate | stockfish 16 score | "
      "true plies (SF) | engine plies | engine right? |")
print("|---|---|---|---|---|---|---|---|")
n_right = n_wrong = 0
for key, r in rows.items():
    lp = r.get("last_pv")
    if not lp or lp.get("score", ("",))[0] != "mate":
        continue
    n = lp["score"][1]
    eng_plies = 2 * n - 1 if n > 0 else 2 * (-n)
    s = sf_lookup(r["fen"])
    if not s or s[0] != "mate":
        true_plies = "?"
        sfs = "?"
        verdict = "?"
    else:
        m = s[1]
        true_plies = 2 * m - 1 if m > 0 else 2 * (-m)
        sfs = f"mate {m:+d}"
        # engine right means: same sign and same distance
        verdict = "yes" if eng_plies == true_plies else "NO"
        if verdict == "yes":
            n_right += 1
        else:
            n_wrong += 1
    print(f"| {key} | mate {n:+d} | {lp['plies']} | {lp['ends_checkmate']} | {sfs} | {true_plies} | "
          f"{eng_plies} | {verdict} |")
print()
print(f"rows with a mate score: {n_right + n_wrong}; engine distance CORRECT: {n_right}; WRONG: {n_wrong}")
