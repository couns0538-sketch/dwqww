r"""spd_prof_query.py - re-read a sampler histogram and break one emitted function down by the inlined
source functions and source lines inside it.

usage: spd_prof_query.py HIST_DIR SYMEXE EMITTED_SUBSTRING [--symbolizer PATH] [--top N]
Writes HIST_DIR\rva_frames.tsv (rva, samples, frames innermost first) on the first call and reuses it.
"""
import collections
import json
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard  # noqa: E402

SYMBOLIZER = r"C:\opus_5h\oss_scout\dl\llvm-mingw-20261104\x\llvm-mingw-20261104-ucrt-x86_64\bin\llvm-symbolizer.exe"


def frames_for(hist_dir: str, symexe: str, symbolizer: str):
    cache = os.path.join(hist_dir, "rva_frames.tsv")
    rows = []
    if os.path.exists(cache):
        with open(cache, encoding="utf-8") as f:
            for line in f:
                rva, n, fr = line.rstrip("\n").split("\t", 2)
                rows.append((int(rva, 16), int(n), [tuple(x.split("|")) for x in fr.split(" <- ") if x]))
        return rows
    hist = {}
    with open(os.path.join(hist_dir, "rva_hist.tsv"), encoding="utf-8") as f:
        for line in f:
            rva, n = line.split("\t")
            hist[int(rva, 16)] = int(n)
    cmd = [symbolizer, f"--obj={symexe}", "--relative-address", "--inlines", "--functions=linkage", "--demangle",
           "--output-style=JSON"]
    r = subprocess.run(cmd, input="\n".join(hex(x) for x in sorted(hist)) + "\n", capture_output=True, text=True,
                       encoding="utf-8", errors="replace")
    sym = {}
    for line in r.stdout.splitlines():
        if line.startswith("{"):
            o = json.loads(line)
            sym[int(o["Address"], 16)] = [(f.get("FunctionName") or "??", os.path.basename(f.get("FileName") or ""),
                                           str(f.get("Line") or 0)) for f in o.get("Symbol", [])]
    with open(cache, "w", encoding="utf-8", newline="\n") as f:
        for rva in sorted(hist):
            fr = sym.get(rva, [])
            f.write(f"{rva:#x}\t{hist[rva]}\t{' <- '.join('|'.join(x) for x in fr)}\n")
            rows.append((rva, hist[rva], fr))
    return rows


def short(name: str) -> str:
    return name.replace("forge::", "").replace("(anonymous namespace)::", "").replace("`anonymous namespace'::", "")[:70]


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    top = int(sys.argv[sys.argv.index("--top") + 1]) if "--top" in sys.argv else 25
    symbolizer = sys.argv[sys.argv.index("--symbolizer") + 1] if "--symbolizer" in sys.argv else SYMBOLIZER
    if "--top" in sys.argv:
        args.remove(str(top))
    hist_dir, symexe, needle = args[0], args[1], args[2]
    pinguard.ensure()
    rows = frames_for(hist_dir, symexe, symbolizer)
    total = sum(n for _, n, _ in rows)
    inner = collections.Counter()
    lines = collections.Counter()
    sub = 0
    for _rva, n, fr in rows:
        if not fr or needle not in fr[-1][0]:
            continue
        sub += n
        inner[short(fr[0][0])] += n
        lines[f"{fr[0][1]}:{fr[0][2]} {short(fr[0][0])[:40]}"] += n
    print(f"emitted function matching '{needle}': {sub} of {total} samples = {100.0 * sub / max(total, 1):.2f} % of all time")
    print("-- by inlined source function (share of ALL time) --")
    for k, n in inner.most_common(top):
        print(f"{100.0 * n / total:6.2f} %  {n:5d}  {k}")
    print("-- by source line (share of ALL time) --")
    for k, n in lines.most_common(top):
        print(f"{100.0 * n / total:6.2f} %  {n:5d}  {k}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
