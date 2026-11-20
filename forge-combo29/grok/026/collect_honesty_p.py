#!/usr/bin/env python3
"""Paste the four exe-P honesty raw files into HONESTY_P.txt."""

from pathlib import Path

S = Path.home().joinpath("grok_seat.txt").read_text(encoding="utf-8").strip()
repo = Path.home().joinpath("grok_repo.txt").read_text(encoding="utf-8").strip()
folder = Path(repo) / "forge-combo29" / "grok" / S
parts = [
    ("bench 11", "honesty_p_bench11.txt"),
    ("bench 13", "honesty_p_bench13.txt"),
    ("bench 16", "honesty_p_bench16.txt"),
    ("go perft 5", "honesty_p_perft5.txt"),
]
out = []
for title, name in parts:
    text = (folder / name).read_text(encoding="utf-8")
    out.append(f"===== {title} raw {name} =====")
    out.append(text.rstrip("\n"))
    out.append("")
(folder / "HONESTY_P.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
print(folder / "HONESTY_P.txt")
