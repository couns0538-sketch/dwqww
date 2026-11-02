#!/usr/bin/env python3
"""Execute reviewed native adapters and qualify their bound lock-proof receipts.
IDEA_SOURCE: crew reproducible-build/lock-proof contract; original code.
Adapters are trusted executable code, not a sandbox. Fixture PASS is never a gate PASS.
"""
from __future__ import annotations
import argparse, hashlib, json, math, os, pathlib, re, subprocess, sys, time

STAGES=('build_a','build_b','off_pins','on_active','perft','smoke_t1','smoke_t4','asan_ubsan')
SCOPE='Executed adapter receipts plus artifact identity/metrics; adapter correctness and native log semantics require review. No speed or Elo claim.'

def need(ok,message):
 if not ok:raise ValueError(message)

def pairs(items):
 result={}
 for k,v in items:
  need(k not in result,'duplicate JSON key: '+k);result[k]=v
 return result

def finite(text):
 x=float(text);need(math.isfinite(x),'nonfinite number');return x

def decode(text):
 def invalid(x):raise ValueError('nonfinite JSON constant: '+x)
 return json.loads(text,object_pairs_hook=pairs,parse_constant=invalid,parse_float=finite)

def load(path):return decode(path.read_text(encoding='utf-8-sig'))

def sha(path):
 with path.open('rb') as f:
  before=os.fstat(f.fileno());h=hashlib.sha256()
  for part in iter(lambda:f.read(1024*1024),b''):h.update(part)
  after=os.fstat(f.fileno());end=path.stat()
  key=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns)+((s.st_ctime_ns,) if os.name=='posix' else ())
  need(key(before)==key(after)==key(end),'file changed while hashing: '+str(path))
 return h.hexdigest()

def hexhash(value,n):return isinstance(value,str) and re.fullmatch('[0-9a-fA-F]{'+str(n)+'}',value)
def number(value,minimum=0):return type(value) is int and value>=minimum

def vector(x):
 need(isinstance(x,dict) and x and all(re.fullmatch('[0-9]+',k) and number(v) for k,v in x.items()),'invalid node vector')
 return x

def artifact(stage,name):
 need(isinstance(name,str) and name and not pathlib.PureWindowsPath(name).anchor and not pathlib.Path(name).is_absolute() and '\\' not in name and ':' not in name,'artifact needs relative forward-slash path')
 p=stage/name;need(not any((stage/pathlib.Path(*pathlib.Path(name).parts[:i])).is_symlink() for i in range(1,len(pathlib.Path(name).parts)+1)),'symlink artifact')
 p=p.resolve();need(p.is_relative_to(stage.resolve()) and p.is_file(),'artifact escapes stage or is missing')
 return p

def evidence(path,out):return {'path':path.relative_to(out).as_posix(),'sha256':sha(path)}

def check_inputs(inputs):
 for p,digest in inputs:need(sha(p)==digest,'input hash changed: '+str(p))

def flags(commands,prefix):
 return any(any(t==prefix or t.startswith(prefix+'=') for t in cmd) for cmd in commands)

def clean_sanitizer_log(path):
 markers=(b'error: addresssanitizer',b'error: leaksanitizer',b'addresssanitizer:deadlysignal',b'summary: undefinedbehaviorsanitizer',b'runtime error:')
 tail=b''
 with path.open('rb') as stream:
  for block in iter(lambda:stream.read(65536),b''):
   data=(tail+block).lower();need(not any(marker in data for marker in markers),'sanitizer error in original log: '+str(path));tail=data[-64:]

def clean_profile_log(path):
 with path.open('rb') as stream:
  for line in stream:
   line=line.lower()
   diagnostic=any(t in line for t in (b'warning:',b'error:',b'fatal:'))
   profile=any(t in line for t in (b'missing-profile',b'coverage-mismatch',b'profile count data file',b'profile data'))
   need(not(diagnostic and profile),'missing/outdated PGO diagnostic in original build log: '+str(path))

