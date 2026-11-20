#!/usr/bin/env python3
"""Print the fastchess results block and the game count. Usage: match_summary.py LOG"""
import sys

def main():
    path = sys.argv[1]
    finished = 0
    block = []
    capture = False
    with open(path, encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("Finished game "):
                finished += 1
            if line.startswith("Results of "):
                capture = True
                block = [line.rstrip("\n")]
                continue
            if capture:
                block.append(line.rstrip("\n"))
                if line.startswith("Finished match"):
                    capture = False
    print("finished_games", finished)
    for line in block:
        print(line)

if __name__ == "__main__":
    main()
