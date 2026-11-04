#!/usr/bin/env python3
"""o30_fit.py - Opus 30-h job: CPU fine-tune of a Forge v2 net (FORGENN2, feature set 0) from the self-play FPOS +
FHCE shards (own code; torch CPU, 1 thread). GPU-free path while the GPU is booked.

  train   python -I -B o30_fit.py train --out RUN --data D:\\o30\\data --init lock|<file.nnue2> [--kb-map one|rank4]
                  [--ob 8] [--stand-alone] [--blend 0.6] [--lr 1e-4] [--lr-end 1e-6] [--positions 2e9] [--batch 16384]
                  [--save-minutes 25] [--seed 1] [--until "YYYY-MM-DD HH:MM"] [--resume]
  stop    python -I -B o30_fit.py stop RUN     (asks a running trainer to save and exit: a named event it created)

Model = the engine's v2 net: per perspective acc = b1 + sum of w1 columns (king bucket, mirror like
include/forge/nnue_v2.hpp), SCReLU, out = a_stm . w2[ob][:H] + a_ntm . w2[ob][H:] + b2[ob] (logit units),
residual: pred = sigmoid(out + hce * K / 400); target = b * sigmoid(clamp(score * K / 400, +-40)) + (1 - b) * stm_result,
MSE (the lock net's training loss; S31 metric). Weights are clamped to the int16 grid range after every step and exported
as round(w * 4096) int16. --init lock = the compiled-in lock net (src/nnue_weights.inc of the base lock copy), copied into
every king bucket / output bucket: the same function at step 0 (mirror off), so the run starts at the lock's loss.
Data: shards forge_selfplay_NNN.pos/.hce with role train in RUN_DATA/shards.json, minus RUN_DATA/skip/<shard>.npy
(holdout-overlap keys, |score| >= 30000, jobA val rows), jobA 20k-node labels from RUN_DATA/override/<shard>.npz.
Order: chunk c (seed, c) picks a shard (weighted by rows) and a random contiguous block of --block rows, shuffled;
a resumed run continues at the saved chunk / batch, so the stream does not depend on stops.
Every --save-minutes: RUN/last.pt (atomic), RUN/nets/step<N>.nnue2, holdout scores (o30_score_v2.exe on the S31 subset and
on jobA_val) appended to RUN/val.csv; RUN/best.pt + RUN/best.nnue2 follow the lowest S31 b0.6. Free RAM < 6 GB or the
deadline -> save and exit. Never deletes anything; refuses to start a fresh run in an existing RUN.
"""
import argparse
import ctypes
import csv
import datetime as dt
import json
import math
import os
import subprocess
import sys
import time

os.environ.setdefault('OMP_NUM_THREADS', '1')
os.environ.setdefault('MKL_NUM_THREADS', '1')
os.environ.setdefault('OPENBLAS_NUM_THREADS', '1')
import numpy as np  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from o30_v2net import king_map, output_map, parse_inc, write_v2  # noqa: E402

K = 2.25
INPUTS = 768
HERE = os.path.dirname(os.path.abspath(__file__))
SCORER = r'D:\o30\tools_bin\o30_score_v2.exe'
S16_POS = r'F:\opus_scratch\sol_S31\inputs\prod\holdout_013_014_s16.pos'
S16_HCE = r'F:\opus_scratch\sol_S31\inputs\prod\holdout_013_014_s16.hce'
LOCK_INC = r'D:\o30\repos\base\src\nnue_weights.inc'


def free_ram_gb():
    class MS(ctypes.Structure):
        _fields_ = [('dwLength', ctypes.c_ulong), ('dwMemoryLoad', ctypes.c_ulong), ('ullTotalPhys', ctypes.c_ulonglong),
                    ('ullAvailPhys', ctypes.c_ulonglong), ('ullTotalPageFile', ctypes.c_ulonglong),
                    ('ullAvailPageFile', ctypes.c_ulonglong), ('ullTotalVirtual', ctypes.c_ulonglong),
                    ('ullAvailVirtual', ctypes.c_ulonglong), ('ullAvailExtendedVirtual', ctypes.c_ulonglong)]
    m = MS()
    m.dwLength = ctypes.sizeof(MS)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
    return m.ullAvailPhys / 2 ** 30


def event_name(run):
    return 'Local\\O30_Fit_Stop_' + ''.join(ch if ch.isalnum() else '_' for ch in os.path.abspath(run))[-180:]


