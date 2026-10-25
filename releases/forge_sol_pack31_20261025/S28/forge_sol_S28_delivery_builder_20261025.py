#!/usr/bin/env python3
"""Seal the closed S28 qualification evidence without exporting sources or binaries."""
from pathlib import Path
import base64,gzip,hashlib,json,re,shutil,subprocess
ROOT=Path('/workspace/forge-pack24-20261025/S28')
NATIVE=ROOT/'forge_sol_S28_native_v2_20261025'
OUT=ROOT/'forge_sol_S28_delivery_20261025'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
def write(name,text):(OUT/name).write_text(text,encoding='utf-8')
ctl=load(NATIVE/'forge_sol_S28_native_controller_result_20261025.json')
assert ctl['status']=='PASS' and len(ctl['runs'])==4
post=load(ROOT/'forge_sol_S28_final_pin_postcheck_20261025.json')
identity=load(ROOT/'forge_sol_S28_source_identity_results_20261025.json')
assert post['status']=='PASS' and len(post['checks'])==10 and len(post['manifest_checks'])==4
assert identity['status']=='PASS' and identity['original_input_files']==151 and len(identity['source_stages'])==10
raw_commands=sorted(NATIVE.glob('forge_sol_S28_*_20261025/forge_sol_S28_raw_*_20261025.json'))
assert len(raw_commands)==209
cases={}
for row in ctl['runs']:
    folder=Path(row['argv'][row['argv'].index('--out')+1])
    result=load(folder/'forge_sol_S28_results_20261025.json')
    assert result['status']=='PASS_OBSERVATIONAL_NOT_ADOPTED' and result['input_immutability']['equal']
    cases[row['case']]=(folder,result)
assert sum(len(r['stages']) for _,r in cases.values())==10
OUT.mkdir(exist_ok=False)
kit=ROOT/'forge_sol_S28_lock_transition_kit_20261025'
for p in sorted(kit.iterdir()):
    if p.is_file():shutil.copyfile(p,OUT/p.name)
# Original private files remain untouched. Each bundle line preserves the original file bytes.
files=set(raw_commands)
files.add(NATIVE/'forge_sol_S28_native_controller_result_20261025.json')
for folder,result in cases.values():
    files.update(folder.glob('*.json'))
    files.update(folder.glob('forge_sol_S28_*_pins_20261025/*.json'))
    files.add(folder/'forge_sol_S28_SHA256SUMS_20261025.txt')
    for stage in result['stages']:
        build=Path(stage['engine']).parent
        for rel in ('Testing/Temporary/LastTest.log','Testing/Temporary/LastTestsFailed.log',
                    'uci-regression.log','ownbook-regression.json',
                    'CMakeFiles/forge_core.dir/flags.make','CMakeFiles/forge.dir/flags.make',
                    'CMakeFiles/forge.dir/link.txt','CMakeFiles/forge_tests.dir/flags.make',
                    'CMakeFiles/forge_tests.dir/link.txt'):
            p=build/rel
            if p.is_file():files.add(p)
files.update((ROOT/'forge_sol_S28_initial_apply_20261025').glob('*.json'))
for name in ('forge_sol_S28_first_dryrun_20261025','forge_sol_S28_final_dryrun_20261025','forge_sol_S28_final_dryrun_v2_20261025'):
    files.update((ROOT/name).glob('*'))
files={p for p in files if p.is_file()}
bundle=OUT/'forge_sol_S28_native_evidence_20261025.jsonl.gz'
index=[]
with bundle.open('xb') as f:
    with gzip.GzipFile(filename='',mode='wb',fileobj=f,mtime=0) as z:
        for p in sorted(files):
            b=p.read_bytes();entry={'original_path':str(p.relative_to(ROOT)),'bytes':len(b),'sha256':hashlib.sha256(b).hexdigest()}
            row=dict(entry,encoding='base64',data=base64.b64encode(b).decode('ascii'))
            z.write((json.dumps(row,separators=(',',':'),sort_keys=True)+'\n').encode());index.append(entry)
# Validate actual compressed bytes after closure, not just the in-memory producer.
observed=[]
with gzip.open(bundle,'rt') as f:
    for line in f:
        row=json.loads(line);b=base64.b64decode(row['data'],validate=True)
        assert len(b)==row['bytes'] and hashlib.sha256(b).hexdigest()==row['sha256']
        observed.append({k:row[k] for k in ('original_path','bytes','sha256')})
