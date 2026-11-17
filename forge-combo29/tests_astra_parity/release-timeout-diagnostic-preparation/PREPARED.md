# Release diagnostics for the two TSan response-deadline positions

Preparation only. No engine, Git, root-state or engine-source changes were made. This helper is for Fable0018's diagnosis, not soak coverage or a claim that either original failure is resolved.

The immutable declaration specifies forty searches: two exact recorded position histories × Threads1/2 × depths9/12 × five repeats. Each search gets its own fresh process and `ucinewgame`. The root explicitly chose this interpretation of “fresh process, depth9 and then depth12”: within each case/repeat, T1 depth9 then depth12, followed by T2 depth9 then depth12. No depth12 result is warmed by a preceding depth9 search. Original warm TT/history state is not reproduced.

Case4 keeps HindsightDepth and MateAlphaGuard false; case10 keeps both true. Every run uses Hash16, OwnBookfalse, UseNNUEtrue and MultiPV1. The fixed release engine is `/workspace/work/parity-run/builds/step2-release/forge`, SHA256 `df76cddaea8a37dae7f8d1a5178700e0168aad8c463764ed6870d9c4fce2dc56`, source `d9a8587df8ad4d0ff1231632cb1ac72b590c04bf`. All26 source/header/CMake hashes, eight objects, compile/link flags, the original fault files and decision0018 are pinned. The engine has no sanitizer flags.

The helper is a minimal parameterized copy of the two-case TSan diagnostic. Its measured UCI transport and label parser are byte-identical. The frozen independent Board oracle checks each complete move history and resulting FEN, and checks any returned move for legality. It supports only Threads1/2 and target depth9/12. Setup is bounded at7seconds, response at an absolute60seconds, shutdown at250ms; the outer native command is75seconds plus2seconds kill grace, with a78second controller bound.

The outcome is frozen before `quit`. A bestmove or target-depth line emitted only while shutting down cannot count as natural completion. Raw stdin/stdout/stderr and event timing are retained. The auditor extracts every unbounded-score info line before the pre-quit marker, with depth, nodes and engine-reported time. It rejects missing, duplicate, partial or unsafe numeric fields. Bound lines and post-quit lines remain in raw output but are excluded from the completed-depth table. Engine-reported time and observed response time are distinct measurements; neither is presented as a speed claim.

Root commands, one search at a time, in declared order:

```text
node /workspace/work/parity-release-timeout-0018-preparation/control.mjs R-001 --diagnostic-authorized
node /workspace/work/parity-release-timeout-0018-preparation/audit.mjs R-001
# Continue R-002 through R-040, subject to root priority and remaining budget.
node /workspace/work/parity-release-timeout-0018-preparation/summarize.mjs
```

Use the root command logger for exact command/output retention. Runtime files go under `/workspace/work/parity-run/release-response-diagnostic-0018/R-NNN`. An exclusive lock and a native-process check prevent overlap at launch; root must keep other workloads out throughout each diagnostic. The prior row must have finalized before the next row can start. Existing rows cannot be overwritten. A timeout's controller exit is1, but its audit can return0 when the failure evidence is valid: audit success is not search success. Inspect `searchCompletedBeforeQuit`, `result.diagnostic_success`, process outcome, diagnostics and errors separately. Neither the auditor nor the summarizer clears any stop or gives soak credit.

Offline validation: both exact histories passed frozen-Board legality/FEN checks; eight native completion cases passed; twelve table/accounting cases passed, including exclusion of post-quit/bounded output and rejection of malformed counters. Six JavaScript syntax checks passed. Commands and outputs are in `compile.txt`, `selftest.txt`, `VALIDATION.txt`, `FINAL-VALIDATION.txt` and `DIFFS.txt`. No engine was executed during those checks.

The actual controller/artifact/auditor integration awaits root's first live run. The forty-search target is not a completed count. Missing rows remain pending, and timed-out searches retain every finished lower-depth observation without gaining target-depth completion credit. No Elo, speed or regression conclusion is inferred automatically.
