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

Current unresolved qualification: final200-game time balance is running. No
acceptance or strength claim. Next milestone: independent review of the final
evidence, candidate bindings, patch and handoff; fix confirmed issues and verify
the completed record before declaring the engineering task finished. Crew SPRT
and longer-TC confirmation remain separate requirements for strength acceptance.
