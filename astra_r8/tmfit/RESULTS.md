# Astra R8 fitted time model — UNPROVEN

Authoritative gate base: `294dbed3a15dfd821aaf9d4edc6e5f62832fd460`, actual AL1 s198.
Historical reference base: `905e2325caeabea92b1017b22b434218a43145a7`, the initially
permitted `forge-bundle-int` parent fallback. Lock executable identifier: FD3A5190.
Branch: `astra-r8-tmfit`. Crew builds the LTO+PGO gate executable.

## Current qualification status

Implemented and fitted on real data; the authoritative CR patch applies to the
actual AL1 s198 source294dbed3. Its Linux identity, liveness, hard-limit, clamp
and sanitizer checks pass. Fresh200-game actual-lock timing qualification is
running. CR's sleep-based CPU/free-RAM governor is installed and reviewed;
native Windows startup is waiting for permissible host load.
No search algorithm changes. Strength remains UNPROVEN.

Storage: C: 182.1 GB, D: 83.8 GB, F: 49.1 GB at setup. User authorized D: scratch
instead of F: with 50 GB minimum free. Scratch is
`D:/grok-pc-data/dwqww/astra8-scratch`, capped at 5 GB.

| Test | Status | Evidence / next action |
|---|---|---|
| Data: >=50,000 real root iterations | PASS | 52,012 /19 games; 0 illegal/flags; hashed 1% sample |
| Fit: grouped 20% held-out AUC | PASS | 4/19 held-out groups; AUC0.682619, fixed0.682835 |
| 1 OFF pins d11/13/16/20/22 | PASS actual lock/Linux | CI41296951735:312866 /862329 /3024920 /12389307 /34048354 |
| 1 ON fixed-depth identity | PASS actual lock/Linux | Same CI identity step; identical five pins |
| 1 perft5 | PASS actual lock/Linux | start4865609; kiwipete193690690 |
| 2 timed live proof | PASS actual lock/Linux | CI clock-check step passed; exact medians/count pending final artifact; original fallback failures retained |
| 3 200-game average time | PENDING actual lock | Fallback200 PASS:ratios0.99016836/move,0.99001560/game-side;0flags/illegal |
| 4 hard limits | PASS actual lock/Linux | CI clock-check step passed50positions; exact maxima pending final artifact |
| 5 absurd coefficient clamp | PASS actual lock/Linux | CI clock-check step passedA1000000/50positions; exact maxima pending artifact |
| 6 ASan+UBSan ON smoke | PASS actual lock/Linux | CI41296951735 job124819689489:4allONgames/389plies,0reports/faults |
| 7 patch/README/fitter/tests/skill | IN PROGRESS | Exact CR patch applies to294dbed3; final runtime/evidence audit pending |
| Crew SPRT | UNPROVEN | CR first, then Strength and QA; UHO primary, 8moves separate, longer TC confirm |

Native Windows blocker: host CPU exceeds80% startup limit; the builder sleeps.
Linux CI qualification continues. Optional CodeRabbit/Sonar CLIs and MCP analysis
tools are unavailable. Never treat missing analysis as PASS.

Next: implement/review the resource governor and actual-lock port, verify its
OFF pins, and rerun candidate-dependent checks before the final handoff.

## Checkpoint 2 — implemented, collecting; UNPROVEN

Logger, model, NumPy fitter, native referee and six harness modes implemented.
Fitter 13 tests PASS, harness 4 tests PASS, numeric bounds test PASS. An independent
review corrected unstable-search selection bias and noise-only live-proof criteria.
Initial build failed due to omitted FORGE_NNUE_HIDDEN=256; original failed log is
preserved in scratch. Corrected x86-64-v3 GCC15.2 O3, ffp-contract=off, static,
Expose+TM_LOG build succeeds. Embedded net SHA256:
`0cc9ac542ed4a2271459f3e4819277f3d9b77122ec1bf1ab536673d34af21807`.
OFF bench d11/d13/d16/d20 matches 312866/862329/3024920/12389307;
full matrix remains running. Collection at 8+0.08, seed2026110108, 8moves_v3,
Threads1/Hash16 is running. Coefficients remain UNFITTED neutral placeholders.
Source checkpoint1 published: 79ff4d68. New sanitizer workflow is branch-scoped.
Next: finish 50k data, real fit and mapping calibration, final binary validation.
Prior art limitation: requested named variants except TimeManV2 were not found in
available refs; see PRIOR_ART_AUDIT.md. No claim to have reviewed absent source.

