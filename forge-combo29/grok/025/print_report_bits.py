#!/usr/bin/env python3
"""Read raw files in this folder and print the numbers the report quotes."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def rows(name: str):
    out = []
    for line in (HERE / name).read_text().splitlines():
        if not line.strip():
            continue
        index, nodes, move, _fen = line.split("\t", 3)
        out.append((int(nodes), move))
    return out


def compare(left_name: str, right_name: str) -> str:
    left = rows(left_name)
    right = rows(right_name)
    n = min(len(left), len(right))
    node_diff = sum(1 for i in range(n) if left[i][0] != right[i][0])
    move_diff = sum(1 for i in range(n) if left[i][1] != right[i][1])
    return (
        f"{left_name} sum {sum(r[0] for r in left)} n {len(left)}\n"
        f"{right_name} sum {sum(r[0] for r in right)} n {len(right)}\n"
        f"node_differ {node_diff} of {n}\n"
        f"move_differ {move_diff} of {n}"
    )


def honesty(path: Path) -> None:
    print(f"FILE {path.relative_to(HERE)}")
    for line in path.read_text().splitlines():
        if line.startswith("info string bench") or line.startswith("nodes "):
            print(line)


def results_block(path: Path) -> None:
    lines = path.read_text().splitlines()
    start = None
    for i, line in enumerate(lines):
        if line.startswith("Results of "):
            start = i
    if start is None:
        print(f"NO RESULTS in {path.name}")
        return
    for line in lines[start:]:
        print(line)
        if line.startswith("Finished match") or line.startswith("EXIT:"):
            break


def main() -> int:
    print("== honesty B ==")
    honesty(HERE / "HONESTY_B.txt")
    print("== honesty P ==")
    honesty(HERE / "p_honesty" / "HONESTY_B.txt")
    print("== honesty partner build ==")
    honesty(HERE / "partner_honesty" / "HONESTY_B.txt")
    print("== off O ==")
    print(compare("O_B_d12.rows", "O_P_off.rows"))
    print("== off G ==")
    print(compare("G_B_d12.rows", "G_P_off.rows"))
    print("== on O ==")
    print(compare("O_B_d12.rows", "O_P_on.rows"))
    print("== partner off vs B ==")
    print(compare("O_B_d12.rows", "partner_O_off.rows"))
    print("== partner on vs claimed ==")
    claimed = []
    for line in (HERE / "partner_claimed_O_on.txt").read_text().splitlines():
        parts = line.split()
        claimed.append(int(parts[3]))
    mine = [n for n, _m in rows("partner_O_on.rows")]
    n = min(len(claimed), len(mine))
    diff = sum(1 for i in range(n) if claimed[i] != mine[i])
    print(f"claimed_sum {sum(claimed)} mine_sum {sum(mine)} n {n} differ {diff}")
    print("== uci IdeaS33 ==")
    for line in (HERE / "uci_options.txt").read_text().splitlines():
        if "IdeaS33" in line:
            print(line)
    print("== san G100 meta ==")
    text = (HERE / "san_G100.meta").read_text().splitlines()
    for line in text:
        if line.startswith(("sanitizer_lines", "positions_finished", "asan_symbols", "returncode", "exe ")):
            print(line)
    print("== san scratch meta ==")
    for line in (HERE / "san_scratch.meta").read_text().splitlines():
        if line.startswith(("sanitizer_lines", "asan_symbols", "returncode", "sanitizer ")):
            print(line)
    print("== my match ==")
    results_block(HERE / "match_on_vs_off.txt")
    print("== partner match ==")
    results_block(HERE / "partner_match.txt")
    print("== apply ==")
    print((HERE / "partner_apply_check.txt").read_text().strip())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
