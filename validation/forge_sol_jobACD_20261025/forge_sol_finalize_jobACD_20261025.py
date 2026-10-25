from pathlib import Path
import json,hashlib,shutil,datetime,subprocess
r=Path('/workspace/dwqww');h=Path('/workspace/forge-jobACD-20261025');v=r/'validation/forge_sol_jobACD_20261025';release=r/'releases/forge_sol_jobACD_20261025';d=Path('/workspace/forge-jobACD-D-20261025')
a=json.loads((v/'forge_sol_jobA_public_readback_20261025.json').read_text());c=json.loads((v/'forge_sol_jobC_public_readback_20261025.json').read_text());dp=json.loads((v/'forge_sol_jobD_public_readback_20261025.json').read_text());assert all(x['status']=='PASS' for x in [a,c,dp])
patch=json.loads((v/'forge_sol_a_patch_identity_20261025.json').read_text());sm=json.loads((v/'forge_sol_jobD_evidence_20261025/forge_sol_cpu_smoke_20261025/forge_sol_data32_cpu_smoke_20261025.json').read_text());assert sm['status']=='PASS_ACTUAL_UNCHANGED_V3B_CPU_CLI'
nettable=(v/'forge_sol_net_audit_20261025/evidence/forge_sol_accumulator_bounds_20261025.md').read_text()
qa=json.loads((v/'forge_sol_a_lock_checks_20261025/forge_sol_nnue_checks_20261025.json').read_text());stats='|Depth|Refreshes OFF/ON|Updates OFF/ON|Refresh construction share|\n|---|---:|---:|---:|\n'
for row in qa['modes']['OFF']['refresh_statistics']:stats+=f"|{row['depth']}|{row['refreshes']}/{row['refreshes']}|{row['updates']}/{row['updates']}|{100*row['refreshes']/(row['refreshes']+row['updates']):.9f}%|\n"
body=f'''# Forge Sol A, C, D — 20261025 final checkpoint

All three jobs were completed and published independently in order. **No speed, Elo or training-gain claim.** Accepted engine/integration source remains unchanged. Earlier work and failed approaches are preserved. New delivery contains dated patches/tools/reports and raw evidence, without a new ZIP, licence or agent/skill directory.

|Job|Decision|Independent artifact commit|Report|
|---|---|---|---|
|A exact-int32 AVX2|DROP from adoption: advisory medians below+1%; correctness gates pass|`{a['artifact_commit']}`|[Job A](forge_sol_jobA_report_20261025.md)|
|C known-failure labels|Validated tests-only patch; original expectations preserved|`{c['artifact_commit']}`|[Job C](forge_sol_jobC_report_20261025.md)|
|D offline filter|Sample-validated; production holdouts/game proof remain UNVERIFIED|`{dp['artifact_commit']}`|[Job D](forge_sol_jobD_report_20261025.md)|

## Delivered patches and tools

|File|SHA256|Diffstat / scope|
|---|---|---|
|forge_sol_exactint32_h256e12_20261025.patch|`{patch['sha256']}`|6files,232insertions/5deletions; original README/IDEA_SOURCE additions plus CMake/header/NNUE/UCI|
|forge_sol_knownfail_h256e12_20261025.patch|`4ac98f92d45f67fae8aaa8067fe28c0fca36662b3688013105f738245ee55805`|tests/tests.cpp only,55insertions/7deletions|
|forge_sol_datafilter_20261025.py|`6ccf78c864c44155cea22044fe05d0584bec5241acdc5ebb2b71e23886007ab3`|Offline stdlib reader/writer/filter; no engine or trainer edits|

Every patch dry-runs and applies with zero offsets/fuzz to the supplied h256_e12 lock and h256_e12+buffix. Buffer patch SHA2569ce56b3d9b5291e450679209ac991c4d560bf40f64aa0281492c53ad37d96a5c; buffer searchMD59553f697fa7bed500f945bc247d70dbf. Source lock C++ is f4911f2 /1ab50b2d+netMD56d22f612c855e17c62d396d32da99ea4. Nothing replaces the prior engine/source accepted improvements.

## A qualification

|Check|Result|
|---|---|
|Both bases, runtimeOFF and ON, d11/13/16/20/22|PASS:308972 /745494 /2460422 /11901452 /31111774|
|Actual build-defaultOFF profile, ON unavailable proof|PASS; no false activation or backend counter|
|Both bases OFF/ON perft5|PASS:4865609|
|Both bases OFF/ON exact kiwipete5|PASS:193690690|
|All three NNUE decoded-code profiles FMA|PASS:0; NNUE symbol scope, external runtime excluded|
|UCI output and atomic admission|PASS; only new option, OFF default, immutable afterfirstgo/bench|
|Activation once / counter / no perft or NNUE-disabled false proof|PASS; original negative controls retained|
|Incremental vs fresh and independent scalar vs AVX2|PASS:1M unique legal positions,0 lane/output mismatches|
|Special coverage|426castles,118EP,6025promotions,232nulls; in-place checks|
|Release and ASan/UBSan original suites|Each13/14; exactly4 historical FAIL lines, no new sanitizer finding|
|Actual ON ASan/UBSan parity|PASS10k positions,0 mismatches|
|Lifecycle-correct private-board TSan|PASS4threads/8000 transitions|
|Concurrent first-ever Board construction|FAIL independently reproduced on unchanged lock; separate open issue|
|Native Windows/target-box adoption|UNVERIFIED|

Only one feature/option was implemented. It uses int32 accumulators, never narrows to int16, and converts the exact q/4096 grid into the unchanged float output kernel. No search/eval-value/TT/order/net-format changes or make/unmake allocations. Build macro and UCI option both default OFF. Feature-enabled accumulator size2080→4128bytes, including runtimeOFF, measured by native sizeof; buildOFF keeps old layout. TLS/dispatch/layout overhead is included in the advisory candidate-versus-untouched-lock comparison.

One preregistered singleCPU0/nice19 Linux ABBA run:10blocks per depth,80normal processes,20adjacent ratios at each depth. Median ON/lock ratios d13=0.9759681528985205, d16=0.9298144110530071. Shared Intel/GCC14.2 results are advisory only; no A/A confidence or Zen5 speed claim. Both are below the requested+1% screen, so drop from adoption. No retries or outlier deletion.

{stats}
These are refresh/(refresh+update) construction counts, not elapsed refresh-time share. Time share is UNVERIFIED. Only8 full refreshes occur per bench; a refresh-only cache was not added.

### All13 networks: exactness and overflow

{nettable}
All conservative full768+four-dirty bounds are below2^24 andINT32_MAX; original float output arithmetic remains unchanged. These are superset bounds, not empirical maxima. Current corpus q range−78343..16160. Full per-lane bound evidence/recheck is under validation.

## C qualification

Four prior FAIL lines are explicitly labelled only for their guarded documented outcomes. WAC001 expects g3g6 and>=31997 atd12; lockobservedf6h5/661 with matchingPV/d12 is known. Original rook promotion expectations c7c8r/c2c1r,PV,d1,score>100 remain intact; lock's alternate winning king moves c6d7/c3d2 scored642 each. Historical exact old numeric mate/promotion scores are UNVERIFIED; only old thresholds are documented.

Full14-command original CTest harness passes14/14 with four explicitKNOWN labels. Eight independent compiled negative mutations still exit1. Patch/runtime pass both bases using original-source macro0 objects; no A feature is linked. This relabel is not an engine bug repair or strength acceptance.

## D qualification and counts

Pure-stdlib deterministic SHA256(board32+STM) dedupe, paired columnar FPOS/FHCE preservation, fixed-seed order, optional score/result filter OFF default, counted reasons, new-output-only writes, read-only sealing and MD5 manifests. SQLite bounds index memory.21behavior tests and final source review pass; consumer-path tests run from the published layout also pass. Original inputs and trainer hashes remain unchanged. Native OFF output8files are entirely byte-identical to inputs.

|Shard|OFF kept/dropped|Threshold300 kept|Dropped|Draw|Loss/positive|Win/negative|
|---|---:|---:|---:|---:|---:|---:|
|t00000|50000/0|39533|10467|5288|2676|2503|
|t01000|50000/0|39447|10553|5174|2714|2665|
|t02000|50000/0|39342|10658|5378|2665|2615|
|t03000|50000/0|39344|10656|5282|2701|2673|
|Total|200000/0|157666|42334|21122|10756|10456|

Both independently reread output sets have **0 supplied h000 stand-in holdout overlap and0 duplicates**. Actual013/014 production overlap remains **UNVERIFIED** because those files/hashes are absent. Binary data32 game isolation is **UNVERIFIED**. Optional complete ordered text produces conservative game supersets across shards under documented chronology/legal-trajectory/constant-result assumptions; planted cross-shard group overlap0 passes, not authentic gameIDs. All916 supplied real-text board/score/meta rows match their POS; their HCE is absent and none was fabricated.

Actual unchanged v3b SHA2565cebba4d44133630e247d9ab4c0085fa6301dde8db1dfe1389452ac19d92313f loads all157666 filtered records through both RAM and mmap paths, all four arrays equal. An independent original-record lookup validates every retained score/meta/HCE. The real CLI ran3CPUsteps/768positions on filteredOFF data, seed20261025, train_mse **0.029621**, exit0, all inputs unchanged. PyTorch2.5.1+cpu lives in a private task runtime, not a global installation; no running GPU training was touched. This is a smoke loss, not training-gain evidence.

Original sample outputs (both modes), MD5 manifests, raw commands/logs, review records and CPU proof are published under `validation/forge_sol_jobACD_20261025/forge_sol_jobD_evidence_20261025/`. Generated three-step toy model exports remain local with exact hashes; they are not delivered as engine weights.

## Reuse and next action

- A: retain the dropped source/evidence; no same-host retry, implicit adoption or automatic merger.
- C: independently review/apply its tests-only patch; new outcomes beyond exact guards must fail.
- D: Engine NNUE reviews the tool/outputs, then runs it with BOTH authoritative013/014 files and complete ordered text for conservative game isolation. Check supplied-input hashes against authoritative originals before interpreting0 as production exclusion. Then run a separate training line; no training gain is established here.
- Concurrent direct-API first Board construction needs a separate init-once repair/review; current UCI serial bootstrap avoids the witnessed initialization race. This was not changed under A's scope.

Use `forge_sol_nnue_check_20261025.sh` with its dated Python checker; reproduce flags/options in JobA report. Use `python3 -B forge_sol_datafilter_tests_20261025.py` and CLI examples in JobD report. The CPU helper pins the exact supplied trainer hash and explicit CPU device. Existing validation skills were reused; no duplicate skill or unavailable plugin was claimed installed. All owned native/filter/training jobs are closed. Three old untracked teacher/NNUE work areas remain untouched. Checkpoints and restore maps permit recovery of losslessly compressed closed build products without discarding prior work.
'''
(release/'forge_sol_jobACD_report_20261025.md').write_text(body)
(v/'forge_sol_jobACD_report_20261025.md').write_text(body)
for name,paragraph in {'CURRENT_BASELINE.md':'A exact-int32 correctness qualification passes but advisory ratios0.975968/0.929814 fall below+1%; dropped, no adoption. C guarded known-failure relabel passes14/14+8negative controls on both bases; original expectations intact. D stdlib offline filter passes21tests+actualv3bCPU3steps (loss0.029621); real013/014 and binary game isolation remain UNVERIFIED. Accepted engine source untouched.','EXPERIMENT_LEDGER.md':'Completed ordered A/C/D independently on forge/sol-jobACD-20261025. A all5bothbasesOFF/ON/perft/FMA0/1Mexact parity pass; negative advisory drop retained. C tests-only55+/7- patch retains expectations,14/14 fullharness+8negative controls pass. D OFF200000kept, threshold300157666kept/42334drop; suppliedstandinoverlap0/dups0; nativev3bRAM/mmap157666fields match, CPU3steps0.029621. No speed/Elo/training gain claim.','NEXT_EXPERIMENTS.md':'No A speed adoption or same-host retry. Review standalone Cpatch and offline Dtool. Next actualowner action supplies BOTH authoritative013/014 files plus completeorderedtext; verify output position/group audits and hashes, then independentEngineNNUE training. First-ever concurrent Board API initialization race is a separate bounded repair, with unmodified-lock nativeTSan reproducer preserved.'}.items():
 f=r/'docs'/name;s=f.read_text();first,rest=s.split('\n',1);f.write_text(first+'\n\n## 2026-10-25 A/C/D final checkpoint\n\n'+paragraph+' [Combined report](../releases/forge_sol_jobACD_20261025/forge_sol_jobACD_report_20261025.md), [recoverable state](../validation/forge_sol_jobACD_20261025/forge_sol_jobACD_checkpoint_20261025.json).\n\n'+rest.lstrip('\n'))
