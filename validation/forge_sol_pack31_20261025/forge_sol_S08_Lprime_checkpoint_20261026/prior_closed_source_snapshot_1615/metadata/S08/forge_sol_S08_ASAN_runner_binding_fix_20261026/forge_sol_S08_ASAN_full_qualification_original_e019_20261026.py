#!/usr/bin/env python3
"""Run the complete configured repaired-v2 sanitizer CTest inventory.

Requires a closed full-build PASS and the original first-runtime PASS. Keeps
original discovery/JUnit/streams. Fixed-work correctness only, never a speed run.
"""
import argparse, datetime, hashlib, importlib.util, json, os, pathlib, shutil, signal, subprocess, time

HERE = pathlib.Path(__file__).resolve().parent
BUILD = HERE / 'forge_sol_S08_ASAN_v2_window1_20261026/build'
SOURCE = HERE / 'Lprime_v2'
CTEST = pathlib.Path('/workspace/.cloud-setup/venv/lib/python3.12/site-packages/cmake/data/bin/ctest')
HELPER = HERE.parent/'S26/successor_ctest_v4/forge_sol_S26_netbatch_v4_20261026.py'
HELPER_SHA = '4dbf73e63032d7512c6beff12fdca03b7d29e1489b6d0ae3cab26b09753ac36f'
ALLOW = HERE.parent/'S26/forge_sol_S26_allowlist_20261026.json'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--execute', action='store_true')
    ap.add_argument('--closed-build-receipt', required=True, type=pathlib.Path)
    ap.add_argument('--output', required=True, type=pathlib.Path)
    a = ap.parse_args()
    if not a.execute: ap.error('execution must be explicit')
    build_receipt = json.loads(a.closed_build_receipt.read_text())
    assert build_receipt['status'] == 'PASS_BUILD_ONLY'
    assert not build_receipt.get('pending_targets')
    assert len(build_receipt['completed_targets']) == 12
    first_path = HERE/'forge_sol_S08_TLS_v2_FIRST_native_20261026/forge_sol_S08_TLS_v2_first_runtime_result_20261026.json'
    first = json.loads(first_path.read_text())
    frozen = next(r for r in first['results'] if r['label'] == 'ASAN')
    assert frozen['pass'] and frozen['bench_counts'] == [308972]
    assert sha(BUILD/'forge') == frozen['binary_sha256_before']
    assert sha(HELPER) == HELPER_SHA
    assert shutil.disk_usage(HERE).free >= 20*1048576
    spec = importlib.util.spec_from_file_location('s26_full_inventory_guard', HELPER)
    helper = importlib.util.module_from_spec(spec); spec.loader.exec_module(helper)
    a.output.mkdir(exist_ok=False)
    receipt = dict(status='RUNNING', source=str(SOURCE), build=str(BUILD), no_speed_claim=True, first_runtime_receipt_sha256=sha(first_path), closed_build_receipt_sha256=sha(a.closed_build_receipt), helper_sha256=HELPER_SHA, commands=[])
    env = dict(os.environ, ASAN_OPTIONS='detect_leaks=1:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1', PYTHONDONTWRITEBYTECODE='1')
    path = a.output/'forge_sol_S08_ASAN_full_qualification_result_20261026.json'
    def save(): path.write_text(json.dumps(receipt, indent=2)+'\n')
    def run(argv, name, timeout):
        start = time.monotonic()
        row = dict(argv=argv, started_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(), affinity=[4], nice=19)
        with (a.output/(name+'.stdout')).open('xb') as out, (a.output/(name+'.stderr')).open('xb') as err:
            p = subprocess.Popen(['taskset','-c','4','nice','-n','19',*argv], stdout=out, stderr=err, env=env, start_new_session=True)
            row['pid']=p.pid
            try: p.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                row['timeout']=True
                os.killpg(p.pid,signal.SIGTERM)
                try: p.wait(timeout=5)
                except subprocess.TimeoutExpired: os.killpg(p.pid,signal.SIGKILL); p.wait()
        row.update(returncode=p.returncode,elapsed_seconds=time.monotonic()-start,stdout_sha256=sha(a.output/(name+'.stdout')),stderr_sha256=sha(a.output/(name+'.stderr')))
        receipt['commands'].append(row);save()
        return row
    save()
    try:
        discovery = run([str(CTEST),'--test-dir',str(BUILD),'--show-only=json-v1'],'discovery',60)
        assert discovery['returncode']==0 and not (a.output/'discovery.stderr').read_bytes()
        inventory = helper.load_ctest_inventory(a.output/'discovery.stdout',SOURCE,BUILD)
        assert len(inventory['expected_names'])==15
        receipt['inventory']=inventory;save()
        junit = a.output/'forge_sol_S08_ASAN_full_ctest_20261026.xml'
        c = run([str(CTEST),'--test-dir',str(BUILD),'--output-on-failure','--no-tests=error','--parallel','1','--output-junit',str(junit)],'ctest',1800)
        allow = helper.bind_allowlist(json.loads(ALLOW.read_text()),sha(SOURCE/'tests/tests.cpp'),sha(SOURCE/'src/nnue_weights.inc'))
        receipt['ctest_proof']=helper.check_ctest(junit,c['returncode'],allow,inventory['expected_names'])
        assert c['returncode']==0 and not c.get('timeout',False)
        assert not (a.output/'ctest.stderr').read_bytes()
        assert all(not r['failed'] for r in receipt['ctest_proof']['test_cases'])
        assert sha(BUILD/'forge')==frozen['binary_sha256_before']
        receipt['status']='PASS'
    except Exception as e:
        receipt.update(status='FAIL',failure=type(e).__name__+': '+str(e))
    finally:
        receipt['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
    print(json.dumps(dict(status=receipt['status'],output=str(a.output))),flush=True)
    return 0 if receipt['status']=='PASS' else 1

if __name__=='__main__': raise SystemExit(main())
