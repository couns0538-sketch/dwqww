#!/usr/bin/env python3
"""relabel_job.py - R13 P5: resumable, sharded Windows relabel job around Astra's relabel_positions.run (own code).

usage:
  python -I -B relabel_job.py run --pos P.pos --probe forge_data_probe.exe --job JOB_DIR --run-id ID
         [--sidecar FEN_FILE --sidecar-origin original_full_fen | --allow-reconstructed]
         [--rows N] [--shard-size 20000] [--nodes 20000] [--workers 2] [--hash-mb 1] [--until "YYYY-MM-DD HH:MM"]
         [--max-shards K] [--mask 0xC]
  python -I -B relabel_job.py status JOB_DIR

- The subset is deterministic: rows 0 .. N-1 of the input in order (default all rows), cut into shards of --shard-size rows;
  shard k = rows [k*S, min(N, (k+1)*S)).
- Each shard is one relabel_positions.run (Astra, unchanged copy next to this file) into its own NEW directory
  JOB/shards/shard_<k>; it publishes summary.json + manifest.json (sha256 of every output file) last. A shard directory that
  exists without summary.json (interrupted) is left as it is; the shard is redone into shard_<k>_r<attempt>. Inputs are only
  read; nothing is modified in place or deleted.
- Resume = the same command again (job.json pins the config; a different config is refused). Stop: --until / --max-shards
  (no STOP/PAUSE files).
- Priority: this process and every child run at Idle (IDLE_PRIORITY_CLASS) on --mask (default CPUs 2-3); --workers probe
  processes = threads (R13 rule: <= 2).
- Every status file carries the run id: job.json, status.json (rewritten after each shard), shards.tsv (one line per
  finished shard: shard, rows, dir, seconds, output sha256s from its manifest, run id).
"""
import argparse
import ctypes
import datetime as dt
import hashlib
import json
import os
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))


