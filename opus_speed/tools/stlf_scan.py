"""stlf_scan.py - find likely store-to-load-forwarding failures in hot functions (speed hunt, own analysis script).

usage: python -I -B stlf_scan.py <exe> <addresses.tsv> <start hex> <end hex> [<start> <end> ...]
A load from [rsp+C] (no index) of size L that overlaps the most recent store into that range (within a 200-instruction
linear window) but is NOT contained in it (narrow store, wide load) is flagged; indexed stores [rsp+reg+C] count as
writing [C, C+8) somewhere. Each flag is weighted by the samples on the next two instructions (where a stall lands).
Linear order only (no control flow): a heuristic list for reading the code, not a proof.
"""
import re
import subprocess
import sys

SIZES = {'BYTE': 1, 'WORD': 2, 'DWORD': 4, 'QWORD': 8, 'XMMWORD': 16, 'YMMWORD': 32, 'ZMMWORD': 64}
MEM = re.compile(r'(BYTE|WORD|DWORD|QWORD|XMMWORD|YMMWORD|ZMMWORD) PTR \[rsp(?:\+(r\w+)\*\d)?(?:\+(0x[0-9a-f]+))?\]')
LINE = re.compile(r'^\s*([0-9a-f]+):\s+(\S+)\s*(.*)$')


def main():
    exe, tsv = sys.argv[1], sys.argv[2]
    ranges = [(int(sys.argv[i], 16), int(sys.argv[i + 1], 16)) for i in range(3, len(sys.argv), 2)]
    samples = {}
    for line in open(tsv, encoding='utf-8').read().splitlines()[1:]:
        v, c = line.split('\t')
        samples[int(v, 16)] = int(c)
    flags = []
    for lo, hi in ranges:
        out = subprocess.run(['C:/msys64/ucrt64/bin/objdump.exe', '-d', '-M', 'intel', '--no-show-raw-insn',
                              '--start-address=0x%x' % lo, '--stop-address=0x%x' % hi, exe],
                             capture_output=True, text=True).stdout
        ins = []
        for line in out.splitlines():
            m = LINE.match(line)
            if m:
                ins.append((int(m.group(1), 16), m.group(2), m.group(3)))
        stores = []   # (index in ins, off, size, indexed)
        for k, (addr, mn, ops) in enumerate(ins):
            mm = MEM.search(ops)
            if not mm:
                continue
            size = SIZES[mm.group(1)]
            off = int(mm.group(3), 16) if mm.group(3) else 0
            indexed = mm.group(2) is not None
            first = ops.split(',')[0]
            is_store = MEM.search(first) is not None and not mn.startswith(('cmp', 'test', 'bt', 'prefetch'))
            if is_store:
                stores.append((k, off, 8 if indexed else size, indexed))
                continue
            if indexed or mn.startswith(('lea', 'prefetch')):
                continue
            lo_l, hi_l = off, off + size
            for (j, so, ss, sidx) in reversed(stores):
                if k - j > 200:
                    break
                if so < hi_l and lo_l < so + ss:          # overlap
                    if not (so <= lo_l and hi_l <= so + ss):  # not contained -> forwarding fails
                        w = sum(samples.get(ins[q][0], 0) for q in range(k + 1, min(k + 3, len(ins))))
                        flags.append((w, addr, mn, ops.strip(), ins[j][0], ins[j][1], ins[j][2].strip(), sidx))
                    break
    flags.sort(key=lambda f: -f[0])
    for w, addr, mn, ops, saddr, smn, sops, sidx in flags[:40]:
        print('%5d samples  load %x %s %s   <- store %x %s %s%s' % (w, addr, mn, ops[:60], saddr, smn, sops[:50],
                                                                 '  (indexed)' if sidx else ''))
    print('%d flags in total' % len(flags))


if __name__ == '__main__':
    main()
