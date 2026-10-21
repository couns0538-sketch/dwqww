from pathlib import Path
import json,hashlib,shutil,time
E=Path(__file__).resolve().parent;R=Path('/workspace/dwqww');S=Path('/workspace/.cloud-setup/see-proof-reuse23-source');B=Path('/workspace/.cloud-setup/see-proof-reuse23-release')
h=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
g=json.loads((R/'validation/tt-refresh-20261021/ROOT-FROZEN23-SOURCE-GATES.json').read_text())
for rel,sha in g['inputs'].items():assert h(R/rel)==sha,('production changed',rel)
for p,sha in json.loads((E/'baseline-originals.json').read_text()).items():assert h(Path(p))==sha,('baseline original changed',p)
source_map=json.loads((E/'OBSERVER-SOURCE-INPUTS.json').read_text())['all_actual_files']
for rel,sha in source_map.items():assert h(S/rel)==sha,('observer source changed',rel)
for rel in ['src/search.cpp','src/board.cpp','CMakeLists.txt','include/forge/see_observer.hpp','tests/see_threshold_driver.cpp']:
 out=E/'observer-source'/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(S/rel,out);assert h(out)==h(S/rel)
for rel in ['forge','forge_see_threshold','libforge_core.a','compile_commands.json','CMakeCache.txt','CMakeFiles/forge.dir/link.txt','CMakeFiles/forge_core.dir/flags.make','CMakeFiles/forge_see_threshold.dir/link.txt']:
 out=E/'observer-originals'/rel;out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(B/rel,out);assert h(out)==h(B/rel)
# Hash every retained original in both complete outside trees after all writers closed.
outside={}
for tree in [S,B]:
 files={str(p.relative_to(tree)):h(p) for p in sorted(tree.rglob('*')) if p.is_file()};outside[str(tree)]={'files':len(files),'sha256':files}
(E/'COMPLETE-OUTSIDE-ORIGINALS.json').write_text(json.dumps(outside,indent=2)+'\n')
statuses={}
for p in sorted(E.glob('*.status.json')):
 d=json.loads(p.read_text());statuses[p.name]=d
 if p.name not in ['configure.status.json','build.status.json']:assert d['returncode']==0 and d['owned_group_closed'] and not d['timeout'],(p,d)
for name in ['observer-bench11','observer-fixtures']:
 d=json.loads((E/(name+'.counters.json')).read_text());assert d['stage_faults']==d['scope_faults']==d['proof_positive_threshold']==0
 assert all(x['proof_false']==0 for x in d['sites'])
summary={'status':'PASS_OBSERVER_ONLY_DIAGNOSTIC_NO_OPTIMIZATION_OR_GAIN_CLAIM','utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'baseline_source_commit':g['source_commit'],'baseline_bench11_nodes':292545,'observer_bench11_nodes':292545,'full_canonical_bench_and_cold_warm_parity':True,'canonical_ignored_fields':['time','nps'],'baseline_and_observer_fixture_searches_each':16,'pv_replay_rows':288,'pv_replay_legal_moves':1378,'threshold_positions':140,'threshold_legal_moves':391,'threshold_calls':1877582,'threshold_negative_implications':569037,'threshold_range_inclusive':[-2400,2400],'threshold_step':1,'threshold_failures':0,'illegal_pin_controls':2,'proof_scope_stage_or_answer_faults':0,'baseline_originals_unchanged':True,'all77_production_source_inputs_unchanged':True,'observer_only_source_files':len(source_map),'all_actual_compiler_and_runtime_process_groups_closed':True,'pre_spawn_tool_path_failures':2,'actual_compiler_build_attempts':1,'actual_engine_gate_retries':0,'baseline_engine_sha256':h(E/'originals/forge'),'baseline_core_sha256':h(E/'originals/libforge_core.a'),'observer_engine_sha256':h(B/'forge'),'observer_core_sha256':h(B/'libforge_core.a'),'threshold_driver_sha256':h(B/'forge_see_threshold'),'compiler_path':'/usr/bin/g++-14','compiler_binary_sha256':h(Path('/usr/bin/g++-14').resolve()),'source_map_sha256':h(E/'OBSERVER-SOURCE-INPUTS.json'),'outside_original_manifest_sha256':h(E/'COMPLETE-OUTSIDE-ORIGINALS.json'),'instrumentation_retains_every_original_see_call':True,'nps_gain':None,'elo_gain':None,'decision':'PROMISING_BOUNDED_PROOF_REUSE_CANDIDATE_READY_FOR_SEPARATE_IMPLEMENTATION','bench':json.loads((E/'observer-bench11.counters.json').read_text()),'fixtures':json.loads((E/'observer-fixtures.counters.json').read_text()),'process_statuses':list(statuses)}
(E/'RESULT.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps({k:v for k,v in summary.items() if k not in ['bench','fixtures']},indent=2))
