#!/usr/bin/env python3
"""exe_func_diff.py - which functions differ between two builds of the same source (e.g. pc1 vs pc2 LTO+PGO exes).

  exe_func_diff.py A.exe B.exe [--objdump C:/msys64/ucrt64/bin/objdump.exe] [--show 20]

objdump -d --no-show-raw-insn both exes, split at '<symbol>:' headers, replace every hex address/offset by a
placeholder (code moves when anything before it changes size), and report functions present in only one exe and
functions whose normalized instruction text differs, largest first. Read-only; prints a summary.
"""
import re
import subprocess
import sys

HDR = re.compile(r"^[0-9a-f]+ <(.+)>:$")
ADDR = re.compile(r"\b(0x)?[0-9a-f]{4,}\b")


def funcs(objdump, exe):
    out = subprocess.run([objdump, "-d", "--no-show-raw-insn", exe], capture_output=True, check=True).stdout.decode(
        "utf-8", "replace")
    res, cur, body = {}, None, []
    for line in out.splitlines():
        m = HDR.match(line)
        if m:
            if cur is not None:
                res[cur] = body
            cur, body = m.group(1), []
        elif cur is not None and line.strip():
            text = line.split(":", 1)[1] if ":" in line else line
            body.append(ADDR.sub("#", text.strip()))
    if cur is not None:
        res[cur] = body
    return res


def main():
    args = sys.argv[1:]
    objdump = "C:/msys64/ucrt64/bin/objdump.exe"
    show = 20
    if "--objdump" in args:
        i = args.index("--objdump"); objdump = args[i + 1]; del args[i:i + 2]
    if "--show" in args:
        i = args.index("--show"); show = int(args[i + 1]); del args[i:i + 2]
    a, b = funcs(objdump, args[0]), funcs(objdump, args[1])
    only_a = sorted(set(a) - set(b))
    only_b = sorted(set(b) - set(a))
    diff = sorted(((max(len(a[k]), len(b[k])), k) for k in set(a) & set(b) if a[k] != b[k]), reverse=True)
    print("functions: A %d, B %d, only A %d, only B %d, differ %d, same %d" % (
        len(a), len(b), len(only_a), len(only_b), len(diff), len(set(a) & set(b)) - len(diff)))
    for n, k in diff[:show]:
        print("  differ %5d insns  %s (A %d, B %d)" % (n, k, len(a[k]), len(b[k])))
    for k in only_a[:show]:
        print("  only A %s" % k)
    for k in only_b[:show]:
        print("  only B %s" % k)


if __name__ == "__main__":
    main()
