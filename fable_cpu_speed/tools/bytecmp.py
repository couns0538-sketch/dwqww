# bytecmp.py - where do two PE exe files differ, section by section (Python standard library only).
# Used for "flag at 0 = lock code": a build of the patched tree with the flag at 0 must have the same code and
# data bytes as the build of the untouched tree; only the debug record (PDB id and path) may differ.
#   python -I -B bytecmp.py --a A.exe --b B.exe --log L [--label T]
# Verdict: IDENTICAL (same file), CODE-AND-DATA-IDENTICAL (differences only inside .rdata debug-record ranges
# or the PE header), or DIFFERENT (any differing byte in another place). Exit code 0 / 0 / 1.
import argparse
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import uci_common as U  # noqa: E402


def sections(d):
    pe = struct.unpack_from('<I', d, 0x3C)[0]
    nsec = struct.unpack_from('<H', d, pe + 6)[0]
    opt = struct.unpack_from('<H', d, pe + 20)[0]
    magic = struct.unpack_from('<H', d, pe + 24)[0]
    ddir = pe + 24 + (112 if magic == 0x20B else 96)
    dbg_rva, dbg_size = struct.unpack_from('<II', d, ddir + 6 * 8)
    out = []
    off = pe + 24 + opt
    for i in range(nsec):
        name = d[off:off + 8].rstrip(b'\0').decode('ascii', 'replace')
        vsize, vaddr, rsize, rptr = struct.unpack_from('<IIII', d, off + 8)
        out.append((name, vaddr, vsize, rptr, rsize))
        off += 40
    # debug directory entries -> raw ranges of the debug records (CodeView / PDB id and path)
    dbg = []
    for name, vaddr, vsize, rptr, rsize in out:
        if dbg_size and vaddr <= dbg_rva < vaddr + max(vsize, rsize):
            base = rptr + (dbg_rva - vaddr)
            dbg.append((base, base + dbg_size, 'debug directory'))
            for k in range(dbg_size // 28):
                size, _rva, raw = struct.unpack_from('<III', d, base + 28 * k + 16)
                if raw and size:
                    dbg.append((raw, raw + size, 'debug record'))
    return out, dbg, off


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--a', required=True)
    ap.add_argument('--b', required=True)
    ap.add_argument('--log', required=True)
    ap.add_argument('--label', default='')
    a = ap.parse_args()
    U.require_lane()
    da, db = open(a.a, 'rb').read(), open(a.b, 'rb').read()
    L = U.header('BYTECMP %s' % a.label, [os.path.abspath(__file__), U.__file__], [a.a, a.b])
    sa, dbg_a, hdr_end = sections(da)
    sb, dbg_b, _ = sections(db)
    L.append('sections A: ' + ', '.join('%s raw %#x+%#x' % (n, p, s) for n, _, _, p, s in sa))
    L.append('sections B: ' + ', '.join('%s raw %#x+%#x' % (n, p, s) for n, _, _, p, s in sb))
    same_layout = (len(da) == len(db) and [(n, p, s) for n, _, _, p, s in sa] == [(n, p, s) for n, _, _, p, s in sb])
    if da == db:
        verdict = 'IDENTICAL'
    elif not same_layout:
        verdict = 'DIFFERENT'
        L.append('file sizes or section layout differ (%d and %d bytes): the byte ranges cannot be lined up' % (len(da), len(db)))
    else:
        ranges, start = [], None
        for i in range(len(da)):
            if da[i] != db[i]:
                if start is None:
                    start = i
                last = i
            elif start is not None and i - last > 16:
                ranges.append((start, last + 1))
                start = None
        if start is not None:
            ranges.append((start, last + 1))

        # Fixed 16:21: the first version judged a whole merged range at once and did not know the .buildid
        # section, so it called the debug directory plus its record "code or data" (logs bytecmp_*.log without
        # _r2 are superseded). Now every differing byte is judged by itself. In an lld MinGW exe the section
        # .buildid holds only the debug directory and the CodeView record (PDB id, age and path).
        def where_byte(i):
            if i < hdr_end:
                return 'PE header', True
            for x0, x1, what in dbg_a + dbg_b:
                if x0 <= i < x1:
                    return what, True
            for n, _, _, p, s in sa:
                if p <= i < p + s:
                    return 'section ' + n, n == '.buildid'
            return 'outside sections', False

        other = 0
        for lo, hi in ranges:
            kinds, nd, bad = [], 0, 0
            for i in range(lo, hi):
                if da[i] != db[i]:
                    nd += 1
                    what, harmless = where_byte(i)
                    bad += 0 if harmless else 1
                    if what not in kinds:
                        kinds.append(what)
            other += bad
            L.append('differing range %#x..%#x (%d bytes differ): %s%s' % (lo, hi, nd, ' + '.join(kinds), '' if bad == 0 else '  <-- %d bytes of code or data' % bad))
        L.append('differing ranges %d; differing bytes outside debug records and the PE header: %d' % (len(ranges), other))
        verdict = 'CODE-AND-DATA-IDENTICAL' if other == 0 else 'DIFFERENT'
    L.append('VERDICT BYTECMP %s; end %s' % (verdict, U.vienna_now()))
    U.write_log(a.log, L)
    print('\n'.join(L[-8:]))
    return 1 if verdict == 'DIFFERENT' else 0


if __name__ == '__main__':
    sys.exit(main())
