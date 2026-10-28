# S32 [Sol leftover] Self-play datagen v2 (in-engine, direct .pos/.hce) — DONE

Branch `opus-sol-S32` = `d4f4312` + `0d99f02` cherry-picked (`af007bc1`) + `a778ef2d` (engine + tests + evidence) +
`2c0d553b` (CI evidence, `[skip ci]`). Patch: `forge_sol_S32_datagen_20261027.patch` (6 files, +1214 lines).
Machine exclusive: **no** (gate, NNUE training, self-play and other agents running; all runs at IDLE on CPUs 4-11,
never 0-3 = training or 12-15 = production self-play). No Elo or engine-speed claim. Sol left no S32 files
(`git ls-tree -r --name-only 17aa0cae | grep -i S32`: none). Work and results by a sub-agent; this report text is its
hand-back.

## 1. What was done
- `forge datagen ...` (build switch `FORGE_DATAGEN`, **default OFF**): fixed-node (or fixed-depth) self-play inside the
  engine process, random opening plies, win adjudication (default 2000 cp x 4 plies, as forge_selfplay.py), optional
  draw adjudication (off by default), records written directly as the v3b trainer's `.pos` (FPOS v1) + `.hce`
  (FHCE v1), plus `.info`, a `.games` log and optional text. Rules/filters/labels mirror forge_selfplay.py.
- Multi-process safety: exclusive-create `.part` files, publish without replace, `.pos` last; the prefix is claimed by
  `<prefix>.games.part`, so a reused prefix fails before writing (exit 1).
- `--convert`: "FEN | score | result" text -> `.pos/.hce` through the same writer (fen2bin + hce_dump in one step).
- The default engine is untouched: `datagen.cpp` lives in `forge_core` but is linked only into the switch build;
  CMake always builds `forge_datagen` (= forge with the switch) so CTest/CI exercise the path.

## 2. Acceptance

