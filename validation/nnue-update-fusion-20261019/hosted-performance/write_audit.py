import json, hashlib, re, statistics, subprocess, tarfile, math
from pathlib import Path
BASE=Path('/workspace/.cloud-setup/nnue-performance-audit-39334266771')
p=BASE/'hosted-nnue-performance-results'; f=p/'frozen'
checks=[]
def check(name, condition):
 checks.append({'name':name,'passed':bool(condition)})
 if not condition: raise ValueError('Audit failed: '+name)
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
report=json.loads((p/'performance/report.json').read_text())
protocol=json.loads((f/'package/protocol.json').read_text())
commands=json.loads((p/'commands.json').read_text())
check('all35recordedbuildvalidationcommandscompleted',len(commands)==35 and all(c.get('returncode')==0 and not c.get('error') for c in commands))
source={}; artifacts={}; stream_records={}
flags=['-O3','-DNDEBUG','-march=x86-64-v3','-mtune=generic','-fno-fast-math','-ffp-contract=off','-fno-lto']
for label in ('baseline','candidate'):
 m=json.loads((f/f'{label}-source-manifest.json').read_text()); archive=f/f'source-{label}.tar'
 expected=subprocess.check_output(['git','archive','--format=tar',m['source_commit'],*m['archive_paths']],cwd='/workspace/dwqww')
 check(label+'_actual_source_tar_exact_git_commit',archive.read_bytes()==expected and sha(archive)==m['archive_sha256'])
 with tarfile.open(archive) as tf:
  members={q.name:tf.extractfile(q).read() for q in tf.getmembers() if q.isfile()}
 actual_manifest={q:hashlib.sha256(data).hexdigest() for q,data in members.items()}
 check(label+'_source_file_manifest',actual_manifest==m['files_sha256'])
 check(label+'_registered_source_sha',m['source_commit']==protocol[label+'_sha'])
 compile_rows=json.loads((f/f'artifacts/{label}/compile_commands.json').read_text())
 check(label+'_all13translationunits_strict_nonlto',len(compile_rows)==13 and all(all(v in row['command'].split() for v in flags) and not any(v in row['command'].split() for v in ['-ffast-math','-Ofast','-march=native','-flto']) and 'g++-14' in row['command'] for row in compile_rows))
 check(label+'_source_paths_match_export',all('/src-'+label+'/' in row['file'] for row in compile_rows))
 test_text=(p/f'{label}-ctest.stdout').read_text()
 check(label+'_ctest9of9_completed',test_text.count('   Passed')==9 and '100% tests passed, 0 tests failed out of 9' in test_text and '***Skipped' not in test_text and '***Not Run' not in test_text)
 sections=(p/f'{label}-core-sections.stdout').read_text()
 check(label+'_actual_core_nonlto_sections','.gnu.lto_' not in sections)
 disasm=(p/f'{label}-kernel-disassembly.stdout').read_text()
 calls=[s for s in disasm.splitlines() if re.search(r'\bcall\b.*forge::nnue::update\(',s)]
 check(label+'_actual_outofline_update_calls',len(calls)>=2)
 preflight=(p/f'{label}-bench-preflight.stdout').read_text()
 check(label+'_single_preflight_419798',re.findall(r'^info string bench depth 11 nodes ([0-9]+) time [0-9]+ nps [0-9]+\s*$',preflight,re.M)==['419798'])
 artifacts[label]={name:sha(f/f'artifacts/{label}/{name}') for name in ['forge','libforge_core.a','nnue_update_benchmark','nnue_update_snapshot','nnue_snapshot']}
 source[label]={'source_commit':m['source_commit'],'tar_sha256':sha(archive),'file_count':len(members),'compile_translation_units':len(compile_rows),'network_sha256':actual_manifest['src/nnue_weights.inc'],'ctest_passed':9,'outofline_callsite_count':len(calls)}
 if label=='candidate':
  for name in ['nnue_update_snapshot.cpp','nnue_update_benchmark.cpp','nnue_snapshot.cpp']:
   check('shared_driver_'+name+'_exact_candidate_git_source',(f/'drivers'/name).read_bytes()==members['tools/'+name])
