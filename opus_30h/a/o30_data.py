#!/usr/bin/env python3
"""o30_data.py - Opus 30-h job: data audit + training-set preparation for the v2 fine-tune (own code, numpy only).

usage: python -I -B o30_data.py --out D:\\o30\\data [--pos-dir ...] [--hce-dir ...] [--joba D:\\o14b\\r2\\proof\\jobA]
                                [--mates D:\\a13\\p5qc\\mate_rows.jsonl] [--no-sha]

Inputs (read only, never modified): the self-play FPOS / FHCE shards forge_selfplay_001..039 (the source rows of the
npt data: the J1 binpack is these shards minus 013 / 014 re-encoded), the R14-B relabel proof jobA (999,921 rows from
forge_selfplay_001 / 002, 20k-node labels on original FENs, its own game-level train / val split) and Astra R13's
mate-row flags.
Outputs (new files only under --out; refuses an existing --out):
  shards.json        per shard: rows, sha256 of .pos / .hce, mate rows, holdout-overlap rows, role (train / holdout)
  holdout_keys.npy   sorted unique 64-bit keys (board + side to move) of every 013 + 014 row
  skip/<shard>.npy   row indices the trainer must skip: holdout overlap, |score| >= 30000, jobA val-split rows
  override/<shard>.npz  jobA train-split labels (row index, 20k-node score) replacing the self-play score, mates excluded
  jobA_val.pos / .hce   jobA val split (non-mate) as FPOS / FHCE with the 20k-node labels (a second holdout)
  AUDIT.json         every count + the checks (jobA row alignment, Astra's mate list = the |score| >= 30000 rows)
Key = 64-bit mix of the 32-byte board and the side to move (collision chance for ~3.5e8 rows ~1e-3: at worst one
training row is skipped needlessly).
"""
import argparse
import csv
import hashlib
import json
import os
import sys
import time

import numpy as np

MATE = 30000
P = [np.uint64(x) for x in (0x9E3779B97F4A7C15, 0xC2B2AE3D27D4EB4F, 0x165667B19E3779F9, 0xD6E8FEB86659FD93,
                            0xFF51AFD7ED558CCD)]


def rotl(x, r):
    return (x << np.uint64(r)) | (x >> np.uint64(64 - r))


def keys_of(boards, stm):
    """boards uint8 (n, 32), stm uint8/int (n,) -> uint64 (n,)"""
    w = np.ascontiguousarray(boards).view('<u8').reshape(-1, 4)
    with np.errstate(over='ignore'):
        h = w[:, 0] * P[0]
        h ^= rotl(w[:, 1] * P[1], 17)
        h ^= rotl(w[:, 2] * P[2], 31)
        h ^= rotl(w[:, 3] * P[3], 47)
        h ^= (stm.astype(np.uint64) + np.uint64(1)) * P[4]
        h ^= h >> np.uint64(33)
        h *= P[4]
        h ^= h >> np.uint64(33)
        h *= P[1]
        h ^= h >> np.uint64(33)
    return h


def sha256(path):
    d = hashlib.sha256()
    with open(path, 'rb') as f:
        for block in iter(lambda: f.read(1 << 22), b''):
            d.update(block)
    return d.hexdigest()


def read_fpos(path):
    with open(path, 'rb') as f:
        head = f.read(16)
    if head[:4] != b'FPOS':
        raise SystemExit(f'bad FPOS header {path}')
    n = int.from_bytes(head[8:16], 'little')
    if os.path.getsize(path) != 16 + 35 * n:
        raise SystemExit(f'{path}: size {os.path.getsize(path)} != 16 + 35 * {n}')
    boards = np.fromfile(path, dtype=np.uint8, count=32 * n, offset=16).reshape(n, 32)
    score = np.fromfile(path, dtype='<i2', count=n, offset=16 + 32 * n)
    meta = np.fromfile(path, dtype=np.uint8, count=n, offset=16 + 34 * n)
    return n, boards, score, meta


def read_fhce(path, n):
    with open(path, 'rb') as f:
        head = f.read(16)
    if head[:4] != b'FHCE' or int.from_bytes(head[8:16], 'little') != n or os.path.getsize(path) != 16 + 2 * n:
        raise SystemExit(f'bad FHCE {path} for {n} rows')
    return np.fromfile(path, dtype='<i2', count=n, offset=16)


CODE = {c: i + 1 for i, c in enumerate('PNBRQKpnbrqk')}


