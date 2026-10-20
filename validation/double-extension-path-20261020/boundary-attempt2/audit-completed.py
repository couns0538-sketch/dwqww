#!/usr/bin/env python3
"""Offline audit of every completed boundary capture; never executes an engine."""
from pathlib import Path
import collections,datetime,hashlib,io,json,subprocess,sys,tarfile,time
import chess
HERE=Path(__file__).resolve().parent
PREVIOUS=HERE.parent/'boundary-attempt1'
REPO=HERE.parents[2]
REV='cecf0b9e3af5602053bcaf5c5d16ffc09f58850d'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def save(p,x):p.write_text(json.dumps(x,indent=2)+'\n')
x=json.loads((HERE/'commands.json').read_text());prior=json.loads((PREVIOUS/'commands.json').read_text())
identity=json.loads((HERE/'RESUME-IDENTITY.json').read_text());meta=json.loads((PREVIOUS/'SOURCE-PROVENANCE.json').read_text())
assert x['status']=='FAILED_OR_INCOMPLETE' and x['error']=='AssertionError()'
assert sha(PREVIOUS/'commands.json')==identity['original_commands_sha256']
assert sha(PREVIOUS/'run-boundary.py')==identity['original_run_driver_sha256']
assert len(x['cases'])==6 and x['runtime_used_seconds']<=60
assert [s['label'] for s in x['steps']][:3]==['proposal-compile','proposal-core','proposal-link']
assert all(s['exit_code']==0 for s in x['steps'])
for step in x['steps']:
    for stream in ['stdout','stderr']:assert sha(HERE/(step['label']+'.'+stream))==step[stream+'_sha256']
originals={n:sha(n) for n in x['originals_before']};assert originals==x['originals_before']==prior['originals_before']
export=subprocess.check_output(['git','archive',REV,'CMakeLists.txt','LICENSE','src','include','tests','bench','tools'],cwd=REPO)
with tarfile.open(fileobj=io.BytesIO(export)) as tar:
    expected={r.name:hashlib.sha256(tar.extractfile(r).read()).hexdigest() for r in tar if r.isfile()}
sources={};binaries={};core_members={}
for label in ['baseline','proposal']:
    source=Path(meta['variants'][label]['source_export']);actual={str(p.relative_to(source)):sha(p) for p in sorted(source.rglob('*')) if p.is_file()}
    wanted=dict(expected);wanted['src/search.cpp']=meta['variants'][label]['boundary_search_sha256']
    assert actual==wanted,(label,'source export differs from frozen Git plus declared diagnostic')
    sources[label]=actual
    build=Path('/workspace/.cloud-setup/double-extension-boundary-'+label+'-build')
    binaries[label]={n:sha(build/n) for n in ['forge','libforge_core.a','search.cpp.o']}
    assert binaries[label]['forge']==x[label+'_binary_sha256']
    assert binaries[label]['libforge_core.a']==x[label+'_core_sha256']
    members={}
    for n,r in x[label+'_core_members'].items():
        b=subprocess.check_output(['ar','p',str(build/'libforge_core.a'),n]);h=hashlib.sha256(b).hexdigest();assert h==r['variant_sha256']
        members[n]=h
    core_members[label]=members
no_moves={'incoming_parent_path_mismatch','null_parent_path_mismatch'}
checks=0;row_count=0;groups=collections.Counter();per_case={}
fields=list(next(iter(x['cases'].values()))['summary_totals'])
for case,r in x['cases'].items():
    stdout=(HERE/(case+'.stdout')).read_text();stderr=(HERE/(case+'.stderr')).read_text()
    assert 'bench depth 11 nodes '+str(r['bench11_nodes'])+' ' in stdout
    summaries=[json.loads(s.removeprefix('DE_SUMMARY ')) for s in stderr.splitlines() if s.startswith('DE_SUMMARY ')]
    traces=[json.loads(s.removeprefix('DE_TRACE ')) for s in stderr.splitlines() if s.startswith('DE_TRACE ')]
    assert len(summaries)==8 and all(s['ancestral_seed']==r['seed'] for s in summaries)
    assert json.loads((HERE/(case+'-summaries.json')).read_text())==summaries
    assert json.loads((HERE/(case+'-traces.json')).read_text())==traces
    assert {k:sum(s[k] for s in summaries) for k in fields}==r['summary_totals']
    assert max(s['max_true_path'] for s in summaries)==r['max_true_path']
    assert max(s['max_actual_path'] for s in summaries)==r['max_actual_path']
    assert r['summary_totals']['children']>0 and r['summary_totals']['singular_attempts']>0
    for row in traces:
        board=chess.Board(row['fen']);assert board.is_valid(),row;checks+=1
        event=row['event']
        if event in no_moves:assert row['move']=='a1a1',row
        else:assert chess.Move.from_uci(row['move']) in board.legal_moves,row
        checks+=1
        if event=='actual_child_vs_true_path_mismatch':assert row['frame_after']!=row['expected_path_before_move']+(row['extension']==2),row
        elif event=='single_extension_parent_mismatch':assert row['extension']==1 and row['frame_after']!=row['parent_actual'],row
        elif event=='incoming_parent_path_mismatch':assert row['parent_actual']!=row['expected_path_before_move'],row
        elif event in ['null_parent_path_mismatch','probcut_parent_path_mismatch']:assert row['frame_after']!=row['expected_path_before_move'],row
        elif event=='singular_same_ply_changed':assert row['frame_before']!=row['frame_after'],row
        elif event=='double_eligibility_mismatch_true_path':assert (row['frame_after']<=6)!=(row['expected_path_before_move']<=6),row
        elif event=='synthetic_ancestral_true_path_limit_breach':assert row['expected_path_before_move']+(row['extension']==2)>7,row
        else:assert event=='singular_same_ply_before' and row['frame_before']==row['frame_after'],row
        checks+=1;row_count+=1;groups[event]+=1
    per_case[case]={'rows':len(traces),'children':r['summary_totals']['children'],'singular_attempts':r['summary_totals']['singular_attempts'],'max_true_path':r['max_true_path'],'max_actual_path':r['max_actual_path'],'double_extensions':r['summary_totals']['double_extensions'],'engine_exit_code':0}
