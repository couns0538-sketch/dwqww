#!/usr/bin/env python3
"""PREPARED ONLY. No source export; refuses execution without exact root clearance."""
from pathlib import Path
import argparse,hashlib,json,os,re,subprocess,time,sys
sys.dont_write_bytecode=True
from process_facts import cleanup
HERE=Path(__file__).resolve().parent
REV='2e151d019bc58dff2ab4e76e99ef99516af8d222'
FLAGS='-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -fno-lto'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_text())
def snapshot(p):return {str(f.relative_to(p)):sha(f) for f in sorted(p.rglob('*')) if f.is_file()}
def get(d,path):
 for part in path.split('.'):d=d[part]
 return d
p=argparse.ArgumentParser();p.add_argument('--phase',choices=['red','green'],required=True);a=p.parse_args()
# Gate is before directory creation, source export, subprocess or compiler invocation.
c=load(HERE/'EXECUTION-CLEARANCE.json')
assert c['authorized_by_root'] is True and c['phase']==a.phase and c['source_commit']==REV
assert c['native21_complete_and_reviewed'] is True and c['competing_heavy_work_idle'] is True
receipt=Path(c['native21_receipt']['path']);assert sha(receipt)==c['native21_receipt']['sha256']
assert get(load(receipt),c['native21_receipt']['status_field'])==c['native21_receipt']['status_value']
assert c['protocol_sha256']==sha(HERE/'PROTOCOL.md')
assert c['driver_sha256']==sha(Path(__file__))
assert c['probe_sha256']==sha(HERE/'worker_probe.cpp')
assert c['cleanup_sha256']==sha(HERE/'process_facts.py')
source=Path(c['isolated_source']);assert source.is_absolute() and str(source).startswith('/workspace/.cloud-setup/pv-metadata-')
assert source!=HERE.parents[1] and snapshot(source)==c['isolated_source_sha256']
variants=load(HERE/'EXPECTED-VARIANTS.json')
assert c['variants_sha256']==sha(HERE/'EXPECTED-VARIANTS.json')
expected=dict(variants['base76_source_sha256']);expected['src/search.cpp']=variants[a.phase+'_search_sha256']
assert snapshot(source)==expected, 'Only exact instrumented21 source variant allowed'
assert c['diagnostic_patch_sha256']==sha(HERE/'diagnostic-unapplied.patch')
assert c['green_diagnostic_patch_sha256']==sha(HERE/'green-diagnostic-unapplied.patch')
assert c['fix_applied'] is (a.phase=='green')
if a.phase=='green':
 assert sha(HERE/'proposed-unapplied.patch')==c['fix_patch_sha256']
 red=Path(c['reviewed_red_receipt']['path']);assert sha(red)==c['reviewed_red_receipt']['sha256']
 assert load(red)['status']=='RED_REPRODUCED_WITH_NATURAL_WITNESS'
original=Path(c['uninstrumented21_executable']);assert sha(original)==c['uninstrumented21_executable_sha256']
inputs=[Path(__file__),HERE/'worker_probe.cpp',HERE/'process_facts.py',HERE/'PROTOCOL.md',HERE/'diagnostic-unapplied.patch',HERE/'proposed-unapplied.patch',receipt,original]
frozen={str(f):sha(f) for f in inputs};before=snapshot(source)
out=HERE/(a.phase+'-attempt1');out.mkdir(exist_ok=False)
build=Path('/workspace/.cloud-setup/pv-metadata-'+a.phase+'-build-attempt1');build.mkdir(exist_ok=False)
report={'status':'RUNNING','phase':a.phase,'source_commit':REV,'steps':[],'frozen_inputs':frozen,'source_before':before,'scope':'Actual-core diagnostic only; no speed/Elo/full qualification claim'}
def save(): (out/'result.json').write_text(json.dumps(report,indent=2)+'\n')
start=time.monotonic();env=os.environ.copy();env['PYTHONDONTWRITEBYTECODE']='1'
def run(label,cmd,stdin=b'',expected=0):
 row={'label':label,'command':cmd,'stdin_sha256':hashlib.sha256(stdin).hexdigest(),'exit_code':None,'post_cleanup_exit_code':None};proc=None
 (out/(label+'.stdin')).write_bytes(stdin);report['steps'].append(row);save()
 try:
  remaining=600-(time.monotonic()-start)-15
  if remaining<=0:raise RuntimeError('owned diagnostic global deadline exhausted')
  with (out/(label+'.stdout')).open('xb') as stdout,(out/(label+'.stderr')).open('xb') as stderr:
   proc=subprocess.Popen(cmd,stdin=subprocess.PIPE,stdout=stdout,stderr=stderr,env=env,start_new_session=True,cwd=build)
   row['pid']=row['pgid']=proc.pid
   try:proc.communicate(input=stdin,timeout=remaining);row['exit_code']=proc.returncode
   finally:
    # Cleanup runs before hash/assertion/save, including communicate/persistence errors.
    row['cleanup']=cleanup(proc.pid)
    try:proc.wait(timeout=2)
    except subprocess.TimeoutExpired:row['wait_error']='unreaped after owned cleanup'
    row['post_cleanup_exit_code']=proc.returncode
  row['stdout_sha256']=sha(out/(label+'.stdout'));row['stderr_sha256']=sha(out/(label+'.stderr'));save()
  assert row['exit_code']==expected and row['cleanup']['no_live_owned_processes']
 finally:save()
 return (out/(label+'.stdout')).read_text(),(out/(label+'.stderr')).read_text()
