from pathlib import Path
import datetime,hashlib,json,shutil,subprocess
r=Path('/workspace/dwqww');h=Path('/workspace/forge-jobACD-20261025');v=r/'validation/forge_sol_jobACD_20261025';release=r/'releases/forge_sol_jobACD_20261025'
checks={}
for tag in ['lock','buffix','compiled_out']:
 checks[tag]=json.loads((h/f'forge_sol_a_{tag}_checks_20261025/forge_sol_nnue_checks_20261025.json').read_text());assert checks[tag]['status']=='PASS'
par=json.loads((h/'forge_sol_a_million_parity_20261025.stdout').read_text());assert par['status']=='PASS' and par['unique_positions']==1000000
adv=json.loads((h/'forge_sol_a_advisory_abba_20261025/forge_sol_advisory_result_20261025.json').read_text());assert adv['status']=='COMPLETE_ADVISORY_ONLY' and len(adv['rows'])==80
patch=json.loads((h/'forge_sol_a_patch_identity_20261025.json').read_text());assert hashlib.sha256((h/patch['patch']).read_bytes()).hexdigest()==patch['sha256']
# Freeze original logs, including negative/failed approaches; never collect binaries/objects/source exports.
for f in h.iterdir():
 if f.is_file() and f.name.startswith('forge_sol_') and f.suffix in ['.stdout','.stderr','.json','.py','.sh','.cpp']:
  shutil.copyfile(f,v/f.name)
for name in ['forge_sol_a_lock_checks_20261025','forge_sol_a_buffix_checks_20261025','forge_sol_a_compiled_out_checks_20261025','forge_sol_a_advisory_abba_20261025','forge_sol_checker_red_20261025']:
 dst=v/name;dst.mkdir(exist_ok=True)
 for f in(h/name).iterdir():
  if f.is_file():shutil.copyfile(f,dst/f.name)
for folder,label in [('/workspace/forge-jobACD-space-20261025','forge_sol_preservation_20261025'),('/workspace/forge-jobACD-dependency-20261025','forge_sol_dependency_20261025')]:
 dst=v/label;dst.mkdir(exist_ok=True)
 for f in Path(folder).iterdir():
  if f.is_file() and f.suffix in ['.json','.py','.md','.txt','.stdout','.stderr']:shutil.copyfile(f,dst/f.name)
for name in ['forge_sol_exactint32_h256e12_20261025.patch','forge_sol_nnue_check_20261025.py','forge_sol_nnue_check_20261025.sh','forge_sol_exactint32_parity_20261025.cpp','forge_sol_exactint32_uci_test_20261025.py','forge_sol_exactint32_thread_test_20261025.cpp']:
 shutil.copyfile(h/name,release/name)
table=(Path('/workspace/forge-jobACD-net-audit-20261025/evidence/forge_sol_accumulator_bounds_20261025.md').read_text())
stats='|Depth|OFF refresh/update|ON refresh/update|Refresh construction share|\n|---|---:|---:|---:|\n'
for i in checks['lock']['modes']['OFF']['refresh_statistics']:
 stats+=f"|{i['depth']}|{i['refreshes']}/{i['updates']}|{i['refreshes']}/{i['updates']}|{100*i['refreshes']/(i['refreshes']+i['updates']):.9f}%|\n"