assert x['cases']['baseline-seed6']['max_true_path']==8
assert x['cases']['baseline-seed6']['summary_totals']['true_path_limit_breaches']>0
assert x['cases']['baseline-seed6']['summary_totals']['eligibility_mismatch']>0
assert x['cases']['baseline-seed7']['summary_totals']['double_extensions']==0
assert x['cases']['baseline-seed7']['summary_totals']['true_path_limit_breaches']==0
for seed in [6,7]:
    r=x['cases'][f'proposal-seed{seed}'];assert r['max_true_path']==r['max_actual_path']==7
    assert (r['summary_totals']['double_extensions']>0)==(seed==6)
for label in ['baseline','proposal']:assert x['cases'][label+'-seed0']['bench11_nodes']==419798
oracle=[]
for label,expected_exit in [('baseline',1),('proposal',0)]:
    cmd=[sys.executable,str(HERE/'assert-boundary-results.py'),'--commands',str(HERE/'commands.json'),'--variant',label]
    start=time.monotonic()
    with (HERE/(label+'-oracle.stdout')).open('xb') as out,(HERE/(label+'-oracle.stderr')).open('xb') as err:
        done=subprocess.run(cmd,stdout=out,stderr=err,timeout=20)
    assert done.returncode==expected_exit,(label,done.returncode)
    assert (HERE/(label+'-oracle.stderr')).read_bytes()==b''
    oracle.append({'variant':label,'command':cmd,'exit_code':done.returncode,'expected_exit':expected_exit,'elapsed_seconds':time.monotonic()-start,'stdout_sha256':sha(HERE/(label+'-oracle.stdout')),'stderr_sha256':sha(HERE/(label+'-oracle.stderr'))})
result={'status':'PASS_SYNTHETIC_INHERITED_STATE','source':REV,'cases':per_case,'runtime_seconds_all_six_cases':x['runtime_used_seconds'],'runtime_budget_seconds':60,'independent_trace_rows':row_count,'independent_trace_checks':checks,'event_sample_counts':dict(groups),'python_chess_version':chess.__version__,'source_exports_final_sha256':sources,'originals_after':originals,'all_originals_unchanged':True,'binary_and_core_final_sha256':binaries,'core_members_final_sha256':core_members,'oracle_commands':oracle,'unchanged_original_attempt1_commands_sha256':identity['original_commands_sha256'],'preserved_attempt2_commands_sha256':sha(HERE/'commands.json'),'preserved_harness_failure':'After all six engine cases exited0, the original driver incorrectly demanded seed7 overflow. Actual overflow is in seed6. No engine was rerun or output changed; this offline auditor checks the intended budget invariant and preserves the failed oracle.','coverage_limits':['Synthetic root-parent state6/7, not normal-root overflow or Elo evidence.','Seed7 performs233863 children/776 singular attempts but no separately counted margin-qualified-denial opportunities; no claim that every branch of the denial guard was exercised.','Bounded trace journal verifies legal positions/candidate moves and arithmetic; it is not a full game replay.'],'completed_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
save(HERE/'FINAL-BOUNDARY-RESULTS.json',result)
print(json.dumps({k:v for k,v in result.items() if k not in ['source_exports_final_sha256','core_members_final_sha256','binary_and_core_final_sha256','oracle_commands','cases','event_sample_counts']}))
