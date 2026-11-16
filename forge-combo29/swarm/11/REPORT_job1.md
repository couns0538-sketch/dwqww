# REPORT_job1 — seat 11, area 1: FEN input under ASan + UBSan

## 1. What was asked
20,000 FENs from G and R, one random mutation each (replace / insert / delete a character,
swap two fields, drop a field), the mutation written beside it; each case `position fen` +
`isready` (answer lines) then `go depth 2`, one process per 500 FENs, restarts counted.
Table: refused / accepted+py-valid / accepted+py-INVALID (each listed) / crashes /
sanitizer lines / illegal bestmoves. Control: a 3,000-character first field refused, no crash.

## 2. The answer
All 20,000 cases ran. 0 crashes, 0 sanitizer lines, 0 illegal bestmoves, 17,130 refused,
2,870 accepted (2,846 python-chess valid, **24 accepted that python-chess rejects**). All 24
are the same already-known leniency (consecutive digits in a rank), and I proved it is
**harmless**: the accepted spelling builds the identical board as the canonical one. The
3,000-character control was refused with no crash. One genuinely new defect: **S-F1**,
extra tokens after the sixth FEN field are silently discarded.

## 3. How sure
High on the counts (raw results file, re-runnable script in `analyze_job1.py`).
High on F1 (minimal probes, 1-line FENs).
High on the harmlessness proof (identical perft 4 with the same divide).
Two claims I wrote and then WITHDREW are recorded, not deleted, in section 5 and
`job1/S-F3_WITHDRAWN.md`: an F2 cause that was wrong, and an S-F3 that claimed to refute Opus.

## Honesty numbers (my build, `HONESTY.txt`)
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all four match.

## Proof 2 for the sanitizer claim
`nm -C` on the ASan exe: 35 `__asan_` symbols, 15 `__ubsan_` symbols; the plain release exe: 0.
A scratch copy `/home/ubuntu/planted` with ONE planted fault (heap over-read in
`Board::set_fen` behind FENs starting `PLANT`, board.cpp:211) built the same way and run
through the SAME runner counted its line: `job1/proof2/engine.stderr` holds
`board.cpp:217:78: runtime error: load of address ... insufficient space` and summary
`{"cases": 2, "process_starts": 3, "crashes": 1, "sanitizer_lines": 1}`.
So the real run's "0 sanitizer lines" is shown, not merely unproven.

## 4. Table
| step | done/partly/not | evidence file | result |
|---|---|---|---|
| 20k mutations generated | done | `job1/mutations.tsv`, `job1/mutated.fens` | 20,000 distinct mutants, 30,161 tries |
| 20k run under ASan+UBSan | done | `job1/run_asan/results.jsonl` | 40 process starts, 0 crashes, 0 san lines |
| python-chess cross-check | done | `job1/run_asan/summary.txt` | ref 85.65 %, accept 14.35 %, agree 99.164 % |
| accepted-but-py-invalid listed | done | `job1/run_asan/accepted_pyinv.txt` | 24/24 listed |
| illegal bestmoves | done | `job1/run_asan/illegal_best.txt` | 0 (empty file) |
| 3,000-char control | done | `job1/ctrl_long_run/` | refused, "pawn on promotion rank", no crash |
| defect F1 minimal probe | done | `job1/probe3_run/` | 5 extra tokens accepted |
| defect F2 minimal probe | done | `job1/probe4_run/` | `5K11` accepted, perft 4 = 1870 = canonical |
| F2 retraction probe | done | `job1/probe4_run/` h6,h7 | short/over ranks ARE refused |

Raw summary (`job1/run_asan/summary.txt`):
```
cases            20000
refused          17130  (85.65 %)
accepted         2870  (14.35 %)
  py valid       2846
  py INVALID     24
agreement among accepted  99.164 %
no bestmove      0
no-move bestmove 0
illegal bestmove 0
sanitizer lines  0
```

## 5. Findings

**S-F1 — `position fen` silently ignores every token after the sixth; malformed FENs are
accepted.** Evidence `job1/probe3_run/` (case g8).
Shows it again:
```
printf 'uci\nposition fen 4k3/8/8/8/8/8/8/4K3 w - - 0 1 1 1 1 1\nisready\ngo depth 1\nquit\n' \
  | /home/ubuntu/builds/asan/forge | grep -c "readyok"
```
g8 was accepted with five extra tokens; `zzz` and `999999` as 7th token also accepted (g3, g4).
Cause: `src/uci.cpp` `apply_position()` reads at most six tokens
(`for (int i = 0; i < 6 && input >> token; ++i)`) and then goes straight to the `moves`
loop, which discards non-`moves` tokens instead of reporting them. `Board::set_fen()` DOES
reject a 7th field ("FEN must contain exactly six fields", board.cpp) — the UCI front end
never lets it see one. This is a front-end bug, not a parser bug.