def validate(stage,data,c,root,builds):
 need(isinstance(data,dict),'adapter receipt must be an object')
 need(data.get('schema')==1 and type(data.get('schema')) is int and data.get('status')=='PASS','adapter did not report PASS schema1')
 need(data.get('source_commit')==c['candidate_commit'] and data.get('network_sha256')==c['network_sha256'],'adapter source/network mismatch')
 m=data.get('metrics');need(isinstance(m,dict),'metrics missing')
 if stage.startswith('build_'):
  exe=artifact(root,m.get('binary'));need(exe.stat().st_size>0,'empty binary')
  cmds=m.get('compile_commands');need(isinstance(cmds,list) and cmds and all(isinstance(x,list) and x and all(isinstance(t,str) for t in x) for x in cmds),'compile command witness missing')
  need(flags(cmds[:-1],'-fprofile-generate') and flags([cmds[-1]],'-fprofile-use'),'generate then final use/link witnesses required')
  for cmd in cmds:
   lto=[t for t in cmd if t=='-flto' or t.startswith('-flto=')]
   need(lto and all(t=='-flto' or t in ('-flto=auto','-flto=jobserver') or re.fullmatch(r'-flto=[1-9][0-9]*',t) for t in lto) and '-fno-lto' not in cmd,'every compile/link witness needs effective LTO')
   forbidden={'-ffast-math','-Ofast','-funsafe-math-optimizations','-fassociative-math','-freciprocal-math','-ffinite-math-only'}
   need(not forbidden.intersection(cmd),'fast-math breaks lock contract')
   need('-ffp-contract=off' in cmd and '-fno-fast-math' in cmd and all(not t.startswith('-ffp-contract=') or t=='-ffp-contract=off' for t in cmd),'no-FMA flags missing or contradicted')
   if flags([cmd],'-fprofile-use'):
    need('-Werror' in cmd or {'-Werror=missing-profile','-Werror=coverage-mismatch'}<=set(cmd),'profile-use must fail on missing/mismatched profiles')
    need(not {'-w','-Wno-error','-Wno-error=missing-profile','-Wno-error=coverage-mismatch','-Wno-missing-profile','-Wno-coverage-mismatch'}.intersection(cmd),'profile error downgrade/suppression forbidden')
  final=cmds[-1];need(final.count('-o')==1 and final.index('-o')+1<len(final),'final use/link output witness required')
  target=pathlib.Path(final[final.index('-o')+1]);target=target if target.is_absolute() else root/target
  need(target.resolve()==exe,'final use/link output differs from binary')
  need(not any(t in ('-c','-S','-E','-fno-profile-use','-fno-profile-generate') or t=='-fprofile-generate' or t.startswith('-fprofile-generate=') for t in final),'final witness is not a profile-use link')
  profiles=m.get('profile_files');need(isinstance(profiles,list) and profiles,'profile evidence missing')
  for ref in profiles:
   need(isinstance(ref,dict) and hexhash(ref.get('sha256'),64),'invalid profile reference')
   p=artifact(root,ref.get('path'));need(p.stat().st_size>0 and sha(p)==ref['sha256'].lower(),'empty/changed profile')
  builds[stage]=exe
 elif stage=='off_pins':
  for side in ('a','b'):
   need(m.get('binary_'+side+'_sha256')==sha(builds['build_'+side]),'OFF binary mismatch')
   need(vector(m.get('nodes_'+side))==c['expected_off_nodes'],'OFF nodes differ from explicit pins')
  need(m.get('options')==c['off_options'],'OFF options differ')
 else:
  if stage!='asan_ubsan':need(m.get('binary_sha256')==sha(builds['build_a']),'candidate binary mismatch')
  if stage=='on_active':
   nodes=vector(m.get('nodes'));need(nodes.keys()==c['expected_off_nodes'].keys(),'ON depths differ')
   need(nodes!=c['expected_off_nodes'] and number(m.get('active_count'),1),'ON is inactive or nodes did not differ')
   need(m.get('options')==c['on_options'],'ON options differ')
  elif stage=='perft':need(type(m.get('startpos5')) is int and m['startpos5']==4865609 and type(m.get('kiwipete5')) is int and m['kiwipete5']==193690690,'perft mismatch')
  elif stage.startswith('smoke_'):
   need(type(m.get('threads')) is int and m['threads']==(1 if stage=='smoke_t1' else 4),'smoke thread count differs')
   need(number(m.get('searches'),1) and m.get('completed') is True,'smoke did not complete searches')
   need(all(type(m.get(k)) is int and m[k]==0 for k in ('illegal_moves','crashes','time_forfeits')),'smoke fault')
  else:
   need(isinstance(m.get('sanitizers'),list) and len(m['sanitizers'])==2 and set(m['sanitizers'])=={'address','undefined'} and m.get('runtime_started') is True and number(m.get('executed_tests'),1) and type(m.get('failures')) is int and m['failures']==0,'ASan/UBSan tests did not execute cleanly')
   exe=artifact(root,m.get('instrumented_binary'));need(exe.stat().st_size>0,'empty sanitizer binary')
   cmds=m.get('compile_commands',[]);need(isinstance(cmds,list) and cmds and all(isinstance(x,list) and all(isinstance(t,str) for t in x) for x in cmds),'sanitizer commands missing')
   need(flags(cmds,'-fsanitize') and any('address' in t and 'undefined' in t for cmd in cmds for t in cmd if t.startswith('-fsanitize=')),'sanitizer instrumentation missing')

