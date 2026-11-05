# Forge speed job - FINAL REPORT (DRAFT, filled as results land)

State: DRAFT (started 10:15 PC clock = Vienna time). Job window 2026-11-05 08:38 -> 14:38; this report is due 14:08.
Branch `opus-speed-20261105` (fresh from main 5176ddf7). Scratch `F:\ospd\`. Crew vote: A (speed-only lock path) >
B (bit-exact hot-path changes) > C (gate wall time); D only if A-C are done. No Elo claims anywhere; speed numbers
only from this job's ABBA CSVs (named per row); everything else is UNPROVEN.

## 0. Summary
PENDING

## 1. Job A - the speed-only lock path (tools, opus_speed/tools)
| tool | what it does | usage |
|---|---|---|
| build_variants.ps1 | QA kit v2.3 command lines token for token (lp_v1 of the lock source = lock exe FD3A5190 byte for byte); O3 / LTO / PGO / LTO+PGO, flag and PGO-workload variants; pc1 = pc2 with -Twice; fail-closed pins | `build_variants.ps1 -SrcDir <tree> -Tag <t> -Variant lp_v1[,..] [-Twice]` |
| bitexact_check.ps1 | L1 bench d11-22 net on + off, L2 perft, L3 12k six-field FENs at depth 13 (-Quick: 2,000), L4 MSVC ASan + g++ UBSan bench 16; stops at the first FAIL | `bitexact_check.ps1 -Cand <exe> -Out <dir> [-Quick] [-SanSrc <tree>]` |
| abba.ps1 | ABBA/BAAB rounds (>= 10) on CPU 2, fresh copies per round, wall and CPU-time nps, median + Student-t interval, A/A band, WIN rule | `abba.ps1 -A <lock> -B <cand> -Out <dir> -Depth 20 -Rounds 10 -AaCsv <A/A runs.csv>` |
| abba_queue.ps1 / abba_table.py | back-to-back ABBA list, one table from the summaries | |
| speed_pack.ps1 | source tree in -> pack out: flip switch defaults (kit takes no -D), pc1 = pc2, bit-exact proof, ABBA, candidate file | `speed_pack.ps1 -SrcDir <tree> -Name <n> [-Define SW=1] [-Quick] [-ReuseBuildDirs a,b]` |
| make_stack.sh | stacks patches on a fresh lock copy (no fuzz, switch defaults checked) | `bash make_stack.sh <name> <p1.patch> ...` |
| commit_push.sh, name_lint.py, ctrl_char_check.py, ps_parse_check.ps1, pgn_positions.py | checked commits, vendor-name lint, control bytes, PS 5.1 parse, game positions | |
Facts the tools are built on (checked 2026-11-05):
- The lock's net is embedded (`nnue_weights.inc`) and ON by default (`UseNNUE` default true). QA's frozen v1 PGO
  workload (`bench 11/13/16`, no setoption) therefore already profiles the net path: the ~12 % "net loaded" loss
  measured earlier belonged to the HalfKA EvalFile builds, not to this lock. Net off = `setoption name UseNNUE value
  false` (pins 375354 / 907205 / 2448617 / 13573040 / 24506465).
- `build_variants -Variant lp_v1` on the exact lock source reproduces the lock exe FD3A5190 byte for byte (sha256
  fd3a5190...; 09:10, and again as pc1 = pc2 inside the lock-vs-lock pack) = our pipeline is QA's kit.
- The R14 SPEED2 switch ported with R14's own script and built here gives exe de20653c..., R14's kit exe byte for byte.
- `fens_12k.txt` (placement-only) is rejected by the lock; L3 uses `fens_12k_v2.txt` (md5 e7dbf2c8): the lock's
  full 12k reference has 12,000 distinct rows (2,261 s on two Idle CPUs under load).
- MSVC builds can never match g++ node counts (std::sort orders equal scores differently), so L4's ASan run is
  compared with the MSVC ASan build of the lock source, UBSan (g++) with the candidate's own count.
- BOLT: one recorded try = not possible here (no llvm-bolt on the PC; BOLT handles ELF only, deep research T5).
Tests:
- Kit self-test: PASS (above).
- Test 2 (one search constant changed, HistoryMax 16384 -> 16000): bitexact_check FAILS at L1 (10/10 bench lines
  differ), no ABBA (09:15); with the Code Review fix the build itself already fails closed on the pin DIFF.
- Job B test 2 (move order changed, pick_best tie-break `>` -> `>=`): speed_pack stops with exit 3 before any ABBA,
  and bitexact_check on the kept exe says NOT BIT-EXACT at L1 (test_moveorder_mutant 3/3 PASS, 09:53).
- Code Review tests: 13/13 PASS (`tests/test_cr_637b.ps1`).
- Test 1 (lock-vs-lock pack) and test 3 (best variant full pack): see section 2.

## 2. Job A results - build modes, flags and PGO workloads (ABBA vs the lock, d20 x 10, CPU 2)
PENDING (abba_table.py of F:\ospd\abba\q2)

## 3. Job B - bit-exact hot-path changes
PENDING (per change: switch, patch, bit-exact status, ABBA ratio; losers; the stack)

## 4. Job C - gate wall time (worker jobc, DONE 09:59; coordinator re-run 10:01 ALL PASS)
Scripts for the crew to review; the running queue, its config, gate folders and the lock were read only. The crew
vote is unchanged; projections and audits are planning input, never a stop rule. Details and every number's source:
`opus_speed/jobc/README.md`, `opus_speed/jobc/RESULTS.md`; skill `skills/forge-gate-walltime/SKILL.md`.
| tool | what |
|---|---|
| gate_replay.py | replays a finished gate (exact fastchess 1.8.2 GSPRT after every pair, strict PGN / log pairing) and checks the recorded verdict; corrupt or truncated input -> exit 2, no verdict |
| llr_project.py | seeded projection to the cap: P(H1 / H0 before the cap), games to a decision - queue ordering only |
| queue_throughput.py | games/h per gate and per slot, idle gaps between gates |
| adjudication_audit.py | adjudication / book / TC settings per gate and what draw / resign rules would save (report only) |
| book_load_check.py | book load / index times on copies |
| pregate_screen.py | cheap rejects before games: PE header, uciok, options, pins, perft, 20-position movetime smoke with legality check, WAC subset |
| concurrency_plan.py | math only: games/h and hours to each cap for given cores at Threads=1 |
Success tests: (1) replay of 13 finished gates from FORGE_RESULTS.csv: 13/13 same verdict, W/D/L, pentanomial,
Elo / nElo / LLR within 0.006 of RESULT.md, first crossing pair = printed pair count; formula check on all 111 CSV
rows with a pentanomial: 0 differ by more than 0.006. (2) Deliberate failures: 9 corrupt / truncated / unpaired /
duplicated PGN copies x with and without the log = 18/18 exit 2 with an error line and no verdict. Coordinator re-run
of the whole suite at 10:01: ALL PASS (`jobc/results/tests_20261105_100109_coordinator_rerun.md`).
Findings (measured on 109 gates / 260.7 h): every concurrency slot yields 108-124 games/h, so wall time is set by
slots x games; idle between gates is small (median 94 s, 1.25 % of the time) except five > 30 min gaps of an empty or
paused queue (29.7 h); one gate ran at concurrency 2 without a recorded reason (11 h for 2,360 games); adjudication is
off everywhere - fishtest-like draw / resign rules would save ~11-14 % of engine time but change 12-52 results per gate
(a crew decision, not taken here); book loading costs 0.1-1.3 s (no change worth making); the pre-gate screen rejects
broken candidates in under a minute (lock PASS in 58 s). The cheapest wall-time lever is therefore keeping the queue
full and the slot count right (concurrency_plan.py), not per-game settings.

## 5. What QA should time first
PENDING

## 6. Skills created or improved
PENDING

## 7. Code Review 637B report-back
See `CR_637B_REPORT.md` (BLOCKER + SHOULD 1-3 fixed, tests 13/13; the 3 LOW notes were not visible on the PC).

## 8. Deviations, incidents, owner items
PENDING
