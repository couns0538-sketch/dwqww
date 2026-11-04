#!/usr/bin/env python3
"""opus_guardband.py - guard-band split of the jobA rows (R14 finish Job 3, Opus; own code; plan sep/GUARD_BAND_PLAN.md).

Builds a contiguous split of the 999,921 pinned jobA rows: a train prefix and a validation suffix near 1 %, cut only
at an observed UNREACHABLE adjacent-row link (never inside a run of REACHABLE / UNKNOWN links = a conservative
component). Then drops, each with its row id and reason:
  guard_left / guard_right   rows within K plies of the cut endpoints, measured with absolute ply inside the two
                             adjacent components (their plies must increase strictly, else fail closed)
  holdout_board_stm          rows whose board+side-to-move key is a shared key with holdouts 013/014 (the complete
                             Job 2 listing; a raw or EP-normalised 4-field match implies a board+stm match)
  val_board_stm              train rows whose board+stm key also occurs in the retained validation rows
  mate_score                 |relabelled score| >= 30000 (excluded from the export, Job 3 step 6)
Writes (refuses an existing --out): SPLIT.json (inputs with md5, cut, components, guards, counts, WDL and score
histograms per split) and DROPPED.tsv (row_id, source, line, side, reasons). It writes NO training payload; the
candidate rows are written by --stage-dir (outside D:/a14 for size) for the proof step.

  opus_guardband.py --out D:/a14/sep/guardband01 --shared D:/a14/sep/boardstm-probe01/SHARED.jsonl
                    [--stage-dir C:/a14x/guardband01_stage] [--k 8] [--val-fraction 0.01]
"""
import argparse
import bisect
import collections
import datetime
import hashlib
import json
import os
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r14_scan import guard_selection  # noqa: E402  (Astra's reviewed guard utility)

ROWS = Path('D:/o14b/r2/proof/jobA/rows.tsv')
ROWS_MD5 = '57a6742279339282763dff17e97670ce'
LABELS = Path('D:/o14b/r2/proof/jobA/final/labels.tsv')
LABELS_MD5 = '2614e82d55bc5e9572c24d3900a8810a'
MAP_REPORT = Path('D:/a14/sep/segments-joba01/REPORT.json')
MAP_REPORT_MD5 = '77b76a460e569e50196da08f083e95d4'
REACHABLE, UNREACHABLE = {0}, {1, 2, 3}
UNKNOWN = {4, 5, 6, 7, 8, 250, 251}
MATE = 30000


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 22), b''):
            h.update(block)
    return h.hexdigest()


def pinned(path, expected):
    actual = md5(path)
    if actual != expected:
        raise ValueError(f'input md5 mismatch: {path} {actual} != {expected}')
    return dict(path=str(path), md5=actual, bytes=os.path.getsize(path))


def ply_of(fen):
    f = fen.split()
    return 2 * (int(f[5]) - 1) + (f[1] == 'b')


def key_of(fen):
    f = fen.split()
    return f[0] + ' ' + f[1]


def load_rows():
    rows = []
    with open(ROWS, encoding='ascii') as stream:
        header = stream.readline().rstrip('\n').split('\t')
        if header != ['row_id', 'game_id', 'split', 'fen', 'old_score_stm', 'result', 'source', 'source_row']:
            raise ValueError(f'unexpected rows.tsv header {header}')
        for i, line in enumerate(stream):
            f = line.rstrip('\n').split('\t')
            if int(f[0]) != i:
                raise ValueError(f'row_id {f[0]} at position {i}')
            rows.append((f[3], int(f[6]), int(f[7]), f[2], f[1], f[5], int(f[4])))
    return rows   # (fen, source, line, original_split, inferred_group, result, old_score)


def load_labels(rows):
    scores = []
    with open(LABELS, encoding='ascii') as stream:
        header = stream.readline().rstrip('\n').split('\t')
        if header[:7] != ['row_id', 'game_id', 'split', 'fen', 'score_stm', 'old_score_stm', 'result']:
            raise ValueError(f'unexpected labels.tsv header {header}')
        for i, line in enumerate(stream):
            f = line.rstrip('\n').split('\t')
            if int(f[0]) != i or f[3] != rows[i][0] or f[6] != rows[i][5]:
                raise ValueError(f'labels row {i} does not match rows.tsv')
            scores.append(int(f[4]))
    if len(scores) != len(rows):
        raise ValueError('labels.tsv row count differs from rows.tsv')
    return scores


