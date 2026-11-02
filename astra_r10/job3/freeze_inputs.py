"""Freeze only the six expressly authorized Job3 data files, preserving originals."""
import argparse
import hashlib
import json
import pathlib
import sys
import time

ROOT = pathlib.Path('D:/a10')
WT = ROOT / 'wt'
DEST = ROOT / 'job3/inputs'
OUT = WT / 'astra_r10/job3/freeze01'
sys.path.insert(0, str(ROOT / 'pydeps'))
import psutil
sys.path.insert(0, str(WT / 'skills/gate-handover-pack/scripts'))
import seal_evidence as safety
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from discover_inputs import assert_regular

SPEC = [
    ('source001', 'D:/grok-pc-data/selfplay_out/forge_selfplay_001.txt', 29974655,
     'de27d81720c0e33f10e0fa95e48b1f619b1325bf35675cd2fcd016fe48f338a2'),
    ('source002', 'D:/grok-pc-data/selfplay_out/forge_selfplay_002.txt', 201066420,
     '16f3d241c1080b21bd7d05a3a297ef4ff11b49dea025c6301383815e85cb55b0'),
    ('holdout013', 'D:/grok-pc-data/selfplay_out/forge_selfplay_013.txt', 650287208,
     'fa383b67aa30b8df79d5989b8fc5a92b5edf615fcfca0f1b46085c47600e17b9'),
    ('holdout014', 'D:/grok-pc-data/selfplay_out/forge_selfplay_014.txt', 415563024,
     'b2c8ec79a2f24b72d5c1a124a14f64cd46c04221ff405cb4409b755a75abbef0'),
    ('cohort', 'D:/grok-pc-data/dwqww/astra8_data/cohort/million.jsonl', 315050752,
     'a3cc03b258dfe3adbe5e5d84b8c08dec96261d0b9b6fb8c0d9e87b874829ed1e'),
    ('filtered', 'D:/grok-pc-data/dwqww/astra8_data/holdout_cleared/records.jsonl', 315036094,
     '0e73a87c2e1af035aed34f51fdd74daefc05833ce133f254845f09f23aeb5dce'),
]


def digest(path):
    sha = hashlib.sha256()
    md5 = hashlib.md5()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            sha.update(block)
            md5.update(block)
    return {'sha256': sha.hexdigest(), 'md5': md5.hexdigest()}


def stamp(path):
    st = path.stat()
    return {'bytes': st.st_size, 'mtime_ns': st.st_mtime_ns}


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--threads', type=int, choices=[1], required=True)
    p.parse_args()
    me = psutil.Process()
    if me.nice() != psutil.IDLE_PRIORITY_CLASS or not set(me.cpu_affinity()) <= {2, 3}:
        raise RuntimeError('safe launcher required')
    if DEST.exists() or OUT.exists():
        raise ValueError('preserve frozen data and receipts; destination must be fresh')
    total = sum(row[2] for row in SPEC)
    reservation = total + 10_000_000
    safety.disk_budget(reservation)
    used = safety.workspace_bytes()
    if used + reservation > safety.CAP:
        raise ValueError('workspace cap would be exceeded')
    for _, source, size, _ in SPEC:
        src = pathlib.Path(source)
        assert_regular(src)
        if src.stat().st_size != size:
            raise ValueError('source size differs from trusted manifest: ' + source)
    DEST.mkdir(parents=True)
    OUT.mkdir(parents=True)
    (OUT / 'preflight.json').write_text(json.dumps({'bytes_to_copy': total, 'reservation': reservation, 'workspace_before': used,
                                                  'free_C': psutil.disk_usage('C:/').free, 'free_D': psutil.disk_usage('D:/').free}, indent=2))
    results = []
    for role, source, expected_size, expected_sha in SPEC:
        for attempt in range(30):
            load = psutil.cpu_percent(interval=2, percpu=True)
            with (OUT / 'load.jsonl').open('a') as stream:
                stream.write(json.dumps({'role': role, 'attempt': attempt, 'cpu2_3': load[2:4], 'total_mean': sum(load) / len(load)}) + '\n')
            if max(load[2:4]) < 60 and sum(load) / len(load) < 98:
                break
            time.sleep(10)
        else:
            raise RuntimeError('saturated host; no further copying')
        safety.disk_budget(expected_size + 10_000_000)
        src = pathlib.Path(source)
        assert_regular(src)
        before_stat = stamp(src)
        before = digest(src)
        if before['sha256'] != expected_sha or before_stat['bytes'] != expected_size:
            raise ValueError('trusted hash/size mismatch for ' + role)
        target = DEST / role / src.name
        target.parent.mkdir(parents=True)
        copied = hashlib.sha256()
        copied_bytes = 0
        with src.open('rb') as reader, target.open('xb') as writer:
            for block in iter(lambda: reader.read(4 * 1024 * 1024), b''):
                writer.write(block)
                copied.update(block)
                copied_bytes += len(block)
        after_source = digest(src)
        after_target = digest(target)
        after_stat = stamp(src)
        if before != after_source or before != after_target or copied.hexdigest() != expected_sha or copied_bytes != expected_size or before_stat != after_stat:
            raise ValueError('source changed or frozen copy differs for ' + role)
        row = {'role': role, 'source': source, 'copy': str(target), 'bytes': copied_bytes, **after_target,
               'source_before': before, 'source_after': after_source, 'copy_after': after_target,
               'source_before_stat': before_stat, 'source_after_stat': after_stat, 'status': 'HASH_IDENTICAL',
               'trusted_sha256': expected_sha, 'full_hash_reads': 'source before; source after; frozen copy after; copy stream SHA256'}
        results.append(row)
        with (OUT / (role + '.json')).open('x') as stream:
            json.dump(row, stream, indent=2)
        print(json.dumps({'role': role, 'bytes': copied_bytes, 'sha256': after_target['sha256'], 'status': row['status']}), flush=True)
    report = {'status': 'FROZEN_HASH_IDENTICAL', 'classification': 'UNPROVEN', 'bytes': total, 'files': results,
              'meaning': 'Input identity only; no overlap, game-ID, FEN, or training-readiness claim.',
              'source_mapping': {'source001': 'source raw rows 1..466506', 'source002': 'source raw rows 1..533494'},
              'metadata_evidence': str(WT / 'astra_r10/job3/discovery01/DISCOVERY.json')}
    for dst in (OUT / 'INPUTS.json', DEST / 'INPUTS.json'):
        with dst.open('x') as stream:
            json.dump(report, stream, indent=2)


if __name__ == '__main__':
    main()
