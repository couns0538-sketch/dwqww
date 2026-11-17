# Job A closeout guidance — preparation only

This is not a completion declaration. The consistent read-only snapshot is **2026-11-15T03:35:29.163Z**, after continuation2/8 had finalized. The source remains d9a8587df8ad4d0ff1231632cb1ac72b590c04bf. No engines, Git, renderer or root state were changed for this review.

## Current evidence and what remains

| Scope | Clean batches | Accepted games / searches | Retained failed batches |
|---|---:|---:|---:|
| Original final protocol | 0 | 0 / 0 | 1 |
| Extended strict protocol | 2 | 108 / 15514 | 2 |
| SMP-amended protocol | 2 | 148 / 21436 | 2 |
| 0018 continuation | 8 | 388 / 54053 | 0 |
| Accepted final-tree total | 12 | 644 / 91003 | 5 |

Coverage is **8/12 latest0018 conditions: all8 ASan/UBSan conditions and0/4 capped TSan conditions**. The still-missing conditions are `tsan/off/t2/n20000/d0`, `tsan/on/t2/n20000/d0`, `tsan/off/t4/n20000/d0`, `tsan/on/t4/n20000/d0`. Count the set union of condition keys from passed final-tree rows; never add protocol group counts. The earlier T1 and SMP T2 clean coverage remains valid and separately attributed. Old failed TSan depth9 attempts do not supply capped-node coverage. A passed condition is a sampled condition, not proof that the requested two hours of actual sanitizer work happened.

At this snapshot, finalized final-tree batch intervals have **1299.126seconds union**, **2528.724seconds duration sum**, and **1142.156seconds accepted-clean union**. The final-tree soak window from00:58:43.523 to03:35:29.163 spans9405.640seconds;8106.514seconds are not covered by a finalized sanitizer-batch interval. The sum is not CPU time. Union intervals include startup/protocol/shutdown overhead. Failed batch runtime is included only in the all-attempt union, not clean coverage. Preliminary Step1 remains separate. Builds, corpus comparisons, matches, diagnostics, blocked time and missing intervals never inflate sanitizer duration. Do not describe the long elapsed window as a two-hour sanitizer soak.

The two100000-position comparisons are finished. Step1 is strictly identical; Step2 retains one same-clock difference and its explicit effective acceptance. Keep the original strict gate/difference/cutoff records untouched. Default pins312866/862329/4865609,16 option rows, nine unit rows and the targeted mate−5/2566746 result already have evidence; no duplicate checks are needed merely to close the report.

The **0018 diagnostic evidence is still pending in this snapshot**: two fresh-process TSan cases with60second response allowances, and forty fresh release searches (two histories × Threads1/2 × depth9/12 × five repeats). At closure report the actual finalized/target-completed counts, every timeout/diagnostic/abnormal exit, and per-finished-depth nodes/time. Exclude output obtained only after quit from natural completion. A fresh-process result does not reproduce the old warm TT/history state. Do not label either original15second failure “TSan slowness,” a hang, a race or a proven node explosion before the measured comparison supports it. If unfinished, say exactly how many of2 and40 ran and leave the classification open. Source lines can support an explanation, not replace runtime evidence.

## Renderer changes needed at the deadline

Only root edits `/workspace/work/parity-run/report-parity.mjs`.