for name in ['IDEA_SOURCE.md','README.md']:
 f=r/name;s=f.read_text();s+='\nJobC uses the user-supplied behavior-specific known-failure relabel idea; JobD uses the supplied FPOS/FHCE format and conservative ordered-text grouping idea. Original implementation/tests only; no external engine code or tuned parameters. Source links, hashes and separate decisions are in releases/forge_sol_jobACD_20261025/forge_sol_jobACD_report_20261025.md.\n';f.write_text(s)
# Future recovery is self-contained; do not claim indefinite background work.
cp=v/'forge_sol_jobACD_checkpoint_20261025.json';state=json.loads(cp.read_text());state.update({'updated_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'stage':'A_C_D_COMPLETE_INDEPENDENT_PUBLIC_DOWNLOADS_VERIFIED','D_publication':'VERIFIED25_IMMUTABLE_PUBLIC_DOWNLOADS_INCLUDING16RAW_SAMPLE_FILES','D_artifact_commit':dp['artifact_commit'],'owned_live_jobs':[],'live_jobs':[],'engine_source_change_on_checkout':'NONE; isolated patches only; accepted integration untouched','private_CPU_runtime':str(h/'forge_sol_cpu_runtime_20261025/site'),'private_runtime_import_command':'PYTHONPATH='+str(h/'forge_sol_cpu_runtime_20261025/site')+' PYTHONDONTWRITEBYTECODE=1 python3 -B ...','closed_build_products':'Losslessly gzipped with full metadata/restore maps; use dated helpers under preservation evidence before rerunning oldCTest','next':'Owner/EngineNNUE reviews C/D and supplies authoritative013014+orderedtext. NoAadoption/samehostretry. Separateinit-onceBoardAPIbug proposal may use retainedoriginalreproducer. No automated backgroundjob remains.'});cp.write_text(json.dumps(state,indent=2)+'\n')
# Final artifact hashes include every top-level deliverable, self excluded.
manifest=release/'forge_sol_jobACD_sha256_20261025.txt';manifest.write_text(''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name+'\n' for f in sorted(release.iterdir()) if f.is_file() and f!=manifest))
for name in ['forge_sol_jobD_public_readback_20261025.py','forge_sol_jobD_public_readback_20261025.stdout','forge_sol_jobD_public_readback_20261025.stderr','forge_sol_finalize_jobACD_20261025.py']:
 if(h/name).exists():shutil.copyfile(h/name,v/name)
assert not subprocess.check_output(['git','diff','dc5ff59','--','src','include','tests','CMakeLists.txt'],cwd=r)
print('Final ACD report/checkpoint prepared; accepted engine inputs unchanged.')
