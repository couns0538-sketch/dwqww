# Review milestones — UNPROVEN

No existing AGENTS.md was found in this worktree, the shared project root, HEAD,
or origin/main. The requested automatic review policy is now in root AGENTS.md
on astra-r8-tmfit; other branches and crew files were not edited.

| Milestone / identity | Review and disposition | Verification / next action |
|---|---|---|
| Engine/logger/fitter,391f07cc plus reviewed working fixes | Cross-component review found unstable-search selection bias and last-info-time/noise liveness weakness. Retained aborted-return disagreements, label against completed final iteration; use wall medians and nonneutral diagnostics. | Fitter13 tests, numeric tests, preliminary OFF/ON pins+perft PASS. Proceed to real fit. |
| Harness and fixed-point integration,0a271930 lineage | Independent read-only reviewer found hung-quit suppression and rejected-option acceptance. Main agent accepted both; fixed with failure receipts and reserved-option protection. Reviewer rechecked both. No numeric overflow or hard-cap expansion found. | Red/green regressions,16 driver tests PASS. Fitted native identity/live/hard/absurd and fitted ASan+UBSan PASS. |
| Timing qualification design,aded6b62..d386550b | Independent reviewer confirmed color-swapped paired timing, requested both per-move and per-game bounds, and actual opening disjointness. Main agent accepted these; added gate/regression and verified zero intersections. Fixture adaptation after opening-only live failures is explicitly retained, not called untouched holdout evidence. | Paired40 calibration ratios0.986462/0.989479; zero faults. Freeze A742/B3000/Lo650/Hi1750. |
| Parallel200 coordinator,41699d07 | One independent read-only reviewer inspected stable coordinator, shard validation, requirements and surrounding runner. No blocking findings. Confirmed two active searches,100 disjoint opening pairs, frozen hashes/settings, PARTIAL child status and combined200 gate. | Driver16+aggregator5 tests PASS. Both calibration processes exited before launching final200. Candidate exe e9e6c2686350307c8bd73749544c372fd528d5561e87c6b4cc8b6f9df26eefae is copied immutably into final-smoke-v1/bin. |

Native fitted validation above refers exactly to executable
`e9e6c2686350307c8bd73749544c372fd528d5561e87c6b4cc8b6f9df26eefae`,
with [build/source receipt](evidence/qualification_draft_v1/artifacts/000_build.json)
and [identity evidence](evidence/final_v1/bench-fitted-v1/summary.json).
The sanitizer result separately binds Linux CI run41289552546 to source
`0a2719306bac6f40a5b68a4174e9718655ea5aa0`; it is not a run of the Windows executable.

Policy-adoption milestone: independent read-only review found one minor identity
ambiguity in this log. Main agent accepted the finding and added the exact native
binary/build/evidence links above. No policy omissions were found. UTF-8 and
referenced-file checks pass; no engine or running experiment was changed.

Historical CI failure41288852339 was harness wiring (four-game sanitizer smoke
incorrectly subjected to a200-game gate). Corrected all-ON sanitizer mode and
regressions; subsequent runs41289111781,41289552546,41289992830,41290843946 PASS.
CI now checks harness regressions before compilation and watches their files.

The fallback200-game time balance completed and was reviewed below. Actual-lock
runtime qualification is now unresolved after CR's base correction. No acceptance
or strength claim. Crew SPRT and longer-TC confirmation remain separate
requirements for strength acceptance.

CR follow-up on41699d07/6b2b5ece: FIX. Accepted both findings: deliver the patch
against actual AL1 s198 source294dbed3, and add CR's PC resource governor before
further runs. Original CR patches/helper were located locally; their MD5 prefixes
538c4876/c0005114/6d109014 match and their unchanged bytes are in cr_fixes/.
The clarified governor requires8GiB free RAM, starts below80%CPU, and pauses our
work at90%CPU or higher. The earlier interpretation as an8GB own-process memory
ceiling is superseded by CR's actual artifact and Couns's clarification.

Independent focused review of completed fallback200 evidence and Checkpoint10
found no defects: verified200games/100pairs, both time ratios, zero faults,
retained hashes and empty suspension receipt101.006703seconds after completion.
Main agent accepts the findings. These are905fallback results only. New lock
patch, source snapshot and executable must bind to294dbed3, with separate checks.
The independent reviewer also confirmed the authoritative patch/source approach
meets the requested port without replacing unrelated reference engine files.

Actual-lock source-port milestone: independent read-only review of exact CR patch
ef09b342368efd01876bf771726d58cc84d73ec2960b5a70ead710ff0e88d9e3 and the patched294
stage found no concrete code defects. Verified all six changed blobs, untouched
search algorithms/allocation/hard stop, default-OFF path, once-per-search snapshot,
UCI join-before-option-write and completed-iteration-only logging. Main agent
accepts this scope result; quick build/numeric and all actual-lock runtime checks
remain pending, so the candidate is not accepted. Next: review governor, then
governed native build and exact-candidate validation.

Governor/build milestone:33 quick tests initially passed. Independent review
confirmed CR's sleep-boundary policy, free-RAM semantics, unchanged active timing,
BelowNormal and two-worker maximum. It found one missing build dependency receipt:
run_tmfit.py supplied the guard but was not snapshotted. Main agent accepted it;
builder now snapshots all three harness sources and rejects changes after build.
The added tamper regression passed (five builder tests); focused re-review passed.
Windows read-only sampling verified fresh metrics and BelowNormal16384. CPU was
94–95.5%, above startup threshold, so native work must wait. No engine/compiler
ran during those checks.

Couns further restricted all native work to CR's sleep-based governor: no process
suspension of any kind unless a separate pause step is committed and passed by CR.
That approval does not exist. No suspension hook is used by the governor; the
earlier scratch helper remains disabled. Crew processes are outside our control.

Package/CI milestone: review found missing exact-patch hash assertion and a
declaration-file mutation race. Main agent accepted both: CI asserts the exact
SHA before applying; packager reads, retains and hashes declaration bytes once.
The mutation regression passes. Producer source→binary→test linkage is explicitly
a required manual audit, not a claimed automatic feature. Focused re-review
passed these fixes and the new Linux actual-lock qualification job; its results
must retain Linux scope. Reviewer verified fresh100 fixture hash/uniqueness and
zero overlap with training, calibration and previous smoke. Runtime results
remain pending; no candidate acceptance or strength claim.
