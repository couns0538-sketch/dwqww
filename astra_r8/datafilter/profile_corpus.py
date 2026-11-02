"""Bounded-memory descriptive audit of closed Forge self-play sources. UNPROVEN.

Every inspected data row gets an independent full-board check. This produces
statistics and small audit samples, never training inputs or a readiness claim.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import time

import chess

from resource_policy import storage_guard

OUTCOMES = {'0': -1, '0.0': -1, '0.5': 0, '1': 1, '1.0': 1,
            '?': None, '*': None, '': None}
HOLDOUTS = {'forge_selfplay_013.txt', 'forge_selfplay_014.txt'}


def low_priority():
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        kernel.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        if not kernel.SetPriorityClass(kernel.GetCurrentProcess(), 0x4000):
            raise OSError('cannot set BelowNormal priority')
    else:
        os.nice(10)


def sha256(path):
    value = hashlib.sha256()
    with Path(path).open('rb') as fh:
        for block in iter(lambda: fh.read(1024*1024), b''):
            value.update(block)
    return value.hexdigest()


def stat_key(path):
    value = Path(path).stat()
    return [value.st_dev, value.st_ino, value.st_size, value.st_mtime_ns, value.st_ctime_ns]


def freeze_plan(paths):
    sources = []
    seen = set()
    for supplied in paths:
        path = Path(supplied).resolve()
        if path.name.lower() in HOLDOUTS:
            raise ValueError('holdout is not a training-source profile input')
        if path in seen:
            raise ValueError('duplicate source')
        seen.add(path)
        sidecar = Path(str(path) + '.md5')
        content = sidecar.read_bytes()
        match = re.fullmatch(rb'([0-9A-Fa-f]{32})[ \t]+\*?([^\r\n]+)\s*', content)
        if not match or match[2].decode('utf-8').strip() != path.name:
            raise ValueError(f'invalid producer sidecar: {sidecar}')
        sources.append(dict(path=str(path), expected_md5=match[1].decode().lower(),
                            identity=stat_key(path), sidecar=str(sidecar),
                            sidecar_sha256=hashlib.sha256(content).hexdigest()))
    if not sources:
        raise ValueError('at least one closed source is required')
    return dict(schema=1, sources=sources, holdouts_excluded=sorted(HOLDOUTS),
                purpose='descriptive audit only; no training data emitted')


def bin_name(value, limits):
    for limit in limits:
        if value <= limit:
            return '<=' + str(limit)
    return '>' + str(limits[-1])


def correlation(moments):
    n, sx, sy, sxx, syy, sxy = moments
    variance = (n*sxx-sx*sx)*(n*syy-sy*sy)
    return (n*sxy-sx*sy)/math.sqrt(variance) if n > 1 and variance > 0 else None


def decode_row(line):
    fields = [part.strip() for part in line.split('|')]
    if len(fields) != 3:
        raise ValueError('expected three source fields')
    fen, score, token = fields
    parts = fen.split()
    if len(parts) != 6 or int(parts[5]) < 1:
        raise ValueError('complete original FEN required')
    if not re.fullmatch(r'[+-]?\d+', score) or token not in OUTCOMES:
        raise ValueError('invalid score or outcome')
    board = chess.Board(fen)
    if not board.is_valid():
        raise ValueError('invalid board')
    white = OUTCOMES[token]
    stm = None if white is None else white * (1 if board.turn else -1)
    return fen, board, int(score), white, stm


def inspect_source(item, *, max_rows=None, mirror_stride=4096, sample_rows=128, seed=5108):
    path = Path(item['path'])
    if stat_key(path) != item['identity']:
        raise ValueError(f'source identity changed: {path}')
    if sha256(item['sidecar']) != item['sidecar_sha256']:
        raise ValueError(f'producer sidecar changed: {path}')
    start = time.perf_counter()
    counts = Counter()
    histograms = {name: Counter() for name in ('result_white', 'result_stm', 'turn',
                 'absolute_cp', 'ply', 'pieces', 'score_result')}
    moments = [0]*6
    examples, sample = [], []
    rng = random.Random(seed)
    sha, md5 = hashlib.sha256(), hashlib.md5()
    complete = True
    last_source_row = 0
    with path.open('rb') as fh:
        for source_row, raw in enumerate(fh, 1):
            sha.update(raw)
            md5.update(raw)
            if max_rows is not None and counts['data_rows'] >= max_rows:
                complete = False
                # Hash the rest, without claiming it was decoded or inspected.
                for block in iter(lambda: fh.read(1024*1024), b''):
                    sha.update(block)
                    md5.update(block)
                break
            counted = False
            try:
                line = raw.decode('utf-8-sig' if source_row == 1 else 'utf-8')
                if not line.strip() or line.lstrip().startswith('#'):
                    counts['comment_or_blank_lines'] += 1
                    continue
                counts['data_rows'] += 1
                counted = True
                last_source_row = source_row
                fen, board, score, white, result = decode_row(line)
            except (ValueError, UnicodeError) as exc:
                if not counted:
                    counts['data_rows'] += 1
                    last_source_row = source_row
                counts['invalid_rows'] += 1
                if len(examples) < 32:
                    examples.append(dict(source_row=source_row, error=str(exc)[:512],
                                         raw_prefix_hex=raw[:128].hex()))
                continue
            counts['valid_rows'] += 1
            ply = 2*(board.fullmove_number-1) + int(not board.turn)
            in_check = board.is_check()
            mate = abs(score) >= 31872
            counts['in_check'] += in_check
            counts['mate_score'] += mate
            counts['ply_gt160'] += ply > 160
            counts['default_keep'] += not in_check and not mate
            counts['zero_cp'] += score == 0
            counts['abs_cp_gt3000'] += abs(score) > 3000
            counts['native_score_or_ply_out_of_range'] += not (-32768 <= score <= 32767 and 0 <= ply <= 65535)
            counts['castling_rights_present'] += bool(board.castling_rights)
            counts['ep_square_present'] += board.ep_square is not None
            counts['halfmove_ge80'] += board.halfmove_clock >= 80
            histograms['result_white'][str(white)] += 1
            histograms['result_stm'][str(result)] += 1
            histograms['turn']['w' if board.turn else 'b'] += 1
            histograms['absolute_cp'][bin_name(abs(score), (0, 20, 50, 100, 200, 400, 800, 1600, 3000, 31871))] += 1
            histograms['ply'][bin_name(ply, (20, 40, 80, 120, 160, 240))] += 1
            histograms['pieces'][bin_name(chess.popcount(board.occupied), (6, 12, 20, 32))] += 1
            score_bin = bin_name(score, (-800, -400, -200, -100, -50, 0, 50, 100, 200, 400, 800))
            histograms['score_result'][score_bin + ':' + str(result)] += 1
            if result is None:
                counts['unknown_results'] += 1
            else:
                counts['known_results'] += 1
                for index, value in enumerate((1, score, result, score*score, result*result, score*result)):
                    moments[index] += value
            if (counts['valid_rows']-1) % mirror_stride == 0:
                mirror = board.mirror()
                if mirror.mirror().fen(en_passant='fen') != board.fen(en_passant='fen'):
                    raise ValueError(f'board mirror failed: {path}:{source_row}')
                mirrored_result = None if white is None else -white * (1 if mirror.turn else -1)
                if mirrored_result != result:
                    raise ValueError(f'outcome mirror failed: {path}:{source_row}')
                counts['mirror_checks'] += 1
            if sample_rows:
                chosen = len(sample) if len(sample) < sample_rows else rng.randrange(counts['valid_rows'])
                if chosen < sample_rows:
                    evidence = dict(source=str(path), source_row=source_row, fen=fen,
                                    score_stm=score, result_white=white, result_stm=result)
                    if chosen == len(sample):
                        sample.append(evidence)
                    else:
                        sample[chosen] = evidence
            if counts['data_rows'] % 250000 == 0:
                storage_guard(allowance=4096)
                elapsed = time.perf_counter()-start
                print(json.dumps(dict(event='progress', source=path.name,
                      rows=counts['data_rows'], seconds=elapsed,
                      positions_per_second=counts['data_rows']/elapsed)), flush=True)
    if stat_key(path) != item['identity'] or md5.hexdigest() != item['expected_md5']:
        raise ValueError(f'source changed or differs from producer MD5: {path}')
    if sha256(item['sidecar']) != item['sidecar_sha256']:
        raise ValueError(f'producer sidecar changed: {path}')
    for key in ('data_rows', 'valid_rows', 'invalid_rows', 'known_results', 'unknown_results', 'mirror_checks'):
        counts.setdefault(key, 0)
    if counts['valid_rows'] + counts['invalid_rows'] != counts['data_rows']:
        raise ValueError('audit accounting mismatch')
    elapsed = time.perf_counter()-start
    report = dict(path=str(path), status='PASS' if counts['data_rows'] and not counts['invalid_rows'] else 'FAIL',
                  complete_scan=complete, last_source_row=last_source_row,
                  sha256=sha.hexdigest(), md5=md5.hexdigest(), expected_md5=item['expected_md5'],
                  source_identity=item['identity'], sidecar_sha256=item['sidecar_sha256'],
                  **counts, histograms={k: dict(sorted(v.items())) for k, v in histograms.items()},
                  moments=moments, pearson_stm_score_result=correlation(moments),
                  invalid_examples=examples, elapsed_seconds=elapsed,
                  positions_per_second=counts['data_rows']/elapsed,
                  capture_rule='UNAVAILABLE: source has no best moves',
                  qsearch_rule='UNAVAILABLE: exact lock has no UCI oracle',
                  game_ids='UNAVAILABLE: no game identifiers in source')
    return report, sorted(sample, key=lambda row: row['source_row'])


def write_json(path, value):
    payload = json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n'
    storage_guard(path, allowance=len(payload.encode('utf-8'))+1024*1024)
    with Path(path).open('x', encoding='utf-8', newline='\n') as fh:
        fh.write(payload)
        fh.flush()
        os.fsync(fh.fileno())


def run(plan, output, *, max_rows=None, mirror_stride=4096, sample_rows=128):
    if max_rows is not None and (type(max_rows) is not int or max_rows < 1):
        raise ValueError('max rows must be positive')
    if type(mirror_stride) is not int or mirror_stride < 1 or type(sample_rows) is not int or not 0 <= sample_rows <= 10000:
        raise ValueError('invalid audit sampling bounds')
    output = Path(output)
    partial = output.with_name(output.name + '.partial')
    if os.path.lexists(output) or os.path.lexists(partial):
        raise FileExistsError('refusing existing audit output')
    storage_guard(output, allowance=20*10**6)
    if plan.get('schema') != 1 or not plan.get('sources'):
        raise ValueError('invalid profile plan')
    paths = [str(Path(item['path']).resolve()) for item in plan['sources']]
    if len(paths) != len(set(paths)):
        raise ValueError('duplicate source')
    if any(Path(path).name.lower() in HOLDOUTS for path in paths):
        raise ValueError('holdout is not a training-source profile input')
    partial.mkdir(parents=True)
    code = sha256(__file__)
    started = datetime.now(timezone.utc).isoformat()
    write_json(partial/'PLAN.json', plan)
    reports = []
    for index, item in enumerate(plan['sources']):
        storage_guard(partial, allowance=20*10**6)
        report, samples = inspect_source(item, max_rows=max_rows, mirror_stride=mirror_stride,
                                         sample_rows=sample_rows, seed=5108+index)
        sample_lines = [json.dumps(row, sort_keys=True, separators=(',', ':')) + '\n' for row in samples]
        storage_guard(partial, allowance=sum(len(line.encode('utf-8')) for line in sample_lines)+1024*1024)
        with (partial/f'{index:03}.sample.jsonl').open('x', encoding='utf-8', newline='\n') as fh:
            fh.writelines(sample_lines)
        report['sample_sha256'] = sha256(partial/f'{index:03}.sample.jsonl')
        write_json(partial/f'{index:03}.json', report)
        reports.append(report)
        print(json.dumps(dict(event='source_complete', source=item['path'], rows=report['data_rows'],
                             status=report['status'], complete_scan=report['complete_scan'])), flush=True)
    if sha256(__file__) != code:
        raise ValueError('profile source code changed during audit')
    for item in plan['sources']:
        if stat_key(item['path']) != item['identity'] or sha256(item['sidecar']) != item['sidecar_sha256']:
            raise ValueError('source or producer sidecar changed before publication')
    result = dict(schema=1, status='PASS' if all(r['status']=='PASS' for r in reports) else 'FAIL',
                  strength='UNPROVEN', training_ready=False, workers=1,
                  started_utc=started, finished_utc=datetime.now(timezone.utc).isoformat(),
                  script_sha256=code, sample_seed_base=5108, mirror_stride=mirror_stride,
                  sample_rows_per_source=sample_rows, max_rows_per_source=max_rows,
                  total_data_rows=sum(r['data_rows'] for r in reports), sources=reports,
                  scope='descriptive source inspection only; no holdout/game separation or training readiness')
    write_json(partial/'SUMMARY.json', result)
    storage_guard(output, allowance=0)
    partial.rename(output)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('output', type=Path)
    parser.add_argument('--sources', nargs='+', type=Path, required=True)
    parser.add_argument('--max-rows', type=int)
    args = parser.parse_args()
    low_priority()
    result = run(freeze_plan(args.sources), args.output, max_rows=args.max_rows)
    print(json.dumps(dict(status=result['status'], total_data_rows=result['total_data_rows'],
                         source_count=len(result['sources']), strength='UNPROVEN'), indent=2))
    raise SystemExit(0 if result['status']=='PASS' else 1)
