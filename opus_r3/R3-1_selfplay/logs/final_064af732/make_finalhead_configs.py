"""Self-play configs for the final stack head (064af732): the options added after 330237f3.

Reads the R3-1 self-play agent's configs_final.json (read-only) and writes configs_finalhead_064af732.json with
4 configs over the two runners A/B: SmpHelpersPastDepth alone (Threads 2), all_on + SmpHelpersPastDepth, and the
20 R3-4 search-constant spins at about +10% / -10% of their defaults (integers, inside the advertised ranges).
usage: make_finalhead_configs.py <configs_final.json> <out.json>"""
import json
import sys

src, out = sys.argv[1], sys.argv[2]
base = json.load(open(src, encoding="utf-8"))
all_on = next(c for c in base["configs"] if c["name"] == "all_on")

names = ["LmrQuietBase", "LmrQuietDivisor", "LmrNoisyBase", "LmrNoisyDivisor", "LmrHistoryDivisor",
         "LmrCutoffThreshold", "NullMoveBase", "NullMoveDepthDivisor", "NullMoveEvalDivisor", "NullMoveMarginDepth",
         "NullMoveMarginBase", "RfpMargin", "RfpImproving", "RfpDepth", "FutilityBase", "FutilityMultiplier",
         "QsFutilityMargin", "SeeQuietMultiplier", "SeeNoisyMultiplier", "AspirationDelta"]
plus = [94, 242, 11, 374, 6600, 4, 4, 4, 220, 26, 198, 79, 44, 9, 110, 121, 176, 26, 165, 20]
minus = [77, 198, 9, 306, 5400, 2, 2, 2, 180, 22, 162, 65, 36, 7, 90, 99, 144, 22, 135, 16]

configs = [
    {"name": "smp_helpers_past_depth", "runner": "A", "exe": "base", "threads": 2,
     "opts": ["SmpHelpersPastDepth=true"]},
    {"name": "all_on_final", "runner": "B", "exe": "allsw", "threads": 2,
     "opts": all_on["opts"] + ["SmpHelpersPastDepth=true"], "expect": all_on.get("expect", [])},
    {"name": "spsa_plus10", "runner": "A", "exe": "base",
     "opts": [f"{n}={v}" for n, v in zip(names, plus)]},
    {"name": "spsa_minus10", "runner": "B", "exe": "base",
     "opts": [f"{n}={v}" for n, v in zip(names, minus)]},
]
doc = {k: v for k, v in base.items() if k != "configs"}
doc["comment"] = ("R3-1 self-play for the final stack head 064af732 (main session): the options added after 330237f3 "
                  "(R3-6 SmpHelpersPastDepth, R3-4 search-constant spins at about +/-10%), same harness_args as "
                  "configs_final.json. Engines: base = default PC build, allsw = every switch (incl. FORGE_DATAGEN).")
doc["configs"] = configs
with open(out, "w", encoding="utf-8", newline="\n") as f:
    json.dump(doc, f, indent=1)
    f.write("\n")
print("wrote", out, len(configs), "configs")