def bench(label,exe):
 stdout,stderr=run(label,[str(exe)],b'setoption name OwnBook value false\nbench 11\nquit\n')
 nodes=re.findall(r'^info string bench depth 11 nodes (\d+) time \d+ nps \d+\s*$',stdout,re.M)
 assert len(nodes)==1,'actual canonical bench signature absent/duplicated'
 return int(nodes[0]),stderr
save()
try:
 baseline_nodes,baseline_stderr=bench('uninstrumented21-bench11',original)
 assert baseline_stderr==''
 assert baseline_nodes==c['expected_bench11_nodes']
 run('configure',['/workspace/.cloud-setup/venv/bin/cmake','-S',str(source),'-B',str(build),'-DCMAKE_BUILD_TYPE=Release','-DCMAKE_CXX_COMPILER=/usr/bin/g++-14','-DCMAKE_CXX_FLAGS='+FLAGS,'-DCMAKE_EXPORT_COMPILE_COMMANDS=ON'])
 run('build',['/workspace/.cloud-setup/venv/bin/cmake','--build',str(build),'--parallel','1','--target','forge'])
 artifacts={str(build/n):sha(build/n) for n in ['forge','libforge_core.a']}
 probe=build/'worker_probe'
 run('compile-probe',['/usr/bin/g++-14','-std=c++20','-O3','-DNDEBUG',*FLAGS.split(),'-I'+str(source/'include'),str(HERE/'worker_probe.cpp'),str(build/'libforge_core.a'),'-pthread','-o',str(probe)])
 stdout,_=run('actual-worker-probe',[str(probe)],expected=1 if a.phase=='red' else 0)
 rows=re.findall(r'^PV_CASE name=(\S+) singular_calls=(\d+) changed=(\d+) score=(-?\d+)$',stdout,re.M)
 assert len(rows)==4 and len({r[0] for r in rows})==4
 target=next(r for r in rows if r[0]=='PV_nonPVhit');assert int(target[1])>0
 assert (int(target[2])>0) is (a.phase=='red')
 assert all(int(r[2])==0 for r in rows if r[0]!='PV_nonPVhit')
 nodes,stderr=bench('actual-natural-bench11',build/'forge')
 summaries=[json.loads(line[len('PV_SUMMARY '):]) for line in stderr.splitlines() if line.startswith('PV_SUMMARY ')]
 traces=[json.loads(line[len('PV_TRACE '):]) for line in stderr.splitlines() if line.startswith('PV_TRACE ')]
 assert summaries and all(r['events']>=r['changed']>=0 for r in summaries)
 assert all(line.startswith(('PV_SUMMARY ','PV_TRACE ')) for line in stderr.splitlines() if line.strip()), 'unexpected natural-search diagnostics'
 report['natural_summary']=summaries;report['natural_trace']=traces;report['bench_nodes']=nodes
 if a.phase=='red':
  assert nodes==baseline_nodes,'instrumentation changed baseline search work'
  assert sum(r['changed'] for r in summaries)>0 and traces,'no natural witness; do not escalate workload automatically'
 else:assert sum(r['changed'] for r in summaries)==0
 assert snapshot(source)==before and all(sha(f)==v for f,v in frozen.items())
 assert all(sha(f)==v for f,v in artifacts.items())
 report['artifacts']=artifacts;report['probe_sha256']=sha(probe)
 report['status']='RED_REPRODUCED_WITH_NATURAL_WITNESS' if a.phase=='red' else 'GREEN_FINITE_DIAGNOSTIC_ONLY'
except BaseException as error:
 report['status']='FAILED_OR_INCONCLUSIVE_NO_RETRY';report['error']=repr(error);raise
finally:
 report['source_unchanged']=snapshot(source)==before
 report['final_input_hashes']={str(f):sha(f) for f in inputs if f.is_file()}
 save()
