#!/usr/bin/env python3
"""Print the report tables from raw evidence in this directory."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from compare_to_tsv import partner_nodes
from extract_match import main as extract_main
from summarize_nodes import rows_of


def differ(left: Path, right: Path) -> tuple[int, int]:
    a = rows_of(left.read_text(encoding="utf-8"))
    b = rows_of(right.read_text(encoding="utf-8"))
    if len(a) != len(b):
        return -1, len(a)
    count = sum(1 for x, y in zip(a, b) if x[1] != y[1])
    return count, len(a)


def nodes_in(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    found = ""
    for line in text.splitlines():
        parts = line.split()
        if "nodes" in parts:
            found = parts[parts.index("nodes") + 1]
    return found


def main() -> int:
    here = Path(__file__).resolve().parent
    print("honesty_B")
    for name, expect in (("bench11", "312866"), ("bench13", "862329"), ("bench16", "3024920"), ("perft5", "4865609")):
        got = nodes_in(here / f"honesty_b_{name}.txt")
        print(f"{name}\t{got}\t{expect}\t{str(got == expect).lower()}")
    print("honesty_P")
    for name, expect in (("bench11", "312866"), ("bench13", "862329"), ("bench16", "3024920"), ("perft5", "4865609")):
        got = nodes_in(here / f"honesty_p_{name}.txt")
        print(f"{name}\t{got}\t{expect}\t{str(got == expect).lower()}")
    pairs = [
        ("off_O", "B_O_d12.raw.txt", "P_off_O_d12.raw.txt"),
        ("off_G", "B_G_d12.raw.txt", "P_off_G_d12.raw.txt"),
        ("on_O", "B_O_d12.raw.txt", "P_on_O_d12.raw.txt"),
        ("partner_off_O", "B_O_d12.raw.txt", "partner_off_O.raw.txt"),
        ("partner_on_O", "B_O_d12.raw.txt", "partner_on_O.raw.txt"),
    ]
    print("compares")
    for label, left, right in pairs:
        count, total = differ(here / left, here / right)
        print(f"{label}\tdiffer\t{count}\tof\t{total}")
    on_rows = rows_of((here / "P_on_O_d12.raw.txt").read_text(encoding="utf-8"))
    b_o = rows_of((here / "B_O_d12.raw.txt").read_text(encoding="utf-8"))
    b_g = rows_of((here / "B_G_d12.raw.txt").read_text(encoding="utf-8"))
    print(f"B_O_sum\t{sum(row[1] for row in b_o)}\tcount\t{len(b_o)}")
    print(f"B_G_sum\t{sum(row[1] for row in b_g)}\tcount\t{len(b_g)}")
    print(f"on_O_sum\t{sum(row[1] for row in on_rows)}")
    print("step_table")
    print("step\tstatus\tevidence\tresult")
    print("1\tdone\tSEAT.txt stamps.txt\tseat 033 idea 33")
    print("2\tdone\tHONESTY_B.txt B_O_d12.raw.txt B_G_d12.raw.txt\thonesty match and baseline sums above")
    print("3\tdone\tidea.patch.txt proof_off_O.txt proof_on_O.txt match.log\toption off identical, on differs, match played")
    print("4\tdone\tpartner_apply_check.txt partner_on_vs_claim.txt partner_match.log\tpartner 083 CONFIRMS")
    print("5\tdone\tREPORT.md RESULT.txt\tthis report")
    mine = [row[1] for row in rows_of((here / "partner_on_O.raw.txt").read_text(encoding="utf-8"))]
    theirs = partner_nodes(here / "partner083_O_d12_P_on.tsv")
    same = sum(1 for a, b in zip(mine, theirs) if a == b)
    print(f"partner_on_vs_claim\tsame\t{same}\tdiffer\t{len(mine) - same}\tof\t{len(mine)}")
    asan = (here / "asan_G100.raw.txt").read_text(encoding="utf-8", errors="replace")
    scratch = (here / "asan_scratch.raw.txt").read_text(encoding="utf-8", errors="replace")
    print(f"asan_G100_sanitizer_lines\t{asan.count('AddressSanitizer') + asan.count('runtime error:')}")
    print(f"asan_scratch_heap_overflow\t{scratch.count('heap-buffer-overflow')}")
    meta = (here / "asan_G100.raw.meta").read_text(encoding="utf-8")
    for line in meta.splitlines():
        if line.startswith("asan_symbols="):
            print(line)
    print("uci")
    for line in (here / "uci_options.txt").read_text(encoding="utf-8").splitlines():
        if "IdeaA2" in line:
            print(line)
    print("match")
    sys.argv = ["extract_match.py", str(here / "match.log")]
    extract_main()
    print("partner_match")
    sys.argv = ["extract_match.py", str(here / "partner_match.log")]
    extract_main()
    print("stamps")
    print((here / "stamps.txt").read_text(encoding="utf-8"), end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
