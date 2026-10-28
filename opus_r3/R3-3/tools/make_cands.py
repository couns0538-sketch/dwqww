"""Deterministic srand candidates for the R3-3 gate proposals.

value(id, k) = 300000000 + (first 4 bytes of SHA-256("forge-r3-gates/2026-10-27/<id>/<k>") as big-endian uint32)
               mod 1700000000
This is the PC's own fresh-srand range (common_autonomy.ps1 Fresh-Srand: 300000000 + uint32 % 1700000000).
K candidates per entry; the first candidate that is unused and appears nowhere in the scanned corpus is chosen
(choose_srands.py).

Usage: python -I -B make_cands.py <out_cands.json> <out_map.json> [K]
"""
import hashlib
import json
import sys

IDS = ['R3-%02d' % i for i in range(1, 30)] + ['R3-SPARE-%02d' % i for i in range(1, 7)]


def value(eid, k):
    h = hashlib.sha256(f'forge-r3-gates/2026-10-27/{eid}/{k}'.encode()).digest()
    return 300000000 + int.from_bytes(h[:4], 'big') % 1700000000


def main():
    k_max = int(sys.argv[3]) if len(sys.argv) > 3 else 4
    mp = {eid: [value(eid, k) for k in range(k_max)] for eid in IDS}
    allv = [v for vs in mp.values() for v in vs]
    assert len(set(allv)) == len(allv), 'candidate collision inside the set'
    with open(sys.argv[1], 'w', newline='\n') as fh:
        json.dump(sorted(allv), fh)
    with open(sys.argv[2], 'w', newline='\n') as fh:
        json.dump(mp, fh, indent=1)
    print(f'{len(IDS)} ids x {k_max} candidates = {len(allv)} values')


if __name__ == '__main__':
    main()
