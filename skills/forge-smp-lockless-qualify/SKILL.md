---
name: forge-smp-lockless-qualify
description: Build and qualify a default-OFF SMP / shared-TT change on the trial_w6 lineage without a Linux box (Opus 2 job, 2026-11-09, branch opus-smp-layout-20261107, pack opus_smp_layout/) - rebuild the parent from lock d4f4312 + trial_w6.patch (kit = 4181a589 byte for byte), keep every change inside one #if switch (g++ -E -P identity, OFF kit build = parent), the C++-memory-model-valid lockless TT (atomic_ref words + XOR tag, exact bijection with TTEntry), the cache-line layout probe, the contention fixture WITH a positive control, TSan through opus-ci (FORGE_SMP_LAYOUT=ON, NNUE_ZMM=0, tsan_extra.sh driving the real engine over UCI), PS 5.1 identity / stress / liveness / nps tools pinned to CPUs 12-15 Idle, and the pitfalls. Use for any lockless / TT-layout / false-sharing / thread-lifecycle change, a TSan question on Forge, or a new default-OFF switch that must be proven byte- and node-identical.
---

# Forge SMP / lockless TT qualification (Opus 2, 2026-11-09)

Rules first: [[forge-pc-rules]] (no deletes, no process termination, no force-push; Idle). Kit facts: [[forge-ltopgo-pgo]]. The node-identity method follows [[forge-speed-lock-path]], with own PS 5.1 tools. Pack: `opus_smp_layout/` on `opus-smp-layout-20261107` (README / SPEC / BENCH / COMMANDS).

## 1. Parent and envelope
- trial_w6 source = lock `d4f43124` + `opus-speed-20261105:opus_speed/patches/trial_w6.patch` (md5 5786e9b8…, `patch -p1 -F0`), then flip the six `#define NAME 0` lines (exactly one match each):
  - TT_NOTLS=1, NO_ZERO_MOVELISTS=2, SEARCH_SPEED2=1, PREFETCH_EARLY=1, SLIDER_PEXT=1, NNUE_ZMM=1.
  - Commit that as the parent. Its `git archive <c> include src` (20 files, LF) through QA kit v2.3 `-Expose` gives pc1 = pc2 = **4181a589…** (verified 2026-11-09).
- d4f4312's `include/`+`src/` = the lock's SOURCES.sha256 (LF hashes); the lock's on-disk `source` folder is a CRLF copy.
- Envelope used: CPUs 12-15 (`0xF000`), Idle, ≤ 4 own threads, D: floor. Every PS 5.1 tool sets and reads back its own affinity and class first (`tools/o2_uci_lib.ps1`, `tools/run_pinned.ps1`). Start them from the **Bash** tool (`powershell.exe -NoProfile -ExecutionPolicy Bypass -File …`).
- Kit: run a **copy** of `kit_v23\build_ltopgo.ps1`, hash-checked, with Idle instead of BelowNormal and without its termination-on-timeout. Wrapper `tools/kit_build.ps1 -SrcDir <export> -Tag <t> [-CheckOpt 'Opt=true']`; about 2.5 min per build on 12-15.

## 2. One switch, provably inert at 0
- New code only inside `#if FORGE_<SWITCH>`, includes too. P's lines are never edited: use early-return `#if` blocks, or `#if X <new line> #else <P's line> #endif` for one-liners.
- **No new `src/*.cpp`**: the kit compiles every unit.
- Proof chain:
  1. `tools/pp_identity.ps1 -TreeA <parent export> -TreeB <tree>`: `g++ -E -P` with the kit flags, blank lines stripped, all units IDENTICAL;
  2. a kit build of the tip at 0 = the parent's sha256 (pc1 = pc2);
  3. `git diff parent tip -- include src` shows `-0` lines.
- Gate source = export with the single `#define X 0` line flipped to 1, so kit and CI build exactly that.

## 3. The lockless TT that is valid under the C++ memory model
- **Storage.** Separate typed storage per mode (`TTLocklessCluster { std::array<uint64_t,8> words; }`, 4 entries × (K, D)). Every concurrent access is a relaxed `std::atomic_ref<uint64_t>`. Plain value-init or clear happens only while quiescent: UCI `stop_search()` joins first, and `Searcher::search` joins its helpers.
- **No type punning.** Never alias P's `TTEntry` storage as words: switching mode reallocates the other storage type, empty.
- **Encoding.**
  - `D = score|eval<<16|depth<<32|gen_bound<<40|rule50<<48|pad<<56`;
  - `K = (key32 ^ mix32(move, D & ~GenMask)) | move<<32`, where GenMask = generation bits only, so a CAS that refreshes the generation keeps K valid;
  - mix32(0,0) = 0, so zeroed memory is the empty entry;
  - decode is the exact inverse, so Threads 1 is node-identical by construction.
- **Validation.** A K and a D from two different stores fail the tag with p ≈ 2^-32. The TT move stays guarded by MovePicker (`is_pseudo_legal`, `is_legal`).
- **Bodies.** `probe_lockless` / `store_lockless` mirror `probe_body` / `store_body` decision by decision on decoded copies. Store D then K; write only words that changed.
- **Dispatch.** `Worker::tt_lockless_`, set by `Searcher::search` before helpers start. Every public entry point (probe, store, owned variants, hashfull, prefetch) also follows the table mode, so nothing touches the null array.