def sha256(path):
    h = hashlib.sha256()
    with open(path, 'rb') as fh:
        for block in iter(lambda: fh.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def lower_priority(mask):
    if os.name != 'nt':
        os.nice(19)
        return
    k = ctypes.WinDLL('kernel32', use_last_error=True)
    k.GetCurrentProcess.restype = ctypes.c_void_p
    proc = k.GetCurrentProcess()
    if not k.SetPriorityClass(ctypes.c_void_p(proc), 0x40):  # IDLE_PRIORITY_CLASS, inherited by children
        raise SystemExit(f'SetPriorityClass failed: {ctypes.get_last_error()}')
    if not k.SetProcessAffinityMask(ctypes.c_void_p(proc), ctypes.c_size_t(mask)):
        raise SystemExit(f'SetProcessAffinityMask failed: {ctypes.get_last_error()}')


def atomic_json(path, obj):
    tmp = path.with_name(path.name + '.part')
    tmp.write_text(json.dumps(obj, indent=1) + '\n', encoding='utf-8', newline='\n')
    os.replace(tmp, path)


def count_rows(pos_path):
    from forge_pos import PosReader
    with PosReader(Path(pos_path)) as reader:
        return reader.n


def cmd_run(a):
    lower_priority(int(a.mask, 0))
    import relabel_positions as rp
    job = Path(a.job)
    (job / 'shards').mkdir(parents=True, exist_ok=True)
    total = count_rows(a.pos)
    rows = min(a.rows or total, total)
    config = {'pos': str(Path(a.pos).resolve()), 'pos_sha256': None, 'sidecar': a.sidecar, 'sidecar_origin': a.sidecar_origin,
              'allow_reconstructed': a.allow_reconstructed, 'probe': str(Path(a.probe).resolve()), 'rows': rows,
              'shard_size': a.shard_size, 'nodes': a.nodes, 'workers': a.workers, 'hash_mb': a.hash_mb}
    jf = job / 'job.json'
    if jf.exists():
        old = json.loads(jf.read_text(encoding='utf-8'))
        for key in config:
            if key != 'pos_sha256' and old['config'].get(key) != config[key]:
                raise SystemExit(f'job config differs at {key!r}: {old["config"].get(key)!r} vs {config[key]!r}')
        if old['run_id'] != a.run_id:
            raise SystemExit(f'run id differs: {old["run_id"]} vs {a.run_id}')
        config['pos_sha256'] = old['config']['pos_sha256']
    else:
        config['pos_sha256'] = sha256(a.pos)
        atomic_json(jf, {'run_id': a.run_id, 'created': dt.datetime.now().isoformat(timespec='seconds'), 'config': config,
                         'probe_sha256': sha256(a.probe), 'tool': 'opus_r13/p5/relabel_job.py'})
    shards = (rows + a.shard_size - 1) // a.shard_size
    until = dt.datetime.strptime(a.until, '%Y-%m-%d %H:%M') if a.until else None
    tsv = job / 'shards.tsv'
    done = {}
    if tsv.exists():
        for line in tsv.read_text(encoding='utf-8').splitlines()[1:]:
            parts = line.split('\t')
            done[int(parts[0])] = parts
    else:
        tsv.write_text('shard\trows\tdir\tseconds\tpos_sha256\thce_sha256\tfen_sha256\trun_id\n', encoding='utf-8', newline='\n')
    started = time.time()
    ran = 0
    for k in range(shards):
        if k in done:
            continue
        if until and dt.datetime.now() >= until:
            break
        if a.max_shards and ran >= a.max_shards:
            break
        start, count = k * a.shard_size, min(a.shard_size, rows - k * a.shard_size)
        out = job / 'shards' / f'shard_{k:05d}'
        attempt = 0
        while out.exists():
            if (out / 'summary.json').exists():
                break
            attempt += 1
            out = job / 'shards' / f'shard_{k:05d}_r{attempt}'
        if not (out / 'summary.json').exists():
            t0 = time.time()
            c = rp.Config(pos=Path(a.pos), sidecar=Path(a.sidecar) if a.sidecar else None, out=out, probe=Path(a.probe),
                          nodes=a.nodes, workers=a.workers, hash_mb=a.hash_mb, start=start, count=count, stride=1,
                          batch_size=128, allow_reconstructed=a.allow_reconstructed, stem=f'relabel_{k:05d}',
                          sidecar_origin=a.sidecar_origin)
            rp.run(c)
            seconds = time.time() - t0
        else:
            seconds = float('nan')
        manifest = json.loads((out / 'manifest.json').read_text(encoding='utf-8'))
        pick = lambda ext: next((v for name, v in manifest.items() if name.endswith(ext)), '-')
        with open(tsv, 'a', encoding='utf-8', newline='\n') as fh:
            fh.write(f'{k}\t{count}\t{out.name}\t{seconds:.1f}\t{pick(".pos")}\t{pick(".hce")}\t{pick(".fen")}\t{a.run_id}\n')
        ran += 1
        done[k] = [str(k), str(count)]
        finished_rows = sum(int(v[1]) for v in done.values())
        elapsed = time.time() - started
        atomic_json(job / 'status.json', {
            'run_id': a.run_id, 'updated': dt.datetime.now().isoformat(timespec='seconds'), 'shards_total': shards,
            'shards_done': len(done), 'rows_total': rows, 'rows_done': finished_rows,
            'this_session_rows': ran * a.shard_size, 'this_session_seconds': round(elapsed, 1),
            'positions_per_hour_this_session': round(ran * a.shard_size / elapsed * 3600) if elapsed > 0 else None,
            'nodes': a.nodes, 'workers': a.workers})
        print(f'shard {k} done ({count} rows, {seconds:.0f} s), {len(done)}/{shards} shards', flush=True)
    print('stopped' if len(done) < shards else 'all shards done', flush=True)


def cmd_status(a):
    job = Path(a.job)
    print((job / 'status.json').read_text(encoding='utf-8') if (job / 'status.json').exists() else 'no status yet')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    r = sub.add_parser('run')
    r.add_argument('--pos', required=True)
    r.add_argument('--probe', required=True)
    r.add_argument('--job', required=True)
    r.add_argument('--run-id', required=True)
    r.add_argument('--sidecar')
    r.add_argument('--sidecar-origin', default='auto')
    r.add_argument('--allow-reconstructed', action='store_true')
    r.add_argument('--rows', type=int, default=0)
    r.add_argument('--shard-size', type=int, default=20000)
    r.add_argument('--nodes', type=int, default=20000)
    r.add_argument('--workers', type=int, default=2)
    r.add_argument('--hash-mb', type=int, default=1)
    r.add_argument('--until')
    r.add_argument('--max-shards', type=int, default=0)
    r.add_argument('--mask', default='0xC')
    s = sub.add_parser('status')
    s.add_argument('job')
    a = ap.parse_args()
    if a.cmd == 'run':
        if a.workers > 2:
            raise SystemExit('R13 rule: at most 2 worker threads')
        cmd_run(a)
    else:
        cmd_status(a)


if __name__ == '__main__':
    main()
