# Forge Astra round3 report

Checkpoint: 2026-10-29T03:14:10.717214-07:00. **FINAL: primary Linux integration qualification and the requested final review are complete. A2 remains BLOCKED; later jobs are deferred.** The user reported23% usage remaining; internal usage/context-window telemetry is unavailable. Stop starting new experiments; preserve completed and unfinished work.

Accepted input remains`b7c177222038e9332965a95ec53ea3b94e90dbc9`. Integrated candidate engine source is`926c55f33227bc4a030d7ce5b1140528aeba75af`, on isolated`astra3-integration`. No accepted branch, live PC engine, gate, lock, network or trainer was changed. No Elo or speed improvement is claimed.

| Job | Branch / checkpoint | Status | Result / next action |
|---|---|---|---|
| A1 integration | astra3-integration / e0d76ce8a6450573b503852aeca12b929bf4a17a | DONE (primary Linux qualification) | Five required merges, named presets, UCI/echo/ownership fixes and nominal-depth metadata implemented. All3 primary builds match all5 OFF pins, both perfts and FMA0; Windows/adoption pending. |
| A2 mate root cause | astra3-smp-mate-rootcause / 6a9cc2b7a23ed29f6bc77ad9a496b4cfc6e6e391 | BLOCKED | Native fallback reproducer9/28 seeded CP vs0/28 controls. Root-score mask has no effect; child target absent. No production fix. Next: per-store/root-child TT provenance. |
| A3 OFF speed | not created | BLOCKED / deferred budget | No ABBA or CI measurement. |
| A4 autopromote patch | not created | BLOCKED / deferred budget | Attached script preserved read-only; no patch, installation or live execution. |
| C1 known functional failures | not created | BLOCKED / deferred budget | Four allowed lines remain; no expectations weakened. |
| C2 SmpExactNodes | not created | BLOCKED / deferred budget | No new node-budget repair. |
| C3 UCI hygiene | not created | BLOCKED / deferred budget | No case-folding or unsupported-net warning change. |
| C4 singular tests | not created | BLOCKED / deferred budget | New exhaustive exclusion test not implemented. |
| C5 search ideas | not created | BLOCKED / deferred budget | No research candidates accumulated. |
| C6 drawish scaling | not created | BLOCKED / deferred budget | No evaluation change. |
| C7 SPRT audit | not created | BLOCKED / deferred budget | No checker delivered. |
| C8 SPSA pilot | not created | BLOCKED / deferred budget | No pilot or training run started. |
| Final handoff | astra3-report | DONE | Final report and next-action checkpoint; all completed and failed evidence published. |

## Verified identities and tests

Five-depth OFF reference(d11/13/16/20/22):**312866 / 862329 / 3024920 / 12389307 / 34048354**. Startpos perft5**4865609**, kiwipete5**193690690**, whole-executable FMA**0**.

| Primary binary | SHA256 | OFF depth vector | perft / kiwi / FMA | Native tests |
|---|---|---|---|---|
| GCC14 Release |8733bcb06e2ba0d7ecb9b2e29de9fcedb870db71cca8ad50bfeea015cbbd9bbc|All5 exact|4865609 / 193690690 /0|64/65; four known functional lines only|
| ASan/UBSan/LSan |30633d03cc16f5ef82bed33139f463912d78c6df1b1fd7bca4893eb7b5a36d8a|All5 exact|4865609 / 193690690 /0|64/65; same four lines; zero sanitizer diagnostics|
| TSan |9a77389b180ef495b8b9b59bc3e090f8f039f4b135c67b1ebcb95dc4e30c8809|All5 exact|4865609 /193690690 /0|8/9 then unchanged SMP replay1/1;256search stress; zero race reports|

