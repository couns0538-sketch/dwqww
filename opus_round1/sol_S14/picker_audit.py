#!/usr/bin/env python3
"""Static audit of the AL1 lock MovePicker: heap allocation and per-construction zeroing (Sol S14).

Read-only. Works on `objdump -d --no-show-raw-insn -C` text of a forge exe that has symbols
(the PC lock exe forge_h256_s198.exe does). Nothing is built or run.

1. Allocation closure: every function whose name contains "MovePicker" (next(), the std::sort
   instantiations for MovePicker::Scored) plus Board::is_pseudo_legal (the only out-of-line call
   of the inlined constructor) is a root. The tool follows every direct call/jmp to another
   function's entry, transitively, and reports any reachable allocation-family call, any
   indirect call, and the callee list.
2. Construction cost: in every function that calls MovePicker::next, it lists the memset calls
   and their constant size (Windows x64: size in r8).

With --exe, every register-indirect jump in the closure must be a bounded switch table whose
entries (read from the exe's .rdata) all land inside the same function, and every memory-indirect
jump/call must be an import thunk to a CRT memory routine (memmove/memcpy/memset).

Usage:
  objdump -d --no-show-raw-insn -C forge_h256_s198.exe > lock_exe.dis
  python -I picker_audit.py lock_exe.dis --exe forge_h256_s198.exe [--json out.json]
"""
from __future__ import annotations

import argparse
import collections
import json
import re
import struct
import sys
from pathlib import Path

ALLOWED_IMPORTS = {"memmove", "memcpy", "memset"}


class PEImage:
    """Minimal PE32+ reader: map a virtual address to file bytes (sections only)."""

    def __init__(self, data: bytes):
        self.data = data
        if data[:2] != b"MZ":
            raise ValueError("not a PE file")
        pe = struct.unpack_from("<I", data, 0x3C)[0]
        if data[pe:pe + 4] != b"PE\0\0":
            raise ValueError("no PE signature")
        nsec, = struct.unpack_from("<H", data, pe + 6)
        opt_size, = struct.unpack_from("<H", data, pe + 20)
        opt = pe + 24
        if struct.unpack_from("<H", data, opt)[0] != 0x20B:
            raise ValueError("not PE32+")
        self.image_base, = struct.unpack_from("<Q", data, opt + 24)
        self.sections = []
        for i in range(nsec):
            off = opt + opt_size + 40 * i
            name = data[off:off + 8].rstrip(b"\0").decode(errors="replace")
            vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", data, off + 8)
            self.sections.append((name, self.image_base + vaddr, max(vsize, rsize), raddr, rsize))

    def read(self, va: int, n: int) -> bytes:
        for _, start, size, raddr, rsize in self.sections:
            if start <= va and va + n <= start + min(size, rsize):
                off = raddr + (va - start)
                return self.data[off:off + n]
        raise ValueError(f"address {va:#x} not in a file-backed section")


def jump_table(insns, k):
    """For a `jmp *%reg` at insns[k], recover (table_va, entries) from the GCC switch pattern
    `cmp $N,..; ja ..; lea DISP(%rip),%rX # VA; movslq (%rX,%rI,4),%rY; add %rX,%rY; jmp *%rY`."""
    table, count = None, None
    for _, prev in reversed(insns[max(0, k - 8):k]):
        if table is None:
            t = re.search(r"lea\s+-?0x[0-9a-f]+\(%rip\),%r\w+\s+#\s+([0-9a-f]+)", prev)
            if t:
                table = int(t.group(1), 16)
        if count is None:
            c = re.match(r"cmp\s+\$0x([0-9a-f]+),%", prev)
            if c:
                count = int(c.group(1), 16) + 1
    return table, count

FUNC_RE = re.compile(r"^([0-9a-f]+) <(.*)>:$")
INSN_RE = re.compile(r"^\s+([0-9a-f]+):\t(.*)$")
DIRECT_RE = re.compile(r"^(call|jmp)\s+([0-9a-f]+) <(.*)>$")
ALLOC_RE = re.compile(
    r"operator new|\bmalloc\b|\bcalloc\b|\brealloc\b|aligned_malloc|aligned_alloc|posix_memalign|"
    r"HeapAlloc|HeapReAlloc|VirtualAlloc|LocalAlloc|GlobalAlloc|_M_realloc|_M_create|_M_default_append|"
    r"__cxa_allocate_exception|__throw_bad_alloc|get_temporary_buffer|std::vector<|basic_string<")
ROOT_EXTRA = ("forge::Board::is_pseudo_legal(forge::Move const&) const",)


def parse(text: str):
    """-> (funcs: name -> list[(addr, insn)], entry: addr -> name)"""
    funcs: dict[str, list] = collections.OrderedDict()
    entry: dict[int, str] = {}
    cur = None
    for line in text.splitlines():
        m = FUNC_RE.match(line)
        if m:
            cur = m.group(2)
            entry[int(m.group(1), 16)] = cur
            funcs.setdefault(cur, [])
            continue
        i = INSN_RE.match(line)
        if cur is not None and i:
            funcs[cur].append((int(i.group(1), 16), i.group(2).split("\t")[-1].strip()))
    return funcs, entry


def edges(name: str, insns, entry):
    """Direct calls/jumps from `name` to the entry of another function, indirect calls, and the rest."""
    direct, indirect = [], []
    for addr, ins in insns:
        m = DIRECT_RE.match(ins)
        if m:
            target = int(m.group(2), 16)
            callee = entry.get(target)
            if callee is not None and callee != name:
                direct.append((addr, m.group(1), callee))
            continue
        if ins.startswith(("call", "jmp")) and "*" in ins.split(None, 1)[-1][:2]:
            indirect.append((addr, ins))
    return direct, indirect


