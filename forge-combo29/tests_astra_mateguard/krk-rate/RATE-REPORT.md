# Bounded alternating KRK rate observation

The unchanged full test reproduced a missing mate score on **both builds**. The phase stopped immediately after the first reference miss, at trial 012, as answer 0010 required. This observation does not identify a cause or establish equal failure rates.

| Build | Complete invocations | Main tests | Main misses | Missing mate scores | Raw non_mating_move counter | T1 preflight misses/tests |
|---|---:|---:|---:|---:|---:|---:|
| Candidate | 6 | 2400 | 1 | 1 | 0 | 0/600 |
| e04556dd / f27 reference | 6 | 2400 | 1 | 1 | 1 | 0/600 |

Both triggers occurred at position index 2, FEN `8/4K3/8/1R6/8/8/7k/8 w - - 0 1`, whose original oracle DTM is 13 plies. Both logged triggers record T1 selection score mate 10 / b5g5.

| Trial | Build | Zero-based run index | Observed result | Oracle move DTM | Local group misses |
|---:|---|---:|---|---:|---:|
| 009 | Candidate | 5 | cp 563 / b5g5 | 13 plies | 1/10 |
| 012 | Reference | 1 | cp 534 / e7d6 | 21 plies | 1/10 |

**The reference raw non_mating_move count is not a lost mate or a draw.** The unchanged test's move_mate_plies contract (source lines 34–54) returns a positive root DTM for a move that forces mate. It returned 21 for e7d6. The main predicate at lines 373–385 requires `move_plies <= depth` when no mate score is reported. Thus 21 > 14 triggers that raw counter even though the oracle reports a winning move. Candidate b5g5 has DTM 13 <= 14 and triggers only the missing-score counter. These are the test's original predicates and outputs; none were changed.

Every invocation used the unchanged arguments `40 10 2 16 14 1`: 40 selected positions, ten repeats, Threads 2, Hash 16, depth 14 and full clear before each search. The final argument is clear_all, not an NNUE switch; raw configuration reports NNUE true. Each complete invocation contributes 400 main tests and a separate 100-test T1 preflight. Position-selection searches are outside both denominators. The unchanged selection code can select different qualifying sets for different engines; logs do not enumerate every selected FEN, so this is not a demonstrated paired-position rate comparison. The two logged failing FENs are identical.

The fixed window began 2026-11-14T22:53:55.385Z, with deadline 2026-11-14T23:23:55.385Z. The final reference invocation ended 2026-11-14T23:06:39.557Z; no trial 013 was started. All launches satisfied the 465-second remaining-budget guard, all native commands retained the 440-second timeout/two-second kill grace and 450-second outer bound, and all twelve completed before the deadline. No timeout, signal, stderr output or sanitizer diagnostic occurred in these trials. Native exits 1 for trials 009 and 012 are retained as test failures.

The earlier original Release 1/400 result, original ASAN t12 timeout with no credited count, and focused candidate 0/10 are separate observations, not pooled into this table. Repeated searches of a small selected corpus and stopping at the first reference miss limit inference; no statistical equivalence, regression attribution or common causal mechanism is claimed. Attribution/private reverts were not undertaken. The issue remains open as a two-thread missing-mate-score behavior observed on both trees.

Independent audit checked all twelve full raw stdout/stderr pairs, single configuration/preflight/summary markers, exact miss lines and group counts, cumulative aggregates, command/env/cwd/exit records, schedule/runner/binary pins, 99 unchanged current source fingerprints, the baseline source snapshot and byte-identical reference control relink. All 62 root copies of trial/schedule/preparation evidence match. Preparation uses the unchanged original test and frozen engine objects; reference flags retain strict FP/x86-64-v4 and the same test-assertion policy. The earlier controller ancestor-check failure and correction remain preserved separately and are not native trials.

Exact verifier and inert copy: audit-rate.mjs.txt. Actual audit command/output, rate-audit-summary.txt, rate-audit-trials.txt, rate-audit-pins.txt, predicate excerpts and the retained answer 0010 are adjacent. This audit executed no additional tests or searches and changed no engine, test, state or Git data.