assert observed==index
write('forge_sol_S28_native_evidence_index_20261025.json',json.dumps({'status':'PASS','bundle':bundle.name,'bundle_sha256':sha(bundle),'records':index,'count':len(index),'policy':'Original bytes losslessly encoded; no source/build/binary export; original private outputs retained. Native checksum manifests also include retained private source/build products.'},indent=2)+'\n')
copy_names=['forge_sol_S28_rebase_e48f006_timepack4_20261025.patch','forge_sol_S28_missing_tool_red_20261025.json',
'forge_sol_S28_pin_guard_red_20261025.txt','forge_sol_S28_pin_guard_green_20261025.txt',
'forge_sol_S28_print_summary_red_20261025.txt','forge_sol_S28_postcheck_guard_red_20261025.txt',
'forge_sol_S28_tool_tests_20261025.txt','forge_sol_S28_tool_tests_v2_20261025.txt',
'forge_sol_S28_tool_tests_v3_20261025.txt','forge_sol_S28_tool_tests_v3_postcheck_20261025.txt',
'forge_sol_S28_kit_layout_tests_20261025.txt','forge_sol_S28_native_v2_source_20261025.json',
'forge_sol_S28_final_pin_postcheck_20261025.json','forge_sol_S28_postcheck_command_20261025.json',
'forge_sol_S28_source_identity_results_20261025.json','forge_sol_S28_source_identity_command_20261025.json',
'forge_sol_S28_source_identity_audit_20261025.py','forge_sol_S28_final_dryrun_trace_results_20261025.json',
'forge_sol_S28_trace_observer_red_20261025.json','forge_sol_S28_dryrun_trace_20261025.py',
'forge_sol_S28_native_controller_20261025.py','forge_sol_S28_native_queue_20261025.json',
'forge_sol_S28_input_hashes_before_20261025.json','forge_sol_S28_source_review_20261025.md',
'forge_sol_S28_baseline_git_audit_20261025.json']
for name in copy_names:shutil.copyfile(ROOT/name,OUT/name)
for name in ('forge_sol_S28_input_audit_20261025.json','forge_sol_S28_input_audit_20261025.md','forge_sol_S28_tool_review_20261025.json'):
    shutil.copyfile(ROOT.parent/name,OUT/name)
# No copies of the three existing queued patches. Their original paths and hashes stay in the queue.
refs='328459 / 945640 / 3024381 / 9162399 / 20421972'
lines=['# S28 e48f006 rebase qualification — 2026-10-25','','All results are Linux native observations. The accepted lock remains h256_e12. No speed, Elo, gate confirmation or Windows-PC claim.','','Depth order: **11 / 13 / 16 / 20 / 22**. Each patch was applied independently to a fresh f006 source copy.','','| Base | Queue | Original -F0 dry run | Repair used | OFF nodes | ON nodes | First ON difference |','|---|---|---|---|---|---|---|']
for name in ('L_f006','B_f006'):
    for s in cases[name][1]['stages'][1:]:
        p=s['patch'];off=' / '.join(str(x['nodes']) for x in s['off']);on=' / '.join(str(x['nodes']) for x in s['on'])
        lines.append(f"| {name[0]} | {s['id']} | {'PASS' if p['original_dryrun_exit']==0 else 'FAIL (preserved)'} | {'necessary CMake-only context rebase' if p['used_repair'] else 'No'} | {off} | {on} | {s['pc_precheck_depth'] if s['pc_precheck_depth'] is not None else 'null — time-only'} |")
