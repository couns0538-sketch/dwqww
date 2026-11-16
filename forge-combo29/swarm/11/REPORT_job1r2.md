# REPORT_job1 round 2 — seat 11, area 1, SEED 1111, new position set R'

Brief step 2(c): job 1 of my area again with the next seed and a new position set, and say in
the report what differs from the first run.

## 1. What was asked
Same as job 1: 20,000 FENs from G and R by one random mutation each, `position fen` +
`isready` + `go depth 2`, one process per 500, restarts counted, python-chess cross-check.

## 2. What differs from round 1
- mutation seed **1101 → 1111**,
- position set **R regenerated with seed 1111** (300 FENs, **0 overlap** with the 1101 set —
  `comm -12` of the two sorted files),
- G unchanged (the brief asks only for a new R),
- the runner is the **fixed** one: round 1's committed run used a runner whose `readline()`
  had no timeout, so a hung engine would have hung the harness (see `../RULE1.md`). This
  round's numbers are the first whose harness can *prove* a non-answer would have been counted.

## 3. The answer
20,000 cases: **0 crashes, 0 sanitizer lines, 0 illegal bestmoves**, 17,089 refused
(85.44 %), **32** accepted-but-python-chess-invalid, in exactly two classes:
**23** "more parts than expected" (= my F1, extra token) and **9** "two subsequent digits"
(= the already-known digit-summing rule).

Round 1 had 24 py-invalid; round 2 has 32. The extra 23 are F1 cases, which round 1's set did
not contain because of a mutation-set detail I had predicted wrongly (see 4 below).

## 4. How sure, and where my prediction was WRONG
High on the counts (raw file + re-runnable analyzer).
**Prediction 5 was wrong.** I predicted 0 F1-style cases, reasoning that none of my five
mutations appends a token after field 6. But my generator's insert alphabet contains a space,
so `insert field6[1] ' '` splits the fullmove field into two tokens and produces exactly the
7-token input that F1 describes. 23 of the 32 py-invalid cases are that one mutation. So my
round-1 statement "F1 is not reachable by this mutation set" was true only by luck of the RNG,
not by construction. Corrected here, not edited away.
Prediction 1 (82–88 %): measured 85.44 %, inside. Prediction 2 (≥ 99.0 %): **missed**,
98.901 % — still inside the kill range (98.5 %). Prediction 3 (same two classes, count 10–60):
32, inside. Prediction 4: held. Prediction 6 (< 10 min): 6.2 s, held.

## 5. Honesty numbers and Rule 1
Honesty unchanged: 312866 / 862329 / 3024920 / 4865609.
Rule 1 plants committed beside this run: `../controls/plant_run/` (fake engine answering
`bestmove a1a8` → analyzer reports `illegal bestmove 2`) and `../controls/plant_hang_run/`
(fake engine that never sends `readyok` → runner reports `crashes 1`).
Sanitizer proof: `../job1/proof2/` (planted heap over-read counted, 1 line).

## 6. Table
| step | done/partly/not | evidence file | result |
|---|---|---|---|
| new R set, seed 1111 | done | `../positions/R_seed1111.fens` | 300 FENs, 0 overlap with 1101 |
| 20k mutants, seed 1111 | done | `job1r2/mutations.tsv` | 20,000, 30,233 tries |
| 20k run under ASan+UBSan | done | `job1r2/run_asan/results.jsonl` | 40 starts, 0 crashes, 0 san lines |
| python-chess cross-check | done | `job1r2/run_asan/summary.txt` | 85.44 % refused, 98.901 % agreement |
| py-invalid classified | done | `job1r2/run_asan/accepted_pyinv.txt` | 23 extra-token + 9 adjacent-digit |
| F1 reproduced at scale | done | cases 323, 967, 2396, 4721 | 7-token FEN accepted, perft 1 = 8 = 6-token form |

```
cases            20000
refused          17089  (85.44 %)
accepted         2911  (14.55 %)
  py valid       2879
  py INVALID     32
agreement among accepted  98.901 %
no bestmove      0
no-move bestmove 0
illegal bestmove 0
sanitizer lines  0
```

## 7. Findings
- **F1 (S-F1) is now reproduced at scale, independently of round 1.** 23 cases in this set.
  Evidence `job1r2/run_asan/accepted_pyinv.txt` + `job1r2/mutations.tsv`. Shows it again:
  ```
  printf 'uci\nposition fen rn6/p1R1p3/P3k3/2pp1p2/4npqp/2Q1P2P/PB1NKPB1/R5NR w - - 6 2 9\nisready\ngo perft 1\nquit\n' \
    | /home/ubuntu/builds/rel/forge | grep nodes
  printf 'uci\nposition fen rn6/p1R1p3/P3k3/2pp1p2/4npqp/2Q1P2P/PB1NKPB1/R5NR w - - 6 2\nisready\ngo perft 1\nquit\n' \
    | /home/ubuntu/builds/rel/forge | grep nodes
  ```
  Both print `nodes 8`. The 9th token is discarded, the board is the 6-field one.
- The adjacent-digit class (9 cases) again: already-known, and already proven harmless in
  round 1 (`job1/probe4_run/`).
- No third class appeared, so prediction 3's substance held even though its count reasoning
  was wrong.

## 8. Suspicions, not proven
- The 98.90 % (vs round 1's 99.16 %) agreement difference is explained entirely by F1's 23
  cases appearing in this set and not round 1's; I did not verify that by removing them.
- Whether a mutation inserting a `/` could produce a differently-shaped 8th token; my
  alphabet has `/` and it may already have, but those would be caught by the rank checks.

## 9. What I did NOT do
- Did not regenerate G (the brief asks for a new R only).
- Did not run round 2 on the plain build (ASan+UBSan is the stricter build and job 1's point).
- Did not compare mutation-by-mutation against round 1.

## 10. What I am NOT sure about
- Whether the reference "python-chess valid" is the right arbiter for the adjacent-digit
  class; python-chess refuses a form that is unambiguous, which is a conformance choice, not
  a soundness one.

## 11. Times
See `job1r2/stamps.txt`.

## 12. Last command's output
```
$ ls job1r2/
PREDICTION.md  mutated.fens  mutations.tsv  cases.tsv  run_asan/  stamps.txt
```