check('identical_network',source['baseline']['network_sha256']==source['candidate']['network_sha256'])
for name,size,gold in [('nnue_update_snapshot',4097860,'ca9e7405c5f7b7506455a3b6b104683ccc8d83e75b0bbaf8d9c17c3ecce1ff45'),('nnue_snapshot',21192328,'3ef4bacc1877f34b929c6c4cd349c56ff0c07c93545b292914775bcd9ae173a5')]:
 a=f/f'baseline-{name}.bin'; b=f/f'candidate-{name}.bin'
 check(name+'_actual_stream_equality_and_gold',a.read_bytes()==b.read_bytes() and a.stat().st_size==size and sha(a)==gold)
 stream_records[name]={'bytes_each':size,'sha256':gold,'byte_identical':True}
actual={str(q.relative_to(f)):sha(q) for q in f.rglob('*') if q.is_file()}
check('43retained_frozen_files_build_and_workflow_final_manifests',len(actual)==43 and actual==json.loads((p/'frozen-build-SHA256.json').read_text())==json.loads((p/'workflow-final-frozen-SHA256.json').read_text()))
initial=json.loads((p/'performance/initial-inputs.json').read_text())['sha256']
final=report['final_input_rehash']; check('runtime_final44inputs_pass',final['status']=='passed' and len(final['inputs'])==44 and not final['mismatches'] and not final['added_inputs'] and not final['tree_errors'])
remote_prefix='/home/runner/work/dwqww/dwqww/hosted-nnue-performance-results/'
for path,h in initial.items():
 check('actual_final_bytes_'+path.removeprefix(remote_prefix),path.startswith(remote_prefix) and sha(p/path.removeprefix(remote_prefix))==h and final['inputs'][path]['actual_sha256']==h and final['inputs'][path]['matches'])
runs=[]
for plan in report['runs']:
 d=p/'performance/runs'/plan['name']; status=json.loads((d/'status.json').read_text()); command=json.loads((d/'command.json').read_text())
 lines=(d/'stdout.txt').read_text().splitlines(); bench=[re.fullmatch(r'info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)',s) for s in lines if s.startswith('info string bench')]
 check(plan['name']+'_valid_status_stdio_work',status['returncode']==status['wait_status']==0 and not status['timed_out'] and status['cpu']==0 and len(bench)==12 and all(m and m.group(1)=='11' and m.group(2)=='419798' for m in bench) and not (d/'stderr.txt').read_bytes() and (d/'stdin.txt').read_bytes()==b'bench 11\n'*12+b'quit\n')
 check(plan['name']+'_same_baseline_child',status['command']==command['command']==plan['command']==[remote_prefix+'frozen/artifacts/baseline/forge'] and plan['kind']=='primary' and plan['phase']=='aa')
 check(plan['name']+'_wait4_cpu_sum',status['cpu_seconds']==status['user_seconds']+status['system_seconds'] and plan['process']==status and plan['measurement']['cpu_seconds']==status['cpu_seconds'])
 runs.append({'name':plan['name'],'cpu_seconds':status['cpu_seconds'],'wall_seconds':status['wall_seconds'],'user_seconds':status['user_seconds'],'system_seconds':status['system_seconds'],'completed_benches':12,'engine_sha256':artifacts['baseline']['forge'],'stdout_sha256':sha(d/'stdout.txt'),'status_sha256':sha(d/'status.json')})
check('12AAonly_noABorKernel',len(runs)==12 and len(list((p/'performance/runs').iterdir()))==12 and not report['primary'].get('ab_blocks') and report['kernel']['status']=='skipped_failed_primary_calibration')
gates={}
for metric in ('cpu','wall'):
 ratios=[runs[i][metric+'_seconds']/runs[i+1][metric+'_seconds'] for i in range(0,12,2)]
 median=statistics.median(ratios); failures=[i+1 for i,r in enumerate(ratios) if not .97<=r<=1.03]
 gates[metric]={'ratios':ratios,'median':median,'out_of_band_pairs':failures,'median_in_band':.99<=median<=1.01,'passed':not failures and .99<=median<=1.01}
 check(metric+'_recomputed_report_exact',ratios==report['primary']['calibration'][metric]['ratios'] and median==report['primary']['calibration'][metric]['median'] and gates[metric]['passed']==report['primary']['calibration'][metric]['passed'])
