#!/usr/bin/env python3
"""Print the last fastchess results block and the game count."""
import sys
from pathlib import Path

def main() -> int:
    text = Path(sys.argv[1]).read_text()
    marker = "Results of "
    start = text.rfind(marker)
    if start < 0:
        print("no results block")
        return 1
    block = text[start:]
    end = block.find("Finished match")
    if end >= 0:
        block = block[: end + len("Finished match")]
    print(block.strip())
    print(f"result_headers {text.count('Results of ')}")
    print(f"started_games {text.count('Started game ')}")
    return 0

if __name__ == "__main__":
    sys.exit(main())
