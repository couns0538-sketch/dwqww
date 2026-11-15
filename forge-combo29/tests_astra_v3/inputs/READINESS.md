# Job C readiness — offline only

Prepared 2026-11-15 04:33 UTC. Job C has not started. No engine was built or run, no engine source or root state changed, and no branch/ref was created or updated. This directory is a preparation artifact outside every repository. Current source matches all 26 frozen Job A pins at d9a8587df8ad4d0ff1231632cb1ac72b590c04bf; checkout HEAD was b0a32c8fcf0e22da092374f70130bdf81e4b483e at capture. Later report commits do not change that source identity.

## Authority and starting gate

Read the exact copied `FABLE_JOB_C_0017.md.txt` (SHA256 e4a5ce5b4193bc54b3121eba9726affcc0056ad84bc8345d5434edd0cf55ab1e) and `FABLE_ANSWER_0020.md.txt` (5d504f4a1a22ab4ac9abec9911f795a34a85f11a60a781f0375dc001359b9227). Job C begins only after A and B are reported, lasts four hours from its own recorded start, and uses new branch `for-fable-and-opus/astra-0017-v3-path` from the final A tree or its report successor. This memo neither starts that clock nor grants early native execution. The 0020 replay is separate evidence and Job B retains its own deadline.

Only the two pinned source imports, described search/UCI hooks, and checking switch are authorized engine changes. Make three implementation commits in that order. Do not import `search_v3.cpp`, v2, halfka, int8, scripts, binaries or other branch changes. Report at `forge-combo29/REPORT_astra_v3.md`, new test/evidence text under `forge-combo29/tests_astra_v3/`. Keep tooling and generated net files in the VM; the explicitly authorized Python tool is read first and run with `python3 -I` outside repository folders.

## Sources available now

Both exact required blobs are readable locally with `GIT_NO_LAZY_FETCH=1`:

| File | Required Git blob | SHA256 of exact bytes |
|---|---|---|
| nnue_v3.hpp | cc2d0bcfba41993098061cd43d7a88eb450b2074 | cc76d8d7d0237a78e65b66a4a46a105ef60b551219415320ae02b016351b79e2 |
| nnue_v3.cpp | 122ce37ad66b43438c3c8c73a15c61255083b541 | 8dc8b061e2c4f087965d8dd300889c87b0213b39c2d0f310cce42bc262a35ae1 |

Their unchanged bytes are copied as `.hpp.txt` / `.cpp.txt` here for review. Git object hashes were independently recalculated. No matching local or remote-tracking ref for `fable/standalone-h512-20261111` was found in the available clones; having the blobs is sufficient for the two exact imports but does not establish a branch tip. The authorized `h512/train/fable_nnue_v3.py` was not located in worktree files or the locally enumerated trees. Root still needs to retrieve that exact path from the named branch, record its actual source commit/blob/SHA, read the entire tool and dependencies, and inspect its random/eval/seed CLI. No Python generator or reference evaluation was run here. Do not substitute a similarly named tool or import the rest of its tree.

## Minimal hook map against current source

Line numbers refer to the unchanged Job A checkout, not to the earlier standalone branch.

| Site | Required insertion and interface |
|---|---|
| include/forge/nnue.hpp, before namespace/build declarations | Default `FORGE_NNUE_V3` to 0 under `#ifndef`. No v3 include or path compiled when disabled. |
| include/forge/search.hpp:5,477,551 | Under the switch: v3 include; per-worker `unique_ptr<nnue::v3::WorkerState>` beside `stack_`; method declaration beside `static_evaluate`. Existing memory include is present. |
| src/search.cpp:1068 | Immediately after disabled/unavailable-net hand-written return, test v3 active and return its evaluation. Preserve the preceding DeadMaterial handling and all remaining compiled-net code. |
| src/search.cpp:1130 and1163 | Immediately after child accumulator stale marking, invalidate `v3_state_->stack[ss->ply+5]` if the state exists. Child move diff is already stored with `diff_known=true`; null move has `dirty.count=0`. |
| src/search.cpp:2304–2313 | After all search-stack entries are reset, invalidate existing v3 state. In enabled/available root refresh, active v3 calls the new method once; otherwise retain the exact old refresh/residual path. Root is `stack_[4]`; storage is `MaxPly+8`. |
| New search method near static_evaluate | Lazily allocate state, dereference `*nnue::v3::loaded()`, prepare with MaxPly+8, make_valid at ply+4. `dirty_of(k)` addresses `stack_[k]`, calls current `ensure_piece_diff` at1053, then returns that frame's `dirty` by const reference. Evaluate that same v3 stack index. |
| src/uci.cpp:197,238,311,327 | Advertise the two options adjacent to UseNNUE under the switch. Existing setoption calls stop_search before mutation. Parse full file path using existing NnueFile pattern (`value_text + getline(rest)`), retaining spaces. Load/unload and requested changes clear hash and report status. |
| src/uci.cpp:232,427,523 | Check problem at isready/go/bench. Print exactly `info string ERROR NNUE v3: ...` and terminate with code2, after safely stopping/joining any live UCI worker. `go` and `bench` already call stop_search; isready currently does not. A plain return with a joinable thread would terminate incorrectly. main returns uci_loop's code at581. |
| src/uci.cpp:515 | When v3 active, eval reports evaluate_reference for the loaded net. Retain old eval output when inactive; do not change eval.cpp. |
| Only new static_evaluate_v3 | Default VERIFY0; under VERIFY1 compare returned incremental value to evaluate_reference. A mismatch prints ply, both values and board.fen(), then exits3. No checking calls elsewhere. |

