#!/usr/bin/env python3
"""SYNTHETIC toolchain for the S43 tests (not a compiler): `gpp` mode checks that every source argument exists relative
to its cwd (the tool must set an explicit cwd), then writes a Python "engine" to the -o path whose bench node count is
a function of the embedded net's sha256 and the depth; `objdump` mode prints that file (an extra -DFAKE_FMA flag
plants a 'vfmadd231ps' line). `bench_nodes` is the formula the tests use for their reference files."""
import hashlib
import sys
from pathlib import Path


def bench_nodes(net_sha256, depth):
    return int(net_sha256[:8], 16) % 900_000 + 1000 * depth


ENGINE = r'''
import sys
NET = {net!r}
FMA = {fma!r}
def bench(d):
    return int(NET[:8], 16) % 900000 + 1000 * d
for raw in sys.stdin:
    line = raw.strip()
    if line == "uci":
        print("id name FakeForge S43"); print("uciok", flush=True)
    elif line == "isready":
        print("readyok", flush=True)
    elif line.startswith("bench "):
        d = int(line.split()[1]); print("info string fake bench"); print(f"bench depth {{d}} nodes {{bench(d)}}", flush=True)
    elif line == "go perft 5":
        print("nodes " + ("193690690" if KIWI else "4865609"), flush=True)
    elif line.startswith("position"):
        KIWI = "fen" in line
    elif line == "quit":
        break
'''


def main():
    mode = sys.argv[1]
    args = sys.argv[2:]
    if mode == "gpp":
        out = Path(args[args.index("-o") + 1])
        srcs = [a for a in args if a.endswith(".cpp")]
        missing = [s for s in srcs if not Path(s).exists()]
        if missing or not Path("include").is_dir():
            print(f"fake g++: missing sources relative to cwd {Path.cwd()}: {missing}", file=sys.stderr); return 1
        net = hashlib.sha256(Path("src/nnue_weights.inc").read_bytes()).hexdigest()
        out.write_text("KIWI = False\n" + ENGINE.format(net=net, fma="-DFAKE_FMA" in args), encoding="utf-8")
        if "-DFAKE_FMA" in args:
            with open(out, "a", encoding="utf-8") as f:
                f.write("# vfmadd231ps ymm0,ymm1,ymm2\n")
        return 0
    if mode == "objdump":
        print(Path(args[-1]).read_text(encoding="utf-8"))
        return 0
    if mode == "cmake":
        if "--build" in args:
            bd = Path(args[args.index("--build") + 1])
            if not bd.is_absolute():
                print("fake cmake: relative build dir", file=sys.stderr); return 2
            (bd / "built.marker").write_text("ok"); return 0
        src, bd = Path(args[args.index("-S") + 1]), Path(args[args.index("-B") + 1])
        if not (src.is_absolute() and bd.is_absolute()) or not (src / "src").is_dir() or not (src / "CMakeLists.txt").is_file():
            print("fake cmake: -S/-B must be absolute and -S a source tree", file=sys.stderr); return 2
        bd.mkdir(parents=True, exist_ok=True); (bd / "CTestTestfile.cmake").write_text("# fake" + chr(10)); return 0
    if mode == "ctest":
        td, junit = Path(args[args.index("--test-dir") + 1]), Path(args[args.index("--output-junit") + 1])
        if not td.is_absolute() or not junit.is_absolute():
            print("fake ctest: relative path (the historical abort)", file=sys.stderr); return 2
        if not (td / "built.marker").exists():
            print("fake ctest: nothing built", file=sys.stderr); return 2
        junit.write_text('<testsuite><testcase name="forge_tests" status="fail"><failure message="4 known"/></testcase>'
                         '<testcase name="forge_perft" status="run"/></testsuite>', encoding="utf-8")
        for line in ("FAIL: WAC 001 expected g3g6 got f6h5", "FAIL: WAC 001 score 623 below 31997",
                     "FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion",
                     "FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion"):
            print(line)
        return 8
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
