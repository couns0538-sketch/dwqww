# Forge Opus R5C: v4 NNUE (J7 L2=16) engine support + N3 Syzygy / IntendedThreefold / HardDeadline hardening — IN PROGRESS

**Status:** PAUSED at 09:52 Vienna for job R5D (user request: R5D before the next R5C step). Done: 00_baseline, M1. M2: tables sha-verified (290/290), 200-game N3 smoke 200/200 with 0 failures (TB-hit totals in /f/opus_scratch/r5/r5c/smoke/n3/summary.json), prebench pins measured; N3_GATE_SPEC.md not written yet. M3: FNN4_FORMAT.md written; src/nnue_v4.cpp (loader, scalar + AVX2 forward), UCI NNUEv4 / NNUEv4File and the search hook written and compiled (forge_r5c_m3a.exe, 0 warnings, FMA 0), NOT yet tested (no v4 unit test, no parity); M4, M5 not started.

Branch `opus-r5c-netv4` = `origin/forge-bundle-int` b7c1772 + R5C commits. Job folder `opus_r5/r5c/`, scratch
`F:\opus_scratch\r5\r5c\` (exes in `exe\`, sha256 in `EXES.txt`). Machine exclusive: no (live gates, NNUE training
and self-play the whole time). Every build, test and bench at BelowNormal (Git Bash `nice -n 10`), at most 3 threads
in total, engine runs with Threads <= 3 (1 unless a test says otherwise). No Elo claims; no gate run by me.

Time base: the PC clock reads PST but runs 9 h ahead of GitHub's server clock (`gh api -i rate_limit` Date header,
08:19 GMT at 09:20 Vienna); Vienna (CET, UTC+1) = PC "PST" time - 1 h. Every time below is Vienna.
Job start 09:20 Vienna (3 h cap: 12:20 Vienna).

## 00_baseline

Build (job-spec flags, R5B script `tools/build_r5c.sh`, RECIPE=v3: MSYS2 ucrt64 g++ 15.2, 8 units in parallel with
JOBS <= 3 at BelowNormal, static link):
```
RECIPE=v3 bash opus_r5/r5c/tools/build_r5c.sh "$PWD" /f/opus_scratch/r5/r5c/exe/<name>.exe [-D switches]
# g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -ffp-contract=off -fno-fast-math -march=x86-64-v3 -mtune=znver5 -pthread -static
```
Check: lock `2_build/uci_check.py <exe> --full` (fresh process, Threads 1, Hash 16, OwnBook false).

## OFF identity after every milestone (rule 7)

| after | exe (F:\opus_scratch\r5\r5c\exe) | sha256 | bench d11 / d13 / d16 / d20 / d22 | perft 5 | kiwipete 5 | FMA | result |
|---|---|---|---|---|---|---|---|
| 00 baseline | forge_r5c_off_v3_b7c1772.exe | 01aed2d9... | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK (`logs/identity_off_v3_b7c1772.log`) |
| M1 | forge_r5c_m1.exe | decc0675... | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK (`logs/identity_m1.log`) |
| M3a (v4 path, untested) | forge_r5c_m3a.exe | 60d367f2... | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK (`logs/identity_m3a.log`) |
| M3b (+ tbhits; the gate exe) | forge_r5c_m3b.exe | bf9f6f16... | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK (`logs/identity_m3b.log`) |
| rebuild of the committed tree (LF `git archive` of 1004ed26, 11:25 Vienna) | forge_r5c_final.exe | fb94819d... | 312866 / 862329 / 3024920 / 12389307 / 34048354 | 4865609 | 193690690 | 0 | ALL OK; differs from m3b in 4 bytes (PE timestamp and checksum) (`logs/m5_identity_final.log`, `logs/m5_build_final.log`) |

## M1: N3 hardening (done)

Survey (09:22-09:32 Vienna) of what exists on b7c1772:
- Options: SyzygyPath (string, `syzygy::load`, hash cleared after every load; prints `info string Syzygy: N WDL and M
  DTZ tables, up to K pieces` or `... tablebases off`), SyzygyProbeDepth (1-10), Syzygy50MoveRule (default true),
  IntendedThreefold (check, non-root claim floor at the draw score, no TT cutoffs/stores there), CuckooRep (check,
  upcoming-repetition draw lower bound), HardDeadline (0-1000 ms, watchdog at hard limit + N ms, time-critical).
- Tests already there: tests/syzygy_tests.cpp (empty / missing / junk / truncated / corrupt / partial table folders,
  TB score TT encoding, known answers; real tables via FORGE_SYZYGY_PATH), tests/intended_threefold_tests.cpp,
  tests/cuckoo_tests.cpp, tools/hard_deadline_regression.py (watchdog vs a starved search, forge_debughooks).
- Gap for N3: nothing tests the three N3 options together, IntendedThreefold x CuckooRep, the DTZ root filter near
  the 50-move limit with real 3-4-5 tables, a SyzygyPath change between searches, or the HardDeadline timing of
  `go movetime 50` / `go wtime 100 winc 0` / `go infinite` + `stop` with tables loaded. A wrong SyzygyPath only prints
  "0 WDL and 0 DTZ tables, up to 0 pieces".
- Tables: `D:\grok-pc-data\dwqww\.claude\worktrees\syzygy345` holds 290 files (145 WDL + 145 DTZ); sha check in M2.

What changed (OFF-identical; files: `tests/r5c_n3_tests.cpp`, `tools/r5c_n3_uci.py`, `CMakeLists.txt`, `src/uci.cpp`):
- Engine: one line in the SyzygyPath handler. A non-empty path that loads no table at all now also prints
  `info string SyzygyPath: no tablebase found in "<path>", tablebases off` (the existing
  `info string Syzygy: 0 WDL and 0 DTZ tables, up to 0 pieces` line stays as it was; `tools/uci_options_regression.py`
  matches it exactly). Only reached with a non-empty SyzygyPath, so nodes, perft and the default output are unchanged.
- `tests/r5c_n3_tests.cpp` (CTest `forge_r5c_n3_tests`, real tables via FORGE_SYZYGY_PATH):
  1. IntendedThreefold x CuckooRep, all four combinations: mate in 1 / 2 / 3 at depth 20 give the OFF mate score
     exactly, on a cold and a warm TT; the losing side plays the threefold claim (g8h8, score 0, 64 nodes, the same in
     two runs); the winning side with only repetition chances keeps a winning score (1331-1470 cp, warm TT too).
  2. With the 3-4-5 tables and both draw options on: KQRvK root reported 31870 (TB win; search score 1744, the report
     uses `display_score`); a 6-piece root makes 69 in-search WDL probes; the three blessed losses of the reference are
     reported -2 with Syzygy50MoveRule=true and -31870 with false; DTZ root filtering on 486 reference rows (depth 4):
     every bestmove legal, wins kept, draws not lost, and on 176 wins with the 50-move counter one ply short of the
     fastest win, the chosen move still wins in time with Syzygy50MoveRule=true (dtz + counter <= 101) and wins with
     false.
  3. Wrong paths (missing drive, a folder without tables, separators only) load nothing and every search answers; a
     reload after a wrong path gives the first result again (score 1765, 10680 nodes both times); the empty path gives
     the same startpos depth-10 search as a process that never loaded tables.
  Result: **1397 checks, 0 failures** with the tables (`logs/m1_r5c_n3_tests_local.log`), **52 checks, 0 failures**
  without (`logs/m1_r5c_n3_tests_notables.log`, what CI runs).
- `tools/r5c_n3_uci.py` (CTest `r5c_n3_uci`, CI slack 150 ms): info strings for a missing and an empty folder, `<empty>`
  = off and `bench 13` = 862329 afterwards, real tables 145 / 145 / 5 pieces; then HardDeadline=10 + IntendedThreefold
  + tables, Threads 1, five positions (start, middlegame, KQRvK, a blessed loss, a 6-piece root) x 5 reps x three go
  modes: exactly one legal bestmove each time, slowest go->bestmove 40.8 ms for `go movetime 50` (deadline 50 ms),
  7.3 ms for `go wtime 100 btime 100 winc 0 binc 0` (hard limit 20 ms, deadline 30 ms), 0.7 ms from `stop` for
  `go infinite` (PC run with 5 ms slack: **PASS**, `logs/m1_r5c_n3_uci_pc.log`).

Findings (no bug fixed in the search):
- No wrong draw score and no mate-score corruption in any combination. CuckooRep changes when a mate is found: with
  it on, the KR mate in 3 (`4R3/8/8/k2K4/8/8/8/8 w`) is reported from depth 14, with it off from depth 10 (`go depth
  24`, both report mate 3 afterwards); its draw bounds on the rook shuffles reorder the moves. Not a correctness
  problem, but a CuckooRep gate should know that shallow mates can come a few plies later.
- In TB roots the search score and the reported score differ by design (search 1744 vs reported 31870): tools that
  read `SearchInfo.score` directly must apply `syzygy::display_score` as the UCI layer does.
- The watchdog never had to fire in these runs (the search answered on time by itself); the starved-search case is
  covered by the existing `hard_deadline_regression` (forge_debughooks).

M1 exe `forge_r5c_m1.exe` (v3 recipe, M1 tree): 0 warnings, FMA 0, identity ALL OK (`logs/identity_m1.log`).

## M2: N3 gate pack (in progress; paused for R5D)

- Tables: 290/290 files sha256 OK against opus_r3/R3-1L/syzygy345.sha256 (`logs/m2_syzygy345_sha256_check.log`;
  the checked-out sha list has CRLF, so the check uses an LF copy).
- Book `n3_endgame_book.epd`: 100 of 151 positions with 6-9 pieces, no castling, not in check, from
  tests/data/nnue_selfplay_sample_916.txt (`tools/make_endgame_book.py`).
- Prebench of the candidate (SyzygyPath + IntendedThreefold + HardDeadline=10): 313631 / 866959 / 2460490 /
  11465604 / 31972996, perft5 4865609; only SyzygyPath changes bench (`logs/m2_n3_prebench*.log`).
- Smoke 09:39-09:51 Vienna (`smoke_n3.py`, 200 games 5+0.05, Threads 1, conc 2): games 200/200 with 0 illegal,
  0 crashes, 0 time losses, 0 missing bestmoves; verdict FAIL only from the go/stop stress (96 "illegal bestmove"
  problems): **my runner's bug** - the stress checks legality on a board built from startpos + moves instead of the
  FEN opening. Open items for the resume: (1) fix that board and re-run the stress; (2) the engine prints no
  `tbhits` in its info lines (no `tbhits` in src/), so "count TB hits from info output" needs a small engine change
  (print `tbhits N` only while tables are loaded, OFF output unchanged); the smoke counted 0 for that reason.
- Resume 11:00-11:05 Vienna (next to R5D's smoke, 1 thread): (1) `smoke_n3.py` stop stress now builds its board
  from the opening FEN (re-run pending); (2) `tbhits N` = `syzygy::probe_hits` since the search started
  (`SharedSearchState::tb_hits_base`, set by `Searcher::search` before any worker starts), printed in the iteration
  info lines and the SmpBestThread line only while `syzygy::max_pieces() > 0`. `forge_r5c_m3b.exe` (bf9f6f16...,
  0 warnings, FMA 0): OFF identity **ALL OK** (`logs/identity_m3b.log`). UCI check (`logs/m2_tbhits6_*.log`, 6-piece
  root `8/8/4k3/8/2p5/2KR4/P7/3q4 w`, go depth 12): no tables -> 12 info lines, none with `tbhits`; 3-4-5 tables ->
  every info line has it, `tbhits 23` at depth 12. A 4-piece root (`logs/tbhits_*.log`) reports `tbhits 0`, as it
  should: a DTZ-ranked root switches in-search probing off.

## M3: v4 format + engine inference (in progress)

- `tests/r5c_v4_tests.cpp` (CTest `forge_r5c_v4_tests`; standalone build PASS, 54 checks, 0 failures,
  `logs/v4_tests_m3b.log`; CMake build pending): nets built and serialised by the
  test's own FNN4 writer; parser refusals (every header field, size +-1, checksum, both overflow bounds, b_out,
  reserved bytes, short file), `load()` size check and keep-on-failure, scalar forward == the test's int64 reference
  written from FNN4_FORMAT.md == AVX2 on random-game positions for five shapes (H 64..512, KB 1..32, OB 1..16, L2
  1..64, mirror/residual flags) and on a net at the accumulator bound (767 + 32 * 1000 = 32767, 32 pieces).

## M4: exporter + parity (in progress)

- Real J7 checkpoint (read-only): `F:\opus_scratch\fable\fb2\j7\run_l2_60\best.pt` (step 10,035, float holdout b0.6
  0.015417 per its status.json; sha256 9b390b26...). `tools/nnue/export_fnn4.py export` (own code; the trainer's
  model class was read for the tensor names and the forward): factoriser merged into w1, w1/b1/b2 on the trainer's
  fake-quant grid (float32, round half to even), l2w x 1024, l2b x ONE, l2o x 256. Output `j7_best_l2.fnn4`:
  6,325,896 bytes = the FNN4 size formula for KB 8 / H 512 / L2 16 / OB 8, checksum 7e6e69fb36b5b6e0, mirrored,
  standalone (no residual flag), eval_scale 400; nothing clipped; accumulator bound 95 + 32 * 438 = 14,111 <= 32,767;
  largest layer-2 row bound 102,202,761 << 2^31; layer-2 rounding errors at most half a grid step (l2w 0.00049,
  l2b 4.7e-7, l2o 0.0019) (`logs/m4_export.json`).
- Parity, 100,000 positions (`F:\opus_scratch\fable\parity\positions_100k.fen`): engine values from
  `opus_r5/r5c/tools/r5c_v4_eval.cpp` (scalar and AVX2 kernels) vs the exporter's numpy int64 forward read back from
  the FILE: **0 mismatches scalar, 0 mismatches AVX2** (`logs/m4_parity_100k.json`); largest |accumulator| 2,329.
  Float (the trainer's forward with fake-quantised w1/b1/b2 and float layer 2) vs the exact integer value:
  mean 0.96 cp, p99 2.79 cp, max 4.85 cp: the price of not fake-quantising layer 2 in J7. Hashes of the inputs and
  the engine output in `logs/m4_inputs_outputs.sha256`.
- A first engine smoke passed the net as an MSYS path (`/f/...`): the engine refused it loudly
  (`info string ERROR NNUE v4: cannot open ...; the default net evaluates`) and bench stayed 862329, the designed
  failure path; the re-run with the Windows path is below.
- Engine with the net (`forge_r5c_m3b.exe`, Threads 1): `info string NNUE v4: loaded ...: H512 KB8 OB8 L2 16
  mirrored standalone eval_scale 400 checksum 7e6e69fb36b5b6e0, kernel avx2` and `info string NNUE v4 active: ...`;
  `go depth 12` from the start position: score cp 20, bestmove e2e4; bench 13 with v4: 746,646 nodes in all 4 runs
  (deterministic), default 862,329 (`logs/m4_bench_nps.log`, `logs/m5_engine_smoke.log`).
- 50-game legality smoke, v4 net (ON) vs the default net (OFF), same exe, Threads 1, 5+0.05, 8-move book
  (`smoke_n3.py`, `logs/m4_v4_smoke_summary.json`): **PASS**, 50/50 games, 0 illegal, 0 crashes, 0 time losses,
  0 missing bestmoves, 0 error lines, stop stress 20/20 with 0 problems; 29 mates, 18 threefold, 3 insufficient
  material. (ON scored 12.5/50: a 1-hour prototype net at 0.59x speed; not a strength measurement.)

## M5: handoff

What a long L2=16 run needs (Fable's trainer `tools/nnue/fable_nnue_train.py`, branch `fable-fb2-j7`; its files and
runs are read-only for me):
- The run_l2_60 configuration (`F:\opus_scratch\fable\fb2\j7\run_l2_60\log.txt`): `train --pos-glob
  F:/opus_scratch/fable/data/train/fb2_train_*.pos --hce-dir F:/opus_scratch/fable/data/train --hidden 512
  --king-buckets 8 --output-buckets 8 --mirror --l2 16 --eval-scale 400 --steps 93000 --batch 8192 --lr 1e-3
  --lr-schedule cosine --lr-final 5e-5 --warmup-steps 500 --blend-schedule linear --blend-start 0.9 --blend-end 0.6
  --exact-pos/--exact-hce <fb2_holdout_200k> --ckpt-every-minutes 15 --ckpt-at-pause --max-minutes 60` (standalone,
  factoriser on). It paused at step 10,035 of 93,000 (82M positions in 60 min, 22.8k positions/s on one thread): the
  rest of the cosine schedule is about 9.3 hours on one thread. `--resume <run>/ckpt.pt` needs the same `--out`
  (trainer rule), i.e. Fable's folder: the owner decides, or copies the run folder first (FB2 `move_run.py` pattern).
- Fix before the long run: fake-quantise layer 2 in the trainer (`quantised()`: l2w to 1/1024, l2b to 1/ONE, l2o to
  1/256, as w1/b1/b2 already are). Today the exported integer net differs from the trained float by mean 0.96 cp,
  max 4.85 cp (M4 parity); with fake quantisation the gap would be the truncating divisions only.
- After training: `export_fnn4.py export <ckpt> <net.fnn4>`; `export_fnn4.py holdout <net.fnn4>
  F:/opus_scratch/fable/data/holdout/fb2_holdout_200k.pos` (exact integer score); `r5c_v4_eval` + `export_fnn4.py
  parity` on positions_100k.fen (must be 0 mismatches); engine smoke with `NNUEv4File` + `NNUEv4=true`.
- Holdout rule: gate only if the exact holdout b0.6 is below AL1's 0.014417 on the same 200k rows. J7 best (step
  10,035), exported FNN4 scored exactly (`export_fnn4.py holdout`, `logs/m5_holdout.json`): **b0.6 0.015422**
  (b0.8 0.007314, b1.0 0.004636); the trainer's float metric for the same checkpoint was 0.015417 / 0.007313 /
  0.004639, so the exporter, the FPOS reader and the loss agree with Fable's scorer to 5e-6. 0.015422 > 0.014417:
  **not gate-eligible**. Then SPRT [0,10] normalized, cap 3000, the v4 net (candidate options
  `option.NNUEv4File=<path>`, `option.NNUEv4=true`) vs the same exe at its defaults: a string option again, so the
  N3 runner change (N3_GATE_SPEC.md) is needed here too.

NPS cost of the v4 forward (advisory, loaded PC, Threads 1, `logs/m4_bench_nps.log`): bench 13 0.91-0.94 Mnps with
the J7 net vs 1.52-1.60 Mnps default, about 0.59x. The v4 path rebuilds both accumulators at every evaluation; the
incremental update and refresh cache of v3 (fable-nnue-arch) are the first engine task before a v4 net can play at
equal time.

Open risks: (1) the speed above; (2) the layer-2 quantisation gap until the trainer fake-quantises it; (3) J7 trains a
standalone net (no HCE residual), the AL1 net is residual; (4) the gate runner has never passed a string option
(0 of 63 RUN_INFO.json files); (5) v4 was exercised with Threads 1 only (the evaluation keeps no per-worker state and
reads the loaded net read-only, so more threads add no shared writes).

## What to gate first

1. **N3** (`N3_GATE_SPEC.md`, `n3_gate_spec.json`): `forge_r5c_m3b.exe` with SyzygyPath (3-4-5) + IntendedThreefold +
   HardDeadline=10 on the candidate only, vs the same exe at its defaults, 10+0.1, SPRT [0,10] normalized, cap 3000.
   Needs the runner change described there (a string option for the candidate, also in its pre-gate bench).
2. No v4 gate yet: the J7 net is a 1-hour prototype (holdout rule not met, see M5) and the v4 forward costs about
   40 % NPS. Order of work for v4: trainer fake-quantises layer 2 -> long run -> exact holdout below 0.014417 ->
   incremental accumulators in the engine -> gate (same string-option runner change).

## What I did not finish

- No v4 incremental accumulator update (every evaluation rebuilds both accumulators); NPS 0.59x of the default.
- The v4 path is exercised with Threads 1 only (unit test, parity, smokes); no Threads >= 2 v4 games.
- The trainer-side fake quantisation of layer 2 is a proposal for Fable's trainer, not done (not my file).
