# Forge Sol A, C, D — 20261025 final checkpoint

All three jobs were completed and published independently in order. **No speed, Elo or training-gain claim.** Accepted engine/integration source remains unchanged. Earlier work and failed approaches are preserved. New delivery contains dated patches/tools/reports and raw evidence, without a new ZIP, licence or agent/skill directory.

|Job|Decision|Independent artifact commit|Report|
|---|---|---|---|
|A exact-int32 AVX2|DROP from adoption: advisory medians below+1%; correctness gates pass|`e5408cf3a134f1b889c2a0a6d7c74daa772184d8`|[Job A](forge_sol_jobA_report_20261025.md)|
|C known-failure labels|Validated tests-only patch; original expectations preserved|`a0b6811f9a3c03c17bf46d221f833517314ada4d`|[Job C](forge_sol_jobC_report_20261025.md)|
|D offline filter|Sample-validated; production holdouts/game proof remain UNVERIFIED|`6585ecea29db7845e8adbd1f66f98e2af598afca`|[Job D](forge_sol_jobD_report_20261025.md)|

## Delivered patches and tools

|File|SHA256|Diffstat / scope|
|---|---|---|
|forge_sol_exactint32_h256e12_20261025.patch|`e661a145e301d3483ccaeaba65779d1d2002067263c836250e6418b9dccd151d`|6files,232insertions/5deletions; original README/IDEA_SOURCE additions plus CMake/header/NNUE/UCI|
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

|Depth|Refreshes OFF/ON|Updates OFF/ON|Refresh construction share|
|---|---:|---:|---:|
|11|8/8|238992/238992|0.003347280%|
|13|8/8|571275/571275|0.001400357%|
|16|8/8|1862090/1862090|0.000429623%|
|20|8/8|9547266/9547266|0.000083794%|
|22|8/8|23231031/23231031|0.000034437%|

These are refresh/(refresh+update) construction counts, not elapsed refresh-time share. Time share is UNVERIFIED. Only8 full refreshes occur per bench; a refresh-only cache was not added.

### All13 networks: exactness and overflow

# Forge Job A independently recomputed accumulator bounds — 20261025
Each range is a conservative possible-prefix superset in integer q units (real=q/4096), not an observed or attainable range. All13 manifest hashes match. No speed or strength claim.
| Net | q min32 | q max32 | q min64 | q max64 | abs top32+4dirty | abs all768+4dirty | int32 / float exact-grid |
|---|---:|---:|---:|---:|---:|---:|---|
| lock_e12 | -219282 | 123238 | -379512 | 235351 | 259471 | 1662360 | PASS / PASS |
| e32_f003 | -326161 | 145444 | -509013 | 270955 | 377427 | 1978144 | PASS / PASS |
| e16_f004 | -220295 | 109619 | -383973 | 207779 | 259245 | 1523652 | PASS / PASS |
| e24_f005 | -217319 | 107759 | -331211 | 205526 | 256977 | 1438848 | PASS / PASS |
| e48_f006 | -279224 | 148321 | -506797 | 278156 | 323541 | 2218441 | PASS / PASS |
| e16_f007 | -224719 | 130291 | -351616 | 246650 | 265799 | 1526440 | PASS / PASS |
| e20_f008 | -208489 | 117191 | -355056 | 220166 | 246276 | 1591707 | PASS / PASS |
| e16_f009 | -208162 | 132569 | -341538 | 255103 | 251151 | 1557076 | PASS / PASS |
| e16_f010 | -211525 | 127195 | -318754 | 241531 | 247674 | 1477082 | PASS / PASS |
| e20_f011 | -276371 | 131597 | -516727 | 256340 | 315463 | 1569370 | PASS / PASS |
| e16_f012 | -205125 | 145004 | -345733 | 269875 | 242129 | 1539796 | PASS / PASS |
| e20_f013 | -194591 | 113024 | -331427 | 207626 | 229760 | 1516258 | PASS / PASS |
| e20_f014 | -200185 | 115181 | -303279 | 219089 | 236957 | 1530515 | PASS / PASS |

All full768+dirty4 bounds are below2^24=16777216 and int32_max=2147483647. A refresh-only AVX2 int32 path that converts q to float then divides by4096 exactly can feed the unchanged float output layer without loss. This does not justify output requantization. True int16 accumulators are excluded. Existing float accumulators need not be changed.

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
