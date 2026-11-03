"""Independent streaming holdout-key audit with RAM-only 64-bit indexes."""
from __future__ import annotations

from array import array
from collections import Counter
from pathlib import Path
import argparse
import hashlib
import json
import math
import os
import sys
import time

from r14_scan import iter_rows, load_pins
from run_policy import free_guard, safe_path

KEYS = ('four_field', 'board_stm')
ROOT = Path('D:/a14')
SOURCE = Path('D:/grok-pc-data/selfplay_out')


def hash64(value: bytes) -> int:
    return int.from_bytes(hashlib.blake2b(value, digest_size=8).digest(), 'little')


def coverage(receipts):
    rows = sum(r.get('rows', 0) for r in receipts)
    valid = sum(r.get('valid_key_rows', 0) for r in receipts)
    return dict(rows=rows, valid_key_rows=valid, missing_key_rows=rows-valid,
                parse_failures=sum(r.get('parse_failures', 0) for r in receipts),
                key_fill_rate=valid/rows if rows else None,
                complete=bool(receipts) and all(r.get('complete') is True for r in receipts))


def overlap_audit(holdouts, training, pins, *, chunk_rows=65536, guard=lambda: None, progress=lambda value: None, state=None):
    """Position-key audit only. PASS here never supplies authentic game identity."""
    import numpy as np
    if type(chunk_rows) is not int or not 1 <= chunk_rows <= 262144:
        raise ValueError('invalid chunk size')
    if not holdouts or not training:
        raise ValueError('nonempty populations required')
    all_paths = [safe_path(path) for path in [*holdouts, *training]]
    normalized = [str(path).casefold() for path in all_paths]
    if len(set(normalized)) != len(normalized) or any(name not in pins for name in normalized):
        raise ValueError('duplicate or unpinned source')
    holdouts = all_paths[:len(holdouts)]
    training = all_paths[len(holdouts):]
    receipts = {'holdout': [], 'train': []}
    if state is not None:
        state['input_receipts'] = receipts
    storage = {name: array('Q') for name in KEYS}
    for path in holdouts:
        guard()
        receipt = {}
        receipts['holdout'].append(receipt)
        for line, row in iter_rows(path, pins[str(path).casefold()], receipt):
            if row is not None:
                for name in KEYS:
                    storage[name].append(hash64(row.keys[name]))
            if line % chunk_rows == 0:
                guard()
                progress(dict(stage='holdout_index', path=str(path), rows=line, coverage=coverage(receipts['holdout'])))
        progress(dict(stage='holdout_file_complete', receipt=receipt))
    indexes = {name: np.frombuffer(values, dtype=np.uint64) for name, values in storage.items()}
    for values in indexes.values():
        guard()
        values.sort(kind='quicksort')
    # Candidate exact keys retain counts and bounded examples, not every row.
    candidates = {name: {} for name in KEYS}
    candidate_rows = Counter()

    def check_chunk(chunk, path):
        if not chunk:
            return
        guard()
        for name in KEYS:
            values = indexes[name]
            if not len(values):
                continue
            hashes = np.fromiter((hash64(row.keys[name]) for _, row in chunk), dtype=np.uint64, count=len(chunk))
            locations = np.searchsorted(values, hashes)
            valid = locations < len(values)
            safe_locations = np.minimum(locations, len(values)-1)
            hits = np.flatnonzero(valid & (values[safe_locations] == hashes))
            for offset in hits:
                line, row = chunk[int(offset)]
                key = row.keys[name]
                entry = candidates[name].setdefault(key, dict(rows=0, examples=[]))
                entry['rows'] += 1
                candidate_rows[name] += 1
                if len(entry['examples']) < 3:
                    entry['examples'].append(dict(path=str(path), line=line))
        guard()

    for path in training:
        guard()
        receipt = {}
        receipts['train'].append(receipt)
        chunk = []
        for line, row in iter_rows(path, pins[str(path).casefold()], receipt):
            if row is not None:
                chunk.append((line, row))
            if line % chunk_rows == 0:
                check_chunk(chunk, path)
                chunk.clear()
                progress(dict(stage='train_scan', path=str(path), rows=line, candidate_rows=dict(candidate_rows), coverage=coverage(receipts['train'])))
        check_chunk(chunk, path)
        progress(dict(stage='train_file_complete', receipt=receipt, candidate_rows=dict(candidate_rows)))
    # A digest equality is only a candidate; resolve using independently reread
    # exact keys and full pinned input hashes. No candidate means no second scan.
    matched = {name: set() for name in KEYS}
    holdout_overlap_rows = Counter()
    resolution_receipts = []
    if any(candidates.values()):
        for path in holdouts:
            receipt = {}
            resolution_receipts.append(receipt)
            for line, row in iter_rows(path, pins[str(path).casefold()], receipt):
                if row is not None:
                    for name in KEYS:
                        key = row.keys[name]
                        if key in candidates[name]:
                            matched[name].add(key)
                            holdout_overlap_rows[name] += 1
                if line % chunk_rows == 0:
                    guard()
                    progress(dict(stage='exact_resolution', path=str(path), rows=line))
    key_reports = {}
    holdout_coverage, train_coverage = coverage(receipts['holdout']), coverage(receipts['train'])
    filled = (holdout_coverage['complete'] and train_coverage['complete']
              and holdout_coverage['key_fill_rate'] == 1.0 and train_coverage['key_fill_rate'] == 1.0)
    for name in KEYS:
        overlap_rows = sum(candidates[name][key]['rows'] for key in matched[name])
        examples = [dict(key=key.decode('ascii'), train=candidates[name][key]['examples']) for key in sorted(matched[name])[:100]]
        key_reports[name] = dict(
            status='UNVERIFIED' if not filled else 'FAIL' if overlap_rows else 'PASS',
            shared_exact_keys=len(matched[name]), train_overlap_rows=overlap_rows,
            holdout_overlap_rows=holdout_overlap_rows[name], hash_candidate_rows=candidate_rows[name],
            hash_collision_rows=candidate_rows[name]-overlap_rows,
            holdout=holdout_coverage, train=train_coverage, examples=examples)
    return dict(schema=1, scope='position_keys_only', status='UNVERIFIED' if not filled else 'FAIL' if any(r['train_overlap_rows'] for r in key_reports.values()) else 'PASS',
                keys=key_reports, holdout=holdout_coverage, train=train_coverage,
                input_receipts=receipts, resolution_receipts=resolution_receipts,
                game_identity_status='UNVERIFIED', hash_algorithm='BLAKE2b-64 little-endian with exact collision resolution',
                index_storage='RAM only; no disk indexes or copied source files')


