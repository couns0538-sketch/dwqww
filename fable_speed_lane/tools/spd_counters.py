r"""spd_counters.py - exact execution counters of an instrumented build (frontend PGO counters).

The lock recipe's first stage (m2gen) is instrumented with -fprofile-instr-generate. Its merged profile
holds, for every source function, the entry count and one counter per source region, independent of
inlining and of machine load. This tool dumps them as a TSV (entry count, demangled name, region counters).
`load()` is also used by work_counters.py.

usage: spd_counters.py PROFDATA OUT_TSV [--bin DIR_WITH_LLVM_TOOLS]
"""
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard  # noqa: E402

BIN = r"C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin"


def load(profdata: str, bindir: str = BIN) -> list[dict]:
    """[{name (demangled, without forge::), entry, counts (list of int)}] of one merged profile."""
    show = subprocess.run([os.path.join(bindir, "llvm-profdata.exe"), "show", "--all-functions", "--counts", profdata],
                          capture_output=True, text=True, encoding="utf-8", errors="replace", check=True).stdout
    funcs = []
    cur = None
    for line in show.splitlines():
        m = re.match(r"^  (\S.*):$", line)
        if m:
            cur = {"name": m.group(1), "entry": 0, "counts": []}
            funcs.append(cur)
            continue
        if cur is None:
            continue
        m = re.match(r"^\s+Function count:\s+(\d+)", line)
        if m:
            cur["entry"] = int(m.group(1))
        m = re.match(r"^\s+Block counts:\s+\[(.*)\]", line)
        if m:
            cur["counts"] = [int(x) for x in m.group(1).split(",") if x.strip()]
    mangled = [f["name"].split(":", 1)[1] if re.match(r"^[\w.]+\.(cpp|hpp|h):", f["name"]) else f["name"] for f in funcs]
    dem = subprocess.run([os.path.join(bindir, "llvm-cxxfilt.exe")], input="\n".join(mangled) + "\n", capture_output=True,
                         text=True, encoding="utf-8", errors="replace", check=True).stdout.splitlines()
    for f, d in zip(funcs, dem):
        f["name"] = d.replace("forge::", "")
    return funcs


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    bindir = sys.argv[sys.argv.index("--bin") + 1] if "--bin" in sys.argv else BIN
    if bindir in args:
        args.remove(bindir)
    profdata, out = args[0], args[1]
    pinguard.ensure()
    funcs = load(profdata, bindir)
    with open(out, "w", encoding="utf-8", newline="\n") as f:
        f.write("entry_count\tfunction\tregion_counters\n")
        for fn in sorted(funcs, key=lambda x: -x["entry"]):
            f.write(f"{fn['entry']}\t{fn['name']}\t{', '.join(str(c) for c in fn['counts'])}\n")
    print(f"{len(funcs)} functions -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
