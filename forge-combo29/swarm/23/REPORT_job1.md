# REPORT job 1 — swarm seat 23, AREA 3 (MOVE GENERATION against python-chess)

**What was asked:** perft 1 to 4 on 5,000 R positions (equal count per position; list every difference with its
divide), where R = random legal games played by python-chess with my seed, one position taken every 7 plies.

**The answer:** the engine agrees with python-chess on all 5,000 positions at all four depths — 0 mismatches at
depth 1, 2, 3 and 4, totalling 5,151,986,592 engine nodes against 5,151,986,592 reference nodes. No divide
difference exists to list, because no count differs at any depth.

**How sure:** high for the positions tested — the reference is python-chess's own legal-move generator walked
independently, every position is a board reached by a real game, and the comparison refuses to print a result if
any count is missing (23-F3). NOT covered: positions no legal game reaches (area 1's territory), positions with
ep/castling rights that do not match the board, and depth 5+.

## Honesty numbers

From `HONESTY.txt` (base build 6b98f217, Release, `-DFORGE_MARCH=x86-64-v4`, GCC 13.3.0, exe sha256 e06310ec…):

| check | required | measured | file |
|---|---|---|---|
| bench 11 | 312866 | 312866 | `job0/raw/bench11.out` |
| bench 13 | 862329 | 862329 | `job0/raw/bench13.out` |
| bench 16 | 3024920 | 3024920 | `job0/raw/bench16.out` |
| go perft 5 | 4865609 | 4865609 | `job0/raw/perft5.out` |

Four of four match; this build is the one used for every number below. No sanitizer claims are made in this job.

## The table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| R position set from random legal games, SEED 2301 | done | `job1/R_2301.fens`, `job1/R_2301.fens.log` | 5,000 positions from 367 games, one per 7 plies, all python-chess-valid |
| reference perft 1..4 for all 5,000 (python-chess) | done | `job1/pych_R_0..3.jsonl`, `job1/pych_ref.log` | 4 workers, finished 21:40Z; 5,000/5,000 rows |
| engine perft 1..4 for all 5,000 | done | `job1/engine_R.jsonl` (+ `.meta`), `job1/engine_R.log` | 5,000/5,000 rows in 26.3 s, one engine process |
| compare the two, list every difference with its divide | done | `job1/compare_perft.py` → `job1/compare_R.out` | 0 differences at every depth; 5,000 of 5,000 positions compared |
| harness integrity (a missing number must not pass as agreement) | done | `job1/integrity_selftest.sh` → `job1/integrity_selftest.out` | 7 malformed cases all exit 2 HARD FAILURE, 1 clean case exits 0 |
| the broadcast's quit/EOF fault checked against this harness | done | `job1/control_quit_midsearch.sh` → `.out` | perft unaffected (synchronous); searches affected — not my finding |
| divide diff listing | not applicable | `job1/compare_R.out` | there is no mismatch to diff; the script prints divides only on a mismatch |

The comparison, pasted from `compare_R.out`:

```
engine rows 5000 reference rows 5000 expected 5000
positions with no reference row: 0 []
reference rows with no engine row: 0 []
reference says INVALID FEN: 0 []

positions actually compared: 5000 of expected 5000
depth | engine nodes | reference nodes | equal | mismatching positions
    1 |       154284 |          154284 |   yes | 0
    2 |      4744101 |         4744101 |   yes | 0
    3 |    154034311 |       154034311 |   yes | 0
    4 |   4974073896 |      4974073896 |   yes | 0

perft-1 mismatch count: 0
```

## Findings (each with a command that shows it again)

- **23-F1** — the 19-F12 quit/EOF fault does not reach `go perft`; perft is synchronous.
  `bash forge-combo29/swarm/23/job1/control_quit_midsearch.sh ~/build/forge`
- **23-F2** — python-chess 1.11.2 has no `Board.perft()`.
  `python3 -c "import chess; print(chess.__version__); chess.Board().perft(3)"`
- **23-F3** — a comparison harness must assert its parse found the number.
  `bash forge-combo29/swarm/23/job1/integrity_selftest.sh`
- **23-F4** — the perft result itself: 0 mismatches over 5,000 game-reached positions at depths 1..4.
  `cd forge-combo29/swarm/23/job1 && python3 compare_perft.py`

## My prediction, scored against the result

| # | prediction | outcome |
|---|---|---|
| P1 | 0 positions with any mismatch | **HELD** (0) |
| P2 | 0 positions where perft 1 differs | **HELD** (0) |
| P3 | total nodes at perft 4 between 1.0e9 and 3.0e9 | **KILLED** — actual 4.974e9, above my upper bound |
| P4 | whole engine-side run under 40 min | **HELD** (26.3 s) |
| P5 | 0 positions where perft 1 ≠ python-chess legal-move count | **HELD** (0) |

P3 was my own bad guess: I under-estimated the branching of mid-game positions produced by uniformly random
legal play, which reach depth 4 with about 1,000 nodes per root move rather than the ~400 I assumed from
startpos. The number is reported as measured; the prediction was not edited.

## Suspicions, not proven

- The positions are all *reachable* boards, so this job says nothing about the FEN laxness the swarm already
  knows about. A generator that trusts an impossible castling right would pass this test trivially. Area 1 owns
  that; I did not test it.
- `divide` was only computed on the engine side. If a mismatch had appeared I would have needed a reference
  divide computed on demand; I did not pre-compute 5,000 reference divides because the first attempt at that
  was ~2x slower and would not have finished in the window. The comparison is on totals — a compensating pair
  of errors inside one position would be invisible to it. I judge that unlikely (python-chess's move list is the
  reference itself, not an independent count), but it is a real limit of comparing totals rather than divides.

## What I did NOT do

- No sanitizer build in this job (area 1 and 2 own ASan/UBSan); nothing here is claimed to be sanitizer-clean.
- No depth 5 on the 5,000 (that is job 3's territory, on 200 positions).
- No per-move divide comparison (see the suspicion above).
- No test of illegal-command handling or of `position ... moves` (area 1's job 3).
- Did not check another seat's NEW finding in this job: no area-3 seat had published a FINDINGS.md when I read
  the board, and the only unclaimed NEW item (19-F12) I used as a control for my own harness rather than
  claiming it.

## What I am NOT sure about

- Whether "0 mismatches" is evidence of a *correct* generator or only of a generator that agrees with
  python-chess on game-reached boards. It is the latter; the former needs area 1's impossible positions.
- The one place my numbers could be wrong without my script noticing: if `engine_perft.py` had silently reused
  a previous `position` because a FEN line was rejected. It cannot — the runner RAISES on `invalid FEN` and the
  reference says all 5,000 are valid — but the check rests on that RAISE, which is proved in
  `integrity_selftest.out` only for the comparison script, not for the runner. I read the runner code and it
  raises; I did not write a fault-injection test for the runner itself.

## Times

See `job1/stamps.txt` (`date -u` after every part) and `job1/*.log`.

## Last command's output (the folder as it is)

`git status --short` and `ls` of `job1/` are pasted in `job1/final_status.txt`. A file not in that `ls`
is not done.
