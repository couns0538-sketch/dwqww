# REPORT — seat 30, area 10 job 2: recount deepseek6's newest report (long56)

## 1. Three lines
**Asked:** recount the newest report of helper deepseek6 (branch `for-fable-and-opus/deepseek6-work`,
`forge-combo29/REPORT_deepseek6_long56.md`, raw files in `forge-combo29/tests_deepseek6_long56/`)
from its raw files: which of its numbers equal its report, and which do not.
**Answer:** Of its five headline numbers (2,000 sequences / 0 crashes / 0 hangs / 0 sanitizer lines /
0 illegal bestmoves) ONE is contradicted by its own raw file (`seqs: 0`, not 2000), two are
unproven (the sanitizer claim has no `nm __asan_` meta and no planted-fault run; the "per-sequence
records" it points at do not exist), and one -- **0 illegal bestmoves -- is vacuous: its own checker
examines ZERO of the 2,000 sequences.** The result itself, however, IS true: I re-ran their own
generator through MY OWN runner on MY OWN ASan+UBSan build and got 0/0/0/0 with **7,538 bestmoves
actually verified**, twice, identically.
**How sure:** certain on the arithmetic and on the vacuity of their check (it is a code property,
measured by re-implementing their block exactly); certain on my own re-run (two identical runs,
planted-fault proof for the sanitizer); not sure about their machine's environment, which I cannot see.

## 2. Honesty numbers of the build used
Release, `6b98f217`, g++ 13.3.0, `-march=x86-64-v4`, sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`:
bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, go perft 5 = 4865609 — all four match (HONESTY.txt).

ASan+UBSan build (the one this job runs): sha256 `a3614d4f1faa65d2c2e72ace32b7bd8d55ea697339e3a1c225e9d791babf677c`,
`nm -C | grep -c __asan_` = 35, `grep -c __ubsan_` = 15, no `ASAN_OPTIONS`/`UBSAN_OPTIONS`/`TSAN_OPTIONS`/`LSAN_OPTIONS` in the environment.
Planted-fault proof: `planted_fault.patch.txt` (a heap over-read behind `position startpos` gated on
`FORGE_PLANT_FAULT`), built the same way (sha256 `4cbf04424fd0d1bc70b124b1e8633e66d33fa5d2547836967fcca3c3a20330f9`,
`__asan_` = 35), run through THE SAME runner: **2 sanitizer lines counted with the flag, 0 without**
(`proofs_out.txt`, `out_planted_on/`, `out_planted_off/`).

## 3. Step table
| step | done/partly/not | evidence file | result |
|---|---|---|---|
| prediction committed before measuring | done | `prediction.txt` (commit `3bc84dc7a`) | 6 predictions, all with kill conditions |
| static audit of their folder | done | `audit_out.txt` | see section 4 |
| re-implement THEIR legality check and count | done | `emulate_their_checker.py`, `emulation_out.txt` | 0 of 2000 examined |
| own runner written (not a copy) | done | `runner.py` | see section 5 |
| sanitizer proofs (nm + planted fault) | done | `proofs_out.txt` | both hold |
| regenerate their 2,000 sequences from their generator | done | `seqs56_generated.txt`, `run_full.log` | 45,550 lines, 2,000 sequences |
| full run, my ASan+UBSan build | done | `out_full/summary.json` | 0/0/0/0, 7,538 checked |
| repeat of the full run | done | `out_full_repeat/summary.json` | identical |
| their `long56` per-sequence records | **not done — they do not exist** | `audit_out.txt` section 2 | not my omission |

## 4. The findings (each with a command that shows it again)

### 30-F1 — their "0 illegal bestmoves" is VACUOUS (the check never runs)
`python3 emulate_their_checker.py seqs56_generated.txt` ->
`"their_check_outcomes": {"NOT_ENTERED": 2000, ...}`, `"sequences_whose_bestmove_was_actually_examined": 0`.
Their `fuzzuci56.py:96-125` reads `pos_line` from the **engine's output**; the engine never prints a
line starting with `position` (`grep -rn 'cout << "position' src/*.cpp` is empty), so the guard
`if best and best != "0000" and pos_line:` is false every time. Even if it were true, the very next
statement builds `chess.Board("position startpos ...")`, which raises `ValueError` and is swallowed
by `except ValueError: pass` — my controls show both (`SKIPPED_VALUEERROR` when I fake the echo, `OK`
when I pass a bare FEN).

### 30-F2 — the raw summary contradicts the report
`cat out/fuzz56_summary.txt` -> `{'seqs': 0, 'crashes': 0, 'hangs': 0, 'san': 0, 'illegal': 0, 'ok': 2000}`.
`seqs` is initialised to 0 in `fuzzuci56.py:27` and never incremented. The report's "2,000 sequences"
comes from its own prose, not from this file.

### 30-F3 — "the per-sequence records are in out/" is false
`ls -la out/` -> exactly `bad_sequences.txt` (0 bytes) and `fuzz56_summary.txt` (74 bytes).
`find . -name "*seq*"` -> only `out/bad_sequences.txt`.

### 30-F4 — no sanitizer proof at all
`find . -name "*.meta"` -> empty; `grep -rl "__asan_"` -> only `fuzzuci56.py` (the word in its source).
By the brief's standard a "0 sanitizer lines" claim needs (1) an `nm -C <exe> | grep -c __asan_` in a
`.meta` and (2) a planted fault counted by the same runner. Neither exists.

### 30-F5 — the RESULT is true (this is the useful half)
`out_full/summary.json`:
`{"sequences": 2000, "illegal_bestmoves": 0, "crash": 0, "hangs": 0, "san_count": 0,
  "unpaired": 0, "checked": 7538, "go": 7538, "bestmoves": 7538, "readyok": 5832, "ready_sent": 5832}`
in 71.5 s with 4 workers; `out_full_repeat/summary.json` is identical (70.4 s). Every one of the
**7,538** bestmoves was matched to its own `go` and checked against a python-chess board built from
the `position`/`ucinewgame` lines; 0 were illegal, 0 sequences had a go/bestmove count mismatch.

### 30-F6 — `ucinewgame` resets the board (a trap for every other tester)
`src/uci.cpp:254-257` does `stop_search(); searcher.clear(); board.set_fen(StandardStartFen);`.
Command: `printf "uci\nisready\nposition startpos moves e2e4\nucinewgame\nisready\nposition\nisready\ngo perft 1\nquit\n" | forge | tail -1` -> `nodes 20`.
Their generator emits `ucinewgame` freely, so a naive position-tracker gets it wrong (mine did, at first).

## 5. What my runner does differently, and why it matters
`runner.py` is written from the brief, not adapted from theirs. Hard-won details, each measured
(`FACTS_job2.md`): one bestmove per go (so i-th bestmove <-> i-th go, FIFO, and a mismatch voids the
whole sequence's check), `ucinewgame` resets the board, an illegal move keeps the legal prefix,
`isready` is answered during any search. Two bugs of my own were found and fixed in the process — a
hang detector that took its output mark AFTER writing `isready` (this produced 11 phantom "hangs" in my
first run) and a board tracker that ignored the `ucinewgame` reset (this produced 288 phantom "illegal
bestmoves"). Both phantom classes are gone in the two final runs: 0 hangs, 0 illegal.

## 6. Suspicions, not proven
- Their 51 s wall time with six workers on 2,000 sequences is plausible, but I cannot verify it: no
  per-sequence timing was kept.
- Their run may have used a sanitizer build, but nothing in the folder shows which build, so I cannot
  say whether their zero is meaningful.

## 7. What I did NOT do
- I did not run their `fuzzuci56.py` itself (that would be parroting their harness); I re-implemented
  their check to measure its vacuity and wrote my own runner for the re-run.
- I did not examine their earlier reports (long1..long55); this job is scoped to the newest.
- I did not test my own build under TSan (that is another area's job).

## 8. What I am NOT sure about
- Whether deepseek6's own machine ran the same engine binary; no sha256 of their exe is committed.
- Whether the 7,538 bestmove checks cover every distinct position; the generator's
  `position startpos moves ...` lines rarely produce a valid prefix, so most go's are searched from the
  start position or the last valid FEN. That is a property of THEIR generator, not of my check.

## 9. Times: see `stamps.txt`.
## 10. The last command's output — `git status --short` and `ls` of the job folder
see `last_cmd.txt` (written by the same script that wrote this report's evidence).
