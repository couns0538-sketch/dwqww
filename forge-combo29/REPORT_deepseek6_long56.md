# REPORT — deepseek6, long 56 (UCI fuzz: 2,000 random command sequences under ASan + UBSan)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long56/ · claimed with claim.sh (the claim line in stamps.txt, per-chat format); PREDICTION.md before the runs.

## 1. Three lines
**Asked:** 2,000 random UCI command sequences of 5-30 lines (seed 56) from file 15's grammar — setoptions with real names and random/missing values, positions with 0-40 legal-or-illegal moves, all go forms, stop/ponderhit, garbage — each ending with isready + quit, run under ASan+UBSan.
**Answer:** **2,000 sequences, ZERO crashes, ZERO hangs, ZERO sanitizer lines, ZERO illegal bestmoves — every sequence completed (ok 2000), in 51 seconds wall with six parallel workers.** All four predictions held. The bad_sequences.txt is empty; the per-sequence records are in out/.
**How sure:** certain (the harness kills at a 20-second readyok silence = the hang; the exit-code check; the legality classifier of long 55 with its corrections).

## 2. Honesty numbers
The sanitizer build /tmp/l46_san/build/forge; the sequences file /tmp/uci56_seqs.txt (committed generation script).

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh | done | stamps.txt | exit 0 |
| the generator (seed 56, the file-15 grammar) | done | make_uci56.py, /tmp/uci56_seqs.txt | 2,000 sequences |
| the parallel run (6 workers, one process per sequence) | done | out/fuzz56_summary.txt | 51 s wall; all clean |
| the classification | done | the runner's checks | 0/0/0/0 |
| prediction own commit first | done | PREDICTION.md | all four held |

## 4. Findings
1. **The UCI layer survives 2,000 adversarial command sequences under the sanitizer with zero findings** — the strongest robustness result of the series (long 46's twelve cases generalised to random compositions of the same commands).
2. The grammar's nastiest generators (valueless setoptions, "go banana", "go depth -3", bare "position", 40-move illegal tails) all passed through the refusal paths long 37/46 mapped.
3. Suspicions, not proven: none.

## 6. What I read from my colleagues
File 15 (the item, the grammar).

## 7. What I did NOT do
Longer sequences, deeper fuzzing of the clock options (the go movetime/infinite interplay got its share of sequences but not a dedicated stress).

## 8. What I am NOT sure about
Nothing material.

## 9. A better way
The same runner should be pointed at any future UCI-facing patch before its matches — cheap (51 s) and broad.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long56/stamps.txt
?? forge-combo29/REPORT_deepseek6_long56.md
?? forge-combo29/tests_deepseek6_long56/out/
$ ls forge-combo29/tests_deepseek6_long56/
CLAIM.txt
fuzzuci56.py
make_uci56.py
out
PREDICTION.md
stamps.txt
```