## Checkpoint 3 — preliminary identity complete; UNPROVEN

All five OFF and ON node pins and both perft5 values PASS on logging v0.
Nonlogging Expose build SHA256:
`11f0cd92dd052ea685e6a33cbaab75756fc26702dd80977a55c321b53e94bce4`.
Collection passed 34,299 iterations with no recorded flags or illegal moves.
GitHub sanitizer run41288852339 built ASan+UBSan and executed395 plies without
reports, but the workflow FAILED because the four-game diagnostic smoke was
incorrectly checked against the 200-game qualification requirement. Preserved
as a failed run; fixed with a dedicated all-ON sanitizer command and regression.
New native build script records exact command, source hashes and binary hash.
Next: finish dataset, fit, calibrate on separate openings, rerun final checks.

## Checkpoint 4 — real fit installed, mapping under calibration; UNPROVEN

Collection COMPLETE:52,012 root iterations /19 games, zero illegal moves/time losses.
Raw dataset SHA256 `884e458c7298f465dd3b3810c5a98132647d2d15701e53ccbdd4ba10e036eb8c`.
Fitter:49,400 eligible rows,42,124train/7,276heldout,15/4 opening groups.
Heldout AUC0.6826193881; integer AUC0.6828350984. One interrupted-return disagreement
retained with the completed-final-iteration label. Committed sample521rows (~178KB).
Q12 coefficients: -3201,-5127,6120,-3440,-1537,-167,1284 (bias/depth/change/effort/score/delta/elapsed).
First mapping A914/B1000/Lo750/Hi1500 failed robust live threshold:5/20 positions.
Preserved; stronger A742/B3000/Lo650/Hi1750 is being assessed. Both remain UNPROVEN.
ASan+UBSan corrected run41289111781 PASS:4allON games399plies, no reports or faults,
neutral preliminary coefficients. Final fitted-coefficient sanitizer rerun pending.
Independent review found two harness P2s (hung quit and rejected option accepted);
red/green regressions now pass and both are fixed before timing qualification.
Couns clarified off-repo prior art; descriptions recorded in IDEA_SOURCE, no blocker.
Next: mapping calibration, frozen200game smoke and final timed/identity checks.

## Checkpoint 5 — fitted source validation; UNPROVEN

Native fitted-v1 executable SHA256:
`e9e6c2686350307c8bd73749544c372fd528d5561e87c6b4cc8b6f9df26eefae`.
Fitted source ASan+UBSan run41289552546 PASS (allON4games, no reports/faults).
Clock fixture60positions was frozen using seed81230, SHA ordering within three
ply phases, without consulting ON timing outcomes. Seeded20 subset with A742/B3000
changed median time on10/20 positions; original opening-only failures retained.
Final fitted-default identity/live/hard/absurd checks are running.
Calibration now uses per-game ON-vsOFF, colors reversed per opening pair, to
control game-length confounding. Original same-mode40game pilot remains preserved.
Final200game smoke has not yet run. No acceptance or strength claim.
Evidence files are marked binary in .gitattributes to preserve byte hashes across
Windows/Linux checkouts. Scratch remains below5GB and D retains >50GB free.

## Checkpoint 6 — complete local correctness, calibration ongoing; UNPROVEN

Fitted default identity, revised-fixture liveness, both50-position hard/clamp
tests and fitted-source ASan+UBSan all PASS; current table above is authoritative.
Original40-game same-mode A914 calibration completed with zero faults, ratios
1.02226 per move /1.02528 per game; it is preliminary, not the final paired test.
Paired40-game A742 and paired20-game A842 calibration are in progress. Final
100 openings are frozen with zero intersection with19 training and20 calibration
openings. The final200-game smoke will follow mapping freeze.

The original failed GitHub run41288852339 is retained as historical evidence.
Its four-game-versus200-game check wiring is fixed; later runs41289111781 and
41289552546 PASS. Sixteen driver regressions now pass, including the specific
sanitizer-count distinction. CI runs them before compilation and triggers on
harness, referee and build-file changes so this class of regression is checked.

