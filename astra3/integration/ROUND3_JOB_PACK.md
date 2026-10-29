# Forge Astra round 3: integrate round 2, root-cause the SMP mate bug, fix the gate pipeline, then research jobs

Written 2026-10-28 ~11:59 PM PT by Engine QA for Couns. Self-contained. Run as long as your remaining usage allows (round 1 used only ~20%). Work down the list in order. When usage gets low, stop starting new work, finish the current milestone, update REPORT.md and push.

## 0. Hard rules (breaking any of these fails the job)

1. **Push every 10 minutes, finished or not.** Repo `github.com/couns0538-sketch/dwqww`. Every 10 minutes: `git add`, commit, `git push origin <your astra3-* branch>`. WIP commits are fine (prefix `[WIP]`). Never hold unpushed work longer than 10 minutes. Update that job's REPORT.md in the same commit every time. New branches only, all named `astra3-*`.
2. **Git safety.**
   - Never touch `main`. Never push to `forge-bundle-int`, `opus-*`, `fable-*`, `astra-*` or `astra2-*`. Read them and merge them into your own branches only.
   - Never force-push. Never rebase or amend pushed commits. Never run `git clean` or `reset --hard`.
   - **Never delete anything**: no files (`git rm` counts), no branches, no tags, no releases, no PC files. Mark obsolete files in REPORT.md instead.
3. **Ideas only.** Every new idea gets an `IDEA_SOURCE.md` entry (paper, engine, forum post or crew bot, with a link or citation). Write your own implementation and never copy engine code verbatim (GPL or otherwise). Constants tuned in another engine count as code: do not import them.
4. **One option per gate, default OFF.** Every new behaviour sits behind its own UCI option or build switch, defaulting to OFF/0. Bundles only exist as presets of options that were already gated on their own.
5. **OFF identity after every milestone.** With all new options OFF, Threads 1, Hash 16, OwnBook false, fresh process per depth:
   - `bench` d11/13/16/20/22 = **312866 / 862329 / 3024920 / 12389307 / 34048354**
   - `go perft 5` = **4865609** (and kiwipete unchanged)
   - **FMA count 0** (`objdump -d` of the whole binary, grep `vfn?m(add|sub)`) Recipe: GCC 14, C++20, Release, `-march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off -DFORGE_NNUE_HIDDEN=256`. Put an identity table in REPORT.md for every exe you build. If an OFF pin moves, stop and fix it before going on.
6. **Tests.** The only failures allowed are the 4 known `forge_tests` lines (WAC 001 ×2, rook underpromotion ×2), the single-core `forge_smp_tests` SmpExactNodes timing flake and the intermittent baseline `forge_tt_mate_tb_tests` cp-instead-of-mate. Never weaken an expected value to make a test pass. Threads=1 search must stay deterministic.
7. **No Elo or speed claims without a gate.** You don't run gates; gates decide. You deliver gate-ready candidates plus a proposed gate spec: one option set per gate, SPRT normalized [0,10], `cap_games` 3000 (int), srand and openings start left blank (QA assigns them, never reuse an srand). Speed-only, node-exact switches get NPS evidence plus a [-10,0] non-regression spec, not an Elo gate.
8. **If you run anything on grok-pc** (Windows, PowerShell 5.1, never nest `powershell -Command`):
   - Run every build, test and bench at **BelowNormal priority with at most 3 threads in total** (`-j3` max, engine Threads ≤ 3).
   - **Never stop, pause or touch NNUE training, self-play/datagen, the running gate (fastchess), `forge_queue.ps1`, the watchdog/guards, `forge_gates.json`/the manifest, `forge_push\bin`, `FORGE_RESULTS.csv` or the lock directories.** Never create a STOP or PAUSE file.
   - Never kill a process you did not start.
   - Don't write to E: (almost full). Work only in your own worktree under `D:\grok-pc-data\dwqww\.claude\worktrees\astra3-*` and scratch under `F:\opus_scratch\astra3\`.
   - Heat: the PC must not die. If CPU Tctl/Tdie stays at or above 90 °C, or you see any thermal-throttle or shutdown warning, pause YOUR OWN work until it cools, and log it in REPORT.md.
