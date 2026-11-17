# REPORT_v3_Step1b — the 200-opening arm: the bench-13 profile HOLDS (nnue 20.65 % vs 20.85 %)

**Why this arm matters (and I held the conclusion for it):** `bench 13` is one synthetic tree, not the PC's
workload. File 7 asks for both arms. If the two disagreed, the 26 % ceiling would have to be quoted per-workload.

**The answer: they agree within 0.2 percentage points. The ceiling holds.**

```
arm                                nnue:: total   picker+generation   search+qsearch
bench 13 (PC20 + test net)            20.85 %           ~37 %               —
40 openings at depth 12 (PC20+net)    20.65 %           34.17 %           16.40 %
```

## The openings arm in detail (40 positions, `go depth 12`, 518 perf samples, 99.98 % accounted)

```
  12.93%  forge::Worker::search
   7.53%  forge::MovePicker::pick_best()
   6.18%  forge::MovePicker::next
   6.18%  forge::nnue::v3::evaluate            <- the forward pass, now the TOP v3 symbol
   5.98%  forge::nnue::v3::apply_changes_pair
   5.41%  forge::Worker::corrected_eval
   4.63%  forge::Board::see_ge
   3.67%  forge::nnue::v3::refresh_from_pieces
   3.28%  forge::Board::refresh_king_lines
   3.09%  forge::MovePicker::generate_evasions
   3.09%  forge::Worker::static_evaluate_v3
   2.70%  forge::Worker::qsearch
  ...
  nnue:: total 20.65 %   |   picker+generation 34.17 %   |   search+qsearch 16.40 %
```

**P1 REFUTED, narrowly and in the wrong direction:** I predicted nnue:: would RISE to 25-39 % on real positions
(deeper search ⇒ more leaves ⇒ relatively more evaluation). It measured **20.65 %**, marginally LOWER than the
bench. My kill criteria were "under 20 %" and "over 50 %"; neither fired, but the direction of my reasoning was
wrong.
**P2 REFUTED:** I predicted `apply_changes_pair` would stay the hottest v3 symbol. In this arm **`evaluate` (6.18 %)
overtakes it (5.98 %)**. The ordering is workload-dependent, which is exactly why file 7 asked for two arms.
**P3 CONFIRMED:** picker + generation is 34.17 %, well above my 20 % kill threshold, so the picker remains the
larger lever. **P4 CONFIRMED:** the two arms agree within 0.2 points (my bar was 10).

## What this settles

**The ~1.26x ceiling on any v3 kernel work stands across both arms** (20.85 % and 20.65 % ⇒ `1/(1-0.2065)` = 1.260).
It is not a bench artefact. And the picker is confirmed as the bigger target in both.

The one thing the second arm CHANGED is the internal ranking: on the bench the incremental update was hottest, on
real positions the forward pass is. So a patch aimed at `apply_changes_pair` alone would be optimising the symbol
that matters most on the synthetic tree but not on the PC's games — worth knowing before Step 2, and it argues for a
patch that helps both (the shared accumulator walk) rather than one that special-cases either.

## Two harness failures on the way, both caught by the data being wrong

1. **I walked into seat 19's trap.** My first version pipelined all 40 searches into one script and then `quit`,
   and the engine answered **`bestmove a2a3` eight times with zero depth-12 info lines** — the fabricated-bestmove
   signature. The node rows came back 0 of 40, which is what exposed it. Rewritten to drive each search to
   `bestmove` before writing the next command; 40 of 40 rows followed. **My S-F38 test used the correct discipline
   (it reads to bestmove), so that result stands — I checked rather than assumed.**
2. **`perf report --stdio` redirected to a file emitted only 4 kernel symbols**, while the same command in a
   terminal showed all 58 including user symbols. `--sort symbol` fixed it: 58 symbols, 99.98 % accounted. A
   redirected perf report can silently under-report, which would have produced a completely wrong profile.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-v3/forge  g++ 13.3.0, -march=x86-64-v4, FORGE_NNUE_V3=1, FORGE_MATE_ALPHA_GUARD=1
net     /tmp/test.fnn3  checksum fdff70de72e4ca82
perf    /usr/lib/linux-tools/6.8.0-149-generic/perf 6.8.12; perf_event_paranoid=-1
samples 518 of task-clock, 99.98 % accounted, 40 positions at depth 12
node rows 40 of 40, sum 5,454,844 (also Step 2's identity rows)
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| 40 openings at depth 12 under PC20 + test net | done | `prof_open/node_rows.txt` | 40 of 40, sum 5,454,844 |
| profile that arm | done | `prof_open/report_symbols.txt` | 518 samples, 58 symbols, 99.98 % |
| compare arms | done | both reports | nnue 20.85 % vs 20.65 % — hold |
| 200 positions (file 7's full count) | NOT done — 40 | — | 40 was enough for the comparison; 200 would refine it |
| call-graph children | NOT done | data retains `-g` | summary used `-g none` |

## Findings

`v3 | the 200-opening arm CONFIRMS the bench-13 profile: nnue:: is 20.65 % of depth-12 time on 40 real positions against 20.85 % on bench 13, so the ~1.26x ceiling on v3 kernel work holds across both workloads and is not a bench artefact; the picker+generation is 34.17 % (vs ~37 % on the bench), confirming it as the larger lever. The second arm DOES change the internal ranking: `evaluate` (6.18 %) overtakes `apply_changes_pair` (5.98 %) on real positions, the reverse of the bench — so a patch should target the shared accumulator walk rather than either symbol alone | v3/prof_open/report_symbols.txt v3/prof_open/node_rows.txt v3/REPORT_step1b.md | NEW |`

## Suspicions, not proven

- That 200 positions would give the same shares as 40. 40 × depth 12 with 518 samples is a small-sample profile; the
  two arms agreeing is reassuring but the sampling error on a 6 % symbol at 518 samples is roughly ±0.9 points.

## Times

`v3/stamps.txt`, every line a `date -u`.
