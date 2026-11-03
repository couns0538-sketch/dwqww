"""Owned sequential audit handoff after the closed-source scan. UNPROVEN."""
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

WORK = Path('D:/grok-pc-data/dwqww/astra-r8-datafilter')
ROOT = Path('C:/astra8_data/quality6h_20261102')
HERE = WORK/'astra_r8/datafilter'
sys.path.insert(0, str(HERE))
from filter_positions import low_priority, sha256
from resource_policy import storage_guard
import audit_raw_labels
import native_forge_smoke
import report_corpus


def save(path, value):
    payload=json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n'
    storage_guard(path,allowance=len(payload.encode('utf-8'))+1024*1024)
    with path.open('x',encoding='utf-8',newline='\n') as out:
        out.write(payload)


def main():
    low_priority()
    control=ROOT/'corpus_completion'
    storage_guard(control,allowance=64*1024*1024)
    control.mkdir()
    watched=[Path(__file__),*(HERE/name for name in (
        'report_corpus.py','profile_corpus.py','audit_raw_labels.py',
        'native_forge_smoke.py','filter_positions.py','records.py',
        'resource_policy.py','pgn_input.py'))]
    pins={str(path):sha256(path) for path in watched}
    plan=dict(source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=WORK,text=True).strip(),
              script_files=pins,priority='BelowNormal',compute_processes=1,
              strength='UNPROVEN',training_ready=False,
              stages=['complete_profile_report','literal_original_reservoir_replay','native_FD3A5190_perft2_and_bench'],
              started_utc=datetime.now(timezone.utc).isoformat())
    save(control/'RUN.json',plan)
    deadline=datetime(2026,11,3,3,11,tzinfo=timezone.utc)
    while True:
        try:
            json.loads((ROOT/'profile_rest_exit.json').read_text())
            break
        except (FileNotFoundError,json.JSONDecodeError):
            pass
        if datetime.now(timezone.utc)>=deadline:
            raise TimeoutError('complementary source profile did not finish before the reserved-review deadline')
        time.sleep(5)
    # The independent profile supervisor emits this only after its child closes.
    for prefix,launch_name,exit_name in (
            ('corpus_profile','profile_launch.json','profile_exit.json'),
            ('corpus_profile_rest','profile_rest_launch.json','profile_rest_exit.json')):
        exit_receipt=json.loads((ROOT/exit_name).read_text())
        if (exit_receipt.get('status')!='PASS' or exit_receipt.get('exit_code')!=0
                or exit_receipt.get('runtime_unchanged') is not True):
            raise ValueError('profile completion failed: '+prefix)
        for stream in ('stdout','stderr'):
            if sha256(ROOT/(prefix+'.'+stream+'.log'))!=exit_receipt[stream+'_sha256']:
                raise ValueError('closed profile log changed: '+prefix)
        launch=json.loads((ROOT/launch_name).read_text())
        if any(sha256(path)!=digest for path,digest in launch['runtime']['files'].items()):
            raise ValueError('profile runtime drift')
    if any(sha256(path)!=digest for path,digest in pins.items()):
        raise ValueError('auditor changed while awaiting profiles')
    profiles=[ROOT/'corpus_profile/SUMMARY.json',ROOT/'corpus_profile_rest/SUMMARY.json']
    timings={}
    start=time.perf_counter()
    report=report_corpus.run(profiles,ROOT/'corpus_report')
    timings['report_seconds']=time.perf_counter()-start
    print(json.dumps(dict(stage='corpus_report',status=report['status'],rows=report['totals']['data_rows'])),flush=True)
    start=time.perf_counter()
    reservoir=audit_raw_labels.audit_reservoirs(profiles,ROOT/'reservoir_audit')
    timings['reservoir_seconds']=time.perf_counter()-start
    if reservoir['rows']!=4736 or len(reservoir['sources'])!=37:
        raise ValueError('incomplete bounded reservoir')
    start=time.perf_counter()
    native=native_forge_smoke.run(ROOT/'native_corpus',ROOT/'reservoir_audit/audit_reservoir.jsonl',
                                  max_positions=4736)
    timings['native_total_seconds']=time.perf_counter()-start
    if (native['sample_positions']!=4736 or native['positions']!=9486
            or native['sample_sha256']!=reservoir['reservoir_sha256']):
        raise ValueError('native proof does not bind complete original reservoir')
    if any(sha256(path)!=digest for path,digest in pins.items()):
        raise ValueError('auditor changed during completion checks')
    receipt=dict(status='PASS',strength='UNPROVEN',training_ready=False,
                 source_commit=plan['source_commit'],script_files=pins,
                 source_rows=report['totals']['data_rows'],source_count=len(report['sources']),
                 reservoir_rows=reservoir['rows'],native_positions=native['positions'],
                 timings=timings,finished_utc=datetime.now(timezone.utc).isoformat(),
                 report_sha256=sha256(ROOT/'corpus_report/corpus_report.json'),
                 reservoir_receipt_sha256=sha256(ROOT/'reservoir_audit/reservoir_receipt.json'),
                 native_receipt_sha256=sha256(ROOT/'native_corpus/report.json'),
                 resource=storage_guard(control,allowance=1024*1024))
    save(control/'COMPLETE.json',receipt)
    print(json.dumps(receipt),flush=True)


if __name__=='__main__':
    main()
