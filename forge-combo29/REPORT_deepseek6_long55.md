# REPORT — deepseek6, long 55 (FEN fuzz: 20,000 mutated FENs under ASan + UBSan)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long55/ · claimed with claim.sh (the claim line is stamps.txt's first line, in the new per-chat model format); PREDICTION.md before the runs.

## 1. Three lines
**Asked:** 20,000 FENs mutated from G (seed 55; one mutation each, written beside it) run under ASan+UBSan in one process per 500 FENs: the refused / accepted-valid / accepted-pc-INVALID / crash / sanitizer / illegal-bestmove classes.
**Answer:** **refused 18,808 (94.0 %); accepted+python-chess-valid 1,145; accepted+pc-INVALID 47 (all listed); crashes 0 (0 restarts); sanitizer lines 0; and the two flagged "illegal bestmoves" are reclassified as CORRECT: both were `bestmove 0000` on positions where python-chess also counts ZERO legal moves (checkmate/stalemate) — the engine's "no move" answer, not an illegal move.** The planted control (a 3,000-character first field) was refused and did not crash. The 47 accepted-invalid rows are a REAL lenience finding: their board fields contain multi-digit runs like "17", "13", "115" — the engine READS consecutive digits by ADDING them (17 = 1+7 = 8 squares), python-chess refuses the FEN outright; the engine then searches its (well-formed) interpretation and its bestmoves are legal for that interpretation.
**How sure:** certain of the classes (my runner's per-FEN protocol: ucinewgame + a known base position before every FEN so refusals cannot inherit state); the digit-sum mechanism verified on the listed rows.

## 2. Honesty numbers
The sanitizer build /tmp/l46_san/build/forge (clean 6b98f217, ASan+UBSan); 40 batches of 500.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh (new per-chat model format) | done | stamps.txt first line | exit 0 |
| the generator (seed 55, five mutation kinds) | done | make_fuzz55.py, /tmp/fuzz55.fens | 20,000 rows, mutation noted per FEN |
| the planted control (3,000-char field) | done | /tmp/plant3k_out.txt | refused (invalid FEN x1), no crash, no sanitizer line |
| the 40-batch run | done | out/classes.txt, fuzz_out.txt | the classes above; 0 restarts |
| the two flagged bestmoves examined | done | out/illegal_bestmoves.txt + the python-chess analysis | both 0000 on zero-legal-move positions: reclassified CORRECT |
| the accepted-invalid rows listed | done | out/special_invalid_accepted.txt | 47 rows, the digit-sum mechanism named |
| prediction own commit first | done | PREDICTION.md | 1, 2, 3, 5 held; 4 held after the reclassification (its first read was my harness's naive 0000 check) |

## 4. Findings
1. **The engine sums consecutive FEN digits** ("17" = 8 squares) where python-chess refuses the FEN — 47 of the 47 accepted-invalid rows carry such a run in their board field. The engine's interpretation is still a full, searchable board, and its bestmoves are legal for it.
2. **The validator's rule-coverage is broad**: 94 % of the mutations refused, with the rule-naming lines of long 37.
3. **No crash, no sanitizer line, no restart across 20,000 hostile FENs** — the FEN handler is robust under the sanitizer.
4. Suspicions, not proven: whether the digit-sum reading is deliberate (a lenient-FEN feature) or an accident of a digit loop.

## 6. What I read from my colleagues
File 15 (the item; the per-chat claim format — applied).

## 7. What I did NOT do
Mutations deeper than one character; non-G base positions (the item names G).

## 8. What I am NOT sure about
The digit-sum intention (4.1).

## 9. A better way
The two 0000-on-finished-position cases deserve their own class in the harness ("finished position: bestmove 0000 expected") — my first pass mislabeled them.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long55/fuzzrun55.py
 M forge-combo29/tests_deepseek6_long55/stamps.txt
?? forge-combo29/REPORT_deepseek6_long55.md
?? forge-combo29/tests_deepseek6_long55/fuzz_out.txt
?? forge-combo29/tests_deepseek6_long55/out/
$ ls forge-combo29/tests_deepseek6_long55/
CLAIM.txt
fuzz_out.txt
fuzzrun55.py
make_fuzz55.py
out
PREDICTION.md
stamps.txt
```
