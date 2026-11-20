#!/usr/bin/env python3
"""Print the report numbers by reading the raw evidence files. Nothing is typed."""
import pathlib
import sys

from sum_nodes import nodes_before_bestmove


def tail_sum(path):
    lines = pathlib.Path(path).read_text().splitlines()
    keep = [line for line in lines if line.startswith("COUNT ") or line.startswith("SUM ") or line.startswith("FIRST3 ")]
    return "\n".join(keep)


def compare(path):
    return pathlib.Path(path).read_text().rstrip()


def honesty(path):
    rows = []
    for line in pathlib.Path(path).read_text().splitlines():
        if line.startswith("PASS ") or line.startswith("FAIL "):
            rows.append(line)
    return "\n".join(rows)


def main():
    folder = pathlib.Path(sys.argv[1])
    print("HONESTY_B")
    print(honesty(folder / "HONESTY_B.txt"))
    print("HONESTY_P")
    print(honesty(folder / "HONESTY_P.txt"))
    print("B_O")
    print(tail_sum(folder / "B_O_d12.sum.txt"))
    print("B_G")
    print(tail_sum(folder / "B_G_d12.sum.txt"))
    print("P_ON_O")
    print(tail_sum(folder / "P_on_O_d12.sum.txt"))
    print("OFF_O_VS_B")
    print(compare(folder / "P_off_O_vs_B.txt"))
    print("OFF_G_VS_B")
    print(compare(folder / "P_off_G_vs_B.txt"))
    print("ON_O_VS_B")
    on = (folder / "P_on_O_vs_B.txt").read_text().splitlines()
    print("\n".join(line for line in on if not line.startswith("POS ")))
    print("UCI")
    for line in (folder / "uci_P.txt").read_text().splitlines():
        if "IdeaK2" in line:
            print(line)
    print("ASAN_CLEAN_META")
    print((folder / "asan_G100_on.meta").read_text().rstrip())
    print("ASAN_SCRATCH_STDERR")
    err = (folder / "asan_scratch.stderr").read_text().splitlines()
    print(err[0] if err else "EMPTY")
    def last_match(path):
        lines = pathlib.Path(path).read_text().splitlines()
        kept = [line for line in lines if line.startswith("Elo:") or line.startswith("Games:") or line.startswith("Results of") or line.startswith("fastchess_exit")]
        # fastchess reprints the rating as the match grows. The last three facts are the finished match.
        start = 0
        for i, line in enumerate(kept):
            if line.startswith("Results of"):
                start = i
        print("\n".join(kept[start:]))

    print("MATCH")
    last_match(folder / "match_OG.log")
    print("PARTNER_OFF_VS_B")
    print(compare(folder / "partner_off_O_vs_B.txt"))
    print("PARTNER_ON_VS_CLAIMED")
    print(compare(folder / "partner_on_O_vs_claimed.txt"))
    print("PARTNER_MATCH")
    last_match(folder / "partner_match_R.log")
    print("HONESTY_PARTNER")
    print(honesty(folder / "HONESTY_PARTNER.txt"))


if __name__ == "__main__":
    main()
