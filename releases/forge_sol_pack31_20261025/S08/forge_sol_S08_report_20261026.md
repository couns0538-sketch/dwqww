# Forge S08 profiling and feature-frequency audit — 2026-10-26

S08 is correctness-qualified on both supplied development bases. It adds optional counters; it does not change evaluation, search decisions or the accepted lock. No speed, Elo, Windows or new-lock acceptance is claimed. Publication is established separately by the immutable-download receipt for the artifact commit.

## Source and implementation

Reference code is `1ab50b2dd64d9b2f752f7f1285f6968cad2fd792` with the supplied H256 network SHA256 `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`, MD5 `6d22f612c855e17c62d396d32da99ea4`. Lprime and B include the reviewed Job C/S01 test source SHA256 `55334ba94fd508d5f8e8e0e715c86a6996eddc69b20b1c110110a96e46deaa2c`; B additionally retains the buffer fix.

Core patch `forge_sol_S08_profcounters_TLS_v2_20261026.patch` SHA256 `91c28d9f3b70af08885d50239141890813722cf00114bda8a2d12b71eb5e476c` changes nine files, with 467 insertions and two deletions. It supplies 55 fixed counters, including 15 MovePicker stages, per-search atomic storage and scoped thread-local routing. `FORGE_PROF` defaults OFF; only compiled-ON builds advertise `Profile`, whose runtime default is false. The requested setting is atomic; workers use the search's immutable active setting. Ordinary `bench` keeps its original output policy; `bench_prof` separately requests counters. Counter overflow is reported, never hidden. There are no hot-path heap allocations in the counter implementation.

Apply the core patch plus the matching additive documentation patch for L, Lprime or B. Those three documentation patches append README and IDEA_SOURCE entries without replacing earlier content. The exact documentation hashes are in the delivery manifest. Documentation v2 corrects the earlier corpus description and explains the TLS repair; it does not change the qualified engine code. Earlier documentation and failed versions remain in the evidence checkpoint.

## Checks

| Check | Lprime | B |
|---|---|---|
| Git apply-check and GNU patch -p1 -F0, including plain L where applicable | PASS | PASS |
| First execution of each new main ELF: bare bench11 before UCI | 308972, PASS | 308972, PASS |
| Profile ON bench d11 | 308972 | 308972 |
| Profile ON bench d13 | 745494 | 745494 |
| Profile ON bench d16 | 2460422 | 2460422 |
| Profile ON bench d20 | 11901452 | 11901452 |
| Profile ON bench d22 | 31111774 | 31111774 |
| Start-position perft5 | 4865609 | 4865609 |
| Kiwipete perft5 | 193690690 | 193690690 |
| Scoped NNUE object, scoped linked NNUE and whole Release ELF FMA | 0 / 0 / 0 | 0 / 0 / 0 |
| Full Release CTest | 15/15 PASS | 16/16 PASS |
| Full ASan/UBSan CTest, leak detection ON | 15/15 PASS | 16/16 PASS |
| Source-pinned known diagnostics; additional FAIL lines | 4; 0 | 4; 0 |
| Profile-ON, toggling, legal T1/T2 and clean EOF/exit | PASS | PASS |
| Plain bench output and typed UCI comparison | PASS | PASS |
| OFF production translation units vs canonical source | 16/16 identical tokens | 16/16 identical tokens |
| Windows / native target-PC qualification | UNVERIFIED | UNVERIFIED |

The OFF result reuses canonical OFF executable evidence, backed by complete production-token equality. It is **not** a claim that a new OFF executable was compiled. Fourteen production translation units are byte-identical after preprocessing; the other two differ only in whitespace, with all 500,313 token kinds and spellings equal. The excluded profile source has zero tokens. Canonical OFF executables have zero profiling symbols. Original failed byte/whitespace assumptions and literal/operator negative controls are retained.

Lprime's sanitizer build uses the original static O2 configuration with debug information. B uses an explicitly recorded `ASAN_SHARED_NODWARF` correctness configuration: O2, g0, shared core, ASan, UBSan, frame pointers and the same strict floating-point flags. All 14 runtime artifacts, shared-library dependencies, source and build flags were frozen and unchanged before/after. This reduces storage, not sanitizer coverage. Leak detection remained enabled; it required the authorized nonsandboxed runtime because sandboxed LeakSanitizer is unsupported here. B's NNUE object and linked shared core also each have FMA count zero. The main shared-build ELF alone is not used as an NNUE oracle.

Lprime extra sanitizer searches cover 25 WAC positions and three T2 searches, plus both perft4 positions. B's final sanitizer supplement returns bench11=308972, legal T1/T2 searches (10000/11024 actual nodes), and perft4=197281/4085603. SMP node budgets are soft and are not incorrectly exact-pinned. All owned groups were reaped. B's full gate finished in 131.929 seconds; these are operation durations, not performance comparisons.

## Corpus and frequency findings

