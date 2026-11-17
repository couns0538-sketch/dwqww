#!/usr/bin/env python3
"""The 40-game divergence sample, fixed BEFORE any fresh-process arm is run.

Deterministic stride over the 200-game corpus: every 5th game, starting at index 1.
No dependence on any engine output, so the sample cannot be steered by what it finds.
"""
import json, sys

corpus = json.load(open(sys.argv[1] if len(sys.argv) > 1 else "evidence/games.json"))["games"]
ids = [g["id"] for g in corpus[1::5]][:40]
assert len(ids) == 40, len(ids)
plies = sum(len(g["moves"]) for g in corpus if g["id"] in ids)
json.dump({"rule": "corpus[1::5] -> first 40", "games": ids, "plies": plies},
          open(sys.argv[2] if len(sys.argv) > 2 else "evidence/divergence_sample.json", "w"), indent=0)
print(len(ids), "games,", plies, "plies")
print(ids)
