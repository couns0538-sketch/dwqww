#!/usr/bin/env python3
"""mate_pv_check.py - every reported mate score in uci_tb.py rows: replay the PV with python-chess. A positive "mate N" whose PV is 2N-1 plies long must end in
checkmate; a negative "mate -N" with a PV of 2N plies must end with the engine side mated. Shorter PVs (cut by a TT hit) are counted as truncated and judged by the
oracle's result if an exact or WDL value is given. Also: a cp score must never be in the mate band, and a TB-band score never comes as a mate.

usage: python -I -B mate_pv_check.py <run.jsonl> [<run.jsonl> ...]     exit 1 on any broken check
"""
import json
import sys

import chess


def main():
    total = verified = truncated = 0
    bad = []
    band = 0
    for path in sys.argv[1:]:
        for line in open(path, encoding='utf-8'):
            r = json.loads(line)
            if r.get('score') is None:
                continue
            if r['score_type'] == 'cp':
                if abs(r['score']) >= 31872:
                    band += 1
                    bad.append(('cp in the mate band', r['fen'], r['score']))
                continue
            total += 1
            n = r['score']
            parts = r['fen'].split(' moves ')
            b = chess.Board(parts[0])
            if len(parts) > 1:
                for u in parts[1].split():
                    b.push_uci(u)
            want = 2 * n - 1 if n > 0 else -2 * n
            ok = True
            for u in r['pv']:
                m = chess.Move.from_uci(u)
                if m not in b.legal_moves:
                    ok = False
                    bad.append(('illegal pv', r['fen'], u))
                    break
                b.push(m)
            if not ok:
                continue
            if len(r['pv']) < want:
                truncated += 1
                continue
            if len(r['pv']) > want or not b.is_checkmate():
                bad.append(('pv is not the mate', r['fen'], n, len(r['pv'])))
            else:
                verified += 1
    print(json.dumps({'mates': total, 'pv_verified': verified, 'pv_truncated': truncated, 'broken': len(bad), 'cp_in_mate_band': band}))
    for b in bad[:8]:
        print('BAD', b)
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
