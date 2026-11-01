# Astra R8 fitted time model — UNPROVEN

Source base: `905e2325caeabea92b1017b22b434218a43145a7`, the explicitly permitted
`forge-bundle-int` parent fallback. Lock executable identifier: FD3A5190 (AL1 s198).
Branch: `astra-r8-tmfit`. Crew builds the LTO+PGO gate executable.

## Current qualification status

Implemented and fitted on real data; source patch applies to the lock fallback.
Identity, liveness, hard-limit, clamp and sanitizer checks pass for the fallback
source as scoped below. Its final200-game run also completed cleanly. CR requires
a patch port and identity checks on the actual AL1 s198 source294dbed3, plus a
CPU/RAM governor before further PC runs. These fixes are in progress.
No search algorithm changes. Strength remains UNPROVEN.

Storage: C: 182.1 GB, D: 83.8 GB, F: 49.1 GB at setup. User authorized D: scratch
instead of F: with 50 GB minimum free. Scratch is
`D:/grok-pc-data/dwqww/astra8-scratch`, capped at 5 GB.

| Test | Status | Evidence / next action |
|---|---|---|
| Data: >=50,000 real root iterations | PASS | 52,012 /19 games; 0 illegal/flags; hashed 1% sample |
| Fit: grouped 20% held-out AUC | PASS | 4/19 held-out groups; AUC0.682619, fixed0.682835 |
| 1 OFF pins d11/13/16/20/22 | PASS | fitted-v1:312866 /862329 /3024920 /12389307 /34048354 |
| 1 ON fixed-depth identity | PASS | fitted-v1: identical five pins |
| 1 perft5 | PASS | start4865609; kiwipete193690690 |
| 2 timed live proof | PASS (revised fixture) | fitted-v1:10/20, median3; original opening-only5/20 and1/20 failures retained |
| 3 200-game average time | PASS (fallback source only) | 200 games; ratios0.99016836/move,0.99001560/game-side;0flags/illegal; actual-lock port not yet qualified |
| 4 hard limits | PASS | fitted-v1:50,1s+.01s; max255.124ms;0hard-cap+20ms overruns |
| 5 absurd coefficient clamp | PASS | A1000000,50positions; multiplier capped1500; max255.342ms;0overruns |
| 6 ASan+UBSan ON smoke | PASS | Linux CI41289552546,fittedsource,4allONgames,0reports/faults |
| 7 patch/README/fitter/tests/skill | FIX | CR requires actual AL1 s198 base294dbed3; fallback patch/evidence preserved |
| Crew SPRT | UNPROVEN | CR first, then Strength and QA; UHO primary, 8moves separate, longer TC confirm |

Blockers: none after D: scratch authorization; optional CodeRabbit/Sonar CLIs and
MCP analysis tools are not currently available. Never treat missing analysis as PASS.

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
