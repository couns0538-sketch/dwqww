#!/usr/bin/env python3
"""opus_guardband_proof.py - independent proof of a guard-band split (R14 finish Job 3 step 4, Opus; own code).

Reads only pinned inputs and the staged candidate rows named in SPLIT.json; shares no state with the builder.
  accounting   every jobA row id is exactly one of: staged train, staged val, DROPPED.tsv; train ids < cut <= val ids
  payload      every staged row equals jobA rows.tsv (FEN, White result) and labels.tsv (score) for its row id;
               no staged row has |score| >= 30000
  holdout      three keys of every 013/014 row (md5 of every byte = pin): board+stm, raw 4-field (canonical castling
               order) and EP-normalised 4-field (legal-capture-only, opus_ep) -> staged train and val rows must hit
               none of them; key fill rate 1.0 on both sides (hash hits are resolved exactly)
  train_val    the same three keys: no staged train row shares a key with a staged val row
  chain        from the pinned jobA pairs map: the link at the cut is UNREACHABLE (codes 1-3); train and val share no
               conservative component (runs of REACHABLE / UNKNOWN links); every retained row of the two cut
               components lies more than K plies from its cut endpoint
  audit        npt-data-holdout-check audit_exports.py on JSONL adapter exports (source = all jobA rows, train =
               all staged rows, the two complete holdouts); game_id is null everywhere (no authentic IDs exist), so
               the audit's own status can be at best UNVERIFIED; its failure counters are reported as they are
Writes the proof record given by --out (sep/guardband01/PROOF.json; refuses an existing file); the final
sep/GUARDBAND_SEPARATION.json is written from it by opus_guardband_record.py. Audit inputs and output go below
--big-dir (C:).

  opus_guardband_proof.py --split D:/a14/sep/guardband01/SPLIT.json --out D:/a14/sep/GUARDBAND_SEPARATION.json
                          --big-dir C:/a14x/guardband01_proof
"""
import argparse
import array
import datetime
import hashlib
import json
import os
import struct
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from opus_ep import ep_status  # noqa: E402

SOURCE = Path('D:/grok-pc-data/selfplay_out')
PINS = Path('D:/a14/evidence/r14/input-pins-all.jsonl')
AUDIT = Path('D:/a14/.agents/skills/npt-data-holdout-check/scripts/audit_exports.py')
MATE = 30000


def vienna():
    return datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S') + ' Vienna'


def md5(path):
    h = hashlib.md5()
    with open(path, 'rb') as stream:
        for block in iter(lambda: stream.read(1 << 22), b''):
            h.update(block)
    return h.hexdigest()


def keys3(board, side, rights, ep):
    """(board+stm, raw 4-field, EP-normalised 4-field) as bytes; raises ValueError on an invalid EP field."""
    k1 = board + b' ' + side
    rc = b''.join(c for c in (b'K', b'Q', b'k', b'q') if c in rights) or b'-'
    if ep == b'-':
        ne = b'-'
    else:
        st = ep_status(board.decode('ascii'), side.decode('ascii'), ep.decode('ascii'))
        if st == 'invalid':
            raise ValueError('invalid EP field')
        ne = ep if st == 'legal' else b'-'
    return k1, k1 + b' ' + rc + b' ' + ep, k1 + b' ' + rc + b' ' + ne


def holdout_pass(pins, big_dir):
    """Index the three keys of 013/014 and write the audit JSONL exports in the same pass."""
    idx = [array.array('q'), array.array('q'), array.array('q')]
    receipts = []
    exports = {}
    for name in ('forge_selfplay_013.txt', 'forge_selfplay_014.txt'):
        path = SOURCE / name
        digest = hashlib.md5()
        out_path = big_dir / (name[:-4] + '.jsonl')
        sha = hashlib.sha256()
        rows = bad = 0
        tail = b''
        with open(path, 'rb') as stream, open(out_path, 'xb') as out:
            while True:
                block = stream.read(1 << 23)
                if not block:
                    break
                digest.update(block)
                lines = (tail + block).split(b'\n')
                tail = lines.pop()
                buf = []
                for line in lines:
                    rows += 1
                    fen = line.split(b'|', 1)[0].strip()
                    f = fen.split(b' ')
                    if len(f) != 6 or f[1] not in (b'w', b'b') or b'"' in fen or b'\\' in fen:
                        bad += 1
                        continue
                    for j, k in enumerate(keys3(f[0], f[1], f[2], f[3])):
                        idx[j].append(hash(k))
                    buf.append(b'{"row_id":"%s:%d","fen":"%s","game_id":null}\n' % (name[15:18].encode(), rows, fen))
                data = b''.join(buf)
                sha.update(data)
                out.write(data)
        if tail:
            raise ValueError(f'{name}: last line without newline')
        receipts.append(dict(path=str(path), rows=rows, bad_rows=bad, actual_md5=digest.hexdigest(),
                             pin_md5=pins[str(path).casefold()]))
        exports[name] = dict(path=str(out_path), rows=rows - bad, sha256=sha.hexdigest())
    arrays = []
    for a in idx:
        x = np.frombuffer(a, dtype=np.int64).copy()
        x.sort()
        arrays.append(np.unique(x))
    return arrays, receipts, exports


