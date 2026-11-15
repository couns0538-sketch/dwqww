#!/usr/bin/env python3
# Parse `callgrind_annotate` output: per-line self costs keyed by (file, line no),
# per-line text; and the function table. Diff two runs by (file, line text).
import sys, re, collections

def norm(p):
    for pre in ("hrz_src/", "baseline_src/", "patched_src/", "/tmp/hrz_src/", "/tmp/baseline_src/"):
        if pre in p:
            return p.split(pre, 1)[1]
    return p

def parse_annot(path):
    cur_file, cur_line = None, None
    lines = collections.defaultdict(int)   # (normfile, linetext) -> cost
    lines_no = {}                          # (normfile, linetext) -> line no
    funcs = {}                             # (normfile:funcname) -> cost
    in_funcs = False
    for raw in open(path, errors="replace"):
        line = raw.rstrip("\n")
        m = re.match(r"-- (?:Auto|User)-annotated source: (\S+)", line)
        if m:
            cur_file = norm(m.group(1)); in_funcs = False; continue
        m = re.match(r"-- line (\d+)", line)
        if m:
            cur_line = int(m.group(1)); continue
        m = re.match(r"\s*([\d,]+) \([^)]*\%\)\s+(\S.*):(\S.*)\s+\[", line)
        if m and cur_file is None:
            pass  # function table handled below
        m = re.match(r"^\s*([\d,]+) \([^)]*\)\s+(.+)$", line)
        if m:
            cost = int(m.group(1).replace(",", ""))
            text = m.group(2)
            if text.startswith("=>"):
                continue
            if cur_file is not None and cur_line is not None:
                key = (cur_file, text.strip())
                lines[key] += cost
                lines_no.setdefault(key, cur_line)
            continue
    # function table: lines like "898,006,240 (12.04%)  file:func [bin]" before first source section
    for raw in open(path, errors="replace"):
        line = raw.rstrip("\n")
        if "annotated source:" in line:
            break
        m = re.match(r"^([\d,]+) \([^)]*\%\)\s+(\S[^:]*):(\S.*?)\s+\[[^\]]*\]\s*$", line)
        if m:
            cost = int(m.group(1).replace(",", ""))
            funcs[norm(m.group(2)) + ":" + m.group(3)] = cost
    return lines, lines_no, funcs

if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "linediff":
        la, na, _ = parse_annot(sys.argv[2])
        lb, nb, _ = parse_annot(sys.argv[3])
        topn = int(sys.argv[4])
        keys = set(la) | set(lb)
        rows = []
        for k in keys:
            d = la.get(k, 0) - lb.get(k, 0)
            if d != 0:
                rows.append((d, k, la.get(k, 0), lb.get(k, 0)))
        rows.sort(reverse=True)
        for d, k, va, vb in rows[:topn]:
            ln = na.get(k, nb.get(k, "?"))
            print(f"{d:+13d} {k[0]}:{ln}: {k[1][:90]}  [R1={va} R0={vb}]")
    elif mode == "funcdiff":
        _, _, fa = parse_annot(sys.argv[2])
        _, _, fb = parse_annot(sys.argv[3])
        topn = int(sys.argv[4])
        keys = set(fa) | set(fb)
        rows = sorted(((fa.get(k, 0) - fb.get(k, 0), k, fa.get(k, 0), fb.get(k, 0)) for k in keys), reverse=True)
        for d, k, va, vb in rows[:topn]:
            print(f"{d:+13d} {k[:110]}  [R1={va} R0={vb}]")