V3 API notes from exact blobs: `load(path,&error)` clears the old loaded net immediately and returns false on failure (nnue_v3.cpp:282); it intentionally does **not** preserve the old net. UCI must reject residual nets after successful load, unload them and set an explicit problem. `set_problem` is separate from load/unload; clear stale problem text on successful standalone load/unload as appropriate. `active()` means requested && loaded; `problem()` is nonempty only when requested and no usable loaded net exists. Worker `prepare` resets stack/cache on net generation or stack-size change (source530); every successful load increments generation (375). Keep all net loading/request mutation outside searches using existing stop_search discipline. The imported implementation remains byte-identical even if a test finds a fault.

## Build without modifying CMakeLists.txt

CMakeLists.txt:23 globs every src/*.cpp. The v3 source itself is wrapped in `#if FORGE_NNUE_V3`, so macro0 already compiles no v3 implementation. If literal exclusion of that translation unit is desired for the switch-off proof, an external `CMAKE_PROJECT_INCLUDE` overlay can mark just its absolute source path HEADER_FILE_ONLY when the macro is0. This preserves the repository CMake file and both imported blobs. Proposed external overlay, not executed:

```cmake
if(NOT FORGE_NNUE_V3 MATCHES "^[01]$" OR
   NOT FORGE_NNUE_V3_VERIFY MATCHES "^[01]$")
  message(FATAL_ERROR "v3 switches must be numeric 0 or 1")
endif()
add_compile_definitions(FORGE_NNUE_V3=${FORGE_NNUE_V3}
                        FORGE_NNUE_V3_VERIFY=${FORGE_NNUE_V3_VERIFY})
if(NOT FORGE_NNUE_V3)
  set_source_files_properties("${CMAKE_CURRENT_SOURCE_DIR}/src/nnue_v3.cpp"
                              PROPERTIES HEADER_FILE_ONLY TRUE)
endif()
```

Configure fresh directories with `/workspace/work/tooling/cmake-3.31.6-linux-x86_64/bin/cmake`, source forge-combo29, Release, existing x86-64-v4/nonportable settings, `-DFORGE_MATE_ALPHA_GUARD=1` in CXX flags, numeric v3/verify values, and the external overlay path. Preserve strict FP settings, hidden256 and compiled net weights; v3 hidden512 is a loaded-net property, not the old hidden-size build option. For ASAN/UBSAN add address,undefined and frame-pointer flags to compile/link as in Job A; TSan uses thread sanitizer in a separate directory. Do not carry sanitizer objects across builds. Check compile_commands/build.make/link.txt and actual object hashes: off excludes the extra source object if using the overlay; on includes exactly that extra engine TU. Pin compiler, flags, all source/objects, binaries, net hashes, harness/transport and oracle inputs before launching. No configure/build or syntax compile was performed by this inventory.

## Validation inventory and proposed declarations

Shared release conditions: Threads1, Hash16, OwnBookfalse, UseNNUEtrue, MultiPV1, all existing options default unless measuring one of the16. Preserve exposed MateAlphaGuard defaultfalse. Do not reuse Job A's rare same-clock difference waiver: Job C changes no default search behavior, so the two switch comparisons require zero differences.

| Contract check | Exact target and reusable evidence |
|---|---|
| Switch0 / switch1-optionoff | Both: bench11=312866, bench13=862329, startpos perft5=4865609; each of16 option bench13 counts; 10,000 identical eligible corpus positions against final Job A binary. On build advertises both new options. |
| Integer reference | Authorized random tool: hidden512, king-buckets8, output-buckets8, mirror; declare seedsA/B after reading its CLI. At least5,000 engine eval/reference pairs, exact integer equality; retain FEN/index and coverage of every bucket from both perspectives, preferably mirror halves as well. Tool format/bounds must be read before mutations or generation. |
| Checking ASAN/UBSAN | Net active, VERIFY1, bench12 then depth9:20,000 positions T1 in ONE process without ucinewgame; same with2,000 T2 and2,000 T4. Distinct persistent processes per thread condition are fine; restarting every batch does not satisfy the20k single-process condition. Raw receipts/counts survive observation/checkpoint batches. |
| TSan | VERIFY0, net active:2,000 positions T2 and2,000 T4. Keep sanitizer stderr and search completion/legal checks. Actual findings stop and are sent; no suppressions. |
| Loader robustness | Twenty predeclared mutated files; cover truncation, payload checksum bit flip, wrong magic, king-bucket count claiming more data than present. Record every exact mutation, file hash and rejection result. “Without a diagnostic” means without a sanitizer diagnostic; the normal UCI rejection explanation is required. A requested bad net must fail loudly at ready/go/bench rather than silently use the compiled net. |
| Net switching | Same process A→B→unload→compiled→A, compared with fresh-process counterparts. Root declaration: explicitly `NNUEArch=false` after unload before compiled-net search; re-enable after loadingA. Explicit `ucinewgame` before EACH measured search on both sides matches histories while retaining the tested process/net lifetime. This reset is only for this switching test, not for the24k checking searches. |

For release equality, use final Job A `/workspace/work/parity-run/builds/step2-release/forge`, SHA df76cddaea8a37dae7f8d1a5178700e0168aad8c463764ed6870d9c4fce2dc56. Reuse corpus `/workspace/work/dwqww-all/forge-combo29/soak_all/search_corpus.txt`, SHA571fd73cf5ec3ddad78d6afc1dd65c57d7f4c3f8eaa424cbfbabe94a4a8b06c1, and `/workspace/work/all-run/compare-shards/manifest.txt`. Freeze identical ordered10,000 **eligible** positions (e.g2,500 per shard). Original raw record limits include exclusions, so limit10000 alone does not prove10000 comparisons. Depth9 is the proposed retained Job A depth since Job C's10k paragraph does not restate a depth. Existing comparator is fresh-process and250ms shutdown; use it only for release equality after new namespace/reference pinning, not persistent sanitizer search.

Exact16 count source: `/workspace/work/parity-run/inputs/frozen-option-counts-source.txt`:65–80. Actual Job A results: `/workspace/work/parity-run/option-counts-step2-release/`. Existing runner `/workspace/work/parity-run/check-option-counts.mjs` is hardcoded to old output/state paths: adapt into a fresh Job C namespace, never run it over old evidence.

| Option value | Expected bench13 |
|---|---:|
| EvalRule50Damp=true |1049205|
| ThreatHistory=true |643389|
| LmrSignedCorrection=true |862329|
| LmrLateParentRelief=true |818656|
| HindsightDepth=true |840387|
| NullThreatVerify=true |789456|
| NullSeeVeto=true |929140|
| AspCappedReopen=true |850997|
| AspArmLate=true |870398|
| EvasionOrdering=true |772890|
| DeadMaterial=true |862329|
| QuietExtinction=true |632155|
| DrawJitter=8 |857947|
| TmFinishIteration=true |862329|
| TmNodeShare=true |862329|
| SoundMatePruning=true |980408|

## Required shutdown change and bounded execution

Every new sanitizer protocol declares **5000 ms of genuinely signal-free shutdown observation after quit**, with complete stderr drained and process exit/reap status recorded. No SIGTERM or SIGKILL before the five seconds expire, including exception/destructor cleanup paths. A report, nonzero exit, or no exit by five seconds is a finding. Release runs retain250ms. Old paired transport `uci_process.hpp`:315 gives only60% of its total to graceful exit, so simply calling old finish(5000) would send SIGTERM at3000ms and violate0020. Reuse the new full-history diagnostic's true5s transport only after its final review/pins; do not edit frozen predecessors or retrospectively reclassify old failures.

The one-process20k requirement and per-command<8minute rule both apply. Keep an explicitly supervised persistent native session and divide controller observation/command work into bounded chunks without recreating the engine or sending ucinewgame. Record whether the whole20k session completed before budget. No command may wait indefinitely; do not split into fresh engines and call that the specified test. Record exact persistent process lifetime, search indexes, input/output boundaries, response limit, per-search completion, shutdown and all interrupted work. No partial batch credit or assertion that mere elapsed time was testing.

## Remaining items before Job C launch

1. A and B reports complete; root records actualCstart/deadline and creates only the specified new branch.
2. Authorized Python tool retrieved and read; exact revision/blob/dependencies/CLI/seed behavior pinned. No substitute reference has been approved or run.
3. Three source commits implemented and reviewed against the hook list and imported blob hashes; switch-off and switch-on/optionoff builds verified first.
4. External build overlay, corpus subsets, net seeds/files,20 mutations, persistent driver and true5s transport frozen in a fresh protocol. Root still has to implement this runtime; this memo is not runnable validation tooling.
5. Each required workload counted against the four-hour deadline; unfinished targets stated directly. No self-play or unrelated engine/import changes are part ofC. Stop/send actual checking or sanitizer findings. Owner-PC execution and its independent net-reference results remain reported external context, not locally verified evidence.