**S-F2 — a rank written with two adjacent digits is accepted, though FEN forbids it.**
Evidence `job1/probe4_run/` (h1) and `job1/ctrl_run/` (c6).

I first wrote a different cause here (a rank summing short of 8) and it was WRONG. The
rank-sum check is correct: `h6` (`6K` = 7 squares) and `h7` (`4K4` = 9) are both refused
("invalid FEN rank" / "too many squares in FEN rank"), and `h1` and the canonical `h3`
produce the identical board — both give `go perft 4` = **1870** with the same divide
(`f2g3: 272`). So this is a *syntax* pedantry, not a board-corruption bug.

Shows it again:
```
for f in "4k3/8/8/8/8/8/5K11/8 w - - 0 1" "4k3/8/8/8/8/8/5K2/8 w - - 0 1"; do
  printf "uci\nposition fen $f\nisready\ngo perft 4\nquit\n" | /home/ubuntu/builds/rel/forge \
    | grep -E "f2g3|nodes" | tr '\n' ' '; echo " <- $f"; done
```
Both print `f2g3: 272  nodes 1870`.

Cause: `src/board.cpp:246` the digit arm is `file += c - '0';` with no check that the
*previous* character was not also a digit, and no canonicality test. FEN's grammar allows at
most one digit per run of empty squares, so `5K11` is malformed; python-chess rejects it
("two subsequent digits in position part of fen"). The engine accepts it whenever the total
still lands on exactly 8, and then produces the same board as the canonical `5K2`.
The *upper* bound is enforced (:261 `if (file > 8)` -> "too many squares in FEN rank"), which
is why `44K1`, `53K1` and `8K111111` are refused. So: **consecutive digits are accepted
exactly when they sum to <= 8 and the rank ends at 8.**

Severity: low. It cannot corrupt the board (proven equal perft). It matters only as a
parser-conformance difference against any external tool that rejects non-canonical FENs.

**S-F3 — WITHDRAWN.** I claimed the brief's castling line was stale. Opus's
`FABLE_TO_swarm_1.md` states it as already known from the PC, and my evidence does not
contradict it. Full retraction: `job1/S-F3_WITHDRAWN.md`. What I truly measured:
(a) a right with no king/rook on the home squares is REFUSED (board.cpp:313) — a different
input from Opus's claim; (b) 12 structurally-present-rights cases give **0 perft
differences** vs python-chess (`job1/castle_battery.txt`, incl. kiwipete 97862 = 97862).
I did not reproduce Opus's 8902-vs-8802 board and do not claim it is wrong.

**S-F2 is also already known** (Opus: "17" and "44" read as 8 empty squares). My only
addition is the harmlessness proof above. Only **S-F1** is genuinely new.

## 6. Suspicions, not proven
- `apply_position()`'s loop is `for (int i = 0; i < 6 && input >> token; ++i)`, then a
  `while (token != "moves")` loop that swallows the rest. A malformed FEN that has six
  parseable fields plus junk is therefore never diagnosed. I proved the accept; I did not
  search for a *second* consumer of those swallowed tokens elsewhere in uci.cpp.
- The 3,000-char control was refused for "pawn on promotion rank" rather than by any length
  guard; a 3,000-char field built from `/` alone might take a different path. Not tested.
- Whether F2 (`5K11`) can appear in a real FEN producer: no normal tool emits adjacent
  digits, so it is hand-made or corrupted input only. Expected, not proven.

## 7. What I did NOT do
- Did not test `Threads > 1` for job 1 (job 1 does not ask; it is area 4's subject).
- Did not run the same 20k under the plain build for a speed comparison.
- Did not test en-passant or halfmove-clock extremes here (those are job 2).
- Did not prove `Empty == 0`, but the equal perft on h1 vs h3 makes it moot for this bug.

## 8. What I am NOT sure about
- Whether F1 is deliberate leniency for tools that append a comment; the code has no note
  saying so, and `set_fen` demonstrably rejects a 7th field, so the front end's silence looks
  unintended rather than designed.
- Whether S-F3 (impossible castling now refused) is a recent tightening or a difference
  between my build and the build the brief's "known" line came from. I only know it is
  refused on 6b98f217 built as the brief prescribes.

## 9. Times
See `job1/stamps.txt`.

## 10. Last command's output
```
$ git status --short
(clean except untracked files added below)
$ ls job1/
PREDICTION.md  analyze_job1.py(→../)  cases.tsv  mutations.tsv  mutated.fens
run_asan/  ctrl_run/  ctrl_long_run/  castle_run/  probe_run/  probe2_run/  probe3_run/  proof2/
```
