"""One final offline verification; only benign process fixtures, never engines."""
import hashlib,importlib.util,json,os,signal,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1];PKG=REPO/'.github/hosted-runtime-psqt-performance'
spec=importlib.util.spec_from_file_location('offline_common',PKG/'common.py');common=importlib.util.module_from_spec(spec);spec.loader.exec_module(common)
spec=importlib.util.spec_from_file_location('offline_owned',PKG/'owned_process.py');owned=importlib.util.module_from_spec(spec);spec.loader.exec_module(owned)
cfg=json.loads((PKG/'protocol.json').read_text())
paths=common.inventory(REPO,PKG)+common.proof_paths(REPO,cfg)+list(ROOT.glob('test_*.py'))+[Path(__file__)]+[p for p in (ROOT/'build-fixtures/actual').rglob('*') if p.is_file()]
before=common.snapshot(paths)
command=[sys.executable,'-B','-m','unittest','discover','-s',str(ROOT.relative_to(REPO)),'-p','test_*.py','-v']
facts={'command':command,'cwd':str(REPO),'environment_overrides':{'PYTHONDONTWRITEBYTECODE':'1','PROCESS_TEST_PHASE':'final-combined'},'source_and_proof_inputs_before':before,'scope':'Analysis/guards, actual capture replay and benign/mock process tests only; no engines/build/Git/network/launch.'}
common.save(ROOT/'OFFLINE-COMMAND.json',facts);process=None;started=time.monotonic()
try:
    with (ROOT/'offline-final.stdout').open('xb') as stdout,(ROOT/'offline-final.stderr').open('xb') as stderr:
        process=subprocess.Popen(command,cwd=REPO,stdout=stdout,stderr=stderr,start_new_session=True,env=dict(os.environ,**facts['environment_overrides']))
        facts['pid']=process.pid
        try:process.wait(timeout=60)
        finally:
            facts['returncode_before_verdict']=process.returncode;facts['group_empty_before_verdict']=owned._owned_group_empty(process)
            if process.returncode is None or not facts['group_empty_before_verdict']:owned.stop_group(process)
        facts['returncode']=process.returncode;facts['group_empty_after_cleanup']=owned._owned_group_empty(process)
finally:
    facts['elapsed_seconds']=time.monotonic()-started;facts['final_input_rehash']=common.rehash(before)
    for stream in ('stdout','stderr'):facts[stream+'_sha256']=common.sha(ROOT/('offline-final.'+stream))
    facts['status']='PASS' if facts.get('returncode')==0 and facts.get('group_empty_before_verdict') and facts.get('group_empty_after_cleanup') and facts['final_input_rehash']['status']=='passed' else 'FAIL'
    common.save(ROOT/'OFFLINE-FINAL.json',facts)
if facts['status']!='PASS':raise SystemExit(1)
