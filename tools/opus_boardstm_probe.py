#!/usr/bin/env python3
"""opus_boardstm_probe.py - fast raw-field board+side-to-move overlap probe (R14 finish, Opus; own code).

Independent second implementation of the board+stm part of r14_overlap (RAM-only, no copied source rows):
  pass 1  holdout files: 64-bit hash of the raw "board side" FEN prefix of every row -> sorted numpy index
  pass 2  train files: every row whose prefix hash is in the index is kept as a candidate (path, line, raw FEN)
  pass 3  holdout files again: rows whose hash matches a candidate are recorded; exact keys are compared, so a
          hash collision never becomes an overlap
Every pass hashes every consumed byte with md5 and compares it to the input pin (fail closed: a mismatch, a row
that does not split into six FEN fields, or a deadline stops the probe with status INCOMPLETE).
Why the raw prefix is exact: r14_scan.parse_row (fill rate 1.0 on these pinned files) rejects consecutive empty-
square digits and bad rank widths, so every raw board field is the unique FEN placement of its board.
Pass 1 + 2 also count en-passant fields per file (rows with an EP square, and how many allow a legal capture,
opus_ep.ep_status), to show how each producer writes the EP field.

  opus_boardstm_probe.py --out D:/a14/sep/boardstm-probe01 [--seconds 7200]
Outputs (refuses an existing --out): PROBE.json (receipts, census, counts, tool md5s, Vienna times) and SHARED.jsonl
(one line per shared key: key, train rows, holdout rows, each {path, line, fen}).
"""
import argparse
import array
import datetime
import hashlib
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from opus_ep import ep_status  # noqa: E402

ROOT = Path('D:/a14')
SOURCE = Path('D:/grok-pc-data/selfplay_out')
PINS = ROOT / 'evidence/r14/input-pins-all.jsonl'
BLOCK = 1 << 23
SIDES = (b'w', b'b')


def vienna():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' Vienna'


