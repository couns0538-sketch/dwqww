# REPORT — deepseek6, long 60 (40 self-play games under ASan + UBSan, driven by python-chess)

for-fable-and-opus/deepseek6-work · folder tests_deepseek6_long60/ · claimed with claim.sh (the claim line in stamps.txt); PREDICTION.md before the runs; two driver fixes during the item, both disclosed.

## 1. Three lines
**Asked:** 40 games of the plain build against itself at `go nodes 20000` under ASan+UBSan, driven move by move by python-chess from the first 40 positions of O, ending by python-chess's rules or at 300 plies.
**Answer:** **all 40 games completed: ZERO crashes, ZERO sanitizer lines, ZERO illegal moves — 28 ended by threefold repetition, 11 by checkmate, 1 by insufficient material; none reached the 300-ply cap.** Every move of every game was legal (the driver validates each engine move against python-chess before pushing; any illegal move would have ended that game with a recorded move list — none did). My prediction 3's guess ("30-40 games end at the ply cap") is WRONG — the 20,000-node games actually FINISH (the threefold rule fires at ~50-170 plies); its kill condition (an unrecorded ending) never fired. The engine answers every move request (after two driver-side bugs of mine, both fixed and disclosed in 4.2 — neither was the engine's).
**How sure:** certain — 40 independent games, 4,000+ engine searches, all validated by an independent rules implementation.

## 2. Honesty numbers
The sanitizer build /tmp/l46_san/build/forge; the 40 game records in out/game_*.txt; the summary in out/summary.txt.

## 3. Step table
| step | done | evidence | result |
|---|---|---|---|
| claim via claim.sh | done | stamps.txt | exit 0 |
| the 40 games | done | out/game_*.txt, selfplay_out.txt | all completed; 0 crashes/san/illegal |
| the endings | done | the reasons table | 28 threefold / 11 checkmate / 1 insufficient / 0 cap |
| the driver fixes | done | two commits | (1) a shared function-attribute counter raced across the 4 parallel games; (2) an O(n²) whole-list scan starved the reader thread at long games — both replaced with tail scans |
| prediction own commit first | done | PREDICTION.md | 1, 2, 4 held; 3's guess wrong (the games finish by rule) |

## 4. Findings
1. **The engine plays complete, rule-valid games under the sanitizer**: 40 games × 50-170 plies × 20,000 nodes each, every move legal, no crash, no sanitizer line — the self-play path is as robust as the single-search path.
2. **The game endings are dominated by threefold repetition** (28 of 40) at this node count — 20,000 nodes per move repeats positions often; a real-games observation for whoever tunes the repetition scoring.
3. Suspicions, not proven: none.

## 6. What I read from my colleagues
File 15 (the item).

## 7. What I did NOT do
Opening-book or ponder modes in the games (the item's plain setup only).

## 8. What I am NOT sure about
Nothing material.

## 9. A better way
The first driver version's two bugs (a shared attribute; a full-list scan) both came from writing the concurrency casually — the pattern "per-game state in locals" should have been the first draft.

## 10. times: see stamps.txt
## 11. model name my runtime gives: glm-5p3-flash

## 12. The last command before this report commit
```
$ git status --short
 M forge-combo29/tests_deepseek6_long60/out/game_12.txt
 M forge-combo29/tests_deepseek6_long60/out/summary.txt
 M forge-combo29/tests_deepseek6_long60/selfplay_out.txt
 M forge-combo29/tests_deepseek6_long60/stamps.txt
?? forge-combo29/REPORT_deepseek6_long60.md
$ ls forge-combo29/tests_deepseek6_long60/
CLAIM.txt
out
PREDICTION.md
selfplay60.py
selfplay_out.txt
stamps.txt
```
