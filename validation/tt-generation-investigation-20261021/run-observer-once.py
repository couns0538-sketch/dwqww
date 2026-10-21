from pathlib import Path
import hashlib,json,subprocess,os,sys,time,shlex,shutil,re
sys.dont_write_bytecode=True
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D));from process_facts import cleanup
S=Path('/workspace/.cloud-setup/tt-generation-observer-source');B=Path('/workspace/.cloud-setup/tt-generation-investigation-attempt1');O=D/'attempt1';BASE=Path('/workspace/.cloud-setup/pv-metadata-native-release');sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();F=['-std=c++20','-O3','-DNDEBUG','-march=x86-64-v3','-mtune=znver5','-fno-fast-math','-ffp-contract=off','-fno-lto'];report=json.loads((O/'result.json').read_text());assert report['status']=='ACTUAL_TABLE_FIXTURE_PASS_OBSERVER_NOT_YET_RUN';assert not (O/'compile-baseline-walk.stdout').exists();manifest=json.loads((D/'OBSERVER-SOURCE-77.json').read_text());assert {str(p.relative_to(S)):sha(p) for p in S.rglob('*') if p.is_file()}==manifest
inputs=[BASE/'libforge_core.a',BASE/'compile_commands.json',D/'search_walk.cpp',D/'observer.patch',D/'OBSERVER-SOURCE-77.json',Path(__file__),D/'process_facts.py'];pins={str(p):sha(p) for p in inputs};report['observer_input_pins']=pins;report['observer_source77']=manifest
commands=json.loads((BASE/'compile_commands.json').read_text());compile_search=shlex.split(next(r['command'] for r in commands if r['file'].endswith('/search.cpp')));compile_search=[('-I'+str(S/'include')) if a.startswith('-I') else a for a in compile_search];compile_search[compile_search.index('-o')+1]=str(B/'search.cpp.o');compile_search[compile_search.index('-c')+1]=str(S/'src/search.cpp')
report['frozen_walk']={'depth':8,'roots':12,'HashMB':16,'Threads':1,'book_path':'Direct actual Searcher bypasses UCI book exactly as OwnBook=false','first_root_cold_second_identical_root_warm':True,'walk_plies':['e2e4','e7e5','g1f3','b8c6','f1b5','a7a6','b5a4','g8f6','e1g1','f8e7'],'search_wall_deadline_combined_seconds':90,'performance_inference':False}
report['status']='OBSERVER_BUILD_RUNNING'
def save():(O/'result.json').write_text(json.dumps(report,indent=2)+'\n')
def run(label,cmd,timeout=120):
 row={'label':label,'command':cmd,'exit_code':None};report['steps'].append(row);save();p=None
 try:
  with (O/(label+'.stdout')).open('xb') as out,(O/(label+'.stderr')).open('xb') as err:
   p=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=out,stderr=err,cwd=B,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'},start_new_session=True);row['pid']=p.pid
   try:p.wait(timeout=timeout);row['exit_code']=p.returncode
   finally:row['cleanup']=cleanup(p.pid);p.wait(timeout=2);row['after_cleanup_exit']=p.returncode
  row['stdout_sha256']=sha(O/(label+'.stdout'));row['stderr_sha256']=sha(O/(label+'.stderr'));save();assert row['exit_code']==0 and row['cleanup']['no_live_owned_processes']
 finally:save()
save()
try:
 run('compile-baseline-walk',['/usr/bin/g++-14',*F,'-I'+str(S/'include'),str(D/'search_walk.cpp'),str(BASE/'libforge_core.a'),'-pthread','-o',str(B/'baseline_walk')])
 run('compile-observer-search',compile_search)
 shutil.copy2(BASE/'libforge_core.a',B/'libforge_core.a');run('replace-isolated-search-member',['ar','r',str(B/'libforge_core.a'),str(B/'search.cpp.o')])
 members=[]
 for name in subprocess.check_output(['ar','t',str(BASE/'libforge_core.a')],text=True).splitlines():
  a=subprocess.check_output(['ar','p',str(BASE/'libforge_core.a'),name]);b=subprocess.check_output(['ar','p',str(B/'libforge_core.a'),name]);members.append({'member':name,'original_sha256':hashlib.sha256(a).hexdigest(),'observer_sha256':hashlib.sha256(b).hexdigest(),'identical':a==b});assert (a==b)==(name!='search.cpp.o')
 report['core_members']=members;save()
 run('compile-observer-walk',['/usr/bin/g++-14',*F,'-I'+str(S/'include'),str(D/'search_walk.cpp'),str(B/'libforge_core.a'),'-pthread','-o',str(B/'observer_walk')])
 search_started=time.monotonic();report['status']='ONE_BASELINE_PLUS_ONE_OBSERVER_WALK_RUNNING';save()
 run('baseline-walk',[str(B/'baseline_walk')],timeout=90)
 remaining=90-(time.monotonic()-search_started);assert remaining>0;run('observer-walk',[str(B/'observer_walk')],timeout=remaining)
 baseline=(O/'baseline-walk.stdout').read_bytes();observer=(O/'observer-walk.stdout').read_bytes();assert baseline==observer,'pure observer changed actual fixed-depth search signatures';assert (O/'baseline-walk.stderr').read_bytes()==b''
 rows=baseline.decode().splitlines();assert len(rows)==12 and all(line.startswith('WALK ') for line in rows)
 diagnostics=(O/'observer-walk.stderr').read_text().splitlines();assert len(diagnostics)==12 and all(x.startswith('TT_GEN ') for x in diagnostics);stats=[json.loads(x[7:]) for x in diagnostics];assert stats[0]['old_hits']==0
 import chess
 for idx,line in enumerate(rows):
  m=re.fullmatch(r'WALK root=(\d+) fen=(.*?) depth=(\d+) seldepth=(\d+) score=(-?\d+) nodes=(\d+) best=(\S+) pv=(.*)',line);assert m and int(m[1])==idx and int(m[3])==8;b=chess.Board(m[2]);assert b.is_valid() and chess.Move.from_uci(m[7]) in b.legal_moves
  for text in m[8].split(','):
   if text:move=chess.Move.from_uci(text);assert move in b.legal_moves;b.push(move)
 totals={k:sum(r[k] for r in stats) for k in stats[0] if k!='fen'};report['observer_rows']=stats;report['observer_totals']=totals;report['fixed_depth_full_signature_bytes_identical']=True;report['all12_root_and_fullPV_rows_legal']=True
 assert all(sha(p)==v for p,v in pins.items());assert {str(p.relative_to(S)):sha(p) for p in S.rglob('*') if p.is_file()}==manifest
 report['artifacts_sha256']={n:sha(B/n) for n in ['table_fixture','baseline_walk','observer_walk','search.cpp.o','libforge_core.a']};report['status']='PASS_ACTUAL_TABLE_AND_ONE_PARITY_PRESERVING_OBSERVER_WALK';save();print(json.dumps({'status':report['status'],'totals':totals,'roots':12,'book':'Searcher-only OwnBook=false path','scope':'No speed/Elo inference'},indent=2))
except BaseException as e:report['status']='FAILED_STOP_NO_RETRY';report['error']=repr(e);save();raise
