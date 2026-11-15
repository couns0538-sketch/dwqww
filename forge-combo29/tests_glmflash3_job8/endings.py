#!/usr/bin/env python3
# Count how a match's games ended, from fastchess's own "Finished game ... {reason}" lines.
# Usage: endings.py <match.out> <cand_name>
import re
import sys
from collections import Counter

def main():
    path, cand = sys.argv[1], sys.argv[2]
    reasons = Counter()
    wins = losses = draws = 0
    for line in open(path):
        m = re.search(r'Finished game \d+ \(([^)]+)\): (\S+) \{([^}]*)\}', line)
        if not m:
            continue
        pairing, result, reason = m.group(1), m.group(2), m.group(3)
        reasons[reason] += 1
        cand_white = pairing.startswith(cand + ' vs')
        cand_points = (1.0 if cand_white else 0.0) if result == '1-0' else \
                      (0.0 if cand_white else 1.0) if result == '0-1' else 0.5
        if cand_points == 1.0: wins += 1
        elif cand_points == 0.0: losses += 1
        else: draws += 1
    total = sum(reasons.values())
    print(f"games_with_reason={total} cand W={wins} L={losses} D={draws}")
    for reason, count in reasons.most_common():
        print(f"  {count:5d}  {reason}")
    faults = sum(v for k, v in reasons.items() if
                 'crash' in k.lower() or 'illegal' in k.lower() or 'disconnect' in k.lower()
                 or 'stall' in k.lower() or 'timeout' in k.lower())
    print(f"faults={faults}")

if __name__ == '__main__':
    main()