9. **Never run** Sol's lock, PGO or delivery scripts, the live `autopromote.ps1`, or anything that writes lock records or promotes an engine.
10. **Milestones.** Every job has its own REPORT.md at `astra3/<job>/REPORT.md` on its branch, with: status (DONE / WIP / BLOCKED), exact commands, exe sha256, identity table, test counts with the actual failures, what is UNVERIFIED, and next steps. Label every time with its zone (for example `23:40 PT` or `08:40 Vienna`). Don't stamp PC-local times with a fake `-07:00`.
11. **Not yours (don't redo or edit):**

- Opus R5B (branch `opus-r5b-speed`): FORGE_NNUE_O2, FORGE_NOZERO_MOVE_BUFFERS, FORGE_SPEEDSTACK, the N2 build and its `nps_ab` script.
- Opus R5C (`opus-r5c-*`): the N3 pack (SyzygyPath / Syzygy50MoveRule / IntendedThreefold / HardDeadline hardening and its gate spec) and the v4 `.fnn4` net (format, loader, forward pass, exporter, parity).
- `opus-r5a-singles` itself: you merge it, you don't push to it.
- Fable J1b/J7 training.

## 1. Context (read before you write code)

**Base:** `origin/forge-bundle-int` @ **b7c1772** (Opus R3 stack + buffix + J3 ports; CR PASS; OFF = pins). Read `BUNDLES.md`, `OPUS_R3_REPORT.md` and `opus_r3/R3-1/OPTIONS.md`.

**Your round 2 branches** (all independent off b7c1772; read your own `astra2-report:FINAL_REPORT_R2.md`, especially "Remaining failures, limits and integration work"):

12:02 AM

Job	Branch	Tip	What
B1	`astra2-smpv2-mate`	23e940b	src 931bd49; SmpV2
B2	`astra2-tm-softhard`	45314a5	src 97da33b; TmSoftHardClamp
B3	`astra2-nnue-loader`	9a09e76	tests only; don't merge src
B4	`astra2-uci-strict`	d35d41f	src 2beaad8
B5	`astra2-singularv2`	5c6ee0d	src fde944a; SingularV2 spin 0..1 + preset N1
B6	`astra2-bench-tool`	344e48e	tool
B7	`astra2-report`	4b7c4d8	report

12:02 AM

**Opus R5A:** `opus-r5a-singles` @ 8f1ceac (engine src = ee83d6d = 4ba7bc99; CI green). It adds:

- the per-go `info string active:` echo (src/search/r5a_options.inc);
- the CorrMargins+TtPruneV2 warning;
- the CorrHistPlus 1/2/4/6 ↔ CorrHistV2 refusal;
- new spin `CorrMarginsScale` (default 100) and advertised `CorrExtTripleCorr` (48);
- 64-bit `scaled_term` in corr_margins;
- test `forge_r5a_options_tests`.

Its single-option gates are queued on grok-pc. **Don't change their semantics.**

**Code Review results you must act on.** Both reviews ran on a Linux box and are summarised here because you can't read the box.

*CR_ASTRA2 (2026-10-28 6:30 PM PT):* B1/B2/B4/B5 and their merges PASS-notes.

- **F1 HIGH:** `include/forge/fb2.hpp:75` `case Bundle::N1: return {4, 0, false, {false, false, false, true}};` is positional aggregate init of `fb2::Options`. B1 adds `smp_v2` and B2 adds `tm_soft_hard_clamp` to the same struct. If the merge puts either before `singular_v2`, N1 silently sets the wrong bool, apply_bundle's preserve overwrites it, and N1 becomes "CorrHistPlus=4 only". The echo then lies and nothing fails at compile time. r5a's presets (fb2.hpp:66-69) use the same positional `{…, {a, b, c}}` form.
- **F2 MED:** see A2 below.
- **F3 MED:** B1+B2 conflict in CMakeLists (adjacent add_test), fb2.hpp (adjacent fields), fb2.inc apply_bundle (each preserves its own flag) and uci.cpp (adjacent else-if handlers). The resolution is a union:
  - apply_bundle preserves BOTH smp_v2 and tm_soft_hard_clamp;
  - the SmpV2 handler needs its closing brace before the TmSoftHardClamp handler.
  - B4's uci.cpp auto-merges. B5 conflicts in BUNDLES, CMakeLists, IDEA_SOURCE, NOTES and fb2.hpp.
- **F4 LOW:** `info string override <name> after preset` (B4 uci.cpp:771, :931-933) fires for ANY option, including Hash and LmrQuietBase. Limit it to preset-owned options: CorrHistPlus, HistRework, CuckooRep, CorrHistV2, LmrTableV2, TtPruneV2 and SingularV2.
- **F5 LOW:** the SingularV2, SmpV2 and TmSoftHardClamp handlers assign directly instead of through B4's `assign_option`, so after N1 `SingularV2 0` is silent.
- **F6 LOW:** B1 `result.depth = search_depth` makes odd helpers report depth+1. Keep the nominal depth in its own field, or document it.
- CR's scratch merge in that order kept `singular_v2` as the 4th field, and N1 was live: mrg5 N1 d11/d13 = 277579/814055, not CorrHistPlus=4 alone (340927/734347). CTest 61/63 (known only), OFF = pins, FMA 0.

*CR_R5A (2026-10-28 7:50 PM PT):* r5a PASS-notes.

- **F1 MED:** r5a and B4 both rewrite the `uci` option-listing loop. B4 prints every tunable not in AdvertisedParameters (b4 uci.cpp:511-513); r5a prints R5aAdvertisedParameters separately (r5a uci.cpp:539). A naive union lists CorrMarginsScale and CorrExtTripleCorr TWICE (test_opus_spsa catches "an option is listed twice"). The BundlePreset block conflicts too: r5a re-scoped the lock (non-recursive std::mutex), and B5 added N1 plus refuse-before-apply. Keep both: no nested lock, and warn_combination after the scope.
- **F2 MED:** `active_search_options` (src/search/r5a_options.inc:46-56) lists only this base's fb2 fields, so SingularV2, SmpV2 and TmSoftHardClamp would silently be missing from the `active:` echo.
- **F3 LOW:** an invalid `BundlePreset bogus` still calls warn_combination (uci.cpp:810).
- **F4 LOW:** setting `TtPruneV2 true` after a preset that already set it resets the attribution to OFF (uci.cpp:787). The echo also prints SyzygyPath/NNUEFile even when loading failed.

**Other open items** (QA's MORE_GATES_PLAN §6-§12):

- **D5:** bundle-int OFF NPS has never been measured.
- **D6:** autopromote MED-5/MED-6 and S35 F2.
- **D4:** SmpExactNodes overshoot.
- **D7(a)(b):** no warning for NetScale/NnueInt16 under a v2 net; option names are case-sensitive.
- **D9:** C6 has no singular-exclusion guard unit test.
- WAC001 d12 miss (your own round-1 next-task note).

---

## 2. PHASE A: required, in this order

### A1. Integration branch `astra3-integration` (≈2 h; push after each merge)

1. Branch from `origin/forge-bundle-int` b7c1772. Use real `git merge --no-ff` (no rebase), in this order: **B1 23e940b → B2 45314a5 → B4 d35d41f → B5 5c6ee0d → opus-r5a-singles 8f1ceac**. Don't merge B3's src (there is none), B6 or B7.
   - After each merge: build, check the identity pins (rule 5), run full CTest, then push. Record each merge-resolution decision in REPORT.md.
2. **CR F1 HIGH fix, first commit after the B5 merge:**
   - Rewrite EVERY preset in `bundle_settings` (OFF, B1-B4, N1 and any r5a preset) with C++20 designated initializers. Example: `.fb2 = {.singular_v2 = true}`, never `{…, {false,false,false,true}}`. Also make the `fb2::Options` field order irrelevant everywhere else, including any `effective(...)` helper.
   - Add `static_assert(bundle_settings(Bundle::N1).fb2.singular_v2)`, `static_assert(!bundle_settings(Bundle::N1).fb2.smp_v2)` and `static_assert(!bundle_settings(Bundle::N1).fb2.tm_soft_hard_clamp)`, plus asserts that B1-B4 leave singular_v2/smp_v2/tm_soft_hard_clamp false. If constexpr isn't possible, add a unit test that fails when a field is reordered.
   - Prove it: put a deliberately reordered copy in a scratch build, show that the assert or test fails, then revert it. Record this in REPORT.md and don't commit the broken copy as live code.
3. **CR F3:** apply_bundle preserves smp_v2 AND tm_soft_hard_clamp (and any other non-preset-owned bit). N1 then OFF must give the OFF pins.
4. **CR_R5A F1 (uci option list):** keep ONE listing loop: the 20 base advertised + R5a advertised + the rest of B4's 64 registered tunables, with an exclusion set so every name appears exactly once. Add a test that parses `uci` output and fails on any duplicate name; test_opus_spsa's duplicate check must pass. In the BundlePreset handler, keep r5a's lock re-scope and B5's N1 refuse-before-apply. No nested lock, and warn_combination runs after the lock scope and only for a valid preset (CR_R5A F3).
5. **CR_R5A F2 (echo):** `active_search_options` must include SingularV2, SmpV2 and TmSoftHardClamp. Replace hand-listed coverage with a test that loops over EVERY advertised option: set it to a non-default legal value and assert that it appears in the `active:` line, unless it is on a documented non-search whitelist (Hash, Threads, Move Overhead, Ponder, OwnBook, Book*). At defaults there must be no `active:` line.
6. **CR F5 + F4:**
   - Route the SingularV2, SmpV2 and TmSoftHardClamp setters through `assign_option`, so value_changed and override tracking work.
   - Limit `override X after preset` to the preset-owned options.
   - Set TtPruneV2 attribution only when the value actually changes (CR_R5A F4).
   - Echo SyzygyPath/NNUEFile only when loaded, or mark them `(failed)`.
7. **CR F6:** keep the helper's nominal depth in its own field and document it. The selector behaviour must stay unchanged.
8. **Qualification of the integration head** (table in REPORT.md):
   - OFF pins d11-d22 + perft5 + kiwipete + FMA 0.
   - ON pins d11-d22, which must equal the per-branch numbers:
     - SingularV2=1: 404121 / 1005954 / 4120585 / 11497954 / 34264955
     - N1: 277579 / 814055 / 2651984 / 18648191 / 40304213
     - CorrHistPlus=4 d11/d13: 340927 / 734347
     - SmpV2=true at T1 = OFF pins
     - TmSoftHardClamp=true = OFF pins
     - CorrMargins=1 at CorrMarginsScale 100 = OFF pins
   - Every R5A single (CorrHistPlus=2/4/6, CorrExt=1, CorrMargins=1, NetScale=99, HistRework=1/3) must give the d11-d22 numbers in `opus_r5/r5a/gate_specs.json`. Any mismatch is a blocker; explain it.
   - Exclusivity: CorrExt↔SingularV2 both ways, N1 with CorrExt on refused before apply, CorrHistPlus↔CorrHistV2 both ways.
   - Full CTest (known failures only), plus a full ASan/UBSan CTest and a TSan run of the options/SMP tests (Threads 2, 250 go/stop iterations, 0 reports).
   - fastchess `-strict` 2-game smoke if a runner exists: integration + `BundlePreset=N1` + `CaptureFutilityBase=0` must exit 0, and an unknown option must exit 1.
9. Deliver `astra3/integration/REPORT.md` + `GATE_NOTES.md`: which already-queued gates could move to this exe, and the claim that its OFF pins are byte-for-byte the lock pins. **No gates. No merge to forge-bundle-int**; Couns and CR decide that.

### A2. Root-cause the SmpV2 Threads=2 KRK mate→cp bug. Branch `astra3-smp-mate-rootcause` off the A1 head (≈1.5-2 h)

**Facts from CR (box, 1 core, fresh Searcher(16 MB, 2 threads) per trial, 2 depth-14 searches per trial):**

- FEN `4R3/8/8/k2K4/8/8/8/8 w - - 0 1`, expected mate score 31995 with d5c5.

12:02 AM

Run	Searches	Results that weren't mate
base	6000	0 cp
B1 SmpV2=OFF	6000	0 cp
B1 SmpV2=ON	6000	~28 cp, all cp 463-494 with e8e4
rerun	2000	5
info run	3000	34

12:02 AM

- In bad runs the MAIN thread itself reports cp from depth 1 to 14, and about 13k nodes are already counted at main depth 1. So the skewed (+1 ply) helper filled the TT first, and the selector is not the cause.
- Same signature elsewhere:
  - your B2 finding: base `forge_tt_mate_tb_tests` 2-thread sometimes returns cp 465/e8e4 instead of mate, reproduced on untouched b7c1772 (run 12 of an adaptive replay);
  - `go mate 3` on that FEN returns cp 485 e8e4 at depth 5 on base T1/T2 alike (pre-existing).

**Steps:**

1. Build a deterministic repro driver with a trial count and seeded thread start skew, and log per trial: depth, score, PV, and which thread stored which TT entry for the root and its first 3 plies.
2. Test these hypotheses in order and record each in REPORT.md as confirmed or refuted, with evidence:
   - (a) mate-score ply adjustment on TT store/probe (to-TT and from-TT conversion);
   - (b) bound type on mate scores (a LOWER/UPPER mate bound used as EXACT, or a cutoff with the wrong bound);
   - (c) helper depth+1 entries (skew) trusted at main depth with a depth check that doesn't cover mate scores;
   - (d) aspiration-window widening (even helpers ×1..3) storing fail-low/high mate bounds;
   - (e) a lockless/torn TT read (key/data mismatch) when LocklessTT is off or on;
   - (f) the T1 `go mate 3` cp result: same cause, or a separate mate-search-limit issue?
3. Fix minimally. If the fix keeps T1 OFF pins exact (TT handling that only matters at T≥2), fix it directly. If it changes any T1 node count, put it behind a new default-OFF option (e.g. `TtMateGuard`) and give ON pins. Either way, add regression tests:
   - 500 trials SmpV2=ON, 0 cp allowed;
   - 500 trials SmpV2=OFF Threads=2, 0 cp allowed;
   - make `forge_tt_mate_tb_tests` loop 200× clean.
4. Deliverable: REPORT.md with the root cause in one paragraph, before/after fail rates with exact counts, and what stays UNVERIFIED. If you can't find it in the time budget, leave a narrowed-down hypothesis tree and a repro that fails at least 1% of the time, and say BLOCKED. Don't claim a fix.

### A3. Measure bundle-int all-OFF speed (D5). Branch `astra3-speed-off` (≈45 min)

- **Exes:**
  - `forge-bundle-int` b7c1772 OFF
  - `opus-r3-stack` OFF
  - the A1 integration head OFF
  - AL1 s198 (exe sha 833C47F3…22B3) only if you can read it on grok-pc. Read it only; never copy it into a lock dir, and say so if you skipped it.
- **Method:**
  - Paired ABBA, a fresh process per run, `bench 16` and `bench 20`, at least 10 pairs.
  - Affinity pinned to one core, BelowNormal.
  - Nodes must match within each pair; abort otherwise.
  - Include an A/A control (an exe against its own byte copy).
  - Report the mean and median NPS ratio with a 95% CI. The A/A row is the noise floor; state that live gates make the PC noisy.
- You may use your B6 `bench_matrix` tool or a small ABBA script of your own. Don't reuse or edit Opus R5B's `nps_ab` script, and don't build the N2 switches.
- This is a measurement, not a speed claim. Flag any OFF cost above 1% whose CI excludes 0 as a finding, with the suspected branches (Opus offguard measured A1 OFF at -0.8/-1.0%). Optionally run a perf/callgrind instruction-count diff (Linux) to localise it.

### A4. Gate-pipeline fix: `autopromote.ps1` (D6) as a PROPOSED PATCH ONLY. Branch `astra3-autopromote-patch` (≈1 h)

- **Source:** the live file is on grok-pc in the Forge PC-autonomy folder. Read it only and commit a copy as `astra3/autopromote/autopromote.orig.ps1` with its sha256. If you can't reach it, write `NEEDS_LIVE_COPY` in REPORT.md and work from the newest copy in the repo or the handoff, saying which.
- **Never run the live script, never install the patch, and never edit the live file.**
- **Fixes:**
  - **MED-5 (around line 302):** a nan, missing, empty, `+nan`, `-inf` or non-numeric Elo becomes `[double]$null = 0` and can still pick a winner. Make the parse explicit (`[double]::TryParse` with InvariantCulture and an `IsNaN`/`IsInfinity` check). Any non-finite or missing Elo/LLR/games makes the gate **ineligible** with a logged reason, never 0.
  - **MED-6:** the hold cap is read from RESULT.md's mtime. Use a finish timestamp recorded inside the result/state instead, and fail closed if it is missing. A file copy, touch or `git checkout` must not reset the hold.
  - **S35 F2:** watcher `ReadAllText` failures are silent. Log them and treat them as "not ready".
- **Deliver:**
  - `autopromote.patch` (unified diff, PowerShell 5.1 compatible: no PS7-only syntax, no nested `powershell -Command`, UTF-8 without BOM caveats noted);
  - a standalone dry-run test harness (`test_autopromote_parse.ps1` plus fixture RESULT/state files covering nan, missing, empty, -inf, `+12.3`, comma-decimal locale, an mtime-touched file and a missing timestamp), showing RED on the original functions and GREEN on the patched ones, run on fixtures in scratch only;
  - REPORT.md listing every other `[double]`/`[int]` cast of gate stats in the script, and its verdict on each.
- Couns/QA install it after CR.

---

## 3. PHASE C: research jobs (after Phase A, in this order; one branch and one REPORT.md each; stop cleanly when usage runs low)

Each new search/eval behaviour needs:

- its own default-OFF option;
- an IDEA_SOURCE entry;
- OFF pins exact, plus ON pins d11-d22;
- a node-count screen (report the d13/d20 tree size change);
- a 200-game legality smoke ON vs OFF at 5+0.05, Threads 1 (0 illegal, 0 crash, 0 time loss, 0 missing bestmove), plus 50 go/stop iterations;
- a gate spec (one option, [0,10], cap 3000, srand/openings blank).

Before you build an idea, grep bundle-int and the integration head: if it (or an equivalent) already exists, write "exists as X" and skip it. Base the C jobs on the A1 integration head (or on b7c1772 if A1 is BLOCKED, and say so).

- **C1 `astra3-wac001`.** Root-cause the 4 known `forge_tests` failures:
  - WAC 001: expected g3g6, got f6h5, score 623 below 31997 (mate-in-2 missed at d12);
  - "winning rook underpromotion over stalemating queen promotion" ×2. Decide for each: wrong test expectation (prove it with a perft/mate proof or a deeper search), search bug (pruning of checks or underpromotions, mate distance, qsearch promotion handling), or eval. Fix behind an option if T1 nodes change, otherwise directly. Never change the expected values without proof. Check whether it shares a cause with A2(f).
- **C2 `astra3-smpexact`.** SmpExactNodes overshoot (D4): helpers don't stop at the node budget when the main thread is descheduled. Fix it so node-limited SMP searches are exact, keep SmpExactNodes=false identical, and add a test that passes on 1 core and on ≥2 cores (simulate descheduling with a debug-hook delay).
- **C3 `astra3-uci-hygiene`.**
  - UCI option names case-insensitive, per the UCI spec (D7b). Values stay case-sensitive where they are paths.
  - `info string` warning when NetScale≠100 or NnueInt16 is set with a v2/unsupported net (D7a).
  - Add a test.
  - Must not change search; OFF pins exact.
- **C4 `astra3-singular-tests`.**
  - A unit test for the singular-exclusion guard (D9/C6): the excluded move must never be searched in the exclusion search, for the old singular path and for SingularV2.
  - Exhaustive tests that CorrExt and SingularV2 can never both be live through any order of setoption/preset/snapshot.
  - Tests only.
- **C5 new search ideas** (research-grade; one branch per idea, `astra3-idea-<name>`; pick 3-5, cite a source for each):
  - **Low-ply history:** a separate history table for ply < 4 used in ordering near the root.
  - **Cutoff-count LMR:** reduce more when the child already produced many beta cutoffs.
  - **ProbCut qsearch pre-check:** a qsearch probe before the reduced ProbCut search.
  - **IIR variants:** internal iterative reduction on cut nodes without a TT move.
  - **Hindsight depth adjustment:** adjust depth from the parent's reduction and the eval improvement.
  - **Null-move verification search at high depth:** zugzwang safety.
  - **Off-limits areas** (being gated or owned elsewhere): CorrHist*, CorrMargins, CorrExt, SingularV2, NetScale, HistRework, TtPruneV2, LmrTableV2, CuckooRep, time management, SMP selection, Syzygy/threefold/HardDeadline, the NNUE format or kernels.
- **C6 `astra3-drawish-scale`.** Material-drawishness scaling of the net output (untested idea from Opus O4; D8): scale the eval toward 0 in known drawish material (opposite bishops with few pawns, KR vs KB-type, no pawns with ≤ minor up), as option `DrawishScale` (default 0/OFF). It must not touch the TB/N3 paths. Smoke from endgame-heavy openings.
- **C7 `astra3-sprt-audit`** (tooling only).
  - An independent SPRT/pentanomial checker: from fastchess PGNs or the results output, recompute the W/D/L, pentanomial pairs, normalized-Elo LLR for [0,10] and the stop decision at `cap_games` 3000.
  - Validate it against a published formula reference (cite it) and synthetic data with known answers.
  - Never write to `FORGE_RESULTS.csv` or the manifest. Ship it as a read-only checker that QA can run.
- **C8 `astra3-spsa-plan`** (tooling and spec only; D7e).
  - An SPSA pilot plan for the advertised tunables on the exposed build: CorrMarginsScale, CorrExtTripleCorr, the 20 base tunables; drop QsSeeMargin, which small SPSA steps can't tune.
  - Cover parameter ranges and step sizes with reasoning, a ~4k-game pilot then ~40k at 8+0.08, and the runner command.
  - A dry run of at most 200 games at ≤3 threads proving the tool works.
  - Don't start the real session.
- **Final `astra3-report`.** `FINAL_REPORT_R3.md`: a table of every job with branch, tip, DONE/WIP/BLOCKED, exe sha256, OFF identity, test counts with the actual failures, and the gate specs ready for QA. List the UNVERIFIED items explicitly. No Elo or speed claims.

## 4. Done means

- Every astra3-* branch is pushed, each with REPORT.md.
- A1 integration qualified, or BLOCKED with the reason.
- A2 root cause found, or a narrowed repro.
- A3 NPS table with CIs.
- A4 patch + RED/GREEN harness.
- As many C jobs as usage allows, each gate-ready or clearly marked.
- OFF pins exact on every exe. Nothing deleted, nothing force-pushed, main untouched, no PC process of anyone else touched.