def md5_file(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def load_pins(path):
    pins = {}
    with open(path, encoding='utf-8-sig') as stream:
        for line in stream:
            item = json.loads(line)
            if item.get('match') is not True or item.get('actual_md5') != item.get('expected_md5'):
                raise ValueError('unverified input pin')
            pins[str(Path(item['path']).resolve()).casefold()] = item['actual_md5']
    return pins


class Guard:
    def __init__(self, seconds):
        import psutil
        self.psutil = psutil
        self.proc = psutil.Process()
        self.deadline = time.monotonic() + seconds
        self.n = 0

    def __call__(self):
        self.n += 1
        if time.monotonic() > self.deadline:
            raise TimeoutError('probe deadline')
        if self.n % 16 == 0:
            if self.psutil.virtual_memory().available < 8 * 1024 ** 3:
                raise MemoryError('free RAM below 8 GiB')
            if self.proc.memory_info().rss > 2 * 1024 ** 3:
                raise MemoryError('probe RSS above 2 GiB')
            if self.psutil.disk_usage('D:/').free < 50 * 1024 ** 3 or self.psutil.disk_usage('C:/').free < 30 * 1024 ** 3:
                raise OSError('disk floor')


def blocks(path, receipt, guard):
    """Yield (first_line_number, [lines]) per block; md5 over every byte; receipt gets rows / md5."""
    digest = hashlib.md5()
    before = os.stat(path)
    rows = 0
    tail = b''
    with open(path, 'rb') as stream:
        while True:
            guard()
            block = stream.read(BLOCK)
            if not block:
                break
            digest.update(block)
            lines = (tail + block).split(b'\n')
            tail = lines.pop()
            yield rows + 1, lines
            rows += len(lines)
    if tail:
        yield rows + 1, [tail]
        rows += 1
    after = os.stat(path)
    receipt.update(rows=rows, actual_md5=digest.hexdigest(),
                   unchanged=(before.st_size, before.st_mtime_ns) == (after.st_size, after.st_mtime_ns))


def census_add(census, board, side, ep):
    census['ep_rows'] += 1
    census[ep_status(board.decode('ascii'), side.decode('ascii'), ep.decode('ascii'))] += 1


def new_census():
    return {'ep_rows': 0, 'legal': 0, 'no_capture': 0, 'invalid': 0, 'none': 0}


def index_pass(paths, pins, guard, census_by_file, receipts):
    values = array.array('q')
    for path in paths:
        receipt = {'path': str(path), 'pass': 'holdout_index', 'pin_md5': pins[str(path).casefold()], 'bad_rows': 0}
        census = census_by_file.setdefault(path.name, new_census())
        for _, lines in blocks(path, receipt, guard):
            for line in lines:
                p = line.split(b' ', 4)
                if len(p) != 5 or p[1] not in SIDES:
                    receipt['bad_rows'] += 1
                    continue
                values.append(hash(line[:len(p[0]) + 2]))
                if p[3] != b'-':
                    census_add(census, p[0], p[1], p[3])
        receipts.append(receipt)
    index = np.frombuffer(values, dtype=np.int64).copy()
    index.sort()
    return np.unique(index)


def train_pass(paths, pins, index, guard, census_by_file, receipts, progress):
    hits = []   # (path, line_no, raw)
    for path in paths:
        receipt = {'path': str(path), 'pass': 'train_scan', 'pin_md5': pins[str(path).casefold()], 'bad_rows': 0}
        census = census_by_file.setdefault(path.name, new_census())
        for first, lines in blocks(path, receipt, guard):
            hashes = array.array('q')
            for line in lines:
                p = line.split(b' ', 4)
                if len(p) != 5 or p[1] not in SIDES:
                    receipt['bad_rows'] += 1
                    hashes.append(0)
                    continue
                hashes.append(hash(line[:len(p[0]) + 2]))
                if p[3] != b'-':
                    census_add(census, p[0], p[1], p[3])
            h = np.frombuffer(hashes, dtype=np.int64)
            loc = np.searchsorted(index, h)
            loc[loc == len(index)] = len(index) - 1
            for i in np.flatnonzero(index[loc] == h):
                hits.append((str(path), first + int(i), lines[int(i)].decode('ascii')))
        receipts.append(receipt)
        progress(dict(stage='train_file_complete', path=str(path), rows=receipt['rows'], candidates=len(hits)))
    return hits


def resolve_pass(paths, pins, hit_hashes, guard, receipts):
    found = []
    for path in paths:
        receipt = {'path': str(path), 'pass': 'exact_resolution', 'pin_md5': pins[str(path).casefold()], 'bad_rows': 0}
        for first, lines in blocks(path, receipt, guard):
            for i, line in enumerate(lines):
                p = line.split(b' ', 2)
                if len(p) != 3:
                    receipt['bad_rows'] += 1
                    continue
                if hash(line[:len(p[0]) + 2]) in hit_hashes:
                    found.append((str(path), first + i, line.decode('ascii')))
        receipts.append(receipt)
    return found


def key_of(raw):
    fields = raw.split('|', 1)[0].split()
    return fields[0] + ' ' + fields[1]


def fen_of(raw):
    return ' '.join(raw.split('|', 1)[0].split())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--seconds', type=float, default=7200)
    # Fixture runs only (tests): other inputs and pins. Production = the defaults.
    ap.add_argument('--holdout', type=Path, action='append')
    ap.add_argument('--train', type=Path, action='append')
    ap.add_argument('--pins', type=Path, default=PINS)
    a = ap.parse_args()
    out = a.out.resolve()
    if not str(out).casefold().startswith(str(ROOT.resolve()).casefold() + os.sep):
        sys.exit('refusing: --out must be below D:/a14')
    out.mkdir(parents=True, exist_ok=False)
    started, t0 = vienna(), time.monotonic()
    guard = Guard(a.seconds)
    pins = load_pins(a.pins)
    holdouts = [p.resolve() for p in a.holdout] if a.holdout else [SOURCE / 'forge_selfplay_013.txt',
                                                                     SOURCE / 'forge_selfplay_014.txt']
    training = [p.resolve() for p in a.train] if a.train else [
        SOURCE / f'forge_selfplay_{n:03d}.txt' for n in range(1, 40) if n not in (13, 14)]
    for p in holdouts + training:
        if str(p).casefold() not in pins:
            sys.exit(f'refusing: no pin for {p}')
    receipts, census = [], {}
    tools = {name: md5_file(ROOT / 'tools' / name) for name in ('opus_boardstm_probe.py', 'opus_ep.py')}
    log = open(out / 'progress.jsonl', 'w', encoding='utf-8', newline='\n')

    def progress(item):
        item['elapsed_seconds'] = round(time.monotonic() - t0, 1)
        log.write(json.dumps(item) + '\n')
        log.flush()

    record = dict(schema=1, tool='opus_boardstm_probe.py', tool_md5=tools, key='board_stm (raw FEN placement + side)',
                  hash='in-process 64-bit (Python bytes hash) with exact key resolution', start_vienna=started,
                  status='INCOMPLETE', complete=False)
    try:
        index = index_pass(holdouts, pins, guard, census, receipts)
        progress(dict(stage='holdout_index_complete', unique_keys=int(len(index))))
        hits = train_pass(training, pins, index, guard, census, receipts, progress)
        hit_hashes = {hash(key_of(raw).encode('ascii')) for _, _, raw in hits}
        holdout_rows = resolve_pass(holdouts, pins, hit_hashes, guard, receipts)
        progress(dict(stage='exact_resolution_complete', holdout_candidate_rows=len(holdout_rows)))
        shared = {}
        for side, rows in (('train', hits), ('holdout', holdout_rows)):
            for path, line, raw in rows:
                shared.setdefault(key_of(raw), {'train': [], 'holdout': []})[side].append(
                    dict(path=path, line=line, fen=fen_of(raw)))
        exact = {k: v for k, v in shared.items() if v['train'] and v['holdout']}
        problems = [f"{r['pass']} {r['path']}: md5 {r['actual_md5']} != pin {r['pin_md5']}" for r in receipts
                    if r['actual_md5'] != r['pin_md5']]
        problems += [f"{r['pass']} {r['path']}: {r['bad_rows']} rows without six FEN fields" for r in receipts if r['bad_rows']]
        problems += [f"{r['pass']} {r['path']}: file changed while read" for r in receipts if not r['unchanged']]
        with open(out / 'SHARED.jsonl', 'w', encoding='utf-8', newline='\n') as stream:
            for key in sorted(exact):
                stream.write(json.dumps(dict(key=key, **exact[key])) + '\n')
        train_rows = sum(r['rows'] for r in receipts if r['pass'] == 'train_scan')
        holdout_rows_total = sum(r['rows'] for r in receipts if r['pass'] == 'holdout_index')
        record.update(
            status='COMPLETE' if not problems else 'INCOMPLETE', complete=not problems, problems=problems,
            train_rows=train_rows, holdout_rows=holdout_rows_total, holdout_unique_keys=int(len(index)),
            hash_candidate_train_rows=len(hits),
            shared_exact_keys=len(exact), train_overlap_rows=sum(len(v['train']) for v in exact.values()),
            holdout_overlap_rows=sum(len(v['holdout']) for v in exact.values()),
            hash_collision_train_rows=len(hits) - sum(len(v['train']) for v in exact.values()),
            shared_listing=dict(path=str(out / 'SHARED.jsonl'), md5=md5_file(out / 'SHARED.jsonl')),
            ep_census=census, receipts=receipts)
    except BaseException as exc:  # recorded, never swallowed: the record says INCOMPLETE and the exit code is 2
        record.update(error_type=type(exc).__name__, error=str(exc), receipts=receipts)
    record.update(end_vienna=vienna(), elapsed_seconds=round(time.monotonic() - t0, 1))
    log.close()
    with open(out / 'PROBE.json', 'x', encoding='utf-8', newline='\n') as stream:
        json.dump(record, stream, indent=1)
    print(json.dumps({k: record.get(k) for k in ('status', 'shared_exact_keys', 'train_overlap_rows',
                                                  'holdout_overlap_rows', 'elapsed_seconds', 'error')}))
    return 0 if record['status'] == 'COMPLETE' else 2


if __name__ == '__main__':
    sys.exit(main())