def closure(funcs, entry, roots):
    seen, order = set(), []
    work = [r for r in roots if r in funcs]
    while work:
        f = work.pop()
        if f in seen:
            continue
        seen.add(f)
        order.append(f)
        direct, _ = edges(f, funcs[f], entry)
        work.extend(c for _, _, c in direct if c not in seen)
    return order


def memset_sites(funcs, entry):
    out = []
    for name, insns in funcs.items():
        direct, _ = edges(name, insns, entry)
        if not any("MovePicker::next" in c for _, _, c in direct):
            continue
        for k, (addr, ins) in enumerate(insns):
            m = DIRECT_RE.match(ins)
            if not (m and entry.get(int(m.group(2), 16)) == "memset"):
                continue
            size = None
            for _, prev in reversed(insns[max(0, k - 16):k]):
                s = re.search(r"mov\s+\$0x([0-9a-f]+),%r8", prev)
                if s:
                    size = int(s.group(1), 16)
                    break
            out.append({"function": name, "addr": addr, "size": size})
    return out


def classify_indirect(name, insns, k, ins, pe, funcs_bounds):
    """-> (ok: bool, note: str) for an indirect jump/call at insns[k]."""
    imp = re.search(r"#\s+[0-9a-f]+ <__imp_(\w+)>", ins)
    if imp:
        return imp.group(1) in ALLOWED_IMPORTS, f"import thunk to {imp.group(1)}"
    if re.match(r"jmp\s+\*%r\w+$", ins):
        if pe is None:
            return False, "register-indirect jump (pass --exe to verify the switch table)"
        table, count = jump_table(insns, k)
        if table is None or count is None or count > 4096:
            return False, "register-indirect jump without a recognisable bounded switch table"
        lo, hi = funcs_bounds[name]
        raw = pe.read(table, 4 * count)
        targets = [table + struct.unpack_from("<i", raw, 4 * j)[0] for j in range(count)]
        inside = all(lo <= t < hi for t in targets)
        return inside, (f"switch table at {table:#x}, {count} entries, all targets inside the function"
                        if inside else f"switch table at {table:#x}: a target leaves the function")
    return False, "unclassified indirect transfer"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("disassembly", type=Path)
    ap.add_argument("--exe", type=Path, help="the same exe, to read switch tables from .rdata")
    ap.add_argument("--json", type=Path)
    args = ap.parse_args(argv)
    funcs, entry = parse(args.disassembly.read_text(encoding="utf-8", errors="replace"))
    pe = PEImage(args.exe.read_bytes()) if args.exe else None
    starts = sorted(entry)
    funcs_bounds = {}
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else start + 0x100000
        funcs_bounds[entry[start]] = (start, end)
    roots = [f for f in funcs if "MovePicker" in f] + [f for f in ROOT_EXTRA if f in funcs]
    if not any("MovePicker::next" in f for f in roots):
        print("ERROR: no MovePicker::next symbol (stripped exe?)", file=sys.stderr)
        return 2
    reach = closure(funcs, entry, roots)
    alloc_hits, indirect_hits = [], []
    print(f"functions in disassembly: {len(funcs)}; roots: {len(roots)}; reachable closure: {len(reach)}")
    print("roots:")
    for r in roots:
        print(f"  {r[:150]}")
    print("closure (function: instructions, direct callees):")
    for f in reach:
        direct, indirect = edges(f, funcs[f], entry)
        callees = sorted({c for _, _, c in direct})
        print(f"  {f[:110]}: {len(funcs[f])} insns; callees: {', '.join(c[:60] for c in callees) or '-'}")
        for addr, kind, c in direct:
            if ALLOC_RE.search(c):
                alloc_hits.append({"from": f, "addr": addr, "kind": kind, "callee": c})
        index = {a: j for j, (a, _) in enumerate(funcs[f])}
        for addr, ins in indirect:
            ok, note = classify_indirect(f, funcs[f], index[addr], ins, pe, funcs_bounds)
            indirect_hits.append({"from": f, "addr": addr, "insn": ins, "ok": ok, "note": note})
    for f in reach:
        if ALLOC_RE.search(f):
            alloc_hits.append({"from": "(closure member)", "addr": None, "kind": "member", "callee": f})
    print(f"allocation-family calls reachable from the picker: {len(alloc_hits)}")
    for h in alloc_hits:
        print(f"  {h}")
    print(f"indirect calls/jumps in the closure: {len(indirect_hits)}")
    for h in indirect_hits:
        print(f"  {'ok ' if h['ok'] else 'BAD'} {h['from'][:60]} {h['addr']:x}: {h['insn'][:60]} -> {h['note']}")
    sites = memset_sites(funcs, entry)
    print("memset calls in functions that call MovePicker::next (inlined MovePicker constructors):")
    for s in sites:
        size = f"{s['size']} bytes" if s["size"] is not None else "size not constant"
        print(f"  {s['function'][:70]} {s['addr']:x}: memset {size}")
    verdict = "PASS" if not alloc_hits and all(h["ok"] for h in indirect_hits) else "CHECK"
    print(f"ALLOCATION AUDIT: {verdict} (static, direct-call closure; see REPORT.md for the limits)")
    if args.json:
        args.json.write_text(json.dumps({"roots": roots, "closure": reach, "allocation_calls": alloc_hits,
                                         "indirect_calls": indirect_hits, "memset_sites": sites,
                                         "verdict": verdict}, indent=1) + "\n", encoding="utf-8")
    return 0 if verdict == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