The six Release merge/fix milestone binaries each passed the full OFF vector, both perfts and FMA0. Exact hashes, commands, raw logs and NPS values are in the[A1 report](https://github.com/couns0538-sketch/dwqww/blob/e0d76ce8a6450573b503852aeca12b929bf4a17a/astra3/integration/REPORT.md). Their CTest totals were56/57,58/59,60/61,62/63,62/63,64/65; every failure was the same known forge_tests assertions.

Final Release option matrix:**75/75 PASS**. SingularV2=**404121/1005954/4120585/11497954/34264955**; N1=**277579/814055/2651984/18648191/40304213**; N1→OFF, SmpV2T1 and TmSoftHardClamp match OFF. All eight R5A singles reproduce their external gate pins. CorrMargins1/Scale100 uses**343365/858019/2522546/12894582/22287047**, as explicitly confirmed by the user; CorrMargins0/Scale100 stays OFF. Full values and original streams:[matrix](https://github.com/couns0538-sketch/dwqww/tree/e0d76ce8a6450573b503852aeca12b929bf4a17a/astra3/integration/final_matrix).

Known functional failures retained verbatim:

- FAIL: WAC 001 expected g3g6 got f6h5
- FAIL: WAC 001 score 623 below 31997
- FAIL: unrestricted search chooses the winning rook underpromotion over stalemating queen promotion(two identical lines)

A clean sanitizer diagnostic result is **not** a completely green functional CTest suite. ASan/UBSan raw exit8 is preserved. TSan's original forge_smp_tests300s timeout is preserved; the same full-depth test passed in529.42s with a900s deadline. No test depth or expected value was weakened.

The advertised-option contract passes102/102 in Release and instrumented suites. Official Fastchess strict smoke completed2draws/exit0. Unknown option producedexit1, zero go/position commands and an empty PGN. Its original extra-check FAIL receipt remains with the independent interpretation addendum: Fastchess prints a scheduling label before option validation. These2games establish protocol operation only.

## Mate diagnostic and limits

[A2 source and evidence](https://github.com/couns0538-sketch/dwqww/tree/6a9cc2b7a23ed29f6bc77ad9a496b4cfc6e6e391/astra3/smp-mate-rootcause). Helpers finish before main in the serial reproducer, selector never runs, and LocklessTT is false. All28 empty controls find31995/d5c5; helper-seeded searches produce9CP,18exact mates and1longer mate whose line remains unverified. No timeouts. This does not measure the original concurrent SMP failure frequency.

K1 root no-touch/identical-rewrite/score-mask produce the sameCP484/e8e4 and nodes/PV in round1, recovering the expected mate inround2. Child-after-d5c5 is absent and the driver exits2 without inserting anything. The child-mask case is NOTRUN. Per-store writer/history provenance, root cause, production repair and500+500/200x fix regressions remain UNVERIFIED.

## Review, delivery and next session

The requested20-minute final review began at2026-10-29T02:54:15.116394-07:00; completed at2026-10-29T03:15:14.298523-07:00 after1259.182seconds of source/evidence review. The exact receipt is in A1 final_review/completion.json. It found a stale README hash after a later completion paragraph was appended; the original README was recovered from Git, old failed audit/manifest preserved, and a separate current manifest added. Raw evidence hashes matched. Stale current-status summaries were corrected and historical pending receipts explicitly superseded. No new engine defect was established by this review.

Three test-only debughook UCI binaries are hash-inventoried and covered by native protocol tests; their separate full bench/perft/FMA identity is UNVERIFIED. They are not release candidates. Windows/PS5.1, successful real Syzygy loading and optional CodeRabbit service access remain unavailable/unverified. A proposed improvement to the existing validate-chess-engine skill is preserved, not installed; no duplicate skill was created.

Remaining order: resumeA2 from the saved provenance question. If A2 remains blocked, follow the pack's orderedA3/A4 thenCjobs only when budget is available. No autonomous future restart is promised. Never run supplied/live autopromote or change gates.

Gate handoff is identity/protocol evidence only. All eight R5A single identities are eligible for CR/QA review on this Linux source; Windows checks/adoption remain theirs. No new gate was run or specified as accepted. Future strength proposals retain normalizedSPRT[0,10], cap_games3000 integer, blank srand/openings_start for QA. Original queued semantics stay unchanged.

Checkpoint timing breaches earlier in the turn are acknowledged in A1's report; this is not a claim that every interval met10minutes. All completed code and evidence are on isolated branches. A1 and A2 remote tips were verified against their local commits; the final report push is verified separately after this commit.

IDEA_SOURCE: user/Engine QA round3 handoff, reviewed same-repository Forge branches and original native evidence. No other-engine code or tuned constants imported.

## Qualification tooling checkpoint

Independent review of the new TSan finalizer found and fixed three gaps before native use: disabled assertions under optimized Python, missing build-receipt binding, and lost objdump failure output. Five synthetic-only regression methods pass under normal and optimized Python; original RED evidence is retained. These tests are not native engine or benchmark results. The native driver subsequently completed: d22=34048354, startpos4865609, final kiwipete193690690 and FMA0. The sealer exited0/PASS against the actual recorded build digest; no result was inferred from elapsed time.

## Final publication / continuation checkpoint

No owned native experiment remains running. Final original-log scan covered697files with0sanitizer diagnostic matches. Exact primary TSan receipt, commands, runtime environment, compile flags, executable and manifest are under`astra3/integration/tsan/final_identity` on the final A1 checkpoint. Full original bench timings/NPS for both instrumented builds are in A1 REPORT; no performance claim follows.

SmpV2-on remains unqualified for adoption because A2 is unresolved. Its default remainsfalse; the R5A identities preserve it. The final report does not claim all round3 jobs are complete: A3/A4 and C1-C8 were not started after the user requested conservation of remaining usage. Resume from the exact saved A2 source and its provenance question; do not restart already-completed merges or screenings.

Raw links:

- [A1 report](https://raw.githubusercontent.com/couns0538-sketch/dwqww/e0d76ce8a6450573b503852aeca12b929bf4a17a/astra3/integration/REPORT.md)
- [A1 gate limitations](https://raw.githubusercontent.com/couns0538-sketch/dwqww/e0d76ce8a6450573b503852aeca12b929bf4a17a/astra3/integration/GATE_NOTES.md)
- [A2 report](https://raw.githubusercontent.com/couns0538-sketch/dwqww/6a9cc2b7a23ed29f6bc77ad9a496b4cfc6e6e391/astra3/smp-mate-rootcause/REPORT.md)
- [Timed review receipt](https://raw.githubusercontent.com/couns0538-sketch/dwqww/e0d76ce8a6450573b503852aeca12b929bf4a17a/astra3/integration/final_review/completion.json)