| # | line | result | evidence (logs/ unless noted) |
|---|---|---|---|
| 1 | flag off = standard pass | PASS | Default PC build (no switch) vs lock exe 5d4df7f1: `cmp -l` 5 bytes (offsets 137-139 PE timestamp, 217-218 PE checksum), `uci_check --full` ALL OK, FMA 0 (`build_default.log`, `uci_check_full_default.log`). Datagen build (switch on): bench d11/13/16/20/22 = 312866/862329/3024920/12389307/34048354, perft5 4865609, kiwipete 193690690 ALL OK, FMA 0, 0 warnings (`build_datagen.log`, `uci_check_full_datagen.log`). CI: Linux default forge sha256 6635d4d1 = lock build |
| 2 | CTest + ASan/UBSan/TSan | PASS | PC CMake (box flags, JOBS=1): 15/16, only `forge_tests` with the 4 known lines, `check_known_failures` PASS; no new compiler warnings (the 6 are the lock's `search.cpp` -Wconversion lines) (`ctest_cmake.log`). CI: section 4 |
| 3 | unit + CLI tests | PASS | `forge_datagen_tests`: 46 PASS / 0 FAIL — FPOS nibble layout, meta bits, SplitMix64 reference, terminal rules (mate both colours, stalemate, KBvK, fifty, max-ply, threefold), determinism, clear() per game, record/FEN/HCE consistency, side-to-move signs, mate labels, win/draw adjudication, shard writer (3+3+1, headers, column layout, no overwrite, stale `.part` blocks), text round trip, usage errors (`unit_tests_run1.log`). `datagen_cli_tests.py`: 11 PASS (`cli_tests_pc.log`) |
| 4 | same seed -> same sha256 | PASS | 25 games, 5000 nodes, seed 20261027, run twice: `.games`, `_000.pos`, `_000.hce`, `_000.info`, `_000.txt` byte-identical (pos sha256 6ff0de3d…) (`determinism_runs2.log`, `run_outputs.sha256`); CLI test: another seed differs, two concurrent processes = sequential runs |
| 5 | v3b loads a 1M-position sample (RAM and mmap) | PASS | The v2 writer (`--convert`) on S20's real lock self-play text (1,110,116 lines, sha256 ae014eb3…): `.pos` **byte-identical** to `fen2bin` and `.hce` **byte-identical** to `hce_dump` built at 1ab50b2d (`m1_*.log`). v3b's own `load_set` and `load_set_mmap` (renamed copy, sha256 5cebba4d… = `train_resid_v3b.py`): n = 1,110,116 both, RAM == mmap on 200k rows, 4 batches through `make_batch`/`pack_batch` equal and finite (`v3b_load_1M.json`). Datagen's own output: 2,500-record shard and a 2-shard set (multi-file path) load in both modes. No new "adopted running job" line in supervisor.log (7 before and after) |
| 6 | sign conventions | PASS | (a) **Parity**: all 25 games replayed by forge_selfplay.py's own `play_game()` over UCI with the **lock exe** (forced openings): 25/25 identical — every move (3,365 plies), every recorded (FEN, cp) (2,500), every result (`parity_lock.json`). (b) Datagen's direct `.pos` == `fen2bin` of its text and `.hce` == `hce_dump`@1ab50b2d (2,500 records). (c) Unit tests: rook-up positions give the side-to-move sign in 100% of records for both colours; the flipped-sign / flipped-stm mutants fail. (d) Labels on 1.11M: sign(score) == sign(hce) 99.62% where both >= 100 cp; White >= +300 -> not losing 99.85%; <= -300 -> not winning 99.92% |
| 7 | positions/s >= 1.5x selfplay.py, or explain | MET (advisory) | End-to-end vs forge_selfplay.py (1 worker) median **1.58x** per wall second and **1.54x** per CPU second (pairs 1.48-2.51x wall, 1.42-1.64x CPU); same games (parity run) **2.02x** wall / **1.86x** CPU. Loaded PC, IDLE (`throughput1.json`, `parity_lock.time.json`) |
| 8 | safe with several processes | PASS | Reused prefix -> exit 1, first run's files unchanged (sha256); two concurrent processes in one folder write exactly the sequential runs' bytes; existing shard never overwritten; a leftover `.part` blocks its name |
| 9 | planted bug | PASS | m1 (score sign) -> 2 FAIL lines, m2 (side-to-move bit) -> 4 FAIL lines (`mutants.txt`, `mutant_m1.log`, `mutant_m2.log`) |
| A | default OFF, IDEA_SOURCE, no Elo claim | PASS | `FORGE_DATAGEN` default OFF in CMake and the box recipe; `IDEA_SOURCE.md` |

### Throughput table (5000 nodes/move, 8 random plies, max ply 300, win adj. 2000 cp x 4, Hash 16, Threads 1; IDLE, CPUs 4-11; machine exclusive: no)

| block | tool | games | positions | searched plies | wall s | CPU s | pos/wall-s | pos/CPU-s |
|---|---|---|---|---|---|---|---|---|
| 0 | datagen v2 | 30 | 2,385 | 3,401 | 10.15 | 9.53 | 235.0 | 250.2 |
| 0 | forge_selfplay.py | 30 | 3,065 (3,006 dedup) | – | 20.61 | 17.38 | 148.7 | 176.4 |
| 1 | datagen v2 | 30 | 3,070 | 4,245 | 13.67 | 11.13 | 224.7 | 276.0 |
| 1 | forge_selfplay.py | 30 | 2,813 (2,729) | – | 31.37 | 16.77 | 89.7 | 167.8 |
| 2 | datagen v2 | 30 | 3,040 | 4,087 | 12.40 | 10.88 | 245.1 | 279.5 |
| 2 | forge_selfplay.py | 30 | 3,429 (3,288) | – | 20.77 | 18.86 | 165.1 | 181.8 |
| same 25 games | datagen v2 | 25 | 2,500 | 3,365 | 7.86 | 7.59 | 318.0 | 329.2 |
| same 25 games | play_game() over UCI, lock exe | 25 | 2,500 | 3,365 | 15.85 | 14.09 | 157.7 | 177.4 |

forge_selfplay.py positions = its "eligible" count before its persistent dedupe (deduplicated in brackets); its CPU
time is the whole process tree (parent + worker + engine). Reference: S20's lock self-play with the same tool,
1 worker: 587,374 positions/h = 163/s (`F:\opus_scratch\sol_s20\stageA_selfplay.log`).

## 3. Findings
- **Where the gain comes from:** for the same 3,365 plies the UCI route costs 14.09 CPU-s vs 7.59 (+1.93 ms CPU per
  ply): python-chess parses every `info` line (PVs validated on a board copy), legal-move generation and game-state
  checks run in Python, the engine re-parses the whole `position startpos moves ...` list each move and starts a thread
  per `go`. The 5000-node search itself is ~2.3 ms CPU per ply. forge_selfplay.py's "search=~90%" duty cycle is
  go-to-bestmove wall time and does not isolate engine CPU.
- **HCE channel:** AL1 and 1ab50b2d have identical HCE sources (eval.cpp, eval_params*, board*, bitboard*), so in-engine
  `.hce` equals the pipeline's `hce_dump` byte for byte (verified on 1.11M + 2,500 records).
- **Datagen exe search speed (advisory):** paired bench d16 A/B, lock vs datagen exe: -4.25% and -4.88% CPU NPS (CIs
  -6.52..-1.98 and -8.51..-1.25; nodes identical every run); A/A control lock vs default build (same code): +1.45%
  (CI -1.97..+4.86). Hot functions are at identical addresses in both exes (`nm`); `.data/.rdata/.bss` move. Cause not
  isolated. It does not affect the engine (default build = lock binary) and is already included in the throughput numbers.
- Records per searched ply 0.70-0.74 (captures, checks, mate scores and |score| > 3000 skipped, as before).
- Not in datagen v2: dedupe across games/files (forge_selfplay.py keeps a persistent SQLite set; ~2-4% duplicates in
  30-game blocks). A merge/dedupe step (S40) or a holdout split by `.games` is the place for it.
- Process: copying `fen2bin.exe`/`hce_dump.exe` from F:\forge_nnue_train was denied by the permission system; reference
  copies were built from the archived sources (same sha256 as the PC's), hce_dump linked against the 1ab50b2d tree.

## 4. CI
opus-ci 40508819820 on a778ef2d: release (job 122205009359), asan (122205008990), tsan (122205009348): all success.
Release: Linux forge sha256 6635d4d1… (= the lock's Linux build, as recorded by S13), FMA 0, uci_check --full ALL OK.
CTest 15/16 in all three modes, only forge_tests (4 known lines), known-failure check PASS; forge_datagen_tests and
datagen_cli_tests pass (ASan 3.45 s / 7.97 s, TSan 15.2 s / 33.4 s); no ASan/UBSan report; TSan 0 reports
(`logs/ci_40508819820_summary.log`).

## 5. Left / UNVERIFIED
- The PC's production generator setup (engine `C:\...\nnue\forge.exe` sha256 00e4178c…, 2 workers on CPUs 12-15) was
  not run or compared: it must not be disturbed. The comparison uses the same tool with the lock exe. UNVERIFIED.
- The 1M v3b load used converted real self-play text (the brief caps datagen's own sample: ≈200 datagen games and
  115 forge_selfplay/UCI games in total, at most 30 per block). A 1M sample generated by datagen v2 itself: not
  produced (UNVERIFIED; same writer, byte-identical to fen2bin/hce_dump).
- Throughput is from a loaded PC (advisory); quiet-machine and multi-worker scaling numbers are not done.
- No training on datagen v2 data; no strength claim. Spec input `h256tools/selfplay.py` is missing on the PC.
