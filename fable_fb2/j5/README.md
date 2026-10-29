# FB2-J5: Lazy SMP v2 (branch `fable-fb2-j5`, UCI option `SmpV2`, default false)

With the option off the engine is the lock (OFF identity pins; `logs/identity_off_j5.log`). At Threads 1 the option is
inert (identical node counts, `forge_fb2_j5_tests`). With Threads > 1 and `SmpV2 true`:

- odd helper ids search one ply ahead of the main thread (`search_depth = depth + 1`), even helper ids use a wider
  aspiration window (2x, 3x, 1x the delta in turn) — the helpers' trees differ from the main thread's, so their
  transposition-table entries are new information when the main thread reaches those depths (R3-6 found the lock's
  helpers in lockstep with the main thread);
- after the join, the deepest completed result of any thread (with a best move) is reported; ties keep the main
  thread; node and time totals stay the main thread's (`fb2::smp_select_result`).

## Verify
- Unit tests: CTest `forge_fb2_j5_tests` (`tests/fb2_j5_tests.cpp`): skew / multiplier / selection rules, Threads 1
  inert (5 positions, identical nodes), Threads 2 and 3 depth-9 and node-limited searches legal and finite with the
  option off and on, mate in 1 at 3 threads.
- TSan: the CI hook `opus_round1/fable/tsan_extra.sh` now also runs SmpV2 searches at Threads 3, 4 and 2 (the
  helper-result vector is written by the helpers and read after the join).
- Speed: `tools/smp/fable_smp_ttd.py forge_fable_j5.exe positions30.tsv --threads 1,2,3 --configs off:,on:SmpV2=true`
  (R3-6's 30-position suite, fixed depths 20-32, fresh IDLE process per run, shuffled cells): per (config, threads)
  sum of wall, per-position speedup geometric mean, node inflation, NPS scaling, CPU scaling, and the paired on/off
  wall ratio per thread count. Results in `logs/smp_ttd_*.csv/.log` and the report (advisory: loaded PC).

No Elo claim; an SMP gate needs Threads > 1 on both sides (GATE_BOUNDS.md).
