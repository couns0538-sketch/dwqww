#!/usr/bin/env python3
"""From an engine transcript, write one nodes value per bestmove.

The value is the last info-line nodes count seen before that bestmove.
"""
import sys


def main():
    last = None
    index = 0
    with open(sys.argv[1], encoding="utf-8", errors="replace") as handle:
        for line in handle:
            if line.startswith("bestmove "):
                index += 1
                if last is None:
                    raise SystemExit(f"bestmove {index} had no nodes")
                print(f"{index}\t{last}")
                last = None
                continue
            parts = line.split()
            for token, value in zip(parts, parts[1:]):
                if token == "nodes":
                    last = int(value)
                    break
    if index == 0:
        raise SystemExit("no bestmove")


if __name__ == "__main__":
    main()
