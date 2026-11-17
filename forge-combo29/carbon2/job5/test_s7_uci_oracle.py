#!/usr/bin/env python3
"""Step S7 UCI Parser, PositionCache & Dirty-Clear Differential Oracle + Planted-Fault Verifier."""
import subprocess
import sys

SCRIPT = """uci
setoption name OwnBook value false
setoption name Threads value 1
setoption name Hash value 16
isready
position startpos moves e2e4
eval
position startpos moves e2e4 e7e5
eval
position startpos moves   e2e4\te7e5   g1f3
eval
position startpos moves e2e4
eval
position startpos moves e2e4q
eval
position fen invalid_fen_here 1 2 3 4 5
eval
position fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3 moves f1b5 a7a6
eval
position fen r1bqkbnr/pppp1ppp/2n5/4p3/4P3/5N2/PPPP1PPP/RNBQKB1R w KQkq - 2 3 moves f1b5 a7a6 b5a4 g8f6
go depth 6
position startpos moves e2e4 e7e5 g1f3 b8c6
go depth 5 searchmoves f1b5 f1c4
go nodes 0
go perft 3
setoption name ThreatHistory value true
position startpos
go depth 6
ucinewgame
isready
position startpos
go depth 6
setoption name ThreatHistory value false
setoption name NNUEArchFile value {net768}
setoption name NNUEArch value true
isready
ucinewgame
position startpos moves d2d4 d7d5 c2c4
go softnodes 2000
quit
"""


def run_trace(binary: str, net768: str) -> list[str]:
    p = subprocess.run(
        [binary],
        input=SCRIPT.format(net768=net768),
        text=True,
        capture_output=True,
        check=True,
    )
    out = []
    for ln in p.stdout.splitlines():
        # Strip wall-clock time/nps fields from `info depth ...` so comparison is 100% deterministic.
        if ln.startswith("info depth "):
            toks = ln.split()
            cleaned = []
            i = 0
            while i < len(toks):
                if toks[i] in ("time", "nps"):
                    i += 2
                else:
                    cleaned.append(toks[i])
                    i += 1
            out.append(" ".join(cleaned))
        else:
            out.append(ln)
    return out


def main() -> int:
    ref_bin, var_bin, net768 = sys.argv[1], sys.argv[2], sys.argv[3]
    ref_lines = run_trace(ref_bin, net768)
    var_lines = run_trace(var_bin, net768)
    if ref_lines != var_lines:
        for idx, (a, b) in enumerate(zip(ref_lines, var_lines)):
            if a != b:
                print(f"S7_UCI_ORACLE MISMATCH at line {idx}:\n  ref: {a}\n  var: {b}", file=sys.stderr)
                return 1
        print(f"S7_UCI_ORACLE LENGTH MISMATCH: ref={len(ref_lines)} var={len(var_lines)}", file=sys.stderr)
        return 1
    print(f"S7_UCI_ORACLE PASS: lines_compared={len(ref_lines)} mismatches=0")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
