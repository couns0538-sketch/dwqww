#!/usr/bin/env python3
"""Job 3 B2/B3 scoring.

B2 (material draws): every position is K+B v K or K+N v K, a dead draw. The engine's
last score must be `cp 0`. Anything else is a miss.

B3 (stalemate traps): K+Q v K with the queen side to move and at least one move that
stalemates the bare king. The engine's bestmove must not be one of the stalemating
moves, and its score must be a mate score.

Usage: b23_score.py b2 <results.json> <out.json>
       b23_score.py b3 <stalemate.json> <results.json> <out.json>
"""
import json
import sys


def score_b2(results_path, out_path):
    with open(results_path) as f:
        data = json.load(f)
    misses = []
    passed = 0
    for r in data["results"]:
        score = r.get("score")
        drew = score is not None and score.get("kind") == "cp" and score.get("value") == 0
        if drew:
            passed += 1
        else:
            misses.append({"fen": r["fen"], "bestmove": r.get("bestmove"),
                           "last_info": r.get("last_info"),
                           "problem": "score is not cp 0"})
    out = {"class": "B2-material", "positions": len(data["results"]),
           "passed": passed, "failed": len(misses), "misses": misses}
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "misses"}, sort_keys=True))
    for m in misses[:6]:
        print("  MISS", m["fen"], "|", m["problem"], "|", m["last_info"])


def score_b3(stale_path, results_path, out_path):
    with open(stale_path) as f:
        stale = json.load(f)
    with open(results_path) as f:
        data = json.load(f)
    if len(stale) != len(data["results"]):
        raise SystemExit(f"{len(stale)} stalemate positions vs {len(data['results'])} results")
    misses = []
    passed = 0
    for entry, r in zip(stale, data["results"]):
        problems = []
        move = r.get("bestmove")
        if move in entry["stalemating_moves"]:
            problems.append(f"played a stalemating move {move}")
        score = r.get("score")
        if score is None or score.get("kind") != "mate":
            problems.append(f"score is not a mate ({r.get('last_info')})")
        elif score["value"] <= 0:
            problems.append(f"mate score is not for the queen side ({score['value']})")
        if problems:
            misses.append({"fen": entry["fen"], "bestmove": move,
                           "stalemating_moves": entry["stalemating_moves"],
                           "last_info": r.get("last_info"), "problems": problems})
        else:
            passed += 1
    out = {"class": "B3-stalemate", "positions": len(stale), "passed": passed,
           "failed": len(misses), "misses": misses}
    with open(out_path, "w") as f:
        json.dump(out, f, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "misses"}, sort_keys=True))
    for m in misses[:6]:
        print("  MISS", m["fen"], "|", m["problems"])


def main():
    if sys.argv[1] == "b2":
        score_b2(sys.argv[2], sys.argv[3])
    else:
        score_b3(sys.argv[2], sys.argv[3], sys.argv[4])


if __name__ == "__main__":
    main()