1. Replace stale `newRequiredCoverage` wording: JobB and multiple final protocols have already run. Separate “current protocol coverage” from the accepted cross-protocol12-condition union. Update live `validation.step2.status` presentation without rewriting any frozen audit. The `sanitizerBuilds.runs=0` field is a historical build-freeze observation, not a current runtime total.
2. Rerun the existing interval accountant and the small read-only snapshot helper at the actual closeout time. Publish a fresh immutable timing report; the renderer currently always links `soak-time-review-0017/REPORT.md`, even when it reads the latest `soakTimeReviews` entry. Point the text to the exact newly published snapshot, preserving the old report.
3. Add the0018 continuation decision explicitly: ASan proceeds independently of the timeout diagnosis; future ordinary TSan uses nodes20000 while the soft half stays2500. Label the older depth9 failures and new capped conditions distinctly.
4. Keep all five historical failed sanitizer batches visible and zero-credit: original depth64 contract failure1, Threads2 sample-rule failures2, TSan response-deadline failures2. The first three were resolved by explicit acceptance-rule amendments, not engine fixes. The last two require measured diagnostic classification. Keep failed-batch completed-pair and partial observations apart from accepted counts. The snapshot has ten fault files in total, including the separate equality difference and four shutdown occurrences; recount the actual files at closure rather than hard-coding this number.
5. Include current diagnostic results and any unresolved findings, not just the original two timeout descriptions. The old `responseDiagnosticAuthorization.ordinarySoakRemainsBlocked=true` is historical authorization metadata; current continuation permission comes from0018 and the effective root state. Do not erase the old field or mistake it for the live status.
6. State the duration shortfall plainly if actual sanitizer runtime is below7200seconds, even if all12 conditions become covered. Record72 as reserved inventory, not72 required passes. List unmet optional split-ASan KRK work as optional, if not run. The independent per-node incremental-versus-full NNUE comparison was not performed; warm searches refresh the root accumulator, so that stronger claim remains unverified.

## Close Job A without closing Job B

At **2026-11-15T04:20:00.000Z**, stop new JobA native work and publish its budget-limited closeout after outstanding evidence has been finalized. The paired controller's475second margin already refuses launches at or after04:12:05. Do not launch a bounded diagnostic without its full command/recording margin before the deadline. Unfinished/interrupted batches keep raw evidence and zero clean credit; do not invent an end time or smooth the gap. The original23:19:40 start to04:20 deadline is **5hours00minutes20seconds elapsed**, not five hours of testing.

Use wording such as: “Job A closed at its04:20UTC budget deadline. Source checks and both corpus comparisons are complete under the recorded acceptance decisions. Accepted sanitizer work: [actual counts], [G]/12 latest conditions, [actual clean union] seconds of batch runtime. [Missing conditions/duration/diagnostic classification] remain unverified. Five historical failed sanitizer batches remain unchanged and excluded from clean credit.” Use the actual closure values, not this preparation snapshot. If there is no missing item, say so only after the final evidence proves it.

**Job B remains a separate running job until05:06:50.313UTC**, two hours from its actual03:06:50.313 declaration. Do not reset that clock at04:20. Its snapshot is200 accepted games,100 pairs, W-L-D53-53-94, pair bins4,26,39,28,3, with zero recorded operational findings. These are interim counts. Continue the frozen50000-node match to6000games or its budget, stopping at a pair boundary under its declared rule. Keep raw partial/excluded games separate, and report all failures by side. The optional1000-game250000-node leg is a distinct optional leg and must not be blended into the50000-node totals. Counts only; no Elo or speed conclusion. JobC begins only after A and B have both been reported, as0017 requires.

## Reusable read-only commands

```text
node /workspace/work/parity-job-a-closure-guidance/snapshot.mjs ACTUAL_UTC_TIMESTAMP_WITH_MILLISECONDS
node /workspace/work/parity-soak-time-review/review.mjs --as-of ACTUAL_UTC_TIMESTAMP_WITH_MILLISECONDS --markdown
```

These commands write stdout only. Save their actual outputs and command metadata to a new immutable publication directory. `snapshot.mjs` verifies that the state did not change between its coverage and timing reads; if a recorder completed concurrently, rerun the read-only snapshot. Its timing data includes all discovered final protocols and excludes preliminary/diagnostic work. It is not a closure action and never changes state.

## Owner-PC limitation

Report the tested cloud source, binary hashes, options and compiled network identity. **The owner's actual compiler/ThinLTO/PGO profile, runtime tuning, active network and running PC were not independently tested here.** Fable's source comparison is attributed evidence. A successful cloud run neither establishes identity with every PC-only/default-off addition nor validates the later v3 net path. The cold and warm search tests do not establish NNUE values equal a fresh computation at every node. Nothing ran on the owner's PC.
