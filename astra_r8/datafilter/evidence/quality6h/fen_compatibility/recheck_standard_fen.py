"""Sequential verification of the reviewed FEN admission repair; no training."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

WORK = Path('D:/grok-pc-data/dwqww/astra-r8-datafilter')
HERE = WORK/'astra_r8/datafilter'
ROOT = Path('C:/astra8_data/quality6h_20261102')
sys.path.insert(0, str(HERE))
from audit_followup import run as converter_audit
from filter_positions import low_priority, input_identity, sha256
from records import read_records, dumps
from resource_policy import storage_guard
from native_forge_smoke import run as native_audit
from refresh_handoff import refresh
from verify_handoff import verify


def save(path, value):
    payload = json.dumps(value, indent=2, sort_keys=True, allow_nan=False)+'\n'
    storage_guard(path, allowance=len(payload.encode('utf-8'))+1024*1024)
    with path.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(payload)


def main():
    low_priority()
    output = ROOT/'fen_validation'
    storage_guard(output, allowance=100_000_000)
    output.mkdir()
    paths = [*HERE.glob('*.py'), Path(__file__)]
    pins = {str(path):sha256(path) for path in sorted(paths)}
    plan = dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'], cwd=WORK, text=True).strip(),
                source_files=pins, started_utc=datetime.now(timezone.utc).isoformat(),
                priority='BelowNormal', compute_processes=1, strength='UNPROVEN')
    save(output/'RUN.json', plan)
    timings = {}
    for stage in ('identity', 'orientation'):
        start = time.perf_counter()
        converter_audit(stage, output)
        timings[stage] = time.perf_counter()-start
        print(json.dumps(dict(stage=stage, status='PASS', seconds=timings[stage])), flush=True)
    cohorts = []
    sources = [
        (Path('D:/grok-pc-data/dwqww/astra8_data/cohort/million.jsonl'),
         'a3cc03b258dfe3adbe5e5d84b8c08dec96261d0b9b6fb8c0d9e87b874829ed1e'),
        (ROOT/'pgn_capture_million/records.jsonl',
         '803daf0fd7e5d01d18ec182d5117e7c1d5133534a288b92e7d674a710b50ee66')]
    for source, expected in sources:
        start = time.perf_counter()
        before = input_identity(source)
        if before['sha256'] != expected:
            raise ValueError('cohort changed before replay')
        count = 0
        digest = hashlib.sha256()
        for row in read_records(source):
            count += 1
            digest.update((dumps(row)+'\n').encode('utf-8'))
        after = input_identity(source)
        if before != after or count != 1_000_000 or digest.hexdigest() != expected:
            raise ValueError('cohort admission/serialization identity failed')
        receipt = dict(status='PASS', source=before, rows=count, serialized_sha256=digest.hexdigest(),
                       elapsed_seconds=time.perf_counter()-start)
        cohorts.append(receipt)
        print(json.dumps(dict(stage='cohort', path=str(source), rows=count, status='PASS')), flush=True)
    save(output/'cohort_replay.json', cohorts)
    start = time.perf_counter()
    native = native_audit(output/'native', ROOT/'reservoir_audit/audit_reservoir.jsonl', max_positions=4736)
    if native['sample_positions'] != 4736 or native['positions'] != 9486:
        raise ValueError('native sample coverage differs')
    timings['native'] = time.perf_counter()-start
    print(json.dumps(dict(stage='native', status='PASS', positions=9486)), flush=True)
    start = time.perf_counter()
    refresh(ROOT/'handoff_v5')
    published = verify(ROOT/'handoff_v5/manifest.json')
    save(output/'published_verify.json', published)
    timings['handoff'] = time.perf_counter()-start
    if any(sha256(path) != digest for path,digest in pins.items()):
        raise ValueError('reviewed source changed during verification')
    complete = dict(plan, status='PASS', finished_utc=datetime.now(timezone.utc).isoformat(),
                    timings=timings, known_cohort_rows=2_000_000, native_positions=9486,
                    manifest_sha256=published['manifest_sha256'],
                    receipts={path.name:sha256(path) for path in output.glob('*.json')},
                    native_receipt_sha256=sha256(output/'native/report.json'),
                    resource=storage_guard(output, allowance=1024*1024))
    save(output/'COMPLETE.json', complete)
    print(json.dumps(dict(stage='complete', status='PASS', manifest_sha256=published['manifest_sha256'])), flush=True)


if __name__ == '__main__':
    main()
