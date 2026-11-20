#!/usr/bin/env python3
"""Collect the report numbers by reading the raw files in this folder."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent


def nodes_line(path: Path) -> str:
    hits = [line for line in path.read_text().splitlines() if "nodes" in line]
    return hits[-1] if hits else "MISSING"


def transcript_nodes(path: Path) -> list[int]:
    nodes = []
    pending = []
    in_go = False
    for line in path.read_text().splitlines():
        if line.startswith(">>> go "):
            in_go = True
            pending = []
            continue
        if not in_go:
            continue
        if line.startswith(">>>"):
            in_go = False
            pending = []
            continue
        pending.append(line)
        if line.startswith("bestmove "):
            found = None
            for item in pending:
                fields = item.split()
                if "nodes" in fields:
                    found = int(fields[fields.index("nodes") + 1])
            nodes.append(found if found is not None else -1)
            in_go = False
    return nodes


def differ(left: list[int], right: list[int]) -> str:
    n = min(len(left), right and len(right) or 0)
    d = sum(1 for a, b in zip(left, right) if a != b)
    return f"n {len(left)}/{len(right)} differ {d} sum {sum(left)} vs {sum(right)}"


def elo_block(path: Path) -> str:
    lines = path.read_text(errors="replace").splitlines()
    start = 0
    for i, line in enumerate(lines):
        if line.startswith("Results of "):
            start = i
    return "\n".join(lines[start:start + 6])


def main() -> None:
    print("HONESTY_B")
    for name in ("bench11", "bench13", "bench16", "perft5"):
        print(name, nodes_line(HERE / f"honesty_b_{name}.txt"))
    print("HONESTY_P")
    for name in ("bench11", "bench13", "bench16", "perft5"):
        print(name, nodes_line(HERE / f"honesty_p_{name}.txt"))
    print("PARTNER_HONESTY")
    for name in ("bench11", "bench13", "bench16", "perft5"):
        print(name, nodes_line(HERE / f"partner_honesty_{name}.txt"))
    b_o = transcript_nodes(HERE / "b_O_d12.txt")
    b_g = transcript_nodes(HERE / "b_G_d12.txt")
    print("B_O", len(b_o), sum(b_o), b_o[:3])
    print("B_G", len(b_g), sum(b_g), b_g[:3])
    print("P_OFF_O", differ(transcript_nodes(HERE / "p_off_O_d12.txt"), b_o))
    print("P_OFF_G", differ(transcript_nodes(HERE / "p_off_G_d12.txt"), b_g))
    print("P_ON_O", differ(transcript_nodes(HERE / "p_on_O_d12.txt"), b_o))
    print("P_ON_VS_HINDSIGHT", differ(transcript_nodes(HERE / "p_on_O_d12.txt"), transcript_nodes(HERE / "b_hindsight_O_d12.txt")))
    partner_rows = [int(line.split()[0]) for line in (HERE / "partner092_on_O.tsv").read_text().splitlines() if line.strip()]
    print("PARTNER_OFF", differ(transcript_nodes(HERE / "partner_off_O_d12.txt"), b_o))
    print("PARTNER_ON_VS_THEIRS", differ(transcript_nodes(HERE / "partner_on_O_d12.txt"), partner_rows))
    print("PARTNER_ON_VS_B", differ(transcript_nodes(HERE / "partner_on_O_d12.txt"), b_o))
    meta = (HERE / "asan_G_d10.meta").read_text().splitlines()
    print("ASAN_META")
    for line in meta:
        if line.startswith("asan_symbols") or line.startswith("count") or line.startswith("exe") or line.startswith("sha256"):
            print(line)
    err = HERE / "asan_G_d10.err"
    print("asan_clean_err", "absent" if not err.exists() else f"bytes {err.stat().st_size}")
    scratch = (HERE / "asan_scratch.err").read_text().splitlines()
    print("ASAN_SCRATCH", scratch[0] if scratch else "MISSING")
    nm = [line for line in (HERE / "asan_scratch.meta").read_text().splitlines() if line.startswith("nm_asan")]
    print("ASAN_SCRATCH_META", nm[0] if nm else "MISSING")
    print("MATCH_OG")
    print(elo_block(HERE / "match_og.log"))
    print("PARTNER_MATCH_R")
    print(elo_block(HERE / "partner_match_R.log"))
    uci = [line for line in (HERE / "p_on_O_d12.txt").read_text().splitlines() if line.startswith("option name IdeaK3")]
    print("UCI_OPTIONS")
    print("\n".join(uci))


if __name__ == "__main__":
    main()