class RuntimeGuard:
    def __init__(self, seconds, cpu):
        import psutil
        if not math.isfinite(seconds) or seconds <= 0:
            raise ValueError('finite positive duration required')
        self.psutil = psutil
        self.process = psutil.Process()
        allowed = self.process.cpu_affinity()
        if cpu not in allowed or cpu not in (0, 1, 2, 3):
            raise ValueError('CPU outside admitted spare pool')
        loads = psutil.cpu_percent(interval=.5, percpu=True)
        if loads[cpu] > 70:
            raise RuntimeError(f'CPU admission refused: {cpu} at {loads[cpu]}%')
        self.process.nice(psutil.IDLE_PRIORITY_CLASS)
        self.process.cpu_affinity([cpu])
        self.deadline = time.monotonic() + seconds
        self.next_storage = 0
        self()

    def __call__(self):
        free_guard(1024*1024)
        if time.monotonic() >= self.deadline:
            raise TimeoutError('bounded audit deadline')
        if self.psutil.virtual_memory().available < 8*1024**3 or self.process.memory_info().rss > 2*1024**3:
            raise MemoryError('RAM admission refused')
        if time.monotonic() >= self.next_storage:
            used = sum(path.stat().st_size for path in ROOT.rglob('*') if path.is_file() and not path.is_symlink())
            if used + 16*1024*1024 >= 5_000_000_000:
                raise OSError('owned storage cap')
            self.next_storage = time.monotonic() + 15

    def admit_publication(self, needed):
        # An elapsed computation deadline does not prohibit a small failure
        # receipt, but a disk/storage breach does prohibit further allocation.
        if self.psutil.disk_usage('D:/').free < 50*1024**3 + needed or self.psutil.disk_usage('C:/').free < 30*1024**3:
            raise OSError('publication disk admission refused')
        used = sum(path.stat().st_size for path in ROOT.rglob('*') if path.is_file() and not path.is_symlink())
        if used + needed >= 5_000_000_000:
            raise OSError('publication owned storage cap')


def file_identity(path):
    path = safe_path(path)
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'md5').hexdigest()
    return dict(path=str(path), md5=digest, bytes=path.stat().st_size)