lines += ['', 'The timepack4 control is `TmDecisiveWinStable=60`, advertised default 0; its runtime scale applies to managed-time search. Fixed-depth ON=OFF and a null precheck are expected. P23b uses `RefutLmr=1`; P27R uses `QsEvasionSeeNonPv=1`; both defaults are 0. Requested controls were advertised and checked before ON runs.', '', 'Only the B/timepack4 original failed: two CMake context hunks. Its original failed dry-run is retained before the actual repaired dry-run/application. L used the original unchanged. The repair relocates registration at common EOF; all non-CMake patch bytes equal the original. No engine search change was invented by this rebase.', '', '| Delivered necessary patch | SHA256 | Full patch diffstat |','|---|---|---|','| `forge_sol_S28_rebase_e48f006_timepack4_20261025.patch` | `791f432b6c82f76e478c25bee98a0439e2c91a42abb662fbeeafc24e8b6638c9` | 4 files, +164 −1 (CMakeLists +4; search.hpp +19; search.cpp +17 −1; timepack4_tests +124) |', '', 'All ten engines pass both perft5 totals (4865609 / 193690690), whole-executable and NNUE-object FMA counts 0, and the supplied NNUE-evaluate checker. Full CTest retains only the exact four original FAIL lines in forge_tests. These are compatibility/correctness observations, not acceptance of any queued search change.', '', 'Original queue patches are referenced by full hash in `forge_sol_S28_native_queue_20261025.json`; they are not resubmitted under new names. Original commands/streams, application receipts, source/binary hashes, complete native manifests and test logs are losslessly preserved in the indexed evidence bundle.']
write('forge_sol_S28_rebase_bench_e48f006_20261025.md','\n'.join(lines)+'\n')
report=['# S28 development report — 2026-10-25','','**Qualification complete; adoption/strength UNPROVEN.** Accepted source remains code-base `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792` plus the supplied h256_e12 network overlay `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b` (MD5 `6d22f612c855e17c62d396d32da99ea4`); accepted buffix base is preserved separately. Candidate e48f006 is not adopted. S03 was published before this work at `a57839e55d3c2d2cc7578369c9e09cc7be21b62c`.', '', 'The portable kit copies full build inputs into a NEW output, swaps only its copied net, performs fresh full Release builds, gates every new engine first at OFF d11, observes pins, regenerates exact allowlists/checksums and appends metadata preserving old bytes. It defaults to dry-run. Three existing queue patches were qualified independently; only the demonstrated B/timepack4 CMake conflict received a necessary context repair.', '', '| Check | Status | Actual evidence |','|---|---|---|','| Native full Release matrix | PASS | 10 fresh engines, four controller cases; GCC 14.2, C++20, CMake 3.31.6; strict float H256 x86-64-v3/znver5 recipe in guide and original argv/flags |','| First invocation d11 gate | PASS | Every new engine first invoked OFF; fixed oracle, not self-derived |','| Current-net OFF five references | PASS | L/B: 308972 / 745494 / 2460422 / 11901452 / 31111774 |',f'| Candidate-net OFF five references | PASS | All eight f006 engines: {refs} |','| ON five-depth observations | PASS | Six independent queue runs; exact table in rebase report |','| perft5 / kiwipete5 | PASS | 4865609 / 193690690 on all ten engines |','| FMA | PASS | 0 whole-executable + 0 NNUE-object on all ten; supplied NNUE-body checker also passed |','| Original forge_tests / full CTest | PASS known-failure policy | Only forge_tests fails; each actual run retains exactly four original FAIL lines, not silently relabeled |','| Final strict OFF/base pin postcheck | PASS | All ten stage signatures; original four checksum manifests verified first |','| Input / source / net / executable identity | PASS | 151 original files unchanged; all ten actual net and retained source/binary hashes verified |','| Final tool tests | PASS | 27/27, including relocated five-file kit layout |','| Final shell dry-run filesystem trace | PASS | Four successful mutating file syscalls, all inside NEW output; inside-output checksum check PASS |','| New ASan/UBSan matrix | UNVERIFIED | No new sanitizer matrix in S28; Release results are not a sanitizer claim |','| Full native filesystem syscall trace | UNVERIFIED | Trace proof is final shell dry-run only; native input immutability/source audits are separate |','| Windows / PC / speed / equal-time Elo / G104c confirmation | UNVERIFIED | No PC run, speed percentage, match, Elo claim, or lock switch |', '', 'Native execution used the actual frozen v2 tool SHA256 `7530b90a4e5dcb2cfdd49f4fc186cabd78b193a8523700dc50637038c7543c7d`. The exact original source bytes are preserved, not reconstructed. Final v3 SHA256 `421b156ea48dfbaa5ff0e6b219baa6b4e3e3102b705d0c181144413e8cd39db3` adds strict queued-OFF/base pin equality and printed summaries. Its pure guard was applied read-only to closed native evidence; it is not described as a repeated final-v3 native matrix. Final v3 shell dry-run was executed and traced. Postchecker SHA256 `a091b30611829ddb8319b5d47e6bb2dea7cdb1b1e3042db6df2d7ac6aee15f08` verifies the original captured manifest SHA, actual inside-output sha256sum -c, complete planned stage IDs and all three zero-exit/EOF captures before comparing exact signatures.', '', '## Native engine identities', '', '| Case / stage | Executable SHA256 | CTest passed / total |', '|---|---|---|']
for name in ('L_lock','B_lock','L_f006','B_f006'):
    folder,result=cases[name]
    for s in result['stages']:
        log=load(folder/s['ctest']['raw']);text=base64.b64decode(log['stdout']['data']).decode()
        matches=re.findall(r'\d+% tests passed, (\d+) tests failed out of (\d+)',text);assert len(matches)==1
        failed,total=map(int,matches[0])
        report.append(f"| {name} / {s['id']} | `{s['engine_sha256']}` | {total-failed}/{total}; original known-four forge_tests failure |")
