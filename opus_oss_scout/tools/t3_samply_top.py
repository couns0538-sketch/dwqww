#!/usr/bin/env python3
"""t3_samply_top.py - OSS scout T3: self-time hotspot table of one process from a samply profile (Firefox Profiler
processed format, e.g. `samply import trace.etl`), symbolized with llvm-symbolizer and the program's PDB.

usage: python -I -B t3_samply_top.py <profile.json.gz> --process <exe name> --exe <exe path> --pdb <pdb path>
         --symbolizer <llvm-symbolizer.exe> [--image-base 0x140000000] [--top 30] [--out table.md]
Every sample of every thread of --process counts 1 (the profile's sampling interval). The leaf frame gets the self
sample. Addresses of the program's own module are frame addresses relative to the module (RVA). The tool symbolizes
VA = image base + RVA with llvm-symbolizer --obj <exe> --pdb <pdb> (inlined frames: innermost first). Prints:
  - samples per module (the program, ntdll, kernel, ...);
  - top functions by self samples, by the OUTERMOST function at the address (the physical function after inlining)
    and by the INNERMOST inlined function (closer to the source function);
  - inclusive samples per outermost function (counted once per sample).
Stdlib only.
"""
import argparse
import collections
import gzip
import json
import subprocess
import sys


def load(path):
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        return json.load(f)


def symbolize(symbolizer, exe, pdb, base, rvas):
    """Map each RVA to (innermost, outermost) function names."""
    addrs = sorted(rvas)
    inp = ''.join(f'0x{base + r:x}\n' for r in addrs)
    cmd = [symbolizer, f'--obj={exe}', '--demangle'] + ([f'--pdb={pdb}'] if pdb else [])
    r = subprocess.run(cmd, input=inp, capture_output=True, text=True, encoding='utf-8', errors='replace')
    blocks = r.stdout.replace('\r\n', '\n').split('\n\n')
    out = {}
    for rva, block in zip(addrs, blocks):
        lines = [l for l in block.split('\n') if l.strip()]
        funcs = lines[0::2] if lines else ['??']
        out[rva] = (funcs[0] if funcs else '??', funcs[-1] if funcs else '??')
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument('profile')
    ap.add_argument('--process', required=True)
    ap.add_argument('--exe', required=True)
    ap.add_argument('--pdb', default='', help='PDB of the program (omit for a MinGW exe: COFF symbols / DWARF)')
    ap.add_argument('--symbolizer', required=True)
    ap.add_argument('--image-base', default='0x140000000')
    ap.add_argument('--top', type=int, default=30)
    ap.add_argument('--out')
    a = ap.parse_args(argv)
    base = int(a.image_base, 16)
    d = load(a.profile)
    libs = d['libs']
    total = 0
    by_lib = collections.Counter()
    self_rva = collections.Counter()
    incl_samples = []  # per sample: set of RVAs of the program's module on the stack
    target_lib_names = {a.process.lower()}
    nthreads = 0
    for t in d['threads']:
        if t.get('processName', '').lower() != a.process.lower():
            continue
        nthreads += 1
        st, ft, fu, rt = t['stackTable'], t['frameTable'], t['funcTable'], t['resourceTable']
        samples = t['samples']
        for s in samples['stack']:
            if s is None:
                continue
            total += 1
            leaf = True
            stack_rvas = set()
            node = s
            while node is not None:
                fr = st['frame'][node]
                func = ft['func'][fr]
                res = fu['resource'][func]
                lib = rt['lib'][res] if res is not None and res >= 0 else None
                lname = libs[lib]['name'] if lib is not None else '(no module)'
                addr = ft['address'][fr]
                if leaf:
                    by_lib[lname] += 1
                    if lname.lower() in target_lib_names and addr is not None and addr >= 0:
                        self_rva[addr] += 1
                    leaf = False
                if lname.lower() in target_lib_names and addr is not None and addr >= 0:
                    stack_rvas.add(addr)
                node = st['prefix'][node]
            incl_samples.append(stack_rvas)
    if total == 0:
        sys.exit(f'no samples for process {a.process} ({nthreads} threads)')
    all_rvas = set(self_rva)
    for sset in incl_samples:
        all_rvas |= sset
    names = symbolize(a.symbolizer, a.exe, a.pdb, base, all_rvas)
    self_inner, self_outer = collections.Counter(), collections.Counter()
    for rva, n in self_rva.items():
        inner, outer = names.get(rva, ('??', '??'))
        self_inner[inner] += n
        self_outer[outer] += n
    incl_outer = collections.Counter()
    for sset in incl_samples:
        for f in {names.get(r, ('??', '??'))[1] for r in sset}:
            incl_outer[f] += 1
    lines = []
    lines.append(f'process {a.process}: {nthreads} threads, {total} samples (interval {d["meta"].get("interval")} ms)')
    lines.append('')
    lines.append('| Module | Self samples | % |')
    lines.append('|---|---|---|')
    for lname, n in by_lib.most_common(8):
        lines.append(f'| {lname} | {n} | {100.0 * n / total:.1f} |')

    def short(name, width=110):
        name = name.replace('|', '/')
        return name if len(name) <= width else name[:width - 3] + '...'

    for title, ctr in (('Self samples by innermost (inlined) function', self_inner),
                       ('Self samples by outermost (physical) function', self_outer),
                       ('Inclusive samples by outermost function', incl_outer)):
        lines.append('')
        lines.append(f'### {title} (top {a.top})')
        lines.append('')
        lines.append('| # | Function | Samples | % of process |')
        lines.append('|---|---|---|---|')
        for i, (f, n) in enumerate(ctr.most_common(a.top), 1):
            lines.append(f'| {i} | `{short(f)}` | {n} | {100.0 * n / total:.1f} |')
    text = '\n'.join(lines) + '\n'
    sys.stdout.write(text)
    if a.out:
        with open(a.out, 'w', encoding='utf-8', newline='\n') as f:
            f.write(text)


if __name__ == '__main__':
    main(sys.argv[1:])