ratios='\n'.join(f"- d{d}: median ON/lock NPS ratio **{row['median_ratio']:.9f}**; screen `{row['screen']}` (20 ratios from10 ABBA blocks)." for d,row in adv['depths'].items())
report=f'''# Forge Sol Job A — 20261025

**Correctness-qualified isolated research patch; no speed/Elo claim or adoption.** Job C/D have not started at this checkpoint. Base is supplied1ab50b2d+h256_e12 net MD5 6d22f612c855e17c62d396d32da99ea4 (C++ source matches f4911f2). Alternate base is the supplied buffer patch SHA2569ce56b3d9b5291e450679209ac991c4d560bf40f64aa0281492c53ad37d96a5c; search MD59553f697fa7bed500f945bc247d70dbf. Previous work remains preserved.

Patch `{patch['patch']}` SHA256 **`{patch['sha256']}`**. Feature patch source commit `13672013703abcd8c4eb057c6ea6a04a394fe8e6`. Exactly one build option `FORGE_NNUE_EXACT_INT32_AVX2` and UCI option `NnueExactInt32`, both OFF by default. Configuration is atomic, fixed before first go/bench. Incremental children inherit their parent's representation; worker reads remain race-free in the tested API lifecycle. ON widens stored weights to int32, never narrows accumulators, and converts q/4096 into the unchanged float output arithmetic. Search, eval values, network format, TT and move ordering unchanged; make/unmake allocations unchanged. No refresh cache was added: only8 full refreshes occur per bench.

```text
{patch['diffstat'].strip()}
```

| Check | Result | Evidence |
|---|---|---|
| Patch dry-run + apply on both supplied bases | PASS | No offsets/fuzz; search/eval/net remain unchanged |
| Build switch default OFF | PASS | Actual compiled-out build; ON request reports unavailable, no active counters |
| Runtime OFF/ON five-depth bench, both bases | PASS | 308972 /745494 /2460422 /11901452 /31111774 for every mode |
| Startpos perft5, both bases OFF/ON | PASS |4865609 |
| Kiwipete5, both bases OFF/ON | PASS |193690690; exact user FEN |
| NNUE FMA, all three build profiles | PASS |0 over complete decoded NNUE symbol bodies; static runtime/library code outside this scope |
| UCI output | PASS |Exact lock output plus only the new OFF-default option |
| Actual active-once proof / counters | PASS |Nonzero int32 refresh/update counters ON; zero OFF; no false active for perft/UseNNUEfalse |
| Incremental vs fresh | PASS |1,000,000 unique legal positions;0 lane-bit/output mismatches |
| Independent scalar int64 vs AVX2 int32 | PASS |Same1M positions,0 mismatches; compiler scalar oracle auto-vectorization disabled |
| Special transitions | PASS |{par['castles']} castles,{par['en_passant']} EP,{par['promotions']} promotions,{par['nulls']} nulls; in-place checks included |
| Original Release / ASan+UBSan CTest | KNOWN FAILURES |Each13/14; exactly the four original FAIL lines below, no new sanitizer finding |
| Actual int32 ASan/UBSan parity | PASS |10,000 unique positions,0 mismatches |
| TSan private-board actual-core concurrency | PASS |4threads/8000 transitions; controller Board initialized before workers as in UCI |
| Concurrent first-ever Board construction | FAIL on unchanged lock |Preexisting attacks::init race reproduced separately; no fix in this NNUE patch |
| Windows / target-box adoption | UNVERIFIED |Owner independent qualification required |
| Elapsed refresh-time share | UNVERIFIED |Table below is construction-call share, not profiler time |

Full bounds and output arithmetic establish an exact integer grid, not an Elo result. First standalone TSan attempt omitted serial Board bootstrap, raced and crashed; original trace and untouched-lock reproduction retained. The lifecycle-correct retry is a separate test, not relabeling the failure. UCI already constructs the controller Board first. Fixing concurrent direct-API bootstrap is a separate future task. Review found/fixed a false activation acknowledgement; pre-fix and unfixed-base RED outputs are retained. An initial low-depth UCI smoke preceded its first hard d11 gate; that procedural deviation is saved. Final rebuilt delivery binary began qualification with OFFd11. One initial negative fixture failed on copied-EXE permissions; corrected behavioral RED remains separate. Input pack all219 SHA rows match; its prompt row has a stale byte count5755 versus6546, without a hash mismatch.

```text
FAIL: WAC 001 expected g3g6 got f6h5
FAIL: WAC 001 score 661 below 31997
FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
```

## Refresh statistics

Same counts OFF/ON on each base. ON executes every update in int32. Values are fractions of refresh+update calls, not elapsed time; rounded ppm counters can be0 at deeper depths.

{stats}

## Per-network accumulator safety

All values are conservative supersets of attainable boards, in integer q units (real=q/4096), not empirical extrema. Full all768+4dirty bounds <2^24 and INT32_MAX prove exact float conversion and int32 headroom; runtime qualification rejects future unsupported nets. Observed million-corpus q range {par['q_min']}..{par['q_max']}.

{table}

## Advisory-only Linux timing

One preregistered run, GCC14.2/strict FP/static/znver5 on shared Intel Xeon8573C; singleCPU0/nice19/T1/Hash16. A=untouched lock binary d90f5060; B=final feature build ON. All80 processes have fixed node counts and normal exits; no retries/outlier removal. The feature's extra layout/TLS/dispatch overhead relative to the untouched lock is included. These advisory ratios are **not a speed claim** or hardware adoption decision. Independent box and Windows ABBA remain required.

{ratios}

Feature-enabled H256 accumulator footprint grows2080 to4128 bytes, including runtimeOFF; buildOFF keeps original layout. No heap allocation was added to make/unmake. Even a positive advisory median does not accept this feature; a sub+1% screen is marked drop for that tested depth, without deleting evidence.

## Reproduce

Apply only the feature patch to either supplied source tree. Keep all original docs; the patch adds its idea sources to the existing README/IDEA_SOURCE. All implementation is original; ideas only from the user fixed-grid review and AVX2 semantics, no external engine source or tuned values.

```bash
cmake -S . -B ./forge_sol_a_build_20261025 -DCMAKE_BUILD_TYPE=Release -DFORGE_NNUE_EXACT_INT32_AVX2=ON -DCMAKE_EXE_LINKER_FLAGS=-static '-DCMAKE_CXX_FLAGS=-DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=znver5 -pthread'
cmake --build ./forge_sol_a_build_20261025 -j2
bash forge_sol_nnue_check_20261025.sh --engine ./forge_sol_a_build_20261025/forge --out ./forge_sol_a_checks_20261025
```

The dated Python checker must sit beside its Bash entry. Output directories must be new. It exits nonzero on any hard mismatch and rejects optimized Python that would disable assertions. For a build-defaultOFF profile, add `--compiled-out`; its requestedON run must explicitly remain unavailable, not masquerade as active. The actual-core parity/thread sources are separate dated tests; no tests or unrelated flags are embedded in the engine patch. No ZIP/LICENSE/AGENTS/.agents delivery is added. Native compiler commands, original transcripts, source/binary hashes, predeclared timing protocol and failed approaches live under `validation/forge_sol_jobACD_20261025/`.
'''
(release/'forge_sol_jobA_report_20261025.md').write_text(report)
(v/'forge_sol_jobA_report_20261025.md').write_text(report)
# Sealed per-job delivery manifest; no circular self checksum.
rows=[]
for f in sorted(release.iterdir()):
 if f.is_file() and f.name!='forge_sol_jobA_sha256_20261025.txt':rows.append(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+f.name+'\n')
(release/'forge_sol_jobA_sha256_20261025.txt').write_text(''.join(rows))
cp=v/'forge_sol_jobACD_checkpoint_20261025.json';d=json.loads(cp.read_text());d.update({'stage':'A_COMPLETE_PUBLICATION_PENDING','A':'CORRECTNESS_QUALIFIED_NOT_ADOPTED_NO_SPEED_OR_ELO_CLAIM','A_advisory':adv['depths'],'live_jobs':[],'C':'NOT_STARTED','D':'NOT_STARTED','next':'Publish JobA independently and verify immutable downloads, then implement separate known-failure relabel JobC.'});cp.write_text(json.dumps(d,indent=2)+'\n')
print('JobA finalized, raw evidence preserved:',len(list(v.rglob('*'))),'paths')
