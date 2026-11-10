"""Build a larger, independent position set for etc_probe from an opening file already on the PC.

  count    UHO_EPD                        print the number of lines
  sample   UHO_EPD OUT_EPD STRIDE [MAX]   take every STRIDE-th line of the opening file as a base position
  finalize GEN_EPD OUT_EPD                after `etc_probe --gen`: drop duplicate boards and set the search
                                          depth of every position from its material

The opening file is read only. Each base opening is an independent cluster; the positions generated from
it by the harness (its own best moves played forward) carry the base label plus `_pN`.

Depth rule in `finalize` (pieces = knights, bishops, rooks, queens of both sides):
  more than 6 pieces: depth 16;  3 to 6 pieces: depth 20;  0 to 2 pieces: depth 24.
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import pinguard  # noqa: E402


def pieces(fen: str) -> int:
    return sum(1 for c in fen.split()[0] if c in "nbrqNBRQ")


def sample(src: str, out: str, stride: int, limit: int):
    n = kept = 0
    with open(src, encoding="utf-8", errors="replace") as f, open(out, "w", encoding="utf-8", newline="\n") as o:
        for line in f:
            n += 1
            if n % stride:
                continue
            fields = line.split()
            if len(fields) < 4:
                continue
            kept += 1
            o.write(f"{' '.join(fields[:4])} 0 1 ; depth=16 ; u{kept:04d}\n")
            if kept >= limit:
                break
    print(f"read {n} lines, kept {kept} base positions -> {out}")


def finalize(src: str, out: str):
    seen = set()
    kept = dropped = 0
    with open(src, encoding="utf-8") as f, open(out, "w", encoding="utf-8", newline="\n") as o:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            fen, _depth, label = [x.strip() for x in line.split(";")]
            board = " ".join(fen.split()[:4])
            if board in seen:
                dropped += 1
                continue
            seen.add(board)
            p = pieces(fen)
            depth = 16 if p > 6 else 20 if p > 2 else 24
            o.write(f"{fen} ; depth={depth} ; {label}\n")
            kept += 1
    print(f"kept {kept}, dropped {dropped} duplicate boards -> {out}")


def main():
    pinguard.ensure()
    if sys.argv[1] == "count":
        with open(sys.argv[2], "rb") as f:
            print(sum(1 for _ in f), "lines in", sys.argv[2])
    elif sys.argv[1] == "sample":
        sample(sys.argv[2], sys.argv[3], int(sys.argv[4]), int(sys.argv[5]) if len(sys.argv) > 5 else 10 ** 9)
    elif sys.argv[1] == "finalize":
        finalize(sys.argv[2], sys.argv[3])
    else:
        raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
