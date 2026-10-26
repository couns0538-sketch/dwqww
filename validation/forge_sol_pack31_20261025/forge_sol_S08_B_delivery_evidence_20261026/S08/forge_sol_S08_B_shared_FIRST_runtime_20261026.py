"""FIRST bare-d11 execution of the frozen B shared ASan/UBSan build."""
from pathlib import Path
import hashlib, importlib.util, json, os, re, subprocess, time

HERE=Path(__file__).resolve().parent
RECEIPT=HERE/'forge_sol_S08_B_ASAN_SHARED_NODWARF_window1_20261026/forge_sol_S08_B_shared_ASAN_build_result_20261026.json'
RECEIPT_SHA='d97a6011f3a352ad15461f69bdffac413a9d749fc513c67e2898e05660ebb654'
FREEZE=HERE/'forge_sol_S08_B_v2_source_freeze_20261026.json'
OUT=HERE/'forge_sol_S08_B_SHARED_FIRST_native_20261026'
SHARED=HERE/'forge_sol_S08_build_window_subreaper_20261026.py'

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def main():
    assert sha(RECEIPT)==RECEIPT_SHA
    r=json.loads(RECEIPT.read_text());assert r['status']=='PASS_BUILD_ONLY' and r['pending_targets']==[]
    assert len(r['completed_targets'])==13 and len(r['target_artifacts'])==14
    assert r['runtime_artifact_manifest_complete'] and r['source_unchanged']
    b=Path(r['build_dir']);source=Path(r['source'])
    # The source freeze path is recorded by the actual successful build.
    assert r['source_freeze_sha256']=='fcd93778dc3bae5bed2f941c9ee0fff08f6ee07ce6ecf22bf82a007e8a8904d7'
    for n,x in r['target_artifacts'].items():assert sha(b/n)==x['sha256'] and (b/n).stat().st_size==x['bytes']
    assert sha(SHARED)=='85acc70b0dd987d21e6ae93276f7183eb23806b35a92dc217c72da2018ab8fa0'
    spec=importlib.util.spec_from_file_location('owned',SHARED);owned=importlib.util.module_from_spec(spec);spec.loader.exec_module(owned)
    assert owned.snapshot(source)==r['source_before']==r['source_after']
    OUT.mkdir(exist_ok=False);stdin=b'bench 11\nquit\n';(OUT/'forge.stdin').write_bytes(stdin)
    env=dict(os.environ,ASAN_OPTIONS='detect_leaks=1:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1',LD_LIBRARY_PATH=str(b),PYTHONDONTWRITEBYTECODE='1')
    env.pop('LD_PRELOAD',None)
    start=time.monotonic();timed_out=False;reaped=[]
    with owned.SubreaperScope():
        p=subprocess.Popen(['taskset','-c','4','nice','-n','19',str(b/'forge')],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,start_new_session=True)
        try:stdout,stderr=p.communicate(stdin,timeout=180)
        except subprocess.TimeoutExpired:
            timed_out=True;rows,left=owned._close_group(p);reaped.extend(rows);stdout,stderr=p.communicate()
        rows,left=owned._reap_group(p.pid,timeout=.2);reaped.extend(rows)
        if left:
            rows,left=owned._close_group(p);reaped.extend(rows)
    (OUT/'forge.stdout').write_bytes(stdout);(OUT/'forge.stderr').write_bytes(stderr)
    nodes=re.findall(rb'(?m)^info string bench depth 11 nodes (\d+) time \d+ nps \d+\r?$',stdout)
    unchanged=all(sha(b/n)==x['sha256'] for n,x in r['target_artifacts'].items()) and owned.snapshot(source)==r['source_before']
    result=dict(status='PASS' if p.returncode==0 and not timed_out and not stderr and nodes==[b'308972'] and unchanged and not left else 'FAIL',returncode=p.returncode,timeout=timed_out,bench_counts=[int(n) for n in nodes],first_runtime_bare_bench=True,no_UCI_before_bench=True,engine_executions=1,pid=p.pid,process_group=p.pid,reaped_descendants=reaped,remaining_group=left,elapsed_seconds=time.monotonic()-start,source_and_14_artifacts_unchanged=unchanged,build_receipt_sha256=RECEIPT_SHA,source_freeze_sha256=r['source_freeze_sha256'],runtime_artifacts=r['target_artifacts'],environment={k:env[k] for k in ('ASAN_OPTIONS','UBSAN_OPTIONS','LD_LIBRARY_PATH')},LD_PRELOAD_removed=True,no_speed_claim=True,streams={n:{'bytes':(OUT/('forge.'+n)).stat().st_size,'sha256':sha(OUT/('forge.'+n))} for n in ('stdin','stdout','stderr')})
    (OUT/'forge_sol_S08_B_shared_FIRST_result_20261026.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('status','returncode','bench_counts','elapsed_seconds')}),flush=True)
    return 0 if result['status']=='PASS' else 1

if __name__=='__main__':raise SystemExit(main())
