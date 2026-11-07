#!/usr/bin/env python3
"""t5_compare.py - OSS scout trial T5: Forge's own Syzygy prober (R13 P6 tb_probe) vs Fathom (MIT), per FEN.

usage: python -I -B t5_compare.py <fens> <forge tb_probe output> <fathom batch output> [--show 20] [--json out.json]
Forge lines: "<wdl> <dtz> <rounded>" or "NA". Fathom lines: "<wdl> <dtz> <ok|mate|stalemate|failed>".
WDL must agree exactly (-2..2). DTZ is compared on Fathom "ok" rows: exact, or within 1 when Forge marks its DTZ as
rounded (DTZ tables store some values halved). Mate / stalemate rows are counted separately (Fathom's root probe
reports them as special results; their WDL still has to agree). Prints counts and the first --show mismatches.
"""
import json
import sys


def main(argv):
    if len(argv) < 3:
        sys.exit(__doc__)
    fens_p, forge_p, fathom_p = argv[:3]
    show, out = 20, None
    if '--show' in argv:
        show = int(argv[argv.index('--show') + 1])
    if '--json' in argv:
        out = argv[argv.index('--json') + 1]
    fens = [l.rstrip('\n') for l in open(fens_p, encoding='ascii')]
    fo = [l.split() for l in open(forge_p, encoding='ascii')]
    fa = [l.split() for l in open(fathom_p, encoding='ascii')]
    if not (len(fens) == len(fo) == len(fa)):
        sys.exit(f'length mismatch: fens {len(fens)} forge {len(fo)} fathom {len(fa)}')
    c = dict(n=len(fens), forge_na=0, fathom_failed=0, wdl_equal=0, wdl_diff=0, dtz_rows=0, dtz_exact=0,
             dtz_rounded_ok=0, dtz_diff=0, mate=0, stalemate=0)
    bad = []
    for i, (fen, a, b) in enumerate(zip(fens, fo, fa)):
        if a[0] == 'NA':
            c['forge_na'] += 1
            bad.append((i, fen, 'forge NA', a, b))
            continue
        if b[2] == 'failed' or b[0] == '99':
            c['fathom_failed'] += 1
            bad.append((i, fen, 'fathom failed', a, b))
            continue
        fw, fd, fr = int(a[0]), int(a[1]), a[2] == '1'
        tw = int(b[0])
        if fw == tw:
            c['wdl_equal'] += 1
        else:
            c['wdl_diff'] += 1
            bad.append((i, fen, 'WDL differs', a, b))
        if b[2] in ('mate', 'stalemate'):
            c[b[2]] += 1
            continue
        td = int(b[1])
        c['dtz_rows'] += 1
        if fd == td:
            c['dtz_exact'] += 1
        elif fr and abs(fd - td) <= 1 and (fd > 0) == (td > 0):
            c['dtz_rounded_ok'] += 1
        else:
            c['dtz_diff'] += 1
            bad.append((i, fen, 'DTZ differs', a, b))
    for k, v in c.items():
        print(f'{k:16s} {v}')
    for i, fen, why, a, b in bad[:show]:
        print(f'  line {i + 1}: {why}: {fen} | forge {" ".join(a)} | fathom {" ".join(b)}')
    verdict = 'AGREE' if c['wdl_diff'] == 0 and c['dtz_diff'] == 0 and c['forge_na'] == 0 and c['fathom_failed'] == 0 else 'DIFFER'
    print('VERDICT', verdict)
    if out:
        with open(out, 'w', encoding='utf-8', newline='\n') as f:
            json.dump({'counts': c, 'verdict': verdict, 'first_mismatches': bad[:show]}, f, indent=1)
    return 0 if verdict == 'AGREE' else 1


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
