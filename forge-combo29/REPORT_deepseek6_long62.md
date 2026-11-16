# REPORT — deepseek6, long 62 (the searchmoves subsets, first 100 of O at depth 10)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long62/ · claimed with claim.sh (the claim line in stamps.txt); PREDICTION.md before the runs.

## 1. Three lines
**Asked:** the searchmoves subsets on the first 100 of O at depth 10: (i) searchmoves = only the plain run's bestmove — the bestmove must be that move; (ii) searchmoves = the plain bestmove plus the first other move python-chess lists — the bestmove must be one of the two; (iii) searchmoves with one ILLEGAL move — the engine's answer lines.
**Answer:** (i) **100/100** the engine answers exactly the restricted move. (ii) **100/100** the bestmove is one of the two (0 single-reply positions — the first-other move always existed). (iii) **MY PREDICTION IS KILLED — the engine does NOT refuse**: all 100 runs answer a real move, no "info string illegal move" anywhere. The comparison against class (i) proves what happens: the class-3 node counts equal the class-1 node counts **on 100/100 positions** — the illegal token is **silently dropped before the root move list is built**, and the search is exactly the one-legal-token search; the illegal move is never answered (0/100). Contrast with long 46's case 1: an illegal move in `position ... moves ...` IS refused with an info-string; an illegal token in `searchmoves` is silently discarded — two different illegal-move paths, two different behaviors.
**How sure:** certain on the three classes (every run's full answer log kept in out/); the "silently dropped" mechanism is proven by the exact node equality, not inferred.

## 2. Honesty numbers
300 restricted runs + 100 plain runs, one process per position, Threads 1 / Hash 16 / OwnBook false, the S14 settings; the plain base rows in out/plain_all.txt (their sums belong to the depth-10 story, not re-anchored here); the python-chess "first other move" = the first of its legal_moves iteration order.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh | done | stamps.txt | exit 0 |
| the plain d10 base (100 positions, 3 lanes) | done | out/plain_all.txt | 100 rows; one parse bug fixed before any counted run (my token-splitting, not the engine) |
| the pairs build | done | out/pairs_sm1/2/3.txt | the illegal token = the bestmove's from-square → another own piece's square (a capture of my own piece is always illegal) |
| the three classes (3 lanes each) | done | out/sm1/2/3_all.txt | 100/100, 100/100, 100 answered |
| the node comparison | done | the analysis | class3 == class1 on 100/100 |

## 4. Findings
1. **The searchmoves illegal-token path is silent.** No refusal line, no info string, no crash; the token vanishes and the search runs on the legal remainder. Where the position-moves path refuses (long 46), this path does not — the engine has two inconsistent illegal-move behaviors.
2. (i) and (ii) hold exactly — the restriction contract is respected when the tokens are legal.
3. Small oddity, recorded not chased: with the root restricted to the plain bestmove, the node count is SMALLER than the plain run on 98/100 (expected — fewer root moves) but LARGER on 2/100 — a guess: the plain run's tree was cut short by a fail-high sequence the single-move search must walk fully.
4. Suspicions, not proven: none beyond 3.

## 6. What I read from my colleagues
File 15 (the item); long 46's case-1 behavior (the position-moves refusal) for the contrast.

## 7. What I did NOT do
The illegal-token-in-a-LEGAL-list variations beyond one token (e.g. two illegal tokens); the engine's handling of a searchmoves list containing ONLY illegal tokens (all dropped → zero root moves → untested).

## 8. What I am NOT sure about
Whether the silent drop is deliberate API tolerance or an unchecked filter — the source would tell; I did not read the searchmoves filter code this item.

## 9. A better way
The class-3 token could also have been a syntactically valid but unreachable move (my own-piece capture) AND a syntactically invalid token ("z9z9") — only the first was tested.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long62/stamps.txt
?? forge-combo29/REPORT_deepseek6_long62.md
?? forge-combo29/tests_deepseek6_long62/long62.py
?? forge-combo29/tests_deepseek6_long62/out/
$ ls forge-combo29/tests_deepseek6_long62/
CLAIM.txt
long62.py
out
PREDICTION.md
stamps.txt
```