def hits(index, values):
    v = np.asarray(values, dtype=np.int64)
    loc = np.searchsorted(index, v)
    loc[loc == len(index)] = len(index) - 1
    return np.flatnonzero(index[loc] == v)


def exact_holdout_keys(wanted):
    """Exact resolution for hash candidates: re-read 013/014 and return the wanted keys that really occur."""
    found = set()
    for name in ('forge_selfplay_013.txt', 'forge_selfplay_014.txt'):
        with open(SOURCE / name, 'rb') as stream:
            for line in stream:
                f = line.split(b'|', 1)[0].strip().split(b' ')
                for k in keys3(f[0], f[1], f[2], f[3]):
                    if k in wanted:
                        found.add(k)
    return found


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--split', required=True, type=Path)
    ap.add_argument('--out', required=True, type=Path)
    ap.add_argument('--big-dir', required=True, type=Path)
    a = ap.parse_args()
    if a.out.exists():
        sys.exit(f'refusing: {a.out} exists')
    import psutil
    if psutil.virtual_memory().available < 8 * 1024 ** 3:
        sys.exit('refusing: free RAM below 8 GiB')
    if psutil.disk_usage('C:/').free < 50 * 1024 ** 3 or psutil.disk_usage('D:/').free < 50 * 1024 ** 3:
        sys.exit('refusing: C: or D: below 50 GiB (the audit also keeps a 32 GiB reserve on C:)')
    started, t0 = vienna(), time.monotonic()
    split = json.load(open(a.split, encoding='utf-8'))
    k, cut = split['k'], split['cut']['row_id']
    checks, problems = {}, []
    pins = {}
    with open(PINS, encoding='utf-8-sig') as stream:
        for line in stream:
            item = json.loads(line)
            pins[str(Path(item['path']).resolve()).casefold()] = item['actual_md5']
    # inputs named by SPLIT.json must still carry their md5
    for name, item in split['inputs'].items():
        if md5(item['path']) != item['md5']:
            problems.append(f'input {name} md5 changed')
    for side in ('train', 'val'):
        for kind, item in split['staged'][side].items():
            if md5(item['path']) != item['md5']:
                problems.append(f'staged {side}.{kind} md5 differs from SPLIT.json')
    # jobA rows and labels
    rows, labels = [], []
    with open(split['inputs']['rows']['path'], encoding='ascii') as stream:
        stream.readline()
        for line in stream:
            f = line.rstrip('\n').split('\t')
            rows.append((f[3], f[5], int(f[6]), int(f[7])))
    with open(split['inputs']['labels']['path'], encoding='ascii') as stream:
        stream.readline()
        for line in stream:
            labels.append(int(line.split('\t')[4]))
    n = len(rows)
    staged = {}
    for side in ('train', 'val'):
        ids = [int(x) for x in open(split['staged'][side]['rowids']['path'], encoding='ascii')]
        data = [line.rstrip('\n') for line in open(split['staged'][side]['txt']['path'], encoding='ascii')]
        if len(ids) != len(data):
            problems.append(f'{side}: rowids and rows differ in count')
        staged[side] = list(zip(ids, data))
    dropped = [int(line.split('\t')[0]) for line in list(open(Path(a.split).with_name('DROPPED.tsv'), encoding='ascii'))[1:]]
    tr = [i for i, _ in staged['train']]
    va = [i for i, _ in staged['val']]
    every = tr + va + dropped
    acc_ok = (sorted(every) == list(range(n)) and tr == sorted(tr) and va == sorted(va)
              and (not tr or max(tr) < cut) and (not va or min(va) >= cut)
              and (len(tr), len(va)) == (split['retained']['train'], split['retained']['val']))
    checks['accounting'] = dict(status='PASS' if acc_ok else 'FAIL', rows=n, train=len(tr), val=len(va),
                                dropped=len(dropped), cut_row_id=cut)
    # payload faithfulness
    mism = mate = 0
    for side in ('train', 'val'):
        for i, text in staged[side]:
            fen, score, result = (p.strip() for p in text.split('|'))
            if fen != rows[i][0] or result != rows[i][1] or int(score) != labels[i]:
                mism += 1
            if abs(int(score)) >= MATE:
                mate += 1
    checks['payload'] = dict(status='PASS' if mism == 0 and mate == 0 else 'FAIL', mismatched_rows=mism, mate_rows=mate)
    # holdout three-key check
    a.big_dir.mkdir(parents=True, exist_ok=False)
    index, receipts, exports = holdout_pass(pins, a.big_dir)
    hold_ok = all(r['actual_md5'] == r['pin_md5'] and r['bad_rows'] == 0 for r in receipts)
    names = ('board_stm', 'four_field_raw', 'four_field_ep_normalised')

    def staged_keys(side, i):
        f = staged[side][i][1].split('|', 1)[0].strip().encode('ascii').split(b' ')
        return keys3(f[0], f[1], f[2], f[3])

    val_sets = [set(), set(), set()]
    for i in range(len(staged['val'])):
        for j, key in enumerate(staged_keys('val', i)):
            val_sets[j].add(key)
    overlap, tv = {}, dict.fromkeys(names, 0)
    for side in ('train', 'val'):
        hashed = [array.array('q'), array.array('q'), array.array('q')]
        for i in range(len(staged[side])):
            for j, key in enumerate(staged_keys(side, i)):
                hashed[j].append(hash(key))
                if side == 'train' and key in val_sets[j]:
                    tv[names[j]] += 1
        for j, name in enumerate(names):
            cand = hits(index[j], np.frombuffer(hashed[j], dtype=np.int64))
            exact = 0
            if len(cand):   # rare: resolve hash candidates exactly against the holdout files
                wanted = {staged_keys(side, int(c))[j] for c in cand}
                real = exact_holdout_keys(wanted)
                exact = sum(1 for c in cand if staged_keys(side, int(c))[j] in real)
            overlap.setdefault(name, {})[side] = dict(hash_candidates=int(len(cand)), exact_overlap_rows=exact)
    hold_zero = all(v['exact_overlap_rows'] == 0 for per in overlap.values() for v in per.values())
    checks['holdout'] = dict(
        status='PASS' if hold_ok and hold_zero else 'FAIL', keys=overlap, holdout_receipts=receipts,
        key_fill_rate=dict(holdout=1.0 if hold_ok else None, staged=1.0),
        scope='every staged row vs every row of the complete 013 and 014 files (md5 = pins)')
    # train vs val (counted in the loop above: train rows whose key is a key of a staged val row)
    checks['train_val'] = dict(status='PASS' if not any(tv.values()) else 'FAIL', shared_train_rows=tv)
    # chain
    rep = json.load(open(split['inputs']['map_report']['path'], encoding='utf-8'))
    codes = {}
    for art in rep['artifacts']:
        if art['kind'] == 'pairs':
            if md5(art['path']) != art['md5']:
                problems.append(f"map {art['path']} md5 changed")
            buf = Path(art['path']).read_bytes()
            codes[art['source_id']] = {line: code for line, code, _ in struct.iter_unpack('<IBI', buf)}

    def link(i):   # code of the link (row i-1 -> row i) in jobA order
        src, line = rows[i][2], rows[i][3]
        if src == 1 and line == 1:
            return rep['cross_file_adjacent_pairs'][0]['code']
        return codes[src][line]

    cut_code = link(cut)
    lo = cut - 1
    while lo > 0 and link(lo) not in (1, 2, 3):
        lo -= 1
    hi = cut + 1
    while hi < n and link(hi) not in (1, 2, 3):
        hi += 1
    left, right = range(lo, cut), range(cut, hi)

    def ply(i):
        f = rows[i][0].split()
        return 2 * (int(f[5]) - 1) + (f[1] == 'b')

    tset, vset_ids = set(tr), set(va)
    left_ok = all(ply(cut - 1) - ply(i) > k for i in left if i in tset)
    right_ok = all(ply(i) - ply(cut) > k for i in right if i in vset_ids)
    shared_components = 0 if cut_code in (1, 2, 3) else 1
    min_left = min((ply(cut - 1) - ply(i) for i in left if i in tset), default=None)
    min_right = min((ply(i) - ply(cut) for i in right if i in vset_ids), default=None)
    checks['chain'] = dict(
        status='PASS' if cut_code in (1, 2, 3) and left_ok and right_ok else 'FAIL',
        cut_link=dict(code=cut_code, reason=rep['code_table'][str(cut_code)]['reason'],
                      status=rep['code_table'][str(cut_code)]['status']),
        components_shared_by_train_and_val=shared_components,
        cross_split_links_within_k=0 if shared_components == 0 else None,
        left_component=dict(first_row_id=lo, last_row_id=cut - 1),
        right_component=dict(first_row_id=cut, last_row_id=hi - 1),
        min_retained_ply_distance=dict(left=min_left, right=min_right, k=k),
        scope='observed adjacent-row links of the pinned jobA map only; no claim about interleaving, omitted '
              'continuations or nonadjacent relations')
    # audit adapter exports + audit run
    src_path, trn_path = a.big_dir / 'source.jsonl', a.big_dir / 'train.jsonl'
    with open(src_path, 'xb') as out:
        for i, (fen, _, src, line) in enumerate(rows):
            out.write(b'{"row_id":"%03d:%d","fen":"%s","game_id":null}\n' % (src + 1, line, fen.encode()))
    with open(trn_path, 'xb') as out:
        for i in tr + va:
            fen, _, src, line = rows[i]
            out.write(b'{"row_id":"%03d:%d","fen":"%s","game_id":null}\n' % (src + 1, line, fen.encode()))
    e13, e14 = exports['forge_selfplay_013.txt'], exports['forge_selfplay_014.txt']
    cmd = [sys.executable, '-I', '-B', str(AUDIT), '--source', str(src_path), '--train', str(trn_path),
           '--holdout-013', e13['path'], '--sha256-013', e13['sha256'], '--rows-013', str(e13['rows']),
           '--holdout-014', e14['path'], '--sha256-014', e14['sha256'], '--rows-014', str(e14['rows']),
           '--out', str(a.big_dir / 'audit')]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    (a.big_dir / 'audit_stdout.json').write_text(proc.stdout, encoding='utf-8', newline='\n')
    (a.big_dir / 'audit_stderr.txt').write_text(proc.stderr, encoding='utf-8', newline='\n')
    try:
        audit = json.loads(proc.stdout)
    except ValueError:
        audit = dict(status='BLOCKED', error='no JSON on stdout')
    counters = {key: audit.get(key) for key in ('position_overlap_rows', 'game_overlap_rows', 'state_mismatch_rows',
                                                'unknown_game_id_rows', 'source_rows', 'training_rows', 'holdout_rows')}
    checks['audit'] = dict(
        status=audit.get('status'), exit_code=proc.returncode, counters=counters,
        report=dict(path=str(a.big_dir / 'audit' / 'audit.json'),
                    md5=md5(a.big_dir / 'audit' / 'audit.json') if (a.big_dir / 'audit' / 'audit.json').exists() else None),
        command=' '.join(cmd), tool_md5=md5(AUDIT),
        inputs=dict(source=dict(path=str(src_path), md5=md5(src_path)), train=dict(path=str(trn_path), md5=md5(trn_path)),
                    holdout_013=e13, holdout_014=e14),
        note='game_id is null for every row: no authentic game IDs exist, so the audit cannot return PASS; '
             'its failure counters (position, game, state) are the checkable part')
    scoped = all(checks[c]['status'] == 'PASS' for c in ('accounting', 'payload', 'holdout', 'train_val', 'chain'))
    audit_clean = (checks['audit']['exit_code'] in (0, 2) and counters['position_overlap_rows'] == 0
                   and counters['game_overlap_rows'] == 0 and counters['state_mismatch_rows'] == 0)
    record = dict(
        schema=1, tool='opus_guardband_proof.py', tool_md5=md5(__file__), start_vienna=started,
        split=dict(path=str(a.split), md5=md5(a.split)), problems=problems, checks=checks,
        scoped_checks='PASS' if scoped and not problems else 'FAIL',
        audit_status=checks['audit']['status'], audit_failure_counters_zero=audit_clean,
        authentic_game_ids='UNVERIFIED',
        elapsed_seconds=round(time.monotonic() - t0, 1), end_vienna=vienna())
    with open(a.out, 'x', encoding='utf-8', newline='\n') as stream:
        json.dump(record, stream, indent=1)
    print(json.dumps(dict(scoped_checks=record['scoped_checks'], problems=problems,
                          statuses={c: v['status'] for c, v in checks.items()}, audit_counters=counters)))
    return 0 if record['scoped_checks'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
