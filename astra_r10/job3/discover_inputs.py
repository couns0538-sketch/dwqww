"""Capture bounded, read-only Job3 input metadata; never decode full datasets."""
import argparse
import hashlib
import json
import pathlib
import sys
import time

ROOT = pathlib.Path('D:/a10')
WT = ROOT / 'wt'
SOURCE = pathlib.Path('D:/grok-pc-data/dwqww/astra8_data')
EXPORTS = pathlib.Path('D:/grok-pc-data/selfplay_out')
OUT = WT / 'astra_r10/job3/discovery01'
sys.path.insert(0, str(ROOT / 'pydeps'))
import psutil
sys.path.insert(0, 'D:/a10/wt/astra_r10/job1')  # CR crfix 0e91e02e: shared lane guard (crfix_abcbb9c9 lane_guard.py 596ecbe6)
import lane_guard
sys.path.insert(0, str(WT / 'skills/gate-handover-pack/scripts'))
import seal_evidence as safety


def assert_regular(path):
    for item in (path, *path.parents):
        if item.exists() and getattr(item.lstat(), 'st_file_attributes', 0) & 1024:
            raise ValueError('reparse point refused: ' + str(item))
    if not path.is_file():
        raise ValueError('regular file required: ' + str(path))


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--threads', type=int, choices=[1], required=True)
    p.parse_args()
    lane_guard.check_lane()  # before any output
    proc = psutil.Process()
    if proc.nice() != psutil.IDLE_PRIORITY_CLASS or not set(proc.cpu_affinity()) <= {2, 3}:
        raise RuntimeError('safe launcher required')
    if OUT.exists():
        raise ValueError('preserve existing discovery')
    safety.disk_budget(10_000_000)
    if safety.workspace_bytes() + 10_000_000 > safety.CAP:
        raise ValueError('workspace cap')
    load = psutil.cpu_percent(interval=2, percpu=True)
    if max(load[2:4]) >= 70 or sum(load) / len(load) >= 98:
        raise RuntimeError('saturated host; metadata discovery not started')
    OUT.mkdir(parents=True)
    (OUT / 'load.json').write_text(json.dumps({'cpu2_3': load[2:4], 'total_mean': sum(load) / len(load)}))
    metadata = [
        'handoff/manifest.json', 'handoff/full_output_hashes.json',
        'handoff/verification.json', 'holdout_cleared/clearance.json',
        'holdout_cleared/selection.json', 'cohort/manifest.json',
        'independent_audit/holdout013.json', 'independent_audit/holdout014.json',
    ]
    records = []
    for rel in metadata:
        src = SOURCE / rel
        assert_regular(src)
        if src.stat().st_size > 100_000:
            raise ValueError('metadata size bound')
        raw = src.read_bytes()
        dst = OUT / 'original-metadata' / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        with dst.open('xb') as stream:
            stream.write(raw)
        records.append({'source': str(src), 'copy': str(dst), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()})
    datasets = []
    selected = [EXPORTS / ('forge_selfplay_' + shard + '.txt') for shard in ('001', '002', '013', '014')]
    selected += [SOURCE / 'holdout_cleared/records.jsonl', SOURCE / 'cohort/million.jsonl', SOURCE / 'handoff/sample.jsonl']
    for src in selected:
        assert_regular(src)
        stat = src.stat()
        with src.open('r', encoding='utf-8') as stream:
            line = stream.readline(20_000)
        if not line.endswith('\n'):
            raise ValueError('unexpectedly long first record')
        datasets.append({'path': str(src), 'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns,
                         'first_line': line.rstrip('\r\n'), 'fresh_full_hash': None,
                         'fresh_full_hash_status': 'NOT_RUN_METADATA_DISCOVERY_ONLY'})
    sidecar_names = [p.name for p in EXPORTS.iterdir() if p.is_file() and any(t in p.name.lower() for t in ('001', '002', '013', '014', 'manifest', 'game', 'fen', 'sidecar', 'sha256'))]
    report = {'status': 'METADATA_DISCOVERED', 'classification': 'UNPROVEN',
              'time_unix': time.time(), 'metadata': records, 'datasets': datasets,
              'related_export_filenames': sidecar_names,
              'limitations': ['Full dataset hashes/counts are historical manifest claims until frozen and freshly verified.',
                              'Inspected source records and filtered JSONL have no authentic game ID field.',
                              'No F: reference was followed; no protected live trainer input was opened.',
                              'Existing historical training_ready does not clear the new authentic-game requirement.']}
    with (OUT / 'DISCOVERY.json').open('x') as stream:
        json.dump(report, stream, indent=2)
    print(json.dumps({'status': report['status'], 'metadata_files': len(records), 'dataset_stats': len(datasets), 'report': str(OUT / 'DISCOVERY.json')}))


if __name__ == '__main__':
    main()
