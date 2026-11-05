# Report-back: Code Review CR_OPUS_SPEED_TOOLS_637B_20261105 (opus-speed-20261105 @637be9af)

Received from the owner at ~09:33 PC clock (Vienna) on 2026-11-05 as pasted text. The note file itself is not on this
PC (searched C:\, D:\, F:\ by name, 09:34-09:36), so the 3 LOW notes were not visible here: see the last section.
No speed candidate has been called valid before these fixes (none was called valid at all so far).

## BLOCKER - pin DIFF was fail-open (build_variants.ps1 :188-192 at 637be9af; speed_pack accepted DIFF)
- Fix, build_variants.ps1: a pin table that yields no value throws; any quick-pin DIFF writes `RESULT FAIL <variant> :
  quick pins DIFF` into SUMMARY.txt, writes the FAILED marker, prints `FAIL <variant> : quick pins DIFF ...`, prints NO
  `EXE` line and exits 1. With -Twice a failed pc1 stops the variant (no pc2). The exe stays in its folder for analysis
  only (no deletes on this PC); the FAILED marker says "do not use".
- Fix, speed_pack.ps1: stops with exit 3 unless build_variants exits 0, prints a REPRO line AND every `EXE` line says
  `pins OK` (defence in depth: the bit-exact L1 would also stop it).
- Worst case at 637be9af (found while fixing, already corrected in f0c2da07 at 09:10): `[ordered]@{11=..}[11]` reads
  by position, so the wanted pins were empty and EVERY build printed `pins DIFF` - and still `RESULT PASS`.
- Test: `opus_speed/tests/test_cr_637b.ps1` T1 (mutant HistoryMax 16384 -> 16000: exit != 0, FAIL line with the pin
  DIFF, no EXE line, FAILED marker, SUMMARY RESULT FAIL and never RESULT PASS), T2 (positive control: the lock source
  builds with pins OK, exit 0, RESULT PASS), T3 (speed_pack on the mutant: exit 3, no candidate file). Result: see
  "Test run" below.

## SHOULD 1 - the ABBA summary must not overwrite earlier runs; a new file per run
- `Write-OspdLf` (uci_lib.ps1) now refuses to overwrite an existing file unless -Force (no tool passes -Force).
- abba.ps1 writes `summary_<run id>.txt` (run id = time + pid) besides `summary.txt` in its new folder, prints the run id
  as the first summary line and appends one line per run to `F:\ospd\abba\abba_history.log` (append-only).
- speed_pack.ps1 writes `candidates\<name>_<run id>.md` when `candidates\<name>.md` already exists.
- Test T4 (overwrite refused, first content kept; abba writes the run-unique name).

## SHOULD 2 - L3 FENs need the side-to-move field
- Confirmed and worse than a style issue: `fens_12k.txt` holds placement-only lines; the lock answers each with
  `info string invalid FEN: FEN must contain six fields` and keeps searching its previous position, so the L3 results
  reported before ~09:30 (`2000 / 2000 identical`) compared one position 2,000 times. They are WITHDRAWN (the cache
  file was renamed `*.INVALID_placement_only_fens`).
- Fix: `ConvertTo-OspdFen` completes any FEN to six fields (placement-only -> side to move `w`, castling `-`, ep `-`,
  clocks `0 1`); the default L3 set is now `data/fens_12k_v2.txt` (the same 12,000 placements with their real side to
  move, castling, ep and clocks; md5 e7dbf2c8); both FEN drivers (bitexact L3 and the go-workload trainer) fail on any
  `info string ... invalid` line; L3 refuses a degenerate reference (fewer than n / 10 distinct results).
- The `lp_w12k` PGO-workload build made with the old file is marked INVALID and rebuilt.
- Test T5 (completion rules, bad FEN throws, the lock accepts a completed FEN, a raw placement-only FEN is detected).

## SHOULD 3 - the 300-position TSV must record the source PGN md5
- `pgn_positions.py` writes two `#` header lines (source path + md5, generator settings) and refuses to overwrite;
  every reader skips `#` lines. `data/game_positions_300.tsv` regenerated: data lines identical to before, file md5
  c00eb127 (source `gate_stB_lmrcapvictim1_vs_AL1.pgn` md5 f25a04e2).
- Test T6 (header md5 = md5 recomputed from the named PGN).

## Further defects found during the fix (own review, NOT independent)
- speed_pack.ps1 did not parse under Windows PowerShell 5.1 at all (`"$Name:"` / `"$bxRc:"` read as drive-qualified
  variables). Fixed with `${Name}:`; new `tools/ps_parse_check.ps1` parses every .ps1 with the 5.1 parser (0 errors now).
- (fixed in f0c2da07) L1 / L2 lines were swallowed by `$null = Verdict-Line`; list parameters passed through `-File`
  arrived as one comma-joined string; native stderr (`lto-wrapper` warning) aborted builds under `Stop`.
- ABBA protocol: the A/A runs showed per-slot differences of ~1-2 % (in one run the middle slots, always arm B in plain
  ABBA, were faster), so abba.ps1 now alternates ABBA / BAAB rounds by default (`-Order ABBA` keeps the literal order)
  and records the process CPU time of the bench window as a second metric. Balanced A/A at d20 (09:24-09:31): wall
  median 1.0066 [0.9968, 1.0111] sd 0.99 %/round, cpu 1.0050 [0.9940, 1.0087] sd 1.02 %/round.

## Regressions found after the fix commit (both mine, fixed in the next commit)
- My SHOULD 1 edit wrote the history-log path through a Bash heredoc that collapsed `\\`, so `abba.ps1` held
  `F:\ospd<BEL>bba<BEL>bba_history.log`: the first queued ABBA run after it (o3, 09:41-09:47) ended with "Illegal
  characters in path" AFTER writing its runs.csv and summaries (data intact, the queue marked it ERROR). Repaired with
  the new `tools/ctrl_char_check.py --fix-bell-paths`; a scan of all job files finds 0 control bytes now.
- `build_variants.ps1 -Twice` never printed REPRO: its log helper wrote to the PowerShell output stream inside
  `Build-One`, so the function returned [log strings..., build object] and the pc1 = pc2 check never saw exactly two
  builds; speed_pack then stopped with "BUILD FAILED or NOT REPRODUCIBLE (rc 0)" although pc1 = pc2 (b2_nnue_zmm:
  809f03df both sides, pins OK). The helper now writes straight to stdout. T3 of the CR test only covered the failing
  side; the lock-vs-lock pack (Job A test 1) is the positive end-to-end check of `-Twice`.

## The 3 LOW notes
Not visible here (the note file is not on the PC). Please paste them; each will be fixed with a test and listed here.

## Test run
- `powershell -NoProfile -ExecutionPolicy Bypass -File opus_speed\tests\test_cr_637b.ps1` on the fixes of commit
  54fa02b5 (CPUs 0-1, Idle): run 20261105-094413-13436, 09:44:13-09:45:56, **13 / 13 PASS, exit 0**. Log
  `opus_speed/logs/test_cr_637b_20261105-094413-13436.log` (md5 cb58826e). Mutant build exit 1 with `FAIL o3 : quick
  pins DIFF`, lock build `pins OK` exit 0, speed_pack on the mutant exit 3 without a candidate file, overwrite refused,
  completed FEN accepted by the lock (bestmove e3d2) while the raw placement-only FEN is detected as rejected, TSV
  header md5 = f25a04e2 recomputed.
- A first run at 09:40:45 gave the same 13 PASS lines but printed `12 / 13` and its failure count was wrong: the
  counter matched the word FAIL inside T1b's description. Fixed to count the status field only; the run above is the
  record.
