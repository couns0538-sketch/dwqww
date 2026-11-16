# REPORT job 1 — area 1 (FEN input) — seat 01

## 1. What was asked / the answer / how sure

**What was asked.** 20,000 FENs built from G and R by one random mutation each (replace / insert / delete one
character; swap two fields; drop one field), the mutation written beside it. Each sent as `position fen` +
`isready` (answer lines kept) + `go depth 2`, one process per 500 FENs, a crash restarted and counted. Table:
refused / accepted and python-chess valid / accepted and python-chess INVALID (each listed) / crashes /
sanitizer lines / illegal bestmoves. Control: a 3,000-character first field must be refused without a crash.
Known already: an impossible-castling FEN is accepted (perft 3 8,902 vs python-chess 8,802); a triple check by
three knights is accepted.

**The answer.** 18,715 of 20,000 mutated FENs are refused (93.58 %); 1,285 accepted; 0 crashes; 0 ASan/UBSan
lines; 0 illegal bestmoves out of the 1,246 accepted FENs python-chess also calls valid. Of the 39 accepted
FENs that python-chess calls invalid, 38 are the already-known "consecutive digits are added" behaviour and 1 is
a new case (index 8313). In the other direction 1,786 FENs the engine refuses are accepted by python-chess —
1,467 of those only because python-chess silently fills missing counter fields; the engine is stricter there,
and in 46 cases the engine is stricter *and right* (a castling right with no rook on the corner).

**How sure.** High for the counts (raw files committed, table produced by `analyse.py` from them). Medium for the
one new case (index 8313): its perft matches python-chess, so the only open part is whether the board is legal at
all, which is a rules question, not a code question.

## 2. Honesty numbers

