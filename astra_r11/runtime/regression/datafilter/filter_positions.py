"""Deterministic, opt-in filtering of original normalized records. UNPROVEN."""
import argparse
from collections import Counter
from concurrent.futures import ProcessPoolExecutor
import hashlib
import itertools
import json
import os
from pathlib import Path
import shutil
import time
import chess
from records import read_records, dumps

RULES = ('check', 'capture', 'mate', 'ply')
ARTIFACT_ROOT = Path('D:/a11')

def low_priority():
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        kernel.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        if not kernel.SetPriorityClass(kernel.GetCurrentProcess(), 0x40):
            raise OSError('cannot set Idle priority')
    else:
        os.nice(10)

def storage_guard(root=None, allowance=64*1024*1024):
    if os.name == 'nt':
        # User authorized D-only validation while F is below its reserve; F remains read-only.
        for drive, reserve in [('C:/', 30), ('D:/', 50)]:
            if shutil.disk_usage(drive).free < reserve * 10**9 + (allowance if drive == 'D:/' else 0):
                raise OSError(f'{drive} below {reserve} GB reserve')
    size = sum(p.stat().st_size for p in ARTIFACT_ROOT.rglob('*') if p.is_file())
    if size + allowance > 15 * 10**9:
        raise OSError('new artifact cap exceeded')

def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def matches(r, max_ply=None):
    board = chess.Board(r['fen'])
    move = chess.Move.from_uci(r['best_move']) if r['best_move'] is not None else None
    capture = None if move is None else bool(board.is_capture(move) or move.promotion)
    mate = r['score_type'] == 'mate' or (r['source_kind'] in ('selfplay', 'pgn') and abs(r['score_stm']) >= 31872)
    return (board.is_check(), capture, mate, max_ply is not None and r['ply'] > max_ply)

def inspect_chunk(args):
    rows, max_ply = args
    return [(r, matches(r, max_ply)) for r in rows]

def chunks(rows, size=2048):
    while part := list(itertools.islice(rows, size)):
        yield part

def run_filter(inp, out, *, kind='normalized', workers=1, drop_in_check=False,
               drop_capture_bestmove=False, drop_qs_unquiet=None,
               drop_mate_scores=False, max_ply_from_start=None):
    if drop_qs_unquiet is not None:
        raise ValueError('unsupported oracle: FD3A5190 provides neither static eval nor root qsearch; depth 1 is not equivalent')
    if workers not in (1, 2):
        raise ValueError('workers must be 1 or 2')
    if max_ply_from_start is not None and max_ply_from_start < 0:
        raise ValueError('ply limit must be nonnegative')
    out = Path(out)
    partial = out.with_name(out.name + '.partial')
    if out.exists() or partial.exists():
        raise FileExistsError('refusing existing output destination')
    storage_guard()
    low_priority()
    partial.mkdir(parents=True)
    enabled = (drop_in_check, drop_capture_bestmove, drop_mate_scores, max_ply_from_start is not None)
    independent, first, overlap, coverage = Counter(), Counter(), Counter(), Counter()
    count = kept = 0
    start = time.perf_counter()
    executor = ProcessPoolExecutor(max_workers=workers, initializer=low_priority) if workers == 2 else None
    try:
        source = chunks(iter(read_records(inp, kind)))
        with open(partial / 'records.jsonl', 'x', encoding='utf-8', newline='\n') as records, open(partial / 'metadata.jsonl', 'x', encoding='utf-8', newline='\n') as metadata:
            # Bounded submission; executor.map alone queues the entire input on Python 3.10.
            while window := list(itertools.islice(source, workers * 2)):
                storage_guard(allowance=sum(len(dumps(r).encode('utf-8'))+1 for part in window for r in part)*2 + 1024*1024)
                args = [(part, max_ply_from_start) for part in window]
                results = executor.map(inspect_chunk, args) if executor else map(inspect_chunk, args)
                for part in results:
                    for r, hits in part:
                        count += 1
                        coverage['result'] += int(r['has_result'])
                        coverage['best_move'] += int(r['best_move'] is not None)
                        coverage['full_fen'] += 1
                        coverage['score_type'] += 1
                        coverage['ply'] += 1
                        if drop_capture_bestmove and hits[1] is None:
                            raise ValueError(f"missing best-move metadata at {r['source']}:{r['source_row']}")
                        active = [name for name, hit, on in zip(RULES, hits, enabled) if on and hit]
                        for name, hit in zip(RULES, hits):
                            independent[name] += int(bool(hit))
                        if active:
                            first[active[0]] += 1
                            overlap['+'.join(active)] += 1
                        else:
                            kept += 1
                            text = dumps(r) + '\n'
                            records.write(text)
                            metadata.write(text)
                storage_guard(out.parent)
        if count == 0:
            raise ValueError('empty input: no records; refusing to publish an empty selection')
        elapsed = time.perf_counter() - start
        report = dict(input=count, kept=kept, dropped=count-kept,
                      independent={k: independent[k] for k in RULES},
                      first_drop={k: first[k] for k in RULES}, overlap=dict(sorted(overlap.items())),
                      coverage=dict(coverage), enabled=dict(zip(RULES, enabled)),
                      max_ply_from_start=max_ply_from_start, workers=workers,
                      elapsed_seconds=elapsed, positions_per_second=count/elapsed,
                      capture_measurement='PASS' if coverage['best_move'] == count else 'BLOCKED: missing metadata',
                      qsearch_measurement='BLOCKED: unsupported oracle',
                      hashes={p.name: sha256(p) for p in partial.iterdir()})
        assert count == kept + sum(first.values())
        (partial / 'report.json').write_text(json.dumps(report, indent=2, sort_keys=True), encoding='utf-8')
        partial.rename(out)
        return report
    finally:
        if executor:
            executor.shutdown(wait=True, cancel_futures=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input')
    parser.add_argument('output')
    parser.add_argument('--kind', choices=['normalized', 'selfplay', 'lichess', 'pgn'], default='normalized')
    parser.add_argument('--workers', type=int, default=1)
    parser.add_argument('--drop-in-check', action='store_true')
    parser.add_argument('--drop-capture-bestmove', action='store_true')
    parser.add_argument('--drop-qs-unquiet', type=int)
    parser.add_argument('--drop-mate-scores', action='store_true')
    parser.add_argument('--max-ply-from-start', type=int)
    args = vars(parser.parse_args())
    inp, out = args.pop('input'), args.pop('output')
    print(json.dumps(run_filter(inp, out, **args), indent=2))