The installed C++ plugin checker has actually run:32 artifact hashes PASS,
patch applies with-p1 to905e2325, but draft qualification correctly returnsFAIL
solely for the pending200-game check. Draft remains immutable; final record
will be regenerated. Source/patch and all logs remain UNPROVEN for strength.

## Checkpoint 7 — mapping frozen before final holdout; UNPROVEN

A742/B3000/Lo650/Hi1750 remains the frozen default. Paired40 calibration completed
with0flags/illegal moves; OFF181.5896ms/move, ON179.1312ms/move, ratio0.98646218;
per-game-side ratio0.98947889. This satisfies both calibration limits. Keep742
under the decision rule stated before completion; the842pilot is supplementary.
The final100-opening fixture is disjoint from training/calibration. A reviewed
coordinator will run two disjoint100-game shards, at most2active search threads;
only its combined200-game record can qualify. Driver16 and aggregator5 unit
regressions pass. Raw final game/search logs stay in scratch; commit bounded
game ledgers, summaries and complete hashes. Latest CI41290843946 PASS.

## Checkpoint 8 — automatic review policy adopted; final run active

Root AGENTS.md now contains Couns's automatic review/fix/verification policy.
No prior project AGENTS.md was found; other branch/worktree instructions were
not replaced. Focused independent review of the policy/log found one minor
provenance ambiguity; fixed with exact binary/build/evidence links, verified.
REVIEW_LOG.md records milestones, confirmed fixes, validation and next actions.

Final smoke source41699d07, frozen executablee9e6c268..., mapping742/3000/650/1750:
40/200 games completed at the latest monitor readback, zero faults; two active
searches, no candidate or tested-executable changes. Still PENDING, not accepted.
Normal and Expose UCI surface checks also PASS: onlyTmFitModel public normally,
11coefficients exposed in Expose builds, diagnostics only whenON.

## Checkpoint 9 — final smoke past halfway; UNPROVEN

At 2026-11-01 18:28 UTC, final smoke completed113/200 games (57+56),
with zero recorded time losses/illegal moves. Test3 remains PENDING.
Committed the immutable pre-run configuration as evidence/final_smoke_frozen.json,
binding the executable, driver, coordinator, two disjoint opening shards,
seed and742/3000/650/1750 mapping. No source or executable changed during the run.
Next: finish200 games, evaluate both timing bounds, package proof, then focused
independent review and corrections before engineering completion. Crew strength
acceptance remains UNPROVEN.

## Checkpoint 10 — CR requests actual-lock port and resource governor

CR verdict FIX on41699d07/6b2b5ece is accepted. Actual AL1 s198 source is
294dbed3a15dfd821aaf9d4edc6e5f62832fd460; the local packaged source matches all75
Git blobs. The existing905 fallback patch/evidence is preserved, not relabeled.
CR supplied patch hash prefixes538c4876 (lockport) andc0005114 (governor); file
locations are being located, with equivalent fixes prepared independently.

The original200-game run sealed at18:44:49 UTC: bothchildren exit0, zero faults,
ON176.8014ms/move vsOFF178.5569ms/move, ratio0.99016836; game-side ratio0.99001560.
Bounded evidence and original raw hashes are in evidence/final_smoke_v1.
At a live resource inspection, system CPU was90%. An owned-process pause attempt
executed101seconds after the completed run sealed; no process was suspended.
The original pause-attempt receipt and correction are both retained. This does
not establish governor compliance for the old run. No further engines/builds
will run until the80%CPU/90%peak/8GBRAM governor is installed and reviewed.

Latest code-bearing GitHub CI41699d07 passed run41291623694:16driver+5aggregator
regressions, numeric tests, ASan+UBSan and4all-ON games. Exact logs/receipt saved.
All strength conclusions remain UNPROVEN; final engineering handoff is unresolved.

CR artifacts subsequently located at C:/Users/Administrator/cr_crfix/astra_r8_tmfit.
All three MD5 prefixes match: lockport538c4876, governorc0005114, helper6d109014.
Original bytes and full hashes are versioned under cr_fixes/. Couns clarified
8GB **free** RAM; CR uses8GiB, startCPU<80%, pauseCPU>=90%. That specification
supersedes the initial own-process memory interpretation. Governor and lock-port
matching are under implementation/review; no further native engine runs started.

## Checkpoint 11 — CR port and sleep governor reviewed; actual tests pending