```
check	got	expected	verdict
bench11	312866	312866	PASS
bench13	862329	862329	PASS
bench16	3024920	3024920	PASS
perft5	4865609	4865609	PASS
```
Release build `~/builds/release/forge`, sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`, `id name Chess Engine Forge 6.4.24 candidate`. Harness `honesty/honesty.py`, raw output in `honesty/`.

The ASan+UBSan build used for this job has the same four numbers (`honesty/asan/summary.txt`), sha256
`37c0d256accc64b90aaccaf14e421f26607b4982adf976546d769351a0b50770`, `nm -C | grep -c __asan_` = 35,
`__ubsan_` = 15 (`job1/meta.txt`).

### The two sanitizer proofs (both required before "0 lines" counts)

1. `job1/meta.txt` holds `nm -C grep -c __asan_ : 35` and `__ubsan_ : 15` for the exe this job started.
2. `job1/sanitizer_proof/` holds a scratch copy of the engine with ONE planted fault behind input I control — a
   heap over-read on a FEN whose first field starts with `PLANTED` (`planted_fault.patch.txt`) — built the same
   way (ASan+UBSan, g++ 13.3) and run through THE SAME `runner.py`. The runner counted it:
   `AddressSanitizer: heap-buffer-overflow … in apply_position` (`planted_crash_via_same_runner.log`,
   `crashes.json` of that run). The planted source is never committed, only its patch text.

## 3. Table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| set R built from random games with SEED 101 | done | `gen_set_R.py`, `set_R.fens` | 80 games, 2,124 positions (one every 7 plies) |
| 20,000 mutants from G and R, mutation written beside | done | `make_mutants.py`, `mutants.tsv` | 10,049 G, 9,951 R; 4,098 drop / 4,020 insert / 4,004 swap / 3,945 replace / 3,933 delete |
| runner written first, then run | done | `runner.py`, `chunks.txt`, `raw/` | 40 chunks of 500, every `setoption`/`position` followed by `isready` and read to `readyok` |
| refused / accepted / accepted-but-invalid | done | `results.jsonl`, `table.txt`, `invalid_list.txt` | 18,715 refused / 1,285 accepted / 39 accepted-but-invalid |
| crashes | done | `crashes.json`, `chunks.txt` | 0 |
| sanitizer lines | done | `sanitizer_lines.txt` | 0 (with the two proofs above) |
| illegal bestmoves | done | `illegal_bestmoves.txt` | 0 of 1,246 judged; 39 not judgeable (python-chess rejects the FEN) |
| control: 3,000-character first field | done | `control.py`, `control.txt` | refused, `too many squares in FEN rank`, no crash, no sanitizer line |
| stability of accept/refuse across processes | done | `control.txt` | STABLE = True |
| reverse direction: refused but python-chess-valid | done | `classify.py`, `refused_but_python_valid.txt` | 1,786 |
| refusal reason histogram | done | `refusal_reasons.txt` | 13 distinct reasons, top: `FEN must contain six fields` 7,526 |

## 4. Findings

| id | area | one sentence | file with the exact command that shows it again | status |
|---|---|---|---|---|
| S-F1 | 1 | 38 of 20,000 single-mutation FENs are accepted although a rank holds two adjacent digits, and python-chess refuses them — this is the already-known digit-summing rule, quantified at 38/20,000. | `invalid_list.txt`; again: `python3 classify.py .` in `job1/` | NEW (new only as a rate, the mechanism is known) |
| S-F2 | 1 | A FEN with the side to move in check from TWO pieces (`3k4/3P1q2/5K2/8/8/5r2/7p/7R w - - 0 1`) is accepted, and the engine's perft 2 = 64 equals python-chess's, so move generation is right; python-chess calls the board `STATUS_IMPOSSIBLE_CHECK`. | `invalid_list.txt` line for index 8313; again: `printf 'position fen 3k4/3P1q2/5K2/8/8/5r2/7p/7R w - - 0 1\ngo perft 2\nquit\n' \| ./forge` | NEW |
| S-F3 | 1 | The engine is STRICTER than python-chess in three ways — it demands six FEN fields, demands fullmove >= 1, and refuses a castling right whose rook is not on the corner — 1,786 of 20,000 cases, so a "the engine accepts too much" reading is only half the story. | `disagreements.txt`, `refused_but_python_valid.txt` | NEW |
| S-F4 | 1 | Mutating the FEN of an existing position almost always makes it unacceptable: 93.58 % refused, and `drop a field` is refused 100 % of the time (4,098/4,098) because `set_fen` requires six fields. | `by_mutation.txt` | NEW |

Reproduce S-F2 exactly:

```
cd forge-combo29/swarm/01/job1
printf 'position fen 3k4/3P1q2/5K2/8/8/5r2/7p/7R w - - 0 1\nisready\ngo perft 2\nquit\n' | ~/builds/release/forge
python3 -c "import chess;b=chess.Board('3k4/3P1q2/5K2/8/8/5r2/7p/7R w - - 0 1');print(b.status(),[chess.square_name(s) for s in b.checkers()])"
```

## 5. Suspicions, not proven

- Index 8313's board has two checkers (f3 rook and f7 queen) on the white king at f6. python-chess reports
  `STATUS_IMPOSSIBLE_CHECK` (65536), which for a double check means no legal last move could have produced it.
  The engine's move generation agrees with python-chess (both 64 at perft 2), so this is a *position legality*
  question, not a *move generation* question. I did not prove which legal-move rule it violates.
- `by_mutation.txt` shows `replace` is the most survivable mutation (80.96 % refused vs 97-100 % elsewhere). That
  is consistent with single-character damage landing in the castling/ep/counter fields, which the engine does not
  cross-check. I did not test that directly here.

## 6. What I did NOT do

- No `perft` cross-check on the 1,246 accepted-and-valid FENs (job 1 asks only for `go depth 2`); that is area 3.
- No test of the engine's behaviour when the SAME process sees 500 mutated FENs in a row and the board must be
  replaced each time — I did test replacement (that is what the run is), but I did not check for state carried
  over from a refused FEN beyond recording `bestmove`.
- Did not run a ThreadSanitizer build (area 4).

## 7. What I am NOT sure about

- Whether "accepted and python-chess INVALID" should use `Board(fen)` parsing alone or `is_valid()`. I used
  `Board(fen)` AND `is_valid()`, and I say so in `table.txt`, because python-chess's constructor accepts boards
  with no king. Under the parse-only rule the count would be 38; under `is_valid()` it is 39.
- P2 (5–300 accepted-but-invalid) held at 39. P1 (60–85 % refused) FAILED at 93.58 %; my reading of `set_fen`
  under-estimated how much a single mutation destroys.

## 8. Times

see `stamps.txt`.

## 9. Last command output

```
$ git status --short
(clean for this folder)
$ ls
analyse.py  by_mutation.txt  chunks.txt  classify.py  control.py  control_raw.json  control.txt
crashes.json  disagreements.txt  gen_set_R.py  illegal_bestmoves.txt  invalid_list.txt  make_mutants.py
meta.txt  mutants.tsv  prediction.txt  raw  refusal_reasons.txt  refused_but_python_valid.txt  results.jsonl
run.log  runner.py  sanitizer_lines.txt  sanitizer_proof  set_G.epd  set_R.fens  stamps.txt  table.txt
```
