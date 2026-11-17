# Job A budget closeout

Job A closed at its 2026-11-15T04:20:00.000Z budget boundary; evidence finalized 2026-11-15T04:20:14.695Z. Source d9a8587df8ad4d0ff1231632cb1ac72b590c04bf. Cloud only.

Accepted: 846 games / 120313 searches in 21 clean batches; 12/12 latest0018 conditions covered. 6 historical failed sanitizer batches remain separate and unchanged.

Observed finalized batch union: 2471.685seconds; accepted-clean union: 2312.736seconds; batch-duration sum: 4447.923seconds. These are command intervals, not CPU time or a claim of two continuous hours. Elapsed gaps and preliminary/diagnostic work are not credited.

| Protocol | Clean batches | Accepted games / searches | Retained failed batches |
|---|---:|---:|---:|
| finalPairedSoftnodes | 0 | 0 / 0 | 1 |
| extendedPairedSoftnodes | 2 | 108 / 15514 | 2 |
| smpPairedSoftnodes | 2 | 148 / 21436 | 2 |
| continuationPairedSoftnodes | 17 | 590 / 83363 | 1 |

| Condition | Clean coverage |
|---|---|
| asan/off/t1/n2000/d0 | Yes |
| asan/off/t1/n20000/d0 | Yes |
| asan/off/t2/n2000/d0 | Yes |
| asan/off/t2/n20000/d0 | Yes |
| asan/on/t1/n2000/d0 | Yes |
| asan/on/t1/n20000/d0 | Yes |
| asan/on/t2/n2000/d0 | Yes |
| asan/on/t2/n20000/d0 | Yes |
| tsan/off/t2/n20000/d0 | Yes |
| tsan/off/t4/n20000/d0 | Yes |
| tsan/on/t2/n20000/d0 | Yes |
| tsan/on/t4/n20000/d0 | Yes |

Step1 corpus: 100000/100000, raw gate true. Step2: 100000/100000, raw gate false, effective gate true, retained differences 1. The effective acceptance does not overwrite the strict audit. Local/default/option/unit/target results are individually recorded in CLOSURE.txt and the saved state.

0018 diagnostics: 2/2 TSan and 40/40 release searches completed; 0 response timeouts; zero soak credit. All five release T2 node counts exceed all five T1 counts for both positions at both depths. This establishes greater search work in these tested SMP ending configurations. Source guard conditions are relevant but were not instrumented; original warm TT/history state and original timeout recurrence were not reproduced. No engine fix, speed or strength claim.

Finding0019 remains recorded at /workspace/work/dwqww-parity/forge-combo29/tests_astra_parity/faults/smp-ending-workload-0019.txt, SHA256 70c9a8770a308484f356059a411fb8a3d44639d23ee1355210ee0da3ba2d75f8. No engine fix or warm-state reproduction is claimed.

Unverified work and shortfalls:

- Accepted-clean finalized batch union is 2312.736 seconds, below the requested7200seconds. Elapsed waiting/build/corpus/match/diagnostic time is not sanitizer credit.
- All finalized sanitizer attempts together cover 2471.685 seconds; this is also below7200seconds.
- An effective global engine-work stop remains set; closure does not clear it.

- The actual owner-PC compiler, ThinLTO/PGO profile, runtime tuning, active network and running PC were not independently tested. All work ran in the cloud.
- Warm TT/history reuse does not establish incremental NNUE equals a full recomputation at every node; that per-node comparison was not performed in Job A.
- Original failed audits and observations remain unchanged and excluded from clean credit. Resolved acceptance-rule findings are not engine fixes.
- Optional split-ASan KRK coverage is not credited by this closure; any separately completed optional evidence must be reported separately.

Job B remains separate, with its original deadline 2026-11-15T05:06:50.313Z; its clock is not reset and its live counters are not changed. See the main live report for current match counts. Job C is not started by this closure.

Evidence: [closure values](CLOSURE.txt), [deadline-qualified timing and coverage snapshot](SNAPSHOT.txt), [captured state](STATE-SNAPSHOT.txt), [frozen source/build identities](SOURCE-PINS.txt), [proposed single-field state patch](PROPOSED-STATE-PATCH.txt). No engine or Git command was executed by this closeout helper.