The supplied missing-input note expressly authorizes a substitute when the original STS set is unavailable. The sealed corpus has **2,000 distinct legally verified positions: 300 WAC, seven additional bench positions, and 1,693 supplied opening positions**. It is not 2,000 WAC/STS positions. Original opening provenance was checked through 20,316 legal plies; rerunning selection produced identical bytes.

The single native corpus run completed 2,000 searches at a requested 10,000 nodes each, with 19,881,407 actual nodes and 2,001 complete counter packets including setup. Every raw packet agrees with its parsed representation. No overflow, illegal best move, timeout or native retry occurred. Lprime and B also have identical values for all 55 counters at each of the five benchmark depths.

The accompanying low-frequency table keeps each denominator explicit. At d20, full refresh occurs eight times per 8,129,843 NNUE forwards; in the corpus it occurs 2,000 times per 12,097,858 forwards. Capture-futility pruning is zero because its existing default parameter is zero; this is not evidence of a newly broken feature. Corpus history pruning fires 993/7,754,531 checks. Call frequency is not CPU-time share, and no feature is removed on this evidence. The table's earlier B-pending sentence is retained history and is superseded by the completed B results here.

The delivered collector and corpus pass six standalone tests after relocation to a folder containing spaces, with access to the original workspace paths blocked. Original native packets are used as parser fixtures. Missing authority, wrong digest, padding by duplicate inputs and late/missing counters are rejected. The first relocation wrapper's import-path failure is retained; only the wrapper/location changed, not the six assertions or collector.

## Evidence and failures

Lprime's original native streams, the 2,001 raw packets, corpus provenance and earlier failures are published in checkpoint `605adc9218a484ffcd222f57cf78a8a4469e124a`, under `validation/forge_sol_pack31_20261025/forge_sol_S08_Lprime_checkpoint_20261026/`. The current B, OFF-proof, documentation and relocation evidence is under `validation/forge_sol_pack31_20261025/forge_sol_S08_B_delivery_evidence_20261026/`; its original-to-published bindings and SHA256 manifest are included.

| Receipt | SHA256 |
|---|---|
| Lprime Release qualification | `37e515703074a864a65e2df9d08a39d1d17c7c646272a6a9eff11be1ca76c3ab` |
| B Release qualification | `4e8d07e5f259d78890c9271c9c96aefbe5617997af2c2e5de81eb65abb157e7c` |
| Lprime full sanitizer qualification | `a0f5b2a01c40902b8597ff75ae49ae676ab71feed0c5bbdb61ba6de219f26a07` |
| Lprime extra sanitizer qualification | `dd424968f5239d1b8f1575d91bc9fbe197a30b1e6e40e7bc7f8f4322af7b5de4` |
| B shared sanitizer qualification | `5cad1ecb571a0ce3546eed7db5ea74933d90da4fd238b784fd14a54081d3faf4` |
| Corpus collection report | `a45e190d31eff86eb80f69254ec1150919cfac4b077a2a04b54f7932741b549e` |
| Five-depth 55-counter Lprime/B comparison | `d2e9b85507d8362c733b4a00af655fa1d22a7969fe7d9bdab1c22b1a9df75828` |
| Independent code/delivery review | `a6e76c521066524d15b066a2d7bf4dcbef0b27d26e0d0cbd10143745083b7976` |

The original TLS-v1 sanitizer null-store failure remains failed. Its isolated GCC TLS-initialization reproducer is repaired by `constinit` on both the extern declaration and definition; definition-only remains a failed control. The v2 engine passed the complete suites above. Low-disk build pauses, the B FIRST prelaunch guard (no child created), checker-binding corrections and packaging failures are retained separately; they are not hidden engine retries. Inherited build-only `engine_executions=0` fields in shared runtime receipts do not count executions: actual argv, raw streams, JUnit and owned-process observations establish runtime activity, as the audit explicitly explains.

All builds use GCC14.2/C++20, H256, `-march=x86-64-v3 -mtune=znver5 -ffp-contract=off -fno-fast-math`, native tuning and IPO disabled. No PGO, int16 accumulator or GPU work was performed. Original source hashes, exact commands, compiler flags, stdout/stderr, process status and manifests accompany the evidence.

## Reproduction and continuation

Use a new copy of the correct supplied source; never patch L, baseline or an existing output folder. Apply the core patch and matching documentation patch, then use the commands in the dated README. Verify the manifest from inside this delivery folder first. First execute a new main ELF with bare `bench 11` and `quit`; stop if it differs from 308972. `bench_prof` is available only with `FORGE_PROF=ON`.

This completes S08's local implementation and correctness scope. PC adoption is UNVERIFIED. Next is S09: reuse the reviewed eight-bucket step 1, qualify one-bucket million-position parity and the identical eight-head converter, retain the accepted network and null-pruning regression. Continue the entire saved finite queue; do not interpret this individual delivery as completion of all jobs.
