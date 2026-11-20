#!/usr/bin/env python3
"""Print the fastchess result block and the options the config recorded."""
import json
import sys
from pathlib import Path


def main() -> int:
    out = Path(sys.argv[1]).read_text().splitlines()
    config = json.loads(Path(sys.argv[2]).read_text())
    pgn = Path(sys.argv[3]).read_text().splitlines()
    capture = False
    for line in out:
        if line.startswith("Results of "):
            capture = True
        if capture:
            print(line)
        if capture and line.startswith("Finished match"):
            break
    print(f"finished_games {sum(1 for line in out if line.startswith('Finished game '))}")
    print(f"pgn_events {sum(1 for line in pgn if line.startswith('[Event '))}")
    print(f"rounds {config.get('rounds')} games {config.get('games')} concurrency {config.get('concurrency')}")
    for engine in config["engines"]:
        wanted = [pair for pair in engine["options"] if pair[0] in ("AspCappedReopen", "Threads", "Hash", "NonPawnCorrection")]
        print(f"engine {engine['name']} nodes {engine['limit'].get('nodes')} {wanted}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