def fen_board(fen):
    """FEN -> (uint8[32] FPOS board, stm 0/1)"""
    parts = fen.split()
    codes = [0] * 64
    for r, rank in enumerate(parts[0].split('/')):
        f = 0
        for ch in rank:
            if ch.isdigit():
                f += int(ch)
            else:
                codes[(7 - r) * 8 + f] = CODE[ch]
                f += 1
    return bytes(codes[2 * i] | (codes[2 * i + 1] << 4) for i in range(32)), (0 if parts[1] == 'w' else 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    ap.add_argument('--pos-dir', default=r'D:\grok-pc-data\forge_push\nnue_data\pos')
    ap.add_argument('--hce-dir', default=r'D:\grok-pc-data\forge_push\nnue_data\hce')
    ap.add_argument('--joba', default=r'D:\o14b\r2\proof\jobA')
    ap.add_argument('--mates', default=r'D:\a13\p5qc\mate_rows.jsonl')
    ap.add_argument('--first', type=int, default=1)
    ap.add_argument('--last', type=int, default=39)
    ap.add_argument('--holdout', default='13,14')
    ap.add_argument('--no-sha', action='store_true')
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f'refusing: {a.out} exists')
    os.makedirs(os.path.join(a.out, 'skip'))
    os.makedirs(os.path.join(a.out, 'override'))
    t0 = time.time()
    hold = [int(x) for x in a.holdout.split(',')]
    names = [f'forge_selfplay_{i:03d}' for i in range(a.first, a.last + 1)]
    audit = {'created': time.strftime('%Y-%m-%d %H:%M:%S'), 'pos_dir': a.pos_dir, 'hce_dir': a.hce_dir,
             'holdout_shards': [names[i - a.first] for i in hold], 'mate_cut': MATE, 'shards': {}}

    # 1) holdout keys
    hk = []
    for i in hold:
        nm = names[i - a.first]
        n, boards, score, meta = read_fpos(os.path.join(a.pos_dir, nm + '.pos'))
        hk.append(keys_of(boards, meta & 1))
        print(f'holdout {nm}: {n} rows', flush=True)
    hk = np.unique(np.concatenate(hk))
    np.save(os.path.join(a.out, 'holdout_keys.npy'), hk)
    audit['holdout_unique_keys'] = int(hk.size)

    # 2) jobA: alignment with FPOS 001 / 002, labels, mate rows, split
    labels_path = os.path.join(a.joba, 'final', 'labels.tsv')
    rows_path = os.path.join(a.joba, 'rows.tsv')
    prep = json.load(open(os.path.join(a.joba, 'prepare.json')))
    src_shard = {}
    for inp in prep['inputs']:
        base = os.path.splitext(os.path.basename(inp['path']))[0]
        src_shard[str(inp['index'])] = base
    joba = {}   # row_id -> (shard, fpos_index, split, new_score, old_score, white_result, fen)
    with open(rows_path, newline='') as f:
        r = csv.DictReader(f, delimiter='\t')
        rows_src = {int(row['row_id']): (src_shard[row['source']], int(row['source_row']) - 1) for row in r}
    mates_labels = set()
    with open(labels_path, newline='') as f:
        r = csv.DictReader(f, delimiter='\t')
        for row in r:
            rid = int(row['row_id'])
            shard, idx = rows_src[rid]
            s = int(row['score_stm'])
            joba[rid] = (shard, idx, row['split'], s, int(row['old_score_stm']), float(row['result']), row['fen'])
            if abs(s) >= MATE:
                mates_labels.add(rid)
    astra = set()
    with open(a.mates, encoding='utf-8') as f:
        for line in f:
            rec = json.loads(line)
            if rec.get('cohort') == 'r14b':
                astra.add(int(rec['input_line']) - 2)   # labels.tsv line -> row_id (header is line 1)
    audit['joba'] = {'rows': len(joba), 'mate_rows_by_score': len(mates_labels), 'astra_r14b_mate_rows': len(astra),
                     'astra_equals_score_rule': astra == mates_labels,
                     'labels_sha256': sha256(labels_path), 'rows_sha256': sha256(rows_path),
                     'mates_sha256': sha256(a.mates)}
    by_shard = {}
    for rid, v in joba.items():
        by_shard.setdefault(v[0], []).append((rid,) + v)

    # 3) shards
    val_boards, val_score, val_meta, val_hce = [], [], [], []
    align = {'checked': 0, 'board_mismatch': 0, 'stm_mismatch': 0, 'old_score_mismatch': 0, 'result_mismatch': 0}
    totals = {'train_rows': 0, 'train_skip_overlap': 0, 'train_skip_mate': 0, 'train_skip_joba_val': 0,
              'train_override': 0, 'holdout_rows': 0, 'holdout_mate': 0}
    for i, nm in enumerate(names, start=a.first):
        pos_path = os.path.join(a.pos_dir, nm + '.pos')
        hce_path = os.path.join(a.hce_dir, nm + '.hce')
        n, boards, score, meta = read_fpos(pos_path)
        hce = read_fhce(hce_path, n)
        rec = {'rows': n}
        if not a.no_sha:
            rec['pos_sha256'] = sha256(pos_path)
            rec['hce_sha256'] = sha256(hce_path)
        mate = np.abs(score.astype(np.int32)) >= MATE
        rec['mate_rows'] = int(mate.sum())
        if i in hold:
            rec['role'] = 'holdout'
            totals['holdout_rows'] += n
            totals['holdout_mate'] += rec['mate_rows']
            audit['shards'][nm] = rec
            continue
        rec['role'] = 'train'
        k = keys_of(boards, meta & 1)
        pos_in = np.searchsorted(hk, k)
        pos_in[pos_in >= hk.size] = 0
        overlap = hk[pos_in] == k
        rec['holdout_overlap_rows'] = int(overlap.sum())
        skip = overlap | mate
        jv = np.zeros(n, dtype=bool)
        ov_idx, ov_score = [], []
        for (rid, shard, idx, split, s_new, s_old, res, fen) in by_shard.get(nm, []):
            b, stm = fen_board(fen)
            align['checked'] += 1
            if bytes(boards[idx]) != b:
                align['board_mismatch'] += 1
                continue
            if int(meta[idx] & 1) != stm:
                align['stm_mismatch'] += 1
            if int(score[idx]) != s_old:
                align['old_score_mismatch'] += 1
            if abs(((meta[idx] >> 1) * 0.5) - res) > 1e-9:
                align['result_mismatch'] += 1
            if split == 'val':
                jv[idx] = True
                if abs(s_new) < MATE:
                    val_boards.append(boards[idx].copy()); val_score.append(s_new); val_meta.append(meta[idx]); val_hce.append(hce[idx])
            elif abs(s_new) < MATE and not skip[idx]:
                ov_idx.append(idx); ov_score.append(s_new)
        rec['joba_val_rows'] = int(jv.sum())
        rec['joba_overrides'] = len(ov_idx)
        skip |= jv
        rec['skip_rows'] = int(skip.sum())
        np.save(os.path.join(a.out, 'skip', nm + '.npy'), np.flatnonzero(skip).astype(np.int64))
        if ov_idx:
            np.savez(os.path.join(a.out, 'override', nm + '.npz'), index=np.array(ov_idx, np.int64), score=np.array(ov_score, np.int16))
        totals['train_rows'] += n
        totals['train_skip_overlap'] += int(overlap.sum())
        totals['train_skip_mate'] += int((mate & ~overlap).sum())
        totals['train_skip_joba_val'] += int((jv & ~overlap & ~mate).sum())
        totals['train_override'] += len(ov_idx)
        audit['shards'][nm] = rec
        print(f'{nm}: {n} rows, overlap {rec["holdout_overlap_rows"]}, mate {rec["mate_rows"]}, jobA val {rec["joba_val_rows"]}, '
              f'overrides {len(ov_idx)}, {time.time() - t0:.0f} s', flush=True)
    audit['joba_alignment'] = align
    audit['totals'] = totals
    # 4) jobA val as FPOS / FHCE
    m = len(val_score)
    head = lambda magic: magic + (1).to_bytes(4, 'little') + m.to_bytes(8, 'little')
    with open(os.path.join(a.out, 'jobA_val.pos'), 'wb') as f:
        f.write(head(b'FPOS') + np.array(val_boards, np.uint8).tobytes() + np.array(val_score, '<i2').tobytes()
                + np.array(val_meta, np.uint8).tobytes())
    with open(os.path.join(a.out, 'jobA_val.hce'), 'wb') as f:
        f.write(head(b'FHCE') + np.array(val_hce, '<i2').tobytes())
    audit['joba_val_file_rows'] = m
    audit['seconds'] = round(time.time() - t0, 1)
    with open(os.path.join(a.out, 'AUDIT.json'), 'w', newline='\n') as f:
        json.dump(audit, f, indent=1)
    ok = (align['board_mismatch'] == 0 and align['stm_mismatch'] == 0 and align['old_score_mismatch'] == 0
          and align['checked'] == len(joba) and audit['joba']['astra_equals_score_rule'])
    print(json.dumps({'totals': totals, 'joba_alignment': align, 'joba_val_file_rows': m,
                      'astra_equals_score_rule': audit['joba']['astra_equals_score_rule'], 'ok': ok}, indent=1))
    sys.exit(0 if ok else 1)


if __name__ == '__main__':
    main()
