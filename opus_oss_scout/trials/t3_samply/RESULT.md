# T3 samply profile - RESULT

Tools: samply 0.13.1 (MIT OR Apache-2.0) for import and processing; Windows Performance Recorder (`wpr.exe`, built into
Windows 11) for recording; llvm-symbolizer from llvm-mingw 20261104 with the T2 PDB for symbols; own
`tools/t3_samply_top.py` for the table. Commands: CMDS.md (updated below). Hashes: SHA256SUMS.

## What worked and what did not
- `samply record` **does not run here**: samply 0.13.1 drives `xperf` on Windows ("Could not find an xperf
  installation", `logs/samply_record_xperf_missing.log`). xperf ships only with the Windows ADK (Windows Performance
  Toolkit), a system install that this job may not do.
- What works without any install:
  - Record: `wpr -start CPU -filemode` -> run the program -> `wpr -stop trace.etl` (built-in WPR, admin).
  - Import: `samply import --save-only --symbol-dir <pdb dir> -o profile.json.gz trace.etl`. The 354 MB ETL was
    imported in 3.6 s.
  - Table: `t3_samply_top.py` aggregates the leaf samples of one process and symbolizes them with
    `llvm-symbolizer --obj <exe> [--pdb <pdb>]` (VA = image base 0x140000000 + RVA).
  - `--unstable-presymbolicate` wrote no `.syms.json` on import, so the own symbolization step is needed for a
    table without a browser. The interactive way is `samply load profile.json.gz`, which serves the profile to the
    Firefox Profiler on localhost.
- WPR records **system-wide**: for ~6 s (20:07:04-20:07:10 PC clock) every process was sampled at 1 kHz, including
  the live gate engines. This is a passive kernel sampler with small overhead; it is disclosed here and was not
  repeated. A side effect: the same trace holds a real-game profile of the lock in the running gate (table 2).

## Table 1: bench 20 of the node-identical clang build (forge_m2use_lsx.exe, PDB, inlined frames available)
4,872 samples (1 ms), 98.7 % in the program. Full table: `logs/hotspots_bench20_clang_m2use.md`.

| Physical function (after inlining) | % of samples | Inlined hot spots inside it (innermost function, % of samples) |
|---|---|---|
| `Worker::search` | 36.6 | `Worker::search` itself 8.4, `MovePicker::pick_best` 4.2 (+ its lambda 1.3), `Move::operator==` 3.4, `MovePicker::next` 2.0, `quiet_history_sum` 1.7, `Board::gives_check` 1.5, `Board::key_after` 1.1 |
| `evaluate_position<false>` (HCE) | 20.4 | `evaluate_pieces` 6.4, `evaluate_king` 2.6, `std::__countr_zero` 2.2 (bit loops), `Evaluator::update_runtime_psqt` 1.4 |
| `Worker::qsearch` | 12.9 | `corrected_eval` 2.1, `static_evaluate` 1.4 |
| `Board::generate_pseudo_legal` | 6.3 | magic lookups 1.2 |
| `nnue::evaluate` | 4.6 | plus `nnue::update` 5.1 and `Accumulator::add` 2.1, which are inlined into search / make_move paths |
| `Board::see_ge` | 4.2 | |
| `TranspositionTable::probe_owned` | 3.1 | `probe_body` 1.1 |
| **`std::sort` internals** (`__introsort_loop` 2.2 + `__final_insertion_sort` 2.6) | **4.8** | the MovePicker's `std::sort` of the remaining moves (search.cpp:632) |
| `MovePicker::generate_quiets` / `generate_evasions` / `Board::has_legal_move` | 1.7 / 1.2 / 1.2 | |

## Table 2: the lock exe in the live gate games (forge_ltopgo_x_al1s198_trial_w6.exe = 4181A589, 10+0.1, Threads 2)
14,941 samples from the gate's lock processes (31 threads) in the same 6 s. Symbols come from the exe's COFF symbol
table (no inline information). Full table: `logs/hotspots_lock_in_live_gate.md`.

| Function | % | | Function | % |
|---|---|---|---|---|
| `Worker::search` | 23.0 | | `Board::generate_pseudo_legal` | 6.8 |
| `evaluate_position<false>` (HCE) | 18.6 | | `Board::see_ge` | 4.4 |
| `Worker::static_evaluate` (incl. inlined net eval) | 15.3 | | `std::__introsort_loop` + `std::__insertion_sort` (MovePicker sort) | 3.6 |
| `MovePicker::next` | 11.7 | | `Board::make_move` | 2.1 |
| `Worker::qsearch` | 11.2 | | `pthread_spin_lock` (Threads 2) | 0.03 |

## Compared with R7 (older engine, Linux perf): HCE eval 14.4 %, MovePicker 10.9 %, TT probe 10.7 %
- HCE is larger now: 18.6-20.4 % physical.
- The move picker is about the same: 11.7 % in games for `next` plus 3.6 % sort.
- The TT probe dropped a lot (3.1 % + 1.1 % in the bench build), in line with the speed job's TT_NOTLS / NZM changes.

## Speed leads from the profile (for the Coder / speed crew; none measured here)
1. **`std::sort` in the move picker: 3.6 % (games) to 4.8 % (bench).** A specialised insertion / partial sort of the
   remaining moves could be faster. Because tie order changes node counts, only a replacement that reproduces
   libstdc++'s exact order is "speed-only"; anything else is a new lock. That ties in with T2's finding: a stable,
   library-independent sort would also make MSVC / libc++ builds node-identical.
2. **`Move::operator==` at 3.4 % self** (bench build, innermost): if Move compares field by field, one 32-bit compare
   (as in the hunt's H5 MOVE_STORE32) may be bit-exact and cheaper.
3. **HCE `evaluate_pieces` (6.4 %) and `std::__countr_zero` bit loops (2.2 %)** are the largest single eval costs.
