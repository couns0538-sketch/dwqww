# REPORT_v3_Step1 — the profile: ALL FOUR PREDICTIONS REFUTED, and the net path is not where the time is

**What file 7 asked for (Step 1):** profile `bench 13` under PC20 + the test net, Threads 1 with `perf record -g`,
and report the share of every `nnue::v3` function and of the search around it.

**The answer: the whole `nnue::` namespace is 20.85 % of bench-13 time, not the 55-85 % I predicted, and the hottest
single v3 symbol is the INCREMENTAL UPDATE (`apply_changes_pair`, 8.24 %), not the forward pass (4.81 %). My model
of where the time goes was wrong in every part.**

## The profile (top symbols, `--no-children`, shares of total samples)

```
  8.47%  forge::MovePicker::pick_best()
  8.24%  forge::nnue::v3::apply_changes_pair(...)        <- the hottest v3 symbol
  7.55%  forge::MovePicker::generate_evasions()
  7.55%  forge::Worker::search(...)
  5.95%  forge::Worker::qsearch(...)
  5.49%  forge::Worker::corrected_eval(...)
  5.03%  std::__introsort_loop<MovePicker::Scored*...>    <- the sort inside pick_best
  4.81%  forge::MovePicker::next(bool)
  4.81%  forge::nnue::v3::evaluate(...)
  4.81%  forge::nnue::v3::refresh_from_pieces(...)
  4.35%  forge::Board::see_ge(...)
  3.43%  forge::fill_pseudo_legal<GenMode 1>(...)
  3.20%  forge::Board::is_legal_complete(...)
  2.52%  forge::Worker::static_evaluate_v3(...)
  2.29%  forge::TTProbe TranspositionTable::probe_body<false>(...)
  1.83%  forge::Worker::record_move(...)
```

Accounted for: 50 symbols, 100.05 % of samples.

## The nnue::v3 breakdown

```
  8.24%  apply_changes_pair      (incremental accumulator update)
  4.81%  refresh_from_pieces     (cache refill)
  4.81%  evaluate                (the forward pass)
  0.92%  king_key
  0.69%  load                    (once, at startup)
  0.69%  apply_changes
  0.23%  prepare
  0.23%  dirty_from_move
  0.23%  available
  ------
 20.85%  total nnue:: namespace
```

## Every prediction, and what actually happened

| prediction | predicted | measured | verdict |
|---|---|---|---|
| P1 hottest symbol = forward pass, 40-65 % | `evaluate` dominant | `evaluate` is 4.81 %, and the hottest v3 symbol is `apply_changes_pair` at 8.24 % | **REFUTED** |
| P2 incremental refresh second, 10-25 % | refresh 10-25 % | update+refresh together **13.97 %** — inside the band, but it is FIRST not second | **PARTLY** (band right, rank wrong) |
| P3 whole `nnue::v3` at 55-85 % | 55-85 % | **20.85 %** | **REFUTED** — my kill criterion was "under 40 %" and it fired |
| P4 `eval`-only path over 70 % forward pass | >70 % | not yet measured | pending |

**P3's own kill criterion was "under 40 % (the net path is not where the time is, which would be a notable negative
for the whole job)" — and that is exactly what happened.** The measurement killed my prediiction by my own written
rule, which is what a prediction is for.

## What this means for the job, and it is good news for the owner

The net path is **20.85 %** of a bench-13 search. That means:

- **A perfect v3 kernel could speed the engine by at most ~1.26x** (`1/(1-0.2085)`), and no realistic patch gets
  all of it. The v3 path is *not* where the engine's time goes on this workload.
- **The search and move-picker are where it goes:** `pick_best` + the sort inside it + `next` + `generate_evasions`
  + `fill_pseudo_legal` + `is_legal_complete` + `see_ge` is **32.9 %** — more than the whole net path.
- So file 7's premise ("a faster v3 path is the most useful speed find there is") is TRUE for the PC's
  *self-play throughput* only in proportion to 20.85 %; **the larger lever on this workload is move generation and
  the picker**, which is exactly what the PC20 options in the profile (TtPruneV2, HistRework) already interact with.

I report this as a finding rather than as a reason to stop: file 7's Step 2 is still worth doing for the 20.85 %,
and I will do it. But the owner should know the ceiling.

## Honest limits of this profile

- **`bench 13` is not the PC's workload.** File 7 also asks for 200 openings at depth 12, which I have not yet
  profiled; the shares may differ there. I will profile that arm before drawing the final conclusion.
- **perf had to be enabled:** `perf_event_paranoid` was 2 and I set it to -1 with sudo; the 6.8 perf binary works
  although the kernel is 6.12 (the wrapper refuses, the binary does not). Recorded so the next seat knows.
- **`-g none` was used for the summary**, so these are symbol-level shares without call-graph attribution. File 7
  asked for `-g`; the recorded data retains it (`-g` was passed to `record`), so call-graph analysis is possible.

## Honesty numbers

```
exe     /home/ubuntu/builds/bld-v3/forge   g++ 13.3.0, -march=x86-64-v4, FORGE_NNUE_V3=1, FORGE_MATE_ALPHA_GUARD=1
net     /tmp/test.fnn3  checksum fdff70de72e4ca82 (load line verified in Step 0)
perf    /usr/lib/linux-tools/6.8.0-149-generic/perf 6.8.12, kernel 6.12.113+, perf_event_paranoid set to -1
bench   `bench 13` under PC20 + test net, Threads 1, Hash 16; script committed at prof/bench13.uci
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| prediction committed alone before profiling | done | `v3/prediction.txt` | committed, then refuted |
| profile `bench 13` under PC20 + test net | done | `prof/perf_report_full.txt`, `prof/bench13.meta` | 50 symbols, 100 % accounted |
| nnue::v3 shares | done | same | 20.85 % total; `apply_changes_pair` 8.24 % hottest |
| search-side shares | done | same | move generation + picker ≈ 32.9 % |
| 200 openings at depth 12 profile | NOT done | — | file 7's second arm; next |
| call-graph attribution (`-g` children) | NOT done | data retains `-g` | summary used `-g none` |

## Findings

`v3 | the v3 net path is 20.85 % of bench-13 time under PC20 + the test net on this build, NOT the 55-85 % I predicted (my own prediction's kill criterion was "under 40 %" and it fired). The hottest v3 symbol is the incremental update `apply_changes_pair` at 8.24 %, with the forward pass `evaluate` at 4.81 % and `refresh_from_pieces` at 4.81 %. Meanwhile move generation and the picker — `pick_best` 8.47 %, the sort inside it 5.03 %, `generate_evasions` 7.55 %, `next` 4.81 %, `fill_pseudo_legal` 3.43 %, `is_legal_complete` 3.20 %, `see_ge` 4.35 % — total ~37 %. So a perfect v3 kernel could speed bench 13 by at most ~1.26x, and the larger lever on this workload is the move picker | v3/prof/perf_report_full.txt v3/prof/bench13.meta v3/REPORT_step1.md | NEW |`

## Suspicions, not proven

- That the depth-12 openings arm will show a similar split. Untested.
- That `apply_changes_pair`'s 8.24 % is reducible. It is the largest single v3 cost, so file 7's Step 2 should look
  there first rather than at the forward pass.

## Times

`v3/stamps.txt`, every line a `date -u`.