def source_identities():
    return [file_identity(ROOT/'tools'/name) for name in ('r14_overlap.py', 'r14_scan.py', 'run_policy.py')]


def verify_runtime():
    inventory = ROOT/'evidence/r14/runtime-files.jsonl'
    if file_identity(inventory)['md5'] != '0dee4106b1ab3160fb7f5759ef0ef972':
        raise ValueError('runtime inventory identity changed')
    count = 0
    with inventory.open(encoding='utf-8') as stream:
        for line in stream:
            item = json.loads(line)
            path = safe_path(item['path'])
            if not path.is_relative_to(ROOT/'runtime') or file_identity(path)['md5'] != item['md5']:
                raise ValueError('runtime file identity changed')
            count += 1
    return dict(inventory=file_identity(inventory), verified_files=count, executable=file_identity(sys.executable))


def run_to_report(holdouts, training, pins, out, *, publication_guard, guard=lambda: None,
                  progress=lambda item: None, identities=None, runtime=None):
    state = {}
    started = time.monotonic()
    try:
        report = overlap_audit(holdouts, training, pins, guard=guard, progress=progress, state=state)
        guard()
        if identities is not None and source_identities() != identities:
            raise ValueError('audit source identity changed')
        if runtime is not None and verify_runtime() != runtime:
            raise ValueError('runtime identity changed')
        report['complete'] = True
    except BaseException as exc:
        receipts = state.get('input_receipts', {'holdout': [], 'train': []})
        report = dict(schema=1, scope='position_keys_only', status='UNVERIFIED', complete=False,
                      error_type=type(exc).__name__, reason=str(exc), input_receipts=receipts,
                      partial_coverage={name: coverage(items) for name, items in receipts.items()},
                      game_identity_status='UNVERIFIED', keys=None)
    report.update(elapsed_seconds=time.monotonic()-started, source_identities=identities, runtime=runtime)
    payload = (json.dumps(report, indent=2)+'\n').encode('utf-8')
    try:
        publication_guard(len(payload)+1024*1024)
        with safe_path(Path(out)/'REPORT.json', write=True).open('xb') as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException as exc:
        report.update(status='UNVERIFIED', complete=False, publication_status='REFUSED', publication_reason=str(exc))
        print(json.dumps(report), flush=True)
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pins', type=Path, default=ROOT/'evidence/r14/input-pins-all.jsonl')
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cpu', type=int, default=3)
    parser.add_argument('--seconds', type=float, default=10800)
    args = parser.parse_args()
    for name in ('CUDA_VISIBLE_DEVICES', 'HIP_VISIBLE_DEVICES'):
        os.environ[name] = '-1'
    for name in ('OMP_NUM_THREADS', 'OPENBLAS_NUM_THREADS', 'MKL_NUM_THREADS'):
        os.environ[name] = '1'
    guard = RuntimeGuard(args.seconds, args.cpu)
    identities = source_identities()
    runtime = verify_runtime()
    out = safe_path(args.out, write=True)
    out.mkdir(parents=True, exist_ok=False)
    pins = load_pins(safe_path(args.pins))
    paths = {n: SOURCE/f'forge_selfplay_{n:03}.txt' for n in range(1, 40)}
    started = time.monotonic()
    last_progress = 0.0

    def progress(value):
        nonlocal last_progress
        now = time.monotonic()
        if now-last_progress >= 30 or value['stage'].endswith('complete'):
            value['elapsed_seconds'] = now-started
            guard.admit_publication(1024*1024)
            print(json.dumps(value), flush=True)
            with (out/'progress.jsonl').open('a', encoding='utf-8') as stream:
                stream.write(json.dumps(value)+'\n')
            last_progress = now

    try:
        report = run_to_report([paths[13], paths[14]], [paths[n] for n in paths if n not in (13, 14)], pins, out,
                               publication_guard=guard.admit_publication, guard=guard, progress=progress,
                               identities=identities, runtime=runtime)
        print(json.dumps(dict(status=report['status'], report=str(out/'REPORT.json'), elapsed_seconds=report['elapsed_seconds'])), flush=True)
        return 0 if report['status'] == 'PASS' else 1 if report['status'] == 'FAIL' else 2
    except BaseException as exc:
        print(json.dumps(dict(status='UNVERIFIED', complete=False, error_type=type(exc).__name__, reason=str(exc), elapsed_seconds=time.monotonic()-started)), flush=True)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
