# Patch review QA tests on the six stacks (speed job follow-up, 2026-11-05)

> Note (CR leftovers, 2026-11-05 19:47 PC clock, start tip 00d19e56): `tools/patchrev_qa.py` now takes the LIVE lock
> trial_w6 as LOCK (sha256 4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0,
> `F:\ospd\packs\trial_w6\forge_trial_w6.exe`). The results of record below were run with LOCK = FD3A5190 (14:13-14:53)
> and were not re-run. Since trial_w6 is in the default STACKS, a default run now also compares the lock with itself.

Owner Couns. Branch `opus-speed-20261105`, follow-up from tip c845d886 (first command 14:13:45 PC clock). The patch
review (`REVIEW_PATCHES_INDEPENDENT.md` section 4) listed tests the job had not run; they ran here on stack_w1, stack_w2,
stack_w3, stack_w4, stack_w5 and trial_w6 against the lock FD3A5190. These are the coordinator's own checks (NOT
independent). **No lock is claimed**; no search / eval code changed (the only engine-source edits are in verify copies:
poison and mutant builds, never for QA). Placement: CPUs 0-3 only (checks on 0x3 / 0xC Idle, the soak on 0xF Idle), the
three idle PIDs 11168 / 7524 / 11900 untouched, scratch `F:\ospd\qa2\`, nothing written to D:.

Exes: lock = sha256-checked byte copy `F:\ospd\qa2\bin\lock_fd3a5190.exe` (fd3a5190...); stacks = the pack exes
`F:\ospd\packs\<stack>\forge_<stack>.exe` (05928226 / db957393 / 4b49ae4b / c883623c / 060c578c / 4181a589); their
sanitizer builds from the packs' L4 (`bitexact\san\`, trial_w6 `bitexact_l4_bmi2\san\`); the MSVC ASan build of the lock
source `F:\ospd\packs\b2_nzm1\bitexact\san\ref_asan_msvc.exe`. Python = the venv (python-chess 1.11.2).

## Results

| test | stack_w1 | stack_w2 | stack_w3 | stack_w4 | stack_w5 | trial_w6 | lock (control) | verdict |
|---|---|---|---|---|---|---|---|---|
| 1a game-continuation replay | IDENTICAL | IDENTICAL | IDENTICAL | IDENTICAL | IDENTICAL | IDENTICAL | 2 runs identical | **PASS** |
| 1b ponder / stop protocol | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |
| 1c Threads 2-4 soak (soak only) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** (soak only) |
| 1d poison build (0xA5) | BIT-EXACT | BIT-EXACT | BIT-EXACT | BIT-EXACT | BIT-EXACT | BIT-EXACT | - | **PASS** |
| 1d mutant fails closed | exit 3 | exit 3 | exit 3 | exit 3 | exit 3 | exit 3 | - | **PASS** |
| 1e extreme positions (kit / UBSan / ASan) | PASS | PASS | PASS | PASS | PASS | PASS | PASS | **PASS** |

## 1a - game-continuation replay (`tools/patchrev_qa.py replay`, 14:50:11-14:50:49)
One gate game: index 379 (the first game of `data/game_positions_300.tsv`'s seeded order) of
`F:\forge_push\gate_stB_lmrcapvictim1_vs_AL1\gate_stB_lmrcapvictim1_vs_AL1.pgn` (md5 f25a04e2, read only; no FEN tag, it
starts from the start position), 177 plies, 1-0. Per exe one process: uci, OwnBook false, Ponder false, Hash 32; pass 1 =
`position startpos moves m1..mk` + `go depth 10` for k = 0..177, no ucinewgame, so every later search reuses the warm
subtrees of the earlier ones (the table ages once per search: TT aging / replacement on entries that are hit); pass 2 =
the same 178 searches on the aged table with Hash 1 / Hash 64 / Clear Hash / UseNNUE false / UseNNUE true / Hash 16
every 10 plies; then UseNNUE true and `bench 13`. Result: 356 searches, 4,754 normalised lines (nps / time removed)
per exe, every stack identical to the lock, the lock run twice identical, bench 13 = 862329 on all eight runs, every
bestmove legal, exit 0. `F:\ospd\qa2\replay\final2\results.tsv` (md5 7c06c540), transcripts beside it; two earlier
runs of the same script (14:24, 14:27) gave the same 8 / 8.

## 1b - ponder and stop (`tools/patchrev_qa.py protocol`, 14:50:49-14:51:22)
Per exe one process, Ponder true, OwnBook false: S1 `go infinite` -> 300 ms without a bestmove -> `stop`; S2
`go ponder movetime 300` -> 500 ms without a bestmove -> `ponderhit` (the budget starts there: bestmove after
290-291 ms);
S3 `go ponder wtime 3000 btime 3000` -> `stop`; S4 `go ponder depth 3` -> 1 s (depth 3 done, no bestmove: the engine
must wait) -> `ponderhit`; S5 `go mate 3` on `8/8/7k/1R6/8/8/8/R5K1 w - - 0 1` (built for this test: score mate 3,
bestmove a1a6); S6 `go mate 3` on the back-rank mate `6k1/5ppp/8/8/8/8/5PPP/3R2K1 w - - 0 1` (mate 1, d1d8); S7 20 x
`go movetime 100` on `data/game_positions_300.tsv` rows 0-19 without ucinewgame (worst 91-163 ms); S8 `stop` and
`ponderhit` while idle (ignored, isready answered); `bench 13` = 862329; quit, exit 0. Every bestmove and ponder move legal
(python-chess); no bestmove before stop / ponderhit anywhere; stop answered within 0-3 ms. The deterministic parts
(S4-S6, each after ucinewgame) are identical to the lock's on all six. `F:\ospd\qa2\protocol\final2\results.tsv` (md5
0a60f0ad). (The first run, 14:26, also passed 7 / 7; its latencies used `time.monotonic()`, which ticks in ~15.6 ms on
Windows and once printed -15 ms; the tool now reads `perf_counter` before each command goes out.)

## 1c - Threads 2-4 soak (`tools/patchrev_qa.py soak --mask 0xF`, 14:47:47-14:50:11)
Mask 0xF Idle (CPUs 0-3, read back by the tool), nothing else of this job running. Per exe one process, OwnBook false:
60 game positions (`data/game_positions_300.tsv` rows 20-79) x `go movetime 300`, `setoption name Threads` 2 -> 3 -> 4
before every search, Hash 1 / 64 / 16 / 128 / 32 / 8 every 10 searches, one Clear Hash (search 30); then Threads 1, Hash
32 and 50 FENs (`data/fens_12k_v2.txt` rows 0-49) with ucinewgame + `go depth 13`, `bench 13`, quit. Result: 7 / 7 PASS
- no crash, every bestmove legal (python-chess), worst answer 296-317 ms for movetime 300 (none late), the Threads 1 tail
50 / 50 equal to the lock's cached L3 rows (`F:\ospd\ref\fd3a5190\fens_e7dbf2c8_n2000_d13_ob0.tsv`, md5 3915aea8) and to
the lock's own tail in the same script (the main searcher after helper threads existed: lease / owned flag, histories),
bench 13 = 862329, exit 0. `F:\ospd\qa2\soak\final2\results.tsv` (md5 94098470). **Soak only, not a lock proof**: at
Threads > 1 no node identity is possible, and no TSan exists on this toolchain (CI item). The first soak run
(14:44:34-14:46:58) printed PASS for every exe on these checks and was then marked FAIL by the tool's generic step that
diffed whole transcripts - meaningless for timed Threads 2-4 searches; the tool now compares only the deterministic
tail (as it already did for 1b) and all four tests were re-run with that final version (`final2` folders).

## 1d - poison build and mutant fail-closed (`tests/test_stack_poison.ps1`, `tests/test_stack_mutants.ps1`)
Poison (the review's test 5): `tools/make_poison.py` copies each stack's `src_kit` (all its switches ON) and inserts the
authors' own POISON blocks (from `F:\ospd\src\b2_no_zero_movelists_verify`): 0xA5 fills of `moves_`, `bad_captures_`
and `check_squares_` in the MovePicker constructor, of `quiets_tried` / `captures_tried` after their declaration, and a
poisoning `MoveList()` constructor; each anchor exactly once, the switch must be ON. Plain o3 build with
`-Define FORGE_SPD_NO_ZERO_MOVELISTS_POISON=1` (quick pins fail closed), `g++ -E` of the copy shows the six fills, then
`bitexact_check -Quick -SkipSan`: all six poison exes BIT-EXACT (L1 bench d11-d22 net on + off, L2 perft, L3 2,000 / 2,000
FENs at depth 13 vs the cached lock reference), each followed by the new `LOCK PROOF INCOMPLETE` line (= the edited
script on its BIT-EXACT path). The forge-uci MCP `pin_check` (second harness) also passes on all six (bench d11 / d13 /
d16, perft 5 startpos + kiwipete = the pins). The SPEED2-rebased readers of those slots therefore never read an
unwritten slot on these runs. Runs: 14:17:01-14:33:33 (`F:\ospd\qa2\poison\20261105-141701-7744\`, results md5
1f5b7d4e) and 14:33:36-14:41:07 for stack_w4 / stack_w5 / trial_w6 (`...\20261105-143336-11268\`, md5 aef37163, 12 / 12):
the first run's P3 check said FAIL for those three because its `g++ -E` line lacked `-march=znver5`, so the PEXT
source's own `#error` guard (no `__BMI2__`) fired - the six fills were present and their bit-exact runs passed anyway;
the script was fixed (and its TSV verdict now also requires that exit code) and the three were re-run.
Mutant (the brief's parenthetical): each stack's own LF source and defines (first line of its `pack.log`) + the
move-order mutant `patches/mutant_pickbest_ge.patch` (pick_best tie-break `>` -> `>=`, GNU `patch -p1 -F0`, dry run
first, the mutant line present once) -> `speed_pack -Variant lp_v1 -Quick`: all six exit 3 at the pc1 quick pins (bench
11/13/16 = 309550 / 885689 / 2657981 vs the pins 312866 / 862329 / 3024920), no `abba_d*` folder, no candidate file,
18 / 18 checks (14:41:09-14:44:34, `F:\ospd\qa2\mutants\20261105-144109-10344\results.tsv` md5 6efa662a). Every stack
plus the mutant gives the same nodes as the lock source plus the mutant (the 13:20 test_moveorder_mutant run): stack +
mutant = lock + mutant. Verify builds only, never for QA.

## 1e - extreme positions (`tools/patchrev_qa.py extreme`, 14:51:22-14:51:31)
No extreme list existed in the tree besides the review's three FENs, so the small named set `data/extreme_fens.tsv`
(md5 987a0dfb) was made: set A = 10 positions the lock accepts (the 218-move position, the mass-promotion position, a
high-capture node built here - four queens against a defended pawn chain, all 9 root captures onto defended squares, so
they go to `bad_captures_`; far below its 64 slots, the L1 overflow is not provoked -, an illegal e.p. under a rank pin,
perft positions 3 / 4 / 5, stalemate, checkmate, bare kings), each with ucinewgame + `go depth 8` + `go perft 3`; set R =
6 FENs that are illegal in normal play (nine pawns, castling right without a rook, side not to move in check, pawn on
rank 8, adjacent kings, e.p. square without its pawn): the lock rejects each with its own reason, so each must print
exactly that `info string invalid FEN: <reason>` and `go perft 1` must still count the previous position (5).
20 exes, each one process: g++ group = lock copy, the six stack kit exes and the six UBSan-trap exes (asserts on, `-O1`);
MSVC group = the lock source's MSVC ASan build and the six stack ASan exes (asserts on; MSVC orders equal scores
differently, so this group is compared with its own lock build). Result: 20 / 20 PASS - every transcript (679 normalised
lines) identical to its group's lock run, the perft blocks identical across the groups, published perft 3 counts
matched (2812 / 9467 / 62379), 218 root moves in A1, 0 in A8 / A9, all six rejections with the expected reason and the
position kept, no sanitizer line, exit 0 everywhere. `F:\ospd\qa2\extreme\final2\results.tsv` (md5 ee261e4f; the
14:28 run gave the same 20 / 20).
The first draft of the high-capture node (eight queens) was a mate in 1 (947 nodes); it was replaced before the
recorded run by the four-queen node (lock: go depth 10 cp 2447, 20,237 nodes).

## Notes
- The brief's 1d parenthetical describes the mutant fail-closed check, while the review's test 5 is the 0xA5 poison
  build (which must stay identical); both were run, and 1d counts as PASS only if both pass.
- `bench` builds its own `Searcher(16)`, so "Threads 1 then bench 13" alone never touches the main searcher after
  helper threads existed; the soak therefore ends with a Threads 1 tail compared with the lock's cached L3 rows.
- The review's test 7 (net-off 2k subset at depth 13) is not in the brief's a-e list and was not run.
- Scratch at the end: `F:\ospd` 5.9 GB (cap 8 GB), F: 55 GB free; no process of this follow-up is left (every engine
  exited after quit; the three idle PIDs from the job are still there, untouched).
- Lock-path documentation: `tools/bitexact_check.ps1` (header + a `LOCK PROOF INCOMPLETE` line after every BIT-EXACT
  verdict) and `skills/forge-speed-lock-path/SKILL.md` now say that BIT-EXACT + ABBA is not a lock until L3b warm-table
  identity (warm_identity.py, already IDENTICAL on all six, not rerun) and a Threads 2-4 go-movetime smoke (= 1c) passed.
