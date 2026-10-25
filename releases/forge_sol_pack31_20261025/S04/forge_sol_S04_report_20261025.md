# S04 optional first-Board initialization repair, 20261025

Status: validated Linux correctness candidate, OFF by default. Performance and playing-strength effects remain **UNPROVEN**; no adoption, speed-gain or Elo claim.

The source-code base is `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792` **plus the explicit h256_e12 network overlay**, SHA256 `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`. B additionally contains the supplied buffix patch SHA256 `9ce56b3d9b5291e450679209ac991c4d560bf40f64aa0281492c53ad37d96a5c`. The accepted lock and earlier work are unchanged.

Patch `forge_sol_S04_attacksinit_fix_20261025.patch` SHA256 `29ee0866e90185a6a50f8389d8792399b890338c4e10f6457459652bbb6c15e7`; four files,110 insertions: bitboard.cpp12, CMakeLists.txt25, IDEA_SOURCE.md11, cold test62. It applies with `patch -p1 --fuzz=0` to both pristine supplied bases with no offset/fuzz. No public header, NNUE, evaluation, search, TT, move ordering, attack value or seed changes.

The old initialized bool was set before tables were populated, so another first Board constructor could return while table initialization was still in progress. On the exact current baseline, the new eight-thread cold test actually reports a TSan data race reading/writing this bool and exits66; original fatal signals and complete traces are retained. With `FORGE_ATTACKS_INIT_ONCE=ON`, standard `std::call_once` encloses **all** existing initialization writes. The premature bool exists only in the OFF branch; successful callers wait for completion and exception retry is not short-circuited by that bool. This fixes the demonstrated first-constructor scenario when enabled; it is not a universal full-engine race-free claim.

The option defaults OFF. OFF source tokens are unchanged, the two Release engine files are byte-identical to their original baselines, and no cold target, header, counter, UCI option or runtime output is added. ON registers a dedicated Linux GNU/Clang `forge_sol_S04_cold_tsan_test_20261025` target. It compiles the real Board and bitboard translation units under TSan, independently of the engine core, so ASan/UBSan profiles do not combine incompatible sanitizer flags. Unsupported native TSan platforms do not acquire this Linux test target.

## Completed checks

| Check | Status | Actual evidence |
|---|---|---|
| Exact unchanged baseline, eight first constructors | RED reproduced | TSan init-bool race, exit66; no serial controller Board |
| ON standalone cold TSan batch | PASS |1000 separate execs, eight gated first Board constructors each;1000 exact expected outputs, exits0 and empty stderr |
| Cold raw integrity | PASS |All1000 original streams/base64/SHA and unique recorded PIDs independently audited; no skipped faults, retries or suppressions |
| Active cold probe binding | PASS |Binary SHA256 `aa59cb60f392ce77b7f55ba68ab8ed6eed41a3a52e1f5008b92f260e3faeb9c5`; source/test/build/end identities match |
| L/B Release OFF and ON, all five bench depths | PASS |308972 /745494 /2460422 /11901452 /31111774 |
| L/B Release OFF and ON, both perft5 totals | PASS |4865609 /193690690 |
| L/B Release OFF and ON, supplied NNUE FMA checker | PASS |FMA0; supplied v2 checker scope preserved |
| All eight full Release/ASan+UBSan configurations | PASS known-failure policy |Fresh builds; first bare d11 before other checks; exactly four original FAIL lines in forge_tests, no other failed target |
| ON dedicated cold TSan CTest | PASS |Registered and passes in all four ON configurations; no ASan linkage in its separate target |
| OFF target absence / interface | PASS |Cold target absent in all OFF lists; complete UCI handshake bytes identical across all four Release modes |
| Advisory ABAB | COMPLETED / UNPROVEN |20 fresh d13 processes,10 adjacent pairs, child-only CPU0, no retry/outlier removal; not an adoption gate |
| Independent review | PASS |Source, baseline RED,1000 cold records, all eight profiles and advisory raw records audited |
| Native Windows / PC / Elo | UNVERIFIED |No PC execution or matches; no strength inference |

Each cold process starts eight threads at a barrier **before the first Board exists**, then validates each worker's startpos perft3=8902, restored FEN and kiwipete perft2=2039. The1000 runs are fresh processes, not warm repetitions in one initialized process. This batch took an actual1336.4806380720038seconds. Test source SHA256 `24d2fb04cd1982a592f7ed36cdaa348d3a75cfc7a9ecb00a712265f93881ab88`; candidate bitboard SHA256 `cd929a8445c6286e3c71df985694e5f53aebac2fc214f2610035bf7638b9fb49`.

## Full native matrix

Each row has exactly one failed original target, forge_tests, with the same four known assertion lines. CTest actually exits8; these are policy passes, not falsely reported all-green suites. ON adds one passing cold TSan target. All four sanitizer rows were freshly built and executed, not inherited from earlier qualifications. ASan profiles ran first d11 and the full CTest suite; the five-depth/perft5/FMA sweep was performed on all four Release rows.

