#!/usr/bin/env python3
"""Paste-ready tables. Reads only files in this folder."""
from pathlib import Path

HERE = Path(__file__).resolve().parent


def show(name: str) -> None:
    print(f"----- {name} -----")
    text = (HERE / name).read_text().rstrip()
    print(text)
    print()


def equals(left: str, right: str) -> None:
    def col(path: Path) -> list[int]:
        out = []
        for line in path.read_text().splitlines():
            parts = line.split()
            if len(parts) < 2:
                continue
            try:
                int(parts[0])
                out.append(int(parts[1]))
            except ValueError:
                continue
        return out

    a = col(HERE / left)
    b = col(HERE / right)
    same = [i for i in range(min(len(a), len(b))) if a[i] == b[i]]
    print(f"----- equal positions {left} vs {right} -----")
    print(f"n {min(len(a), len(b))} equal {len(same)} indices {same}")
    print()


def line_with(path: Path, prefix: str) -> str:
    for line in path.read_text().splitlines():
        if line.startswith(prefix):
            return line
    return ""


def main() -> int:
    on = line_with(HERE / "compare_on_O.txt", "differ ")
    off = line_with(HERE / "compare_off_O.txt", "differ ")
    pon = line_with(HERE / "partner_compare_on.txt", "differ ")
    elo = line_with(HERE / "match_result.txt", "Elo:")
    games = line_with(HERE / "match_result.txt", "Games:")
    pelo = line_with(HERE / "partner_match_result.txt", "Elo:")
    pgames = line_with(HERE / "partner_match_result.txt", "Games:")
    print("----- step table -----")
    print("step\tstatus\tevidence\tresult")
    print("1 seat\tdone\tSEAT.txt stamps.txt\t" + (HERE / "SEAT.txt").read_text().strip())
    print("2 builds and baseline\tdone\tHONESTY_B.txt B_sums.txt\t" + (HERE / "B_sums.txt").read_text().replace("\n", " | ").strip())
    print(f"3 idea\tdone\tidea.patch.txt compare_on_O.txt match_result.txt san_G100_d10.san.txt\toff {off}; on {on}; {elo}; {games}")
    print(f"4 partner 049\tdone\tpartner_compare_on.txt partner_match_result.txt\tCONFIRMS; {pon}; {pelo}; {pgames}")
    print("5 report\tdone\tREPORT.md RESULT.txt\tthis file")
    print()
    for name in [
        "B_sums.txt",
        "P_sums.txt",
        "compare_off_O.txt",
        "compare_off_G.txt",
        "compare_on_O.txt",
        "match_result.txt",
        "partner_compare_off.txt",
        "partner_compare_on.txt",
        "partner_compare_off_G.txt",
        "partner_match_result.txt",
        "partner_apply_check.txt",
    ]:
        show(name)
    equals("B_O_d12.rows.txt", "P_on_O_d12.rows.txt")
    san = (HERE / "san_G100_d10.raw.txt.meta").read_text()
    print("----- san_G100 meta lines -----")
    for line in san.splitlines():
        if line.startswith("nm ") or line.startswith("sanitizer") or line.startswith("exe"):
            print(line)
    scratch = (HERE / "san_scratch.san.txt").read_text().splitlines()
    print("----- scratch sanitizer lines -----")
    for line in scratch:
        print(line)
    print("----- uci options -----")
    for line in (HERE / "P_uci.txt").read_text().splitlines():
        if line.startswith("option name IdeaK10"):
            print(line)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
