"""R9: markdown table of the R9Tune parameters from an r9_option_check.py JSON (+ which ones a config tunes).
usage: python -I -B param_table.py <option_check.json> <config.json> > table.md"""
import json
import sys

chk = json.load(open(sys.argv[1], encoding="ascii"))
cfg = json.load(open(sys.argv[2], encoding="utf-8"))
tuned = {p["name"]: p for p in cfg["params"]}
NEW = {"NmpEvalDepthMargin", "NmpEvalBase", "NullMoveEvalMax", "NullMoveVerifyDepth", "ProbcutImproving",
       "ProbcutReduction", "SingularTtDepth", "SingularDoubleMargin", "SingularDoubleLimit", "LmrTtPv", "LmrNotImproving",
       "LmrCutNode", "LmrTtCapture", "LmrGivesCheck", "LmrInCheck", "LmrCutoffCount", "HistoryBonusOffset",
       "HistoryMalusPercent", "HistoryDepthBonusMargin", "AspirationMinDepth", "AspirationGrowPercent",
       "AspirationGrowAdd", "QuietCheckBonus"}
print("| # | parameter | lock value | engine range | origin | bench 11 moves | tuned in stc_main (range, c_end) |")
print("|---|---|---|---|---|---|---|")
for i, r in enumerate(chk["tunables"], 1):
    t = tuned.get(r["name"])
    tune = f"yes ({t['min']}..{t['max']}, {t['c_end']:g})" if t else ""
    origin = "R9 (former literal)" if r["name"] in NEW else "lock tune::"
    print(f"| {i} | {r['name']} | {r['default']} | {r['min']}..{r['max']} | {origin} | "
          f"{'yes' if r['changes_bench'] else 'no'} | {tune} |")