def run(contract,out):
 contract=pathlib.Path(contract).resolve();snapshot=contract.read_bytes();c=decode(snapshot.decode('utf-8-sig'))
 need(isinstance(c,dict) and type(c.get('schema')) is int and c['schema']==1,'contract schema must be1')
 need(c.get('evidence_scope') in ('fixture','native'),'explicit evidence_scope required')
 need(number(c.get('max_worker_threads'),4),'proof set needs an authorized four-thread host; do not override grok-pc-safe-run')
 for k in ('baseline_commit','candidate_commit'):need(hexhash(c.get(k),40),'full source commit required')
 need(hexhash(c.get('network_sha256'),64),'network SHA256 required');vector(c.get('expected_off_nodes'))
 need(isinstance(c.get('off_options'),dict) and isinstance(c.get('on_options'),dict) and c['off_options']!=c['on_options'],'distinct OFF/ON option dictionaries required')
 refs=c.get('inputs');need(isinstance(refs,list) and refs,'pinned inputs missing');inputs=[];roles=set();baseline_hash=None
 for ref in refs:
  need(isinstance(ref,dict) and isinstance(ref.get('role'),str) and isinstance(ref.get('path'),str) and hexhash(ref.get('sha256'),64),'invalid pinned input')
  p=(contract.parent/ref['path']).resolve();need(p.is_file(),'pinned input missing');inputs.append((p,ref['sha256'].lower()));roles.add(ref['role'])
  if ref['role']=='baseline_binary':
   need(baseline_hash is None,'only one baseline binary is permitted');baseline_hash=ref['sha256'].lower()
  if ref['role']=='network':need(ref['sha256'].lower()==c['network_sha256'].lower(),'network input hash differs')
 need({'compiler','recipe','source','network','baseline_binary'}<=roles,'compiler/recipe/source/network/baseline_binary inputs required');check_inputs(inputs)
 stages=c.get('stages');need(isinstance(stages,dict) and set(stages)==set(STAGES),'exact eight native stages required')
 for spec in stages.values():
  need(isinstance(spec,dict) and isinstance(spec.get('argv'),list) and spec['argv'] and all(isinstance(t,str) and '\x00' not in t for t in spec['argv']),'stage argv required')
  need(number(spec.get('timeout_seconds'),1),'positive integer stage timeout required')
  exe=pathlib.Path(spec['argv'][0]);need(exe.is_absolute() and exe.resolve() in {p for p,_ in inputs},'stage executable must be a pinned absolute input')
  need(any('{result}' in t for t in spec['argv']),'adapter argv must receive {result}')
 out=pathlib.Path(out).absolute();out.mkdir(parents=True,exist_ok=False);out=out.resolve();(out/'CONTRACT.json').write_bytes(snapshot)
 report={'schema':1,'status':'FAIL','evidence_scope':c['evidence_scope'],'scope':SCOPE,'baseline_commit':c['baseline_commit'],'candidate_commit':c['candidate_commit'],'contract_sha256':sha(out/'CONTRACT.json'),'baseline_binary_sha256':baseline_hash,'candidate_binary_sha256':None,'net_sha256':c['network_sha256'],'tested_options':{'off':c['off_options'],'on':c['on_options']},'checks':[]}
 inputs.append((out/'CONTRACT.json',report['contract_sha256']))
 builds={};initial_binary={}
 for name in STAGES:
  stage=out/name;stage.mkdir();row={'name':name,'status':'UNVERIFIED','evidence':[]};stdout=stage/'stdout.log';stderr=stage/'stderr.log';result=stage/'result.json'
  try:
   check_inputs(inputs)
   if name not in ('build_a','build_b'):need(set(builds)=={'build_a','build_b'},'build dependency unavailable')
   for p,digest in initial_binary.items():need(sha(p)==digest,'qualified build changed')
   args=[t.replace('{stage}',str(stage)).replace('{result}',str(result)).replace('{out}',str(out)) for t in stages[name]['argv']]
   command=stage/'command.json';command.write_text(json.dumps({'argv':args,'cwd':str(stage),'timeout_seconds':stages[name]['timeout_seconds']},indent=2)+'\n');start=time.monotonic()
   with stdout.open('xb') as so,stderr.open('xb') as se:
    completed=subprocess.run(args,cwd=stage,stdin=subprocess.DEVNULL,stdout=so,stderr=se,timeout=stages[name]['timeout_seconds'],shell=False)
   (stage/'exit.json').write_text(json.dumps({'exit_code':completed.returncode,'elapsed_seconds':time.monotonic()-start})+'\n')
   need(completed.returncode==0,'adapter exited '+str(completed.returncode));data=load(result);need(isinstance(data,dict),'adapter receipt must be an object')
   logs=data.get('logs');need(isinstance(logs,list) and logs,'original native logs required')
   for ref in logs:
    need(isinstance(ref,dict) and hexhash(ref.get('sha256'),64),'invalid log reference')
    p=artifact(stage,ref.get('path'));need(sha(p)==ref['sha256'].lower(),'native log hash mismatch')
   validate(name,data,c,stage,builds)
   if name in ('build_a','build_b'):
    for p in [stdout,stderr]+[artifact(stage,ref['path']) for ref in logs]:clean_profile_log(p)
   if name=='asan_ubsan':
    for p in [stdout,stderr]+[artifact(stage,ref['path']) for ref in logs]:clean_sanitizer_log(p)
   check_inputs(inputs)
   if name in builds:
    initial_binary[builds[name]]=sha(builds[name])
    if name=='build_a':report['candidate_binary_sha256']=initial_binary[builds[name]]
   for p,digest in initial_binary.items():need(sha(p)==digest,'qualified binary changed during test')
   row['status']='PASS'
  except subprocess.TimeoutExpired:
   row['status']='FAIL';row['reason']='Owned direct adapter timed out and was terminated; descendant cleanup is not certified. Review before further runs.'
  except (OSError,ValueError,TypeError,KeyError,RuntimeError) as error:row['status']='FAIL';row['reason']=str(error)
  (stage/'outcome.json').write_text(json.dumps({'status':row['status'],'reason':row.get('reason','')})+'\n')
  row['evidence']=[evidence(p,out) for p in sorted(stage.rglob('*')) if p.is_file() and not p.is_symlink()]
  report['checks'].append(row)
  if row['status']!='PASS':
   # Subsequent checks are preserved as explicit unverified rows without running
   # native work after a failed prerequisite or potentially orphaned timeout.
   for later in STAGES[STAGES.index(name)+1:]:
    report['checks'].append({'name':later,'status':'UNVERIFIED','reason':'earlier stage failed','evidence':[evidence(stage/'outcome.json',out)]})
   break
 row={'name':'reproducible_builds','status':'UNVERIFIED','evidence':[evidence(out/'CONTRACT.json',out)]}
 try:
  need(set(builds)=={'build_a','build_b'},'both builds unavailable');a,b=builds['build_a'],builds['build_b']
  need(a.parent!=b.parent and not os.path.samefile(a,b),'build outputs are not independent files/directories')
  need(sha(a)==sha(b),'LTO+PGO binary bytes differ');check_inputs(inputs)
  row.update(status='PASS',evidence=[evidence(a,out),evidence(b,out)])
 except (OSError,ValueError,RuntimeError) as error:row.update(status='FAIL',reason=str(error))
 report['checks'].insert(2,row)
 for check in report['checks']:
  try:
   for ref in check['evidence']:need(sha(out/ref['path'])==ref['sha256'],'evidence changed after stage: '+ref['path'])
  except (OSError,ValueError,RuntimeError) as error:check.update(status='FAIL',reason=str(error))
 if all(r['status']=='PASS' for r in report['checks']):report['status']='PASS'
 (out/'REPORT.json').write_text(json.dumps(report,indent=2)+'\n')
 table='| Check | Status | Reason |\n|---|---|---|\n'+''.join('| '+r['name']+' | '+r['status']+' | '+r.get('reason','').replace('|','/')+' |\n' for r in report['checks'])
 (out/'TABLE.md').write_text(table);return report

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('contract',type=pathlib.Path);p.add_argument('--out',required=True,type=pathlib.Path);a=p.parse_args()
 try:
  r=run(a.contract,a.out);print((a.out/'TABLE.md').read_text());print('Overall: '+r['status']+'; evidence_scope='+r['evidence_scope']);return 0 if r['status']=='PASS' else 1
 except (OSError,ValueError,TypeError,RuntimeError) as e:print(json.dumps({'status':'BLOCKED','error':str(e)}));return 2

if __name__=='__main__':sys.exit(main())