## 4. Tests that can fail (CI runs them under TSan)
- **Differential.** A legacy table and a lockless table get the same random op stream; compare every probe and the full contents (`debug_entry`).
- **Contention.** 4/8 threads on 1/4/16 clusters store `payload = f(key)`; every hit must carry f(key).
- **Positive control.** The same fixture on an unvalidated two-word table must show incoherent hits. Measured: 1,673,288 natively and 464,076 under TSan. Without it a 0 proves nothing.
- **Lifecycle.** A Searcher at Threads 1/2/4/8 in both modes: stop, ponderhit, `clear_hash` / resize / set_threads / toggle, legal best moves, T1 three-way identity cold and warm.
- **CI.**
  - `opus_round1/ci/run_ci.sh` on this branch passes `-DFORGE_SMP_LAYOUT=ON` and `-DFORGE_SPD_NNUE_ZMM=0`: the runner has no AVX-512F, and the trial_w6 default `#error`s without it.
  - `opus_round1/<pack>/tsan_extra.sh` is picked up by tsan mode. Use it to keep the test output (ctest hides passing output) and to drive the **real** TSan engine over UCI with pipes and sleeps. In this engine a `go` is ended by the next UCI line, which is the stop path.
  - Download the evidence with `gh run download <id> -D <fresh dir>`; "TSan: 0 reports" is in `known_tsan.log`.

## 5. Exe-level evidence (PS 5.1, `tools/`)
- `identity_check.ps1 -Mode pins|cold|warm`:
  - pins = d11-22 net on and off + perft;
  - cold = 12k FENs, depth 13, `ucinewgame` each (about 9 min per run on a free core, about 70 min with 4 runs sharing 2 cores);
  - warm = no `ucinewgame`, with Hash / Clear Hash / UseNNUE changes.
  - Compare the `.body` sha256 of two exes.
- `liveness_check.ps1`: a node-identical option is "IDENTICAL to OFF" in the kit. Prove it is live by its side effect: toggling empties the table, so the search after the toggle equals the search after `Clear Hash` (histories survive both).
- `uci_lifecycle_stress.ps1`: seeded random go / stop / ponder / setoption / ucinewgame, plus legality by the engine's own `go perft 1` (`<move>: 1` lines).
- `layout_probe.cpp`: offsets and cache lines via the existing `SearcherTestProbe` friendship; heap addresses of `make_unique<Worker>`.
- `nps_smoke.ps1`: advisory only (two physical cores). QA's native-core plan is `SCALING_PLAN.md`.

## Results of the first use (2026-11-09; details in `opus_smp_layout/BENCH.md`)
- **Builds.** Engine candidate `0599271`: OFF kit = **4181a589** (= parent = trial_w6); gate kit = **541e8b3d…**, pc1 = pc2.
- **Threads 1 identity.** With `TtLockless` false and true: fens12k net on/off 12,000/12,000 = parent; warm transcript (1,000 FENs, 40 changes) = parent; liveness PASS.
- **Races and stress.**
  - Fixture: 0 incoherent in 2.17 G probes; the positive control saw 0.46-2.46 M per run.
  - CI TSan: 0 reports (4 runs, incl. the real engine over UCI at T2/T4).
  - UCI stress at T1/4/8 PASS.
- **Layout.** `nodes_` was on one line with `local_nodes_`; it now has its own line (+64 B per worker).
- **NPS.** Advisory only: the A/A copy moves by 5 % on CPUs 12-15. ON may cost about 2-3 % at T1 (decode). QA times it on native cores.
- **Review.** R1 (fable) found 3 MINOR: a stale per-worker mode flag, a control that could not fail, and freeing before allocating on toggle. All fixed. The recheck reviewer became unreachable, so a self-review marked NOT independent replaced it.

## Pitfalls hit (2026-11-09)
- Bind every tool config to the exe **sha256** and re-check it after any rebuild. An NPS config written before the review fixes silently timed the superseded gate exe; that run was kept as "superseded, not cited".
- Always add a byte-copy **A/A** config to NPS runs. Without it, a +26 % "gain" from noise on two SMT cores looked real.
- A subagent can become unreachable mid-job (its agent type vanished from the session). Record the open board line, do a structured self-review marked NOT independent, and never substitute an agent type the user's rules do not allow.
- The permission check refuses command text containing the words for ending processes or for deleting (even inside a grep pattern or a kit-copy edit). Edit such files with the Edit tool, and use fresh directory names instead of cleaning.
- Git Bash `sha256sum` prints `hash *name` (binary mode): strip the `*` before comparing manifests. `grep -c $'\r'` miscounts there: count CR bytes with `tr -cd '\r' < f | wc -c`.
- `printf` in Git Bash eats `\f` and `\e` in Windows paths: write TSV/config files with the Write tool.
- Each call of the agent's PowerShell tool is a new process (pinning does not persist): pin inside every script.
- The kit sets BelowNormal on itself (use the Idle copy) and terminates the training exe on timeout (removed in the copy).
- The lock net is 768-input and king-independent: a Finny (king-bucket) refresh cache has no in-tree refresh to save there. Measure refresh counts first (`opus-finny-cache-20261107`, BENCH.md).