check('honest_failedAA_report',report['status']=='failed_primary_calibration_no_ab' and report['qualifies_hosted_speed_claim'] is False and not report['primary']['calibration']['passed'])
host=json.loads((p/'performance/host-before.json').read_text())
check('recorded_exact_singleton_affinity',report['cpu']==0 and host['affinity']==[0] and min(report['inherited_affinity'])==0)
audit={'audit_status':'passed','experiment_status':'failed_primary_calibration_no_ab','run_id':39334266771,'attempt':1,'results_commit':'b3bf48525540e64db12b592c913b160298bad6d1','results_ref':'refs/remotes/origin/results/nnue-performance-39334266771-1','conclusion':'Performance inconclusive. The fixed same-binary calibration failed; no A/B or kernel phase ran, and no NPS, speedup or Elo gain is established. No retry or gate bypass was performed.','source_provenance':source,'actual_artifact_sha256':artifacts,'actual_snapshot_streams':stream_records,'frozen_retained_files':43,'runtime_final_inputs':44,'recorded_build_and_validation_commands':35,'timed_aa_processes':12,'timed_complete_benches':144,'bench_nodes_each':419798,'recomputed_gates':gates,'raw_aa_runs':runs,'checks':checks,'checks_passed':len(checks),'metadata_note':'build-status.json timing_started=false is a builder-stage placeholder, not evidence that the later 12-process calibration did not execute. Candidate ran during correctness/preflight only; it has no comparison timing in the performance phase.','audit_actions':'Read-only Git archive/file audit plus report creation outside checkout; no engines, builds, benchmarks, retries or Git mutations.'}
(BASE/'independent-audit.json').write_text(json.dumps(audit,indent=2)+'\n')
md='''# Independent hosted NNUE performance audit\n\nRun **39334266771 attempt1**, results commit `b3bf48525540e64db12b592c913b160298bad6d1`: the audit passes, and the experiment correctly reports **failed primary calibration; performance inconclusive**. No A/B or kernel timing phase ran. No NPS, speedup or Elo gain is established, and no retry or gate bypass was performed.\n\nAll12retained calibration processes used the same archived649baseline executable, exited normally with wait status0, had empty stderr and exact twelve-bench input, and completed12depth11bench records with419798nodes each:144complete benches. Recorded CPU equals wait4 user+system; CPU0 and singleton affinity are recorded.\n\nBoth CPU and wall controls fail the preregistered gate: pairs3and6 exceed1.03, and medians exceed1.01. Independently recomputed CPU ratios are `%s`, median`%.15f`; wall ratios are `%s`, median`%.15f`. Values match the archived report exactly.\n\nActual source tars are byte-identical to fresh read-only Git exports of649`4edda780c68a742f20565d4e6a54a0c99a2c88a6` and650`36f5b2f6e1ff519e82a4b52edc85caceaf15aed0`; source manifests cover66/68files. Both13-translation-unit builds use GCC14strict genericx86-64-v3non-LTO flags; both full CTest suites pass9/9. All35recorded build/check commands exit0. The identical candidate-commit drivers link to each retained core. Recorded actual disassembly has out-of-line update calls and no core LTO sections. Both NNUE streams are byte-identical across cores and match prior gold SHA256s (4097860and21192328bytes). The network source bytes match.\n\nAll43frozen files are actually retained, including both source tars, core archives, engine/helper binaries and drivers. Build and workflow-final manifests exactly match actual bytes; the runtime final check covers44inputs with no changed, missing or new inputs.\n\nThe builder-stage `timing_started=false` field is a placeholder; the raw performance records demonstrate that calibration executed. Candidate correctness/preflight execution is distinct from A/B timing. All original evidence remains intact. This audit executed no engines, builds, benchmarks or retries.\n''' % (', '.join('%.12f'%r for r in gates['cpu']['ratios']),gates['cpu']['median'],', '.join('%.12f'%r for r in gates['wall']['ratios']),gates['wall']['median'])
(BASE/'independent-audit.md').write_text(md)
print(json.dumps({'audit_status':'passed','checks':len(checks),'outputs':[str(BASE/'independent-audit.json'),str(BASE/'independent-audit.md')],'experiment_status':audit['experiment_status']}))