report += ['', '## Net-specific observations', '', '| Case | Current h256_e12 | Candidate e48f006 |','|---|---|---|','| WAC001, d12 | f6h5, cp661 | f6h5, cp629 |','| White promotion, d1 | c6d7, cp642 | c6d7, cp686 |','| Mirror promotion, d1 | c3d2, cp642 | c3d2, cp686 |', '', 'Only one literal FAIL line changes: `FAIL: WAC 001 score 661 below 31997` becomes `FAIL: WAC 001 score 629 below 31997`. The WAC move line and the two identical promotion FAIL lines stay unchanged. Promotion score pins nevertheless change and are recorded explicitly. No expected test source value was edited.', '', '## Preserved evidence and limitations', '', f'There are **{len(raw_commands)} actual Runner command receipts / 627 stdin+stdout+stderr streams**, plus independent pin captures, full test logs, original manifests, actual patch failure/repair receipts, generated compile flags and hashes. The compressed JSONL evidence bundle has {len(index)} original-file records. Every record was decoded and its original byte count/SHA verified after compression; its index maps each original private path. This gzip file is a lossless raw-evidence container, not a source archive. Complete source/build/binary products remain retained in their original private output directories and were checked by the original manifests.', '', 'Independent closed review verified all 3048 files listed by the four native manifests, all 209 commands/627 streams, ten source/net/executable identities and unchanged original inputs. Source review found and closed the OFF-pin allowance gap. TDD RED/GREEN receipts and the trace-observer false-positive attempt are retained. The first failed observer did not retain its stdout/stderr before assertion: those bytes are marked UNAVAILABLE and were not reconstructed; its original trace is retained. A fresh observer retained raw evidence before checking and passed.', '', 'The current-net baseline executable hashes reproduce the accepted native binaries exactly. Candidate compatibility is not candidate strength acceptance. No NPS percentage or Elo is inferred from changed ON node counts.', '', 'Next action after verified publication: proceed to S04, preserve h256_e12 references globally, and use these f006-specific OFF/ON pins only if a future authorized lock transition is confirmed. No existing queued engine patch is accepted by this tooling task.', '', 'For original-file verification, read each gzip JSONL line, base64-decode `data`, and require its length/SHA256 to equal `bytes`/`sha256`; the published index lists the same records. Never extract over an existing directory. The five-file kit and full dated instructions are adjacent; the S01 pin helper remains a SHA-pinned existing dependency rather than a duplicate.']
write('forge_sol_S28_report_20261025.md','\n'.join(report)+'\n')
checkpoint=(ROOT/'forge_sol_S28_continuation_20261025.md').read_text()
checkpoint+='\nFinal update, 10:52 UTC: all four native cases closed PASS, including all B/f006 queues. B/timepack4 alone used the necessary repair after its original failed. Final strict postcheck PASS: ten stage signatures and four original manifest verifications. Root source audit PASS: ten actual net/source/executable identities and 151 unchanged original files. Publication view is forge_sol_S28_delivery_20261025; root must still commit, push and verify immutable readbacks. S04 follows publication. No lock was switched; PC/new sanitizer/full-native-trace/speed/Elo/gate confirmation remain UNVERIFIED.\n'
write('forge_sol_S28_continuation_20261025.md',checkpoint)
shutil.copyfile(Path(__file__),OUT/Path(__file__).name)
for p in OUT.iterdir():
    if p.is_file() and p.suffix!='.gz':assert bytes.fromhex('4f70656e4149') not in p.read_bytes(),p
names=sorted(p.name for p in OUT.iterdir() if p.is_file())
p=subprocess.run(['sha256sum','--',*names],cwd=OUT,capture_output=True,check=True)
manifest=OUT/'forge_sol_S28_delivery_SHA256SUMS_20261025.txt';manifest.write_bytes(p.stdout)
p=subprocess.run(['sha256sum','-c',manifest.name],cwd=OUT,capture_output=True,check=True)
print(json.dumps({'status':'PASS','out':str(OUT),'files':len(names)+1,'bundle_records':len(index),'bundle_sha256':sha(bundle),'manifest_sha256':sha(manifest),'inside_output_checksum_exit':p.returncode},indent=2))
