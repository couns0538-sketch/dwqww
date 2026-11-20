#!/usr/bin/env python3
"""Print the depth-sum tables and the IdeaS13 lines from the uci dump."""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent


def table(*args: str) -> str:
    return subprocess.check_output([sys.executable, str(HERE / "table_depth.py"), *args], text=True)


def main() -> None:
    parts = [
        "O base\n" + table("12", str(HERE / "O_B_d12.txt")),
        "G base\n" + table("12", str(HERE / "G_B_d12.txt")),
        "O off vs base\n" + table("12", str(HERE / "O_Poff_d12.txt"), str(HERE / "O_B_d12.txt")),
        "G off vs base\n" + table("12", str(HERE / "G_Poff_d12.txt"), str(HERE / "G_B_d12.txt")),
        "O on vs base\n" + table("12", str(HERE / "O_Pon_d12.txt"), str(HERE / "O_B_d12.txt")),
    ]
    uci = (HERE / "HONESTY_P_uci.txt").read_text().splitlines()
    opts = [line for line in uci if "IdeaS13" in line]
    parts.append("uci IdeaS13 lines\n" + "\n".join(opts) + "\n")
    sys.stdout.write("\n".join(parts))


if __name__ == "__main__":
    main()
