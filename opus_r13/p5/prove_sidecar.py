#!/usr/bin/env python3
"""prove_sidecar.py - R14 A1 (own code): proof that the P5 relabel fix carries the original FEN state through.

  audit   --pos P.pos --fen P.fen --out audit.json [--job1-rows 440000]
          Every row: the sidecar FEN's board + side to move equal the .pos record (forge_pos.aligned_records, fen format),
          the line count equals the .pos row count; counts rows whose original FEN has castling rights, an en-passant square
          or a non-zero halfmove clock (all lost by the reconstruction policy no-castling-no-ep-clocks-0-1), over the whole
          file and over job1's rows 0 .. job1_rows-1.
  compare --old OLD_SHARD_DIR --new NEW_SHARD_DIR --fen P.fen --count N --out compare.json [--start 0]
          Rows start .. start+N-1 relabelled by job1 (reconstructed FENs, old shard) and by the fixed job (original FENs, new
          shard): the new shard's .fen lines must equal the sidecar lines (state carried through, engine echo checked by the
          relabel run itself); control rows (original FEN without castling / ep and with halfmove 0, so the reconstructed FEN
          differs only in the fullmove number) must keep exactly the same label; affected rows are counted with |delta| stats.
Exit 1 on any failed check. Reads only; writes only --out (refuses to overwrite).
"""
import argparse
import json
import statistics
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from forge_pos import PosReader, aligned_records  # noqa: E402


def state(fen):
    f = fen.split()
    return {'castling': f[2] != '-', 'ep': f[3] != '-', 'halfmove': f[4] != '0'}


def write_out(path, obj):
    path = Path(path)
    if path.exists():
        raise SystemExit(f'refusing to overwrite {path}')
    path.write_text(json.dumps(obj, indent=1) + '\n', encoding='utf-8', newline='\n')


def cmd_audit(a):
    keys = ('castling', 'ep', 'halfmove', 'any')
    total = {k: 0 for k in keys}
    job1 = {k: 0 for k in keys}
    rows = 0
    with PosReader(a.pos) as reader:
        for i, (_, fen) in enumerate(aligned_records(reader, a.fen, sidecar_format='fen')):
            s = state(fen)
            s['any'] = s['castling'] or s['ep'] or s['halfmove']
            for k in keys:
                if s[k]:
                    total[k] += 1
                    if i < a.job1_rows:
                        job1[k] += 1
            rows += 1
        n = reader.n
    ok = rows == n
    out = {'pos': str(a.pos), 'fen': str(a.fen), 'rows_checked': rows, 'pos_rows': n,
           'board_stm_match_all_rows': ok, 'with_state_lost_by_reconstruction': total,
           'job1_rows': a.job1_rows, 'job1_rows_with_state_lost': job1, 'result': 'PASS' if ok else 'FAIL'}
    write_out(a.out, out)
    print(json.dumps(out))
    return 0 if ok else 1


def shard_files(d):
    d = Path(d)
    pos = sorted(d.glob('*.pos'))
    fen = sorted(d.glob('*.fen'))
    if len(pos) != 1 or len(fen) != 1:
        raise SystemExit(f'{d}: expected one .pos and one .fen output, found {len(pos)} / {len(fen)}')
    return pos[0], fen[0]


def cmd_compare(a):
    old_pos, old_fen = shard_files(a.old)
    new_pos, new_fen = shard_files(a.new)
    with open(a.fen, encoding='utf-8') as f:
        side = [next(f).strip() for _ in range(a.start + a.count)][a.start:]
    old_fens = Path(old_fen).read_text(encoding='utf-8').splitlines()[:a.count]
    new_fens = Path(new_fen).read_text(encoding='utf-8').splitlines()[:a.count]
    fails = []
    if len(new_fens) != a.count or len(old_fens) != a.count:
        fails.append(f'line counts old {len(old_fens)} new {len(new_fens)} want {a.count}')
    carried = sum(' '.join(x.split()) == ' '.join(y.split()) for x, y in zip(new_fens, side))
    if carried != a.count:
        fails.append(f'new .fen equals the sidecar on {carried}/{a.count} rows')
    ctrl_same = ctrl = 0
    groups = {'castling': [], 'ep': [], 'halfmove': []}
    affected, changed, deltas = 0, 0, []
    with PosReader(old_pos) as ro, PosReader(new_pos) as rn:
        if ro.n < a.count or rn.n < a.count:
            fails.append(f'.pos rows old {ro.n} new {rn.n} < {a.count}')
        for i in range(min(a.count, ro.n, rn.n)):
            o, n = ro.row(i), rn.row(i)
            if (o.board, o.meta) != (n.board, n.meta):
                fails.append(f'row {i}: board/meta differ between old and new output')
                break
            s = state(side[i])
            d = n.score - o.score
            if not any(s.values()):
                ctrl += 1
                ctrl_same += d == 0
                continue
            affected += 1
            changed += d != 0
            deltas.append(abs(d))
            for k, v in s.items():
                if v:
                    groups[k].append(abs(d))
    if ctrl_same != ctrl:
        fails.append(f'control rows with a changed label: {ctrl - ctrl_same} of {ctrl}')
    stat = lambda xs: {'rows': len(xs), 'changed': sum(x != 0 for x in xs),
                       'mean_abs_delta': round(statistics.fmean(xs), 2) if xs else None,
                       'median_abs_delta': statistics.median(xs) if xs else None, 'max_abs_delta': max(xs, default=None)}
    out = {'rows': a.count, 'start': a.start, 'old_shard': str(a.old), 'new_shard': str(a.new),
           'new_fen_equals_sidecar': carried, 'old_fen_has_castling_or_ep': sum(any(state(x)[k] for k in ('castling', 'ep')) for x in old_fens),
           'control_rows': ctrl, 'control_rows_same_label': ctrl_same, 'affected_rows': affected, 'affected_rows_changed': changed,
           'affected_abs_delta': stat(deltas), 'by_state': {k: stat(v) for k, v in groups.items()},
           'failures': fails, 'result': 'FAIL' if fails else 'PASS'}
    write_out(a.out, out)
    print(json.dumps(out))
    return 1 if fails else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    p = sub.add_parser('audit')
    p.add_argument('--pos', required=True); p.add_argument('--fen', required=True); p.add_argument('--out', required=True)
    p.add_argument('--job1-rows', type=int, default=440000)
    p = sub.add_parser('compare')
    p.add_argument('--old', required=True); p.add_argument('--new', required=True); p.add_argument('--fen', required=True)
    p.add_argument('--count', type=int, required=True); p.add_argument('--start', type=int, default=0)
    p.add_argument('--out', required=True)
    a = ap.parse_args()
    return cmd_audit(a) if a.cmd == 'audit' else cmd_compare(a)


if __name__ == '__main__':
    sys.exit(main())
