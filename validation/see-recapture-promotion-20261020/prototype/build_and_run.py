#!/usr/bin/env python3
"""FUTURE ONLY: invoke after root build/runtime clearance; default builds only."""
from pathlib import Path
import argparse, datetime, hashlib, importlib.util, json, os, shutil, subprocess, time

ROOT=Path(__file__).resolve().parent
RESEARCH=ROOT.parent
WORK=Path('/workspace/see-recapture-promotion-prototype-20261020')
CORE=Path('/workspace/.cloud-setup/forge-pin-mask-release/libforge_core.a')
ENV=dict(os.environ,PYTHONDONTWRITEBYTECODE='1')
parser=argparse.ArgumentParser()
parser.add_argument('--run',action='store_true',help='Also run two bounded API probes after building.')
parser.add_argument('--engine-budget-seconds',type=float,default=30)
parser.add_argument('--attempt',default='attempt1')
args=parser.parse_args()
if not 0<args.engine_budget_seconds<=120:raise SystemExit('Budget must be finite, positive, and at most120s.')
ATTEMPT=ROOT/args.attempt
ATTEMPT.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
freeze=json.loads((ROOT/'SOURCE-FREEZE.json').read_text())
record={'status':'RUNNING','started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'phases':[],'engine_budget_seconds':args.engine_budget_seconds,'engine_seconds':0,
        'source16_commit':freeze['source16_commit'],'performance_claim':None,'strength_claim':None}
def save():write(ATTEMPT/'record.json',record)
def run(label,command,timeout=60,engine=False):
    if engine and record['engine_seconds']+timeout>args.engine_budget_seconds:
        raise RuntimeError('Insufficient remaining engine budget for full timeout')
    start=time.monotonic()
    try:
        p=subprocess.run([str(x) for x in command],cwd=WORK,env=ENV,capture_output=True,timeout=timeout)
        rc,out,err=p.returncode,p.stdout,p.stderr
    except subprocess.TimeoutExpired as exc:rc,out,err=124,exc.stdout or b'',exc.stderr or b''
    elapsed=time.monotonic()-start
    for ext,data in [('stdout',out),('stderr',err)]: (ATTEMPT/(label+'.'+ext)).write_bytes(data)
    record['phases'].append({'label':label,'command':[str(x) for x in command],
        'exit_code':rc,'timeout_seconds':timeout,'engine_execution':engine,
        'elapsed_seconds_operational_only':elapsed,
        'stdout_sha256':sha(ATTEMPT/(label+'.stdout')),'stderr_sha256':sha(ATTEMPT/(label+'.stderr'))})
    if engine:record['engine_seconds']+=elapsed
    save();print(label,rc,flush=True)
    if rc:raise RuntimeError(label+' failed')
    return out
try:
    assert all(sha(ROOT/'inputs'/n)==h for n,h in freeze['input_sha256'].items())
    assert all(sha(ROOT/n)==h for n,h in freeze['source_only_file_sha256'].items())
    assert sha(CORE)=='a7718ec0555715e45b3aa96789754047e03db3104748a0fe8e03404e8695c267'
    assert sha(WORK/'source-candidate/src/board.cpp')==freeze['candidate_board_sha256']
    for label in ['reference','candidate']:
        assert all(sha(WORK/('source-'+label)/n)==h for n,h in freeze['header_sha256'].items())
    record['original_core_sha256_before']=sha(CORE)
    flags=next(line.split(' = ',1)[1].split() for line in (RESEARCH/'original-flags.make').read_text().splitlines() if line.startswith('CXX_FLAGS = '))
    for label in ['reference','candidate']:shutil.copy2(CORE,ATTEMPT/(label+'-libforge_core.a'))
    run('compile-candidate-board',['/usr/bin/c++',*flags,'-I'+str(WORK/'source-candidate/include'),'-c',
        WORK/'source-candidate/src/board.cpp','-o',ATTEMPT/'board.cpp.o'],90)
    run('replace-candidate-board',['ar','r',ATTEMPT/'candidate-libforge_core.a',ATTEMPT/'board.cpp.o'])
    run('ranlib-candidate',['ranlib',ATTEMPT/'candidate-libforge_core.a'])
    members=run('reference-members',['ar','t',CORE]).decode().splitlines()
    hashes={}
    for label in ['reference','candidate']:
        hashes[label]={m:hashlib.sha256(subprocess.check_output(['ar','p',ATTEMPT/(label+'-libforge_core.a'),m])).hexdigest() for m in members}
    assert [m for m in members if hashes['reference'][m]!=hashes['candidate'][m]]==['board.cpp.o']
    record['core_member_sha256']=hashes
    run('compile-api-driver',['/usr/bin/c++',*flags,'-I'+str(WORK/'source-reference/include'),'-c',
        ROOT/'api_driver.cpp','-o',ATTEMPT/'api_driver.o'],60)
    for label in ['reference','candidate']:
        run('link-api-'+label,['/usr/bin/c++',*flags,ATTEMPT/'api_driver.o',
            ATTEMPT/(label+'-libforge_core.a'),'-pthread','-o',ATTEMPT/('api-'+label)],60)
    if args.run:
        for label in ['reference','candidate']:
            run('api-'+label,[ATTEMPT/('api-'+label),ROOT/'inputs/all326.tsv',ROOT/'inputs/adjacent-brackets.tsv'],10,engine=True)
        spec=importlib.util.spec_from_file_location('promotion_compare',ROOT/'compare_results.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        result=module.evaluate(ATTEMPT/'api-reference.stdout',ATTEMPT/'api-candidate.stdout',ATTEMPT/'comparison.json')
        if result['failures']:raise RuntimeError('API parity/oracle gate failed; preserve attempt')
        record['status']='PASS_BOUNDED_API_GATE'
    else:record['status']='BUILT_NOT_EXECUTED'
    record['original_core_sha256_after']=sha(CORE)
    assert record['original_core_sha256_after']==record['original_core_sha256_before']
    assert all(sha(ROOT/'inputs'/n)==h for n,h in freeze['input_sha256'].items())
    assert all(sha(ROOT/n)==h for n,h in freeze['source_only_file_sha256'].items())
    record['completed_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();save()
except BaseException as exc:
    record['status']='FAILED_PRESERVE_ATTEMPT';record['error']=repr(exc);save();raise