class Data:
    def __init__(self, data_dir, pos_dir, hce_dir, block, seed):
        meta = json.load(open(os.path.join(data_dir, 'AUDIT.json')))
        self.shards = [nm for nm, r in sorted(meta['shards'].items()) if r['role'] == 'train']
        self.rows = np.array([meta['shards'][nm]['rows'] for nm in self.shards], np.int64)
        self.pos = [os.path.join(pos_dir, nm + '.pos') for nm in self.shards]
        self.hce = [os.path.join(hce_dir, nm + '.hce') for nm in self.shards]
        self.skip = [np.load(os.path.join(data_dir, 'skip', nm + '.npy')) for nm in self.shards]
        self.override = []
        for nm in self.shards:
            p = os.path.join(data_dir, 'override', nm + '.npz')
            if os.path.exists(p):
                z = np.load(p)
                self.override.append((z['index'], z['score']))
            else:
                self.override.append(None)
        self.block = block
        self.seed = seed
        self.mix = 1

    def _piece(self, s, start, m):
        """rows [start, start + m) of shard s, overrides applied, skipped rows dropped."""
        n = int(self.rows[s])
        boards = np.fromfile(self.pos[s], np.uint8, count=32 * m, offset=16 + 32 * start).reshape(m, 32)
        score = np.fromfile(self.pos[s], '<i2', count=m, offset=16 + 32 * n + 2 * start).astype(np.int16)
        meta = np.fromfile(self.pos[s], np.uint8, count=m, offset=16 + 34 * n + start)
        hce = np.fromfile(self.hce[s], '<i2', count=m, offset=16 + 2 * start)
        if self.override[s] is not None:
            idx, sc = self.override[s]
            sel = (idx >= start) & (idx < start + m)
            score[idx[sel] - start] = sc[sel]
        keep = np.ones(m, bool)
        sk = self.skip[s]
        sk = sk[(sk >= start) & (sk < start + m)]
        keep[sk - start] = False
        k = np.flatnonzero(keep)
        return boards[k], score[k], meta[k], hce[k]

    def chunk(self, c):
        """rows of chunk c: (boards uint8 (m,32), score int16, meta uint8, hce int16), shuffled; deterministic in (seed, c).
        mix = 1 (runs created before the mix option): one block of `block` rows from one shard (weighted by rows).
        mix = k: k blocks of block / k rows from k shards drawn with replacement (weighted by rows), shuffled together,
        so the batches of a chunk are not all from one stretch of one self-play file."""
        rng = np.random.default_rng([self.seed, c])
        p = self.rows / self.rows.sum()
        if self.mix <= 1:
            s = int(rng.choice(len(self.shards), p=p))
            n = int(self.rows[s])
            m = min(self.block, n)
            start = int(rng.integers(0, n - m + 1))
            b, sc, me, h = self._piece(s, start, m)
            order = rng.permutation(len(sc))
            return self.shards[s], start, b[order], sc[order], me[order], h[order]
        parts = []
        names = []
        for _ in range(self.mix):
            s = int(rng.choice(len(self.shards), p=p))
            n = int(self.rows[s])
            m = min(self.block // self.mix, n)
            start = int(rng.integers(0, n - m + 1))
            parts.append(self._piece(s, start, m))
            names.append(self.shards[s][-3:])
        b, sc, me, h = (np.concatenate([pt[i] for pt in parts]) for i in range(4))
        order = rng.permutation(len(sc))
        return '+'.join(names), 0, b[order], sc[order], me[order], h[order]


def features(boards, stm, kmap, mirror):
    """-> (idx_stm, off_stm, idx_ntm, off_ntm, piece_count) for EmbeddingBag(sum)."""
    codes = np.empty((boards.shape[0], 64), np.int64)
    codes[:, 0::2] = boards & 15
    codes[:, 1::2] = boards >> 4
    occ = codes > 0
    count = occ.sum(1)
    sample, sq = np.nonzero(occ)
    c = codes[sample, sq] - 1
    color = c // 6
    typ = c - color * 6
    sq_all = np.arange(64)[None, :]
    out = []
    for persp in (stm.astype(np.int64), 1 - stm.astype(np.int64)):
        king_code = np.where(persp == 0, 6, 12)
        ksq = np.argmax(codes == king_code[:, None], axis=1)
        kr = np.where(persp == 1, ksq ^ 56, ksq)
        flip = np.where(mirror & ((kr & 7) >= 4), 7, 0)
        bucket = kmap[kr]
        p = persp[sample]
        rel = (color != p).astype(np.int64)
        sqr = np.where(p == 1, sq ^ 56, sq) ^ flip[sample]
        idx = bucket[sample] * INPUTS + (rel * 6 + typ) * 64 + sqr
        out.append(idx)
    offsets = np.concatenate([[0], np.cumsum(count)[:-1]])
    return out[0], offsets, out[1], offsets, count


def build_model(torch, init, kb_map, ob, hidden=256):
    kmap = np.array(king_map(kb_map), np.int64)
    kb = int(kmap.max()) + 1
    if init == 'lock':
        w1, b1, w2, b2, residual = parse_inc(LOCK_INC)
        w1 = np.repeat(w1[None], kb, 0).reshape(kb * INPUTS, -1)
        w2 = np.repeat(w2[None], ob, 0)
        b2 = np.repeat(b2, ob)
    else:
        from o30_v2net import read_v2
        n = read_v2(init)
        if n['kb'] != kb or n['ob'] != ob:
            raise SystemExit(f'init net shape kb {n["kb"]} ob {n["ob"]} != requested kb {kb} ob {ob}')
        w1, b1, w2, b2 = n['w1'].reshape(kb * INPUTS, -1), n['b1'], n['w2'], n['b2']
    f = lambda a: torch.tensor(np.asarray(a, np.float64) / 4096.0, dtype=torch.float32)
    params = {'w1': f(w1), 'b1': f(b1), 'w2': f(w2), 'b2': f(b2)}
    for v in params.values():
        v.requires_grad_(True)
    return params, kmap


def export(params, path, kmap, ob, residual, mirror):
    q = lambda t: np.clip(np.rint(t.detach().numpy().astype(np.float64) * 4096.0), -32768, 32767).astype(np.int16)
    kb = int(kmap.max()) + 1
    w1 = q(params['w1']).reshape(kb, INPUTS, -1)
    return write_v2(path, w1, q(params['b1']), q(params['w2']), q(params['b2']), list(kmap), output_map(ob), residual, mirror)


def score(net_path, pos, hce):
    r = subprocess.run([SCORER, '--net', net_path, '--pos', pos, '--hce', hce], capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'scorer failed: {r.stderr.strip()}')
    return json.loads(r.stdout.strip().splitlines()[-1])


def train(a):
    import torch
    torch.set_num_threads(1)
    run = os.path.abspath(a.out)
    last = os.path.join(run, 'last.pt')
    if a.resume:
        if not os.path.exists(last):
            sys.exit(f'--resume: {last} missing')
        ck = torch.load(last, weights_only=False)
        cfg = ck['config']
        for key in ('until', 'positions'):   # a resume may move the deadline / extend the run
            if getattr(a, key) is not None:
                cfg[key] = getattr(a, key)
    else:
        if os.path.exists(run):
            sys.exit(f'refusing: {run} exists (use --resume)')
        os.makedirs(os.path.join(run, 'nets'))
        cfg = {k: getattr(a, k) for k in ('data', 'pos_dir', 'hce_dir', 'init', 'kb_map', 'ob', 'stand_alone', 'blend', 'lr',
                                           'lr_end', 'positions', 'batch', 'block', 'save_minutes', 'seed', 'until', 'mirror',
                                           'lr_out_mult', 'mix')}
        cfg['created'] = time.strftime('%Y-%m-%d %H:%M:%S')
        with open(os.path.join(run, 'config.json'), 'w', newline='\n') as f:
            json.dump(cfg, f, indent=1)
        ck = None
    residual = not cfg['stand_alone']
    mirror = bool(cfg['mirror'])
    params, kmap = build_model(torch, cfg['init'], cfg['kb_map'], cfg['ob'])
    # output layer (w2, b2) may learn faster than the shared input layer: lr * lr_out_mult
    opt = torch.optim.Adam([{'params': [params['w1'], params['b1']], 'mult': 1.0},
                            {'params': [params['w2'], params['b2']], 'mult': float(cfg.get('lr_out_mult', 1.0))}], lr=cfg['lr'])
    state = {'step': 0, 'positions': 0, 'chunk': 0, 'in_chunk': 0, 'best': None, 'seconds': 0.0}
    if ck is not None:
        for k2 in params:
            params[k2].data.copy_(ck['params'][k2])
        opt.load_state_dict(ck['opt'])
        state = ck['state']
    data = Data(cfg['data'], cfg['pos_dir'], cfg['hce_dir'], cfg['block'], cfg['seed'])
    data.mix = int(cfg.get('mix', 1))   # runs from before the option keep their one-shard chunks
    omap = np.array(output_map(cfg['ob']), np.int64)
    deadline = dt.datetime.strptime(cfg['until'].replace('T', ' '), '%Y-%m-%d %H:%M') if cfg['until'] else None
    lim = 32767.0 / 4096.0
    ev = ctypes.windll.kernel32.CreateEventW(None, True, False, event_name(run))   # held while training runs
    val_csv = os.path.join(run, 'val.csv')
    log_csv = os.path.join(run, 'train.csv')
    first_val = not os.path.exists(val_csv)

    def lr_at(pos):
        frac = min(pos / float(cfg['positions']), 1.0)
        return cfg['lr_end'] + 0.5 * (cfg['lr'] - cfg['lr_end']) * (1 + math.cos(math.pi * frac))

    def checkpoint(tag):
        nonlocal first_val
        tmp = last + '.part'
        torch.save({'config': cfg, 'params': {k2: v.detach().clone() for k2, v in params.items()}, 'opt': opt.state_dict(),
                    'state': state}, tmp)
        os.replace(tmp, last)
        net = os.path.join(run, 'nets', f'step{state["step"]:08d}.nnue2')
        if not os.path.exists(net):
            export(params, net, kmap, cfg['ob'], residual, mirror)
        s16 = score(net, S16_POS, S16_HCE)
        jv = score(net, os.path.join(cfg['data'], 'jobA_val.pos'), os.path.join(cfg['data'], 'jobA_val.hce'))
        row = {'time': time.strftime('%Y-%m-%d %H:%M:%S'), 'tag': tag, 'step': state['step'], 'positions': state['positions'],
               'lr': f'{lr_at(state["positions"]):.3e}', 's16_b06': s16['mse_b0.6'], 's16_b10': s16['mse_b1.0'],
               'joba_b06': jv['mse_b0.6'], 'joba_b10': jv['mse_b1.0'], 'net': net}
        with open(val_csv, 'a', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(row))
            if first_val:
                w.writeheader()
                first_val = False
            w.writerow(row)
        if state['best'] is None or s16['mse_b0.6'] < state['best']['s16_b06']:
            state['best'] = {'s16_b06': s16['mse_b0.6'], 'step': state['step'], 'net': net}
            tmpb = os.path.join(run, 'best.pt.part')
            torch.save({'config': cfg, 'params': {k2: v.detach().clone() for k2, v in params.items()}, 'state': state}, tmpb)
            os.replace(tmpb, os.path.join(run, 'best.pt'))
            with open(net, 'rb') as src, open(os.path.join(run, 'best.nnue2.part'), 'wb') as dst:
                dst.write(src.read())
            os.replace(os.path.join(run, 'best.nnue2.part'), os.path.join(run, 'best.nnue2'))
        print(f'[{row["time"]}] {tag} step {state["step"]} pos {state["positions"]:.3e} s16 b0.6 {s16["mse_b0.6"]:.7f} '
              f'b1.0 {s16["mse_b1.0"]:.7f} jobA b0.6 {jv["mse_b0.6"]:.7f} best {state["best"]["s16_b06"]:.7f}', flush=True)

    if state['step'] == 0 and ck is None:
        checkpoint('init')
    t_save = time.time()
    t_start = time.time()
    loss_ema = None
    pos_since = 0
    log_first = not os.path.exists(log_csv)
    reason = 'positions'
    while state['positions'] < cfg['positions']:
        shard, start, boards, sc, meta, hce = data.chunk(state['chunk'])
        nb = len(sc) // cfg['batch']
        while state['in_chunk'] < nb and state['positions'] < cfg['positions']:
            i0 = state['in_chunk'] * cfg['batch']
            b = slice(i0, i0 + cfg['batch'])
            stm = (meta[b] & 1).astype(np.int64)
            white = (meta[b] >> 1) * 0.5
            stm_res = np.where(stm == 0, white, 1.0 - white)
            i_s, o_s, i_n, o_n, cnt = features(boards[b], stm, kmap, mirror)
            ob = torch.from_numpy(omap[np.minimum(cnt, 32)])
            acc_s = torch.nn.functional.embedding_bag(torch.from_numpy(i_s), params['w1'], torch.from_numpy(o_s), mode='sum') + params['b1']
            acc_n = torch.nn.functional.embedding_bag(torch.from_numpy(i_n), params['w1'], torch.from_numpy(o_n), mode='sum') + params['b1']
            a_s = acc_s.clamp(0.0, 1.0).square()
            a_n = acc_n.clamp(0.0, 1.0).square()
            w2 = params['w2'][ob]
            H = a_s.shape[1]
            out = (a_s * w2[:, :H]).sum(1) + (a_n * w2[:, H:]).sum(1) + params['b2'][ob]
            if residual:
                out = out + torch.from_numpy(hce[b].astype(np.float32)) * (K / 400.0)
            pred = torch.sigmoid(out)
            teacher = torch.sigmoid(torch.from_numpy(np.clip(sc[b].astype(np.float32) * (K / 400.0), -40.0, 40.0)))
            target = cfg['blend'] * teacher + (1.0 - cfg['blend']) * torch.from_numpy(stm_res.astype(np.float32))
            loss = ((pred - target) ** 2).mean()
            for g in opt.param_groups:
                g['lr'] = lr_at(state['positions']) * g.get('mult', 1.0)
            opt.zero_grad(set_to_none=True)
            loss.backward()
            opt.step()
            with torch.no_grad():
                for v in params.values():
                    v.clamp_(-lim, lim)
            lv = float(loss)
            loss_ema = lv if loss_ema is None else 0.99 * loss_ema + 0.01 * lv
            state['step'] += 1
            state['in_chunk'] += 1
            state['positions'] += cfg['batch']
            pos_since += cfg['batch']
            if state['step'] % 200 == 0:
                el = time.time() - t_start
                rate = pos_since / max(el, 1e-9)
                with open(log_csv, 'a', newline='') as f:
                    w = csv.writer(f)
                    if log_first:
                        w.writerow(['time', 'step', 'positions', 'lr', 'loss_ema', 'pos_per_s', 'shard', 'chunk'])
                        log_first = False
                    w.writerow([time.strftime('%Y-%m-%d %H:%M:%S'), state['step'], state['positions'],
                                f'{lr_at(state["positions"]):.3e}', f'{loss_ema:.7f}', f'{rate:.0f}', shard, state['chunk']])
                if free_ram_gb() < 6.0:
                    reason = 'ram'
                    break
                if ctypes.windll.kernel32.WaitForSingleObject(ev, 0) == 0:
                    reason = 'stop event'
                    break
                if deadline is not None and dt.datetime.now() >= deadline:
                    reason = 'deadline'
                    break
            if time.time() - t_save >= 60 * cfg['save_minutes']:
                state['seconds'] += time.time() - t_save
                checkpoint('periodic')
                t_save = time.time()
        else:
            state['chunk'] += 1
            state['in_chunk'] = 0
            continue
        if reason != 'positions':
            break
    state['seconds'] += time.time() - t_save
    checkpoint('final-' + reason.replace(' ', '_'))
    print(f'done: {reason}; best {state["best"]}', flush=True)


def selfcheck(a):
    """The trainer's own forward pass on the S31 holdout subset (no training) must reproduce the engine scorer's MSE:
    checks feature indices, perspectives, output buckets, the residual term and the target of THIS file."""
    import torch
    torch.set_num_threads(1)
    params, kmap = build_model(torch, a.init, a.kb_map, a.ob)
    omap = np.array(output_map(a.ob), np.int64)
    n = int.from_bytes(open(S16_POS, 'rb').read(16)[8:16], 'little')
    boards = np.fromfile(S16_POS, np.uint8, count=32 * n, offset=16).reshape(n, 32)
    sc = np.fromfile(S16_POS, '<i2', count=n, offset=16 + 32 * n)
    meta = np.fromfile(S16_POS, np.uint8, count=n, offset=16 + 34 * n)
    hce = np.fromfile(S16_HCE, '<i2', count=n, offset=16)
    sums = {0.6: 0.0, 1.0: 0.0}
    with torch.no_grad():
        for i0 in range(0, n, 16384):
            b = slice(i0, min(n, i0 + 16384))
            stm = (meta[b] & 1).astype(np.int64)
            white = (meta[b] >> 1) * 0.5
            stm_res = np.where(stm == 0, white, 1.0 - white)
            i_s, o_s, i_n, o_n, cnt = features(boards[b], stm, kmap, a.mirror)
            ob = torch.from_numpy(omap[np.minimum(cnt, 32)])
            acc_s = torch.nn.functional.embedding_bag(torch.from_numpy(i_s), params['w1'], torch.from_numpy(o_s), mode='sum') + params['b1']
            acc_n = torch.nn.functional.embedding_bag(torch.from_numpy(i_n), params['w1'], torch.from_numpy(o_n), mode='sum') + params['b1']
            a_s, a_n = acc_s.clamp(0, 1).square(), acc_n.clamp(0, 1).square()
            w2 = params['w2'][ob]
            H = a_s.shape[1]
            out = ((a_s * w2[:, :H]).sum(1) + (a_n * w2[:, H:]).sum(1) + params['b2'][ob]).double()
            logit = out + torch.from_numpy(hce[b].astype(np.float64)) * (K / 400.0)
            pred = torch.sigmoid(logit).numpy()
            teacher = 1.0 / (1.0 + np.exp(-np.clip(sc[b].astype(np.float64) * (K / 400.0), -40.0, 40.0)))
            for bl in sums:
                sums[bl] += float(np.sum((pred - (bl * teacher + (1.0 - bl) * stm_res)) ** 2))
    res = {f'mse_b{bl}': sums[bl] / n for bl in sums}
    print(json.dumps({'rows': n, **res}))
    want = (0.014310027, 0.004572428)
    ok = abs(res['mse_b0.6'] - want[0]) < 2e-8 and abs(res['mse_b1.0'] - want[1]) < 2e-8
    print('SELFCHECK ' + ('PASS' if ok else 'FAIL') + f' (scorer: b0.6 {want[0]}, b1.0 {want[1]})')
    sys.exit(0 if ok else 1)


def stop(run):
    h = ctypes.windll.kernel32.OpenEventW(0x0002 | 0x00100000, False, event_name(os.path.abspath(run)))
    if not h:
        sys.exit('no running trainer holds the stop event for ' + run)
    ctypes.windll.kernel32.SetEvent(h)
    print('stop requested: the trainer saves and exits at its next check (every 200 steps)')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    t = sub.add_parser('train')
    t.add_argument('--out', required=True)
    t.add_argument('--data', default=r'D:\o30\data')
    t.add_argument('--pos-dir', default=r'D:\grok-pc-data\forge_push\nnue_data\pos')
    t.add_argument('--hce-dir', default=r'D:\grok-pc-data\forge_push\nnue_data\hce')
    t.add_argument('--init', default='lock')
    t.add_argument('--kb-map', default='one', choices=['one', 'rank4'])
    t.add_argument('--mirror', action='store_true')
    t.add_argument('--ob', type=int, default=8)
    t.add_argument('--stand-alone', action='store_true')
    t.add_argument('--blend', type=float, default=0.6)
    t.add_argument('--lr', type=float, default=1e-4)
    t.add_argument('--lr-end', type=float, default=1e-6)
    t.add_argument('--lr-out-mult', type=float, default=1.0)
    t.add_argument('--mix', type=int, default=8, help='shards per chunk (1 = one block of one shard)')
    t.add_argument('--positions', type=float, default=None)
    t.add_argument('--batch', type=int, default=16384)
    t.add_argument('--block', type=int, default=1_000_000)
    t.add_argument('--save-minutes', type=float, default=25.0)
    t.add_argument('--seed', type=int, default=1)
    t.add_argument('--until', default=None)
    t.add_argument('--resume', action='store_true')
    s = sub.add_parser('stop')
    s.add_argument('run')
    c = sub.add_parser('selfcheck')
    c.add_argument('--init', default='lock')
    c.add_argument('--kb-map', default='one', choices=['one', 'rank4'])
    c.add_argument('--mirror', action='store_true')
    c.add_argument('--ob', type=int, default=8)
    a = ap.parse_args()
    if a.cmd == 'stop':
        stop(a.run)
        return
    if a.cmd == 'selfcheck':
        selfcheck(a)
        return
    if not a.resume and a.positions is None:
        a.positions = 2e9
    train(a)


if __name__ == '__main__':
    main()