def load_codes(report):
    """code[source][line] = outcome code of the link (line-1 -> line); from the pinned pairs maps."""
    codes = {}
    for art in report['artifacts']:
        if art['kind'] != 'pairs':
            continue
        path = Path(art['path'])
        if md5(path) != art['md5']:
            raise ValueError(f'map md5 mismatch: {path}')
        data = path.read_bytes()
        if len(data) != 9 * art['records']:
            raise ValueError(f'map size mismatch: {path}')
        arr = bytearray(art['records'] + 1)
        for n, (line, code, _) in enumerate(struct.iter_unpack('<IBI', data), 1):
            if line != n:
                raise ValueError(f'map {path} record {n} names line {line}')
            arr[line] = code
        codes[art['source_id']] = arr
    return codes


def wdl_and_hist(indices, rows, scores):
    wdl = collections.Counter(rows[i][5] for i in indices)
    edges = [-30000, -2000, -1000, -500, -300, -200, -100, -50, -20, 0, 20, 50, 100, 200, 300, 500, 1000, 2000, 30000]
    hist = collections.Counter()
    for i in indices:
        s = scores[i]
        b = bisect.bisect_right(edges, s) - 1
        lo = edges[b] if b >= 0 else None
        hi = edges[b + 1] if 0 <= b + 1 < len(edges) else None
        hist[f'[{lo},{hi})'] += 1
    return dict(white_result_counts=dict(sorted(wdl.items())), score_stm_histogram=dict(hist))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--shared', required=True, type=Path, help='SHARED.jsonl of the board+stm probe (complete listing)')
    ap.add_argument('--shared-md5', required=True)
    ap.add_argument('--stage-dir', type=Path)
    ap.add_argument('--k', type=int, default=8)
    ap.add_argument('--val-fraction', type=float, default=0.01)
    a = ap.parse_args()
    if a.k < 8:
        sys.exit('K must be at least 8')
    out = a.out.resolve()
    if not str(out).casefold().startswith('d:\\a14\\'):
        sys.exit('refusing: --out must be below D:/a14')
    started = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' Vienna'
    inputs = dict(rows=pinned(ROWS, ROWS_MD5), labels=pinned(LABELS, LABELS_MD5),
                  map_report=pinned(MAP_REPORT, MAP_REPORT_MD5), shared=pinned(a.shared, a.shared_md5))
    report = json.load(open(MAP_REPORT, encoding='utf-8'))
    rows = load_rows()
    scores = load_labels(rows)
    codes = load_codes(report)
    n = len(rows)
    # Global order must be the source order without gaps: source 0 lines 1.., then source 1 lines 1..
    expected = [(0, line) for line in range(1, 466507)] + [(1, line) for line in range(1, n - 466506 + 1)]
    if [(r[1], r[2]) for r in rows] != expected:
        raise ValueError('jobA rows are not the contiguous source order the chain map describes')
    cross = report['cross_file_adjacent_pairs']
    if len(cross) != 1 or (cross[0]['left_source'], cross[0]['right_source'], cross[0]['right_line']) != (0, 1, 1):
        raise ValueError('unexpected cross-file pair list')
    link = bytearray(n)   # link[i] = code of the link (i-1 -> i); link[0] = scope start
    for i, (_, src, line, *_rest) in enumerate(rows):
        link[i] = codes[src][line] if not (src == 1 and line == 1) else cross[0]['code']
    starts = [i for i in range(n) if i == 0 or link[i] in UNREACHABLE]   # conservative component starts
    target = round(n * a.val_fraction)
    cut = min((c for c in starts if c > 0), key=lambda c: (abs((n - c) - target), c))
    ci = starts.index(cut)
    left = range(starts[ci - 1], cut)
    right = range(cut, starts[ci + 1] if ci + 1 < len(starts) else n)
    plies = {i: ply_of(rows[i][0]) for i in list(left) + list(right)}
    for comp, name in ((left, 'left'), (right, 'right')):
        seq = [plies[i] for i in comp]
        if any(b <= x for x, b in zip(seq, seq[1:])):
            raise ValueError(f'{name} guard component plies do not increase strictly (fail closed)')
    # Astra's guard utility; row ids must be positive, so pass index + 1.
    kept, dropped = guard_selection([(i + 1, plies[i]) for i in list(left) + list(right)], boundary=cut, k=a.k)
    guard_drop = {r - 1 for r in dropped}
    left_exhausted = all(i in guard_drop for i in left)
    right_exhausted = all(i in guard_drop for i in right)
    reasons = collections.defaultdict(list)
    for i in guard_drop:
        reasons[i].append('guard_left' if i < cut else 'guard_right')
    shared_keys = set()
    with open(a.shared, encoding='utf-8') as stream:
        for line in stream:
            shared_keys.add(json.loads(line)['key'])
    for i, r in enumerate(rows):
        if key_of(r[0]) in shared_keys:
            reasons[i].append('holdout_board_stm')
        if abs(scores[i]) >= MATE:
            reasons[i].append('mate_score')
    val_keys = {key_of(rows[i][0]) for i in range(cut, n) if not reasons[i]}   # retained validation rows only
    for i in range(cut):
        if not reasons[i] and key_of(rows[i][0]) in val_keys:
            reasons[i].append('val_board_stm')
    train = [i for i in range(cut) if not reasons[i]]
    val = [i for i in range(cut, n) if not reasons[i]]
    if not train or not val:
        raise ValueError('a split is empty')
    by_reason = collections.Counter()
    for i, rs in reasons.items():
        for r in rs:
            by_reason[(r, 'train' if i < cut else 'val')] += 1
    out.mkdir(parents=True, exist_ok=False)
    with open(out / 'DROPPED.tsv', 'w', encoding='ascii', newline='\n') as stream:
        stream.write('row_id\tsource_file\tline\tside\treasons\n')
        for i in sorted(i for i in reasons if reasons[i]):
            src, line = rows[i][1], rows[i][2]
            stream.write(f"{i}\tforge_selfplay_{src + 1:03d}.txt\t{line}\t{'train' if i < cut else 'val'}\t"
                         f"{','.join(reasons[i])}\n")
    staged = {}
    if a.stage_dir:
        stage = a.stage_dir.resolve()
        stage.mkdir(parents=True, exist_ok=False)
        for name, idx in (('train', train), ('val', val)):
            with open(stage / f'{name}.txt', 'w', encoding='ascii', newline='\n') as data, \
                    open(stage / f'{name}.rowids', 'w', encoding='ascii', newline='\n') as ids:
                for i in idx:
                    data.write(f'{rows[i][0]} | {scores[i]} | {rows[i][5]}\n')
                    ids.write(f'{i}\n')
            staged[name] = {kind: dict(path=str(stage / f'{name}.{kind}'), md5=md5(stage / f'{name}.{kind}'),
                                       bytes=os.path.getsize(stage / f'{name}.{kind}')) for kind in ('txt', 'rowids')}
    cut_src, cut_line = rows[cut][1], rows[cut][2]
    record = dict(
        schema=1, tool='opus_guardband.py', tool_md5=md5(__file__), start_vienna=started,
        plan='D:/a14/sep/GUARD_BAND_PLAN.md', k=a.k, val_fraction=a.val_fraction, inputs=inputs,
        rows=n, components=len(starts), val_target_rows=target,
        cut=dict(row_id=cut, source_file=f'forge_selfplay_{cut_src + 1:03d}.txt', line=cut_line,
                 link_code=link[cut], link_reason=report['code_table'][str(link[cut])]['reason'],
                 link_status=report['code_table'][str(link[cut])]['status'],
                 left_endpoint=dict(row_id=cut - 1, ply=plies[cut - 1]),
                 right_endpoint=dict(row_id=cut, ply=plies[cut])),
        left_component=dict(first_row_id=left[0], last_row_id=left[-1], rows=len(left), exhausted=left_exhausted),
        right_component=dict(first_row_id=right[0], last_row_id=right[-1], rows=len(right), exhausted=right_exhausted),
        guard_rows=dict(left=sorted(i for i in guard_drop if i < cut), right=sorted(i for i in guard_drop if i >= cut)),
        retained=dict(train=len(train), val=len(val)),
        dropped_by_reason={f'{r}/{s}': c for (r, s), c in sorted(by_reason.items())},
        dropped_rows_total=sum(1 for i in reasons if reasons[i]),
        dropped_listing=dict(path=str(out / 'DROPPED.tsv'), md5=md5(out / 'DROPPED.tsv')),
        stats=dict(train=wdl_and_hist(train, rows, scores), val=wdl_and_hist(val, rows, scores)),
        staged=staged,
        authentic_game_ids='UNVERIFIED',
        scope=('Scoped split construction only: the cut is an observed UNREACHABLE adjacent-row link between '
               'conservative components; no claim about interleaving, omitted continuations, nonadjacent relations '
               'or authentic original game identity (sep/GUARD_BAND_PLAN.md).'),
        end_vienna=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' Vienna')
    with open(out / 'SPLIT.json', 'x', encoding='utf-8', newline='\n') as stream:
        json.dump(record, stream, indent=1)
    print(json.dumps(dict(cut=record['cut'], retained=record['retained'], dropped=record['dropped_by_reason'],
                          left=record['left_component'], right=record['right_component'])))
    return 0


if __name__ == '__main__':
    sys.exit(main())