|Base|Profile|Option|CTest pass count|Actual main-engine SHA256|
|---|---|---|---|---|
|L|release|OFF|13/14; known four only|`e3df99cddb609d9f00168d8df3187fdf6943c10812dd5c4f82206895e594367b`|
|B|release|OFF|14/15; known four only|`55fa7e81768452bf62e5c9fa748d88353e37fbec50492077e70d30f14fc7d406`|
|L|release|ON|14/15; known four only|`73ae743cac18431750e07c2c89878bf6e4caecc0f9b63b3e87dc76e50dbcdaba`|
|B|release|ON|15/16; known four only|`3a32f15cf87bf47a831f4bbe41d6e206ea18e79967c10eda65e7630fe93190b6`|
|L|asan|ON|14/15; known four only|`0e42e3b212efffd5b1325f18660d27d77e2e0a9900be3b6ffdd45f47096e3552`|
|B|asan|ON|15/16; known four only|`d9ec30b460aa51434b34594f862e3e73aea96cbf85a847ed0b4c6bf8485fd943`|
|L|asan|OFF|13/14; known four only|`1dc9b43f19fc5c0062f65a0742e011a96ec468e083abf9f3bf0d087aed614fef`|
|B|asan|OFF|14/15; known four only|`71b251bbb8de879cb6eb6eea9840253bb6f047c8dab4b4a71b1902d31036a96d`|

Original expected values were not edited:

```text
FAIL: WAC 001 expected g3g6 got f6h5
FAIL: WAC 001 score 661 below 31997
FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion
```

## Advisory timing, not acceptance

A local protocol was frozen before timing: SHA256 `31fac99a3f1f07f9d5585db8be101f4cffff9dabf7733fd9f0c7de6f0821885a`. A=L OFF, B=L ON; exactly20 fresh d13 processes in ABAB order,10 chronological adjacent B/A internal-NPS ratios, fixed745494 nodes in every process. Both compiler/cold/compression work and root's CPU work were closed before sampling. Child processes alone were pinned to allowed logical CPU0; parent affinity remained0–4.

CPU: INTEL(R) XEON(R) PLATINUM8573C. Recorded one-minute host-load range 0.21826171875–0.48583984375. Median raw ratio **1.0268573982116145**, observed pair range **0.5264824674848559–1.4375011106745201**. The wide variation, shared host and absence of A/A confidence validation prevent speed-gain inference. This is advisory **UNPROVEN** data only; no sample was discarded or retried and no gate/Elo decision follows. Buffix timing was not separately measured. Earlier qualification NPS output, gathered under concurrent correctness load, is retained separately as uninterpreted raw data.

## Reproduction and preservation

On a private patched Linux source copy:

```sh
cmake -S PRIVATE_SOURCE -B PRIVATE_BUILD -DCMAKE_BUILD_TYPE=Release -DFORGE_ATTACKS_INIT_ONCE=ON \
  -DCMAKE_CXX_FLAGS="-march=x86-64-v3 -mtune=znver5 -ffp-contract=off -fno-fast-math -DFORGE_NNUE_HIDDEN=256"
cmake --build PRIVATE_BUILD -j2
printf 'bench 11\nquit\n' | PRIVATE_BUILD/forge
ctest --test-dir PRIVATE_BUILD -R '^forge_sol_S04_cold_tsan_test_20261025$' --output-on-failure
python3 -B forge_sol_S04_cold_runs_20261025.py PRIVATE_BUILD/forge_sol_S04_cold_tsan_test_20261025 --out NEW_FOLDER --runs 1000
```

Full-project CTest retains the four known failures shown above. The supplied driver refuses an existing output folder, preserves each actual process's original streams/hashes/exits and stops on any unexpected output or sanitizer failure. It sets `TSAN_OPTIONS=halt_on_error=1:exitcode=66`, uses no suppressions and invokes no caller-affinity, host-limit or termination API. The advisory driver changes only child affinity and checks the parent's affinity is unchanged.

Exact compiler argv, stdin, source/binary hashes, complete original logs and1000 JSONL records are retained. Matrix raw JSON records explicit byte lengths, base64 and full SHA256; cold/advisory JSONL rows retain original base64 streams, SHA256 and exits without separate byte-count fields. The final evidence bundle records file byte lengths and hashes. Existing banner text is preserved in encoded evidence. Supplied input trees and completed original evidence remain preserved. The source implementation followed the actual RED test; no failed repair attempt or runtime failure was hidden. No extra cache archival was needed in S04. All native/compiler/cold/timing jobs are closed.

Idea sources only: the user's S4 request, earlier own cold-Board reproducer and standard C++ call_once publication semantics at https://en.cppreference.com/w/cpp/thread/call_once . Implementation and new test are original; no external engine code or tuned constants were imported. Next action is root's isolated publication/download verification, then S05 per the current pack order. No accepted lock, prior patch or gate is replaced.
