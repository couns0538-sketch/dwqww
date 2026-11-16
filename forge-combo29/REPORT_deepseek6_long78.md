# REPORT — deepseek6, long 78 (every (position, go) pair of long 56 replayed in a fresh process, judged on the kept position)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long78/ · claimed with claim.sh (the claim line in stamps.txt); PREDICTION.md before the first run.

## 1. Three lines
**Asked:** replay every (position, go) pair out of long 56's 2,000 sequences (same generator, same seed), each pair in a FRESH engine process, judge each bestmove with python-chess on the position the engine kept, one row per pair in out/records.tsv; plant a fake engine that answers `bestmove a1a8` to every `go` and run it on the first 200 pairs.
**Answer:** **7,538 pairs extracted; 4,803 in the real-search class (go depth/nodes/movetime) — seat 10's count reconciled exactly** (my total 7,538 also counts go infinite 1,064 + go ponder 1,039 + the garbage `go banana` 632 = the 2,735 gap). **The real run: 7,538/7,538 rows recorded, 0 illegal bestmoves, 0 pairs without a bestmove** (the infinite/ponder pairs answer after the runner's stop; `go banana` answers too — recorded, class "other"). **5,009 pairs sit on a refused position** (mostly an illegal move inside the position's moves list) and on those the engine's own `info string illegal move X` lines are read and recorded beside each row (file 19's rule); the bestmove is judged on the kept board (a refused FEN keeps the start position in a fresh process; a refused move keeps the board up to the last legal move). **The plant: 200/200 rows, illegal = 200** — the runner counts what it must; over ALL 7,538 pairs a1a8 is legal on 0 kept boards and 0 boards have no legal moves, so the plant's expected number is 7,538 (the first-200 slice: 200). Also, file 19's ask about long 55: the 47 accepted-invalid rows are ALL "two subsequent digits" FENs — **0 rows with a castling error, so long 55's table stands unchanged**; my long 33/37 already reported the castling FEN as refused.
**How sure:** certain on the counts (the records.tsv has one row per pair with the pair number, the position line, the go line, the bestmove, the judgment, the refusal class and the engine's own refusal lines); the plant proof ran through the SAME runner unchanged.

## 2. Honesty numbers
The runner: fuzzuci78.py (the exe from the command line, spawned via shlex so the plant can be `python3 fake_engine.py`); the sequences regenerated from the committed make_uci56.py (seed 56) into /tmp/uci56_seqs.txt immediately before the runs; the release build /tmp/glmflash5_base/build/forge; the plant's rows in out/records_plant.tsv; the real rows in out/records.tsv (7,539 lines = header + 7,538). One process per pair; uci/isready/position/go/wait-for-bestmove/quit; the infinite/ponder pairs get a stop after a 1.0 s grace, the garbage go lines 0.6 s, movetime+0.4 s, otherwise a 20 s cap then a stop.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh | done | stamps.txt | exit 0 |
| the pair extraction | done | the counts | 7,538 total / 4,803 real-search |
| the plant (first 200 pairs) | done | out/records_plant.tsv | illegal = 200/200 |
| the real run (8 lanes) | done | out/records.tsv | 7,538 rows, 0 illegal, 0 no-bestmove |
| the seat-10 reconciliation | done | the class counts | 4,803 = their count; the gap = infinite+ponder+banana |
| the file-19 long-55 recheck | done | the 47 rows re-parsed | all digit-summing; 0 castling rows |

## 4. Findings
1. **The long 56 conclusion now has its evidence**: every one of the 7,538 (position, go) pairs, replayed isolated and judged on the position the engine kept, answers with a legal move (or none where the board is finished). Seat 10's independent count is explained to the pair: 4,803 real-search pairs, the same number I get.
2. **The runner now passes the plant** (200/200 illegal through the same code path) — long 56's missing leg is fixed; the file-18 rule (a zero needs a planted one) is satisfied for the legality check.
3. My first plant attempt hung 15 s per pair because I passed `python3` alone as the exe and the runner spawned a bare interpreter — fixed by shlex-splitting the exe; recorded because it cost the item ten minutes.
4. Suspicions, not proven: none.

## 6. What I read from my colleagues
File 18 (the item and the seat-10 finding), file 19 (the long 55 recheck rule), long 46's kept-position behavior, long 56's runner and generator.

## 7. What I did NOT do
A judgment of the infinite/ponder answers beyond legality (their bestmoves are judged by the same rule and recorded); a rerun of long 56 itself (the item does not ask for it).

## 8. What I am NOT sure about
Whether seat 10 also replayed the banana class — my "other" class says the engine answers even `go banana` with a bestmove; their 4,803 says they did not count it. Both consistent with the same engine.

## 9. A better way
The grace waits (1.0 s stop, 0.6 s banana) are heuristics; a probe of `go infinite`'s actual answer latency would tune them, but the counts they produced (0 no-bestmove) leave no ambiguity about the engine answering.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long78/fuzzuci78.py
 M forge-combo29/tests_deepseek6_long78/stamps.txt
?? forge-combo29/REPORT_deepseek6_long78.md
?? forge-combo29/tests_deepseek6_long78/__pycache__/
?? forge-combo29/tests_deepseek6_long78/err_plant.txt
?? forge-combo29/tests_deepseek6_long78/out/
$ ls -R forge-combo29/tests_deepseek6_long78/
forge-combo29/tests_deepseek6_long78/:
CLAIM.txt
err_plant.txt
fake_engine.py
fuzzuci78.py
out
PREDICTION.md
__pycache__
stamps.txt

forge-combo29/tests_deepseek6_long78/out:
lane0.log
lane1.log
lane2.log
lane3.log
lane4.log
lane5.log
lane6.log
lane7.log
records_lane0.tsv
records_lane1.tsv
records_lane2.tsv
records_lane3.tsv
records_lane4.tsv
records_lane5.tsv
records_lane6.tsv
records_lane7.tsv
records_plant.tsv
records.tsv

forge-combo29/tests_deepseek6_long78/__pycache__:
fuzzuci78.cpython-312.pyc
```
