#!/usr/bin/env python3
"""Compare the machine code of EVERY function of two Forge executables (unstripped), not only the
hot list of opus_round1/O3/codegen_compare.sh.

For each function name (objdump -d -C) present in both: instruction count, number of differing
instructions after normalising addresses / immediates / jump targets (same rules as
codegen_compare.sh), and the start address mod 64. Prints a summary and every function that differs
in code or in placement, plus the functions that exist in only one of the two.
usage: codegen_all.py <exe_A> <exe_B> [--filter forge::] [--objdump objdump]
"""
import argparse
import difflib
import re
import subprocess

HEAD = re.compile(r"^([0-9a-f]+) <(.*)>:$")


def functions(exe, objdump):
    out = subprocess.run([objdump, "-d", "-C", "--no-show-raw-insn", exe], capture_output=True, text=True,
                         check=True).stdout
    funcs = {}
    name = None
    for line in out.splitlines():
        m = HEAD.match(line)
        if m:
            name = m.group(2)
            if name in funcs:  # duplicate symbol name: keep the first body
                name = None
                continue
            funcs[name] = [int(m.group(1), 16), []]
            continue
        if name is None or not line.strip():
            continue
        if not re.match(r"^\s+[0-9a-f]+:", line):
            continue
        ins = re.sub(r"^\s*[0-9a-f]+:\s*", "", line)
        ins = re.sub(r"<[^>]*>", "", ins)
        ins = re.sub(r"#.*$", "", ins)
        ins = re.sub(r"0x[0-9a-f]+", "IMM", ins)
        ins = re.sub(r"^(j[a-z]+|call|jmp)\s+[0-9a-f]+", r"\1 ADDR", ins)
        ins = re.sub(r"\s+", " ", ins).strip()
        funcs[name][1].append(ins)
    return funcs


def is_padding(ins):
    return ins in ("nop", "xchg %ax,%ax", "int3") or ins.startswith(("nop", "data16", "cs nop", "xchg %ax,%ax"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("a")
    ap.add_argument("b")
    ap.add_argument("--filter", default="forge::")
    ap.add_argument("--objdump", default="objdump")
    args = ap.parse_args()
    fa = {k: v for k, v in functions(args.a, args.objdump).items() if args.filter in k}
    fb = {k: v for k, v in functions(args.b, args.objdump).items() if args.filter in k}
    common = sorted(set(fa) & set(fb), key=lambda k: fb[k][0])
    same = 0
    rows = []
    for name in common:
        (addr_a, body_a), (addr_b, body_b) = fa[name], fb[name]
        # Trailing alignment padding is not part of the function's code.
        ca = [i for i in body_a if not is_padding(i)]
        cb = [i for i in body_b if not is_padding(i)]
        diff = sum(1 for d in difflib.ndiff(ca, cb) if d[:1] in "+-")
        if diff == 0 and addr_a % 64 == addr_b % 64:
            same += 1
            continue
        rows.append((name, len(ca), len(cb), diff, addr_a % 64, addr_b % 64))
    print(f"A = {args.a}\nB = {args.b}\nfilter '{args.filter}': {len(common)} functions in both, "
          f"{same} identical code (padding ignored) at the same address mod 64, {len(rows)} differ")
    print(f"{'insns_A':>8} {'insns_B':>8} {'differing':>9} {'mod64_A':>7} {'mod64_B':>7}  function")
    for name, na, nb, diff, ma, mb in rows:
        print(f"{na:8d} {nb:8d} {diff:9d} {ma:7d} {mb:7d}  {name}")
    only_a = sorted(set(fa) - set(fb))
    only_b = sorted(set(fb) - set(fa))
    print(f"only in A ({len(only_a)}):")
    for name in only_a:
        print(f"  {name}")
    print(f"only in B ({len(only_b)}):")
    for name in only_b:
        print(f"  {name}")


if __name__ == "__main__":
    main()