Authoritative tmfit-lock.patch is byte-identical to CR's supplied file, SHA256
ef09b342368efd01876bf771726d58cc84d73ec2960b5a70ead710ff0e88d9e3. Its actual294
source stage has77 files,71 unchanged originals. Independent source review found
no concrete code defects. The old905 patch is preserved as tmfit-fallback-905.patch.

Governor matches CR's sleep-boundary policy and never suspends processes or
subtracts active timing.34 governor/driver/coordinator/builder regressions pass.
Review found and fixed the missing imported-guard snapshot; all three builder
dependencies are now sealed and rechecked. Native API probes verify16CPUs,
BelowNormal and fresh free-RAM readings. Host CPU94–99% causes60-second sleeps
before startup. The native build request is waiting; no compiler/engine launched.
Couns's later prohibition on all process suspension is recorded in AGENTS.md.

Installed C++ evidence checker ran on evidence/lock-source-draft-v1: eight
artifact hashes and both source/patch checks PASS; all eight experimental checks
remain UNVERIFIED in this source-only draft. Candidate ID:
55114017bc763b71c097ad5e65acec6a6ff2b0e4d2d1353ddf9166fbafc679e5.
Packager declaration mutation regression passes; producer source→binary→test
links require explicit main-agent/reviewer audit and are not automatically inferred.

Actual-lock CI now asserts the exact patch hash, applies it to294dbed3, and builds
that tree for ASan+UBSan and separate release qualification. Independent focused
review found no blockers. Linux results will be labeled as Linux. The fresh
100-opening fixture (seed2026110112, SHA6420d200...) has zero overlap with all139
training/calibration/prior-smoke openings. Parameters remain742/3000/650/1750.
Next: run source-bound checks/200 games on CI while governed PC work waits, then
audit the completed evidence and handoff. All strength remains UNPROVEN.

## Checkpoint 12 — actual-lock Linux checks pass; final200 running

Pushed02e79145998a6fb31c01e455d0b658a3bc6c5c8b. CI41296951735's sanitizer job
124819689489 passed on asserted base294/patch ef09b342: numeric tests and4ONgames,
389plies,0reports/illegal/time losses. Log/status/hash receipts are retained in
evidence/ci_actual_lock_41296951735. Release qualification job124820184414 passed
OFF/ON pins+perft and live/hard/absurd steps; jobs-at-final200-start.json preserves
the exact step statuses. Its fresh200-game qualification is still running.
Do not infer final acceptance or detailed probe numbers before artifact audit.

The native Windows build request remains in CR-governor startup sleeps at
CPU94–99%; no compiler or engine has launched. No process suspension is used.
Linux evidence will not be relabeled Windows or crew LTO+PGO. Next: finish200,
download and audit source→binary→test links, run final evidence checker/review,
and hand off to CR, Strength and QA. Strength remains UNPROVEN.

## Checkpoint 13 — sanitizer artifact audited; timing test still running

Downloaded the completed sanitizer artifact into authorized scratch. All nine
producer hashes verify; runner/governor snapshots match exact Git blobs from
02e79145. Four all-ON games and zero sanitizer transcript markers are confirmed.
Bounded manifests/game ledger and source→binary→test audit are retained under
ci_actual_lock_41296951735/sanitizer_artifact. The ASan executable was not in that
artifact; its runtime SHA is producer-reported and linked through the successful
source-asserting build job. This limitation is explicit in identity-audit.json.

Actual-lock final200 remains in progress without a reported failure. The native
builder still sleeps before startup (latestCPU97.6%,11.64GiB free RAM); no native
compiler/engine or suspension has occurred. No code/parameter changes or interim
timing decisions. Next: final timing result, artifact audit, final review/checker.

## Checkpoint 14 — sanitizer review correction preserved; UNPROVEN

Independent sanitizer audit confirmed all389ON moves and nine producer hashes,
with zero faults/reports. A minor receipt label called the workflow SHA the
candidate_commit. Added sanitizer-status-corrected.json with workflow_commit and
patched-source candidate_id; preserved the sealed original and all old hashes.
REVIEW_LOG.md records the finding and accepted correction. Final200 remains in
progress without a reported failure; coefficients/source remain frozen. Native
startup still sleeps at97.5%CPU. No process suspension or native compiler launch.
