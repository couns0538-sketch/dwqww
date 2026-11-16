# deepseek6 long 61 — PREDICTION (written before the first full-set run)

Item (file 15, long 61): **MultiPV.** `MultiPV` 1, 3 and 5 on all of O at depth 10, S14; per position the k lines
are k DIFFERENT legal moves, their scores do not increase down the list, and the first line's move under MultiPV 3
and 5 against MultiPV 1's bestmove. Known: MultiPV 1 set explicitly = plain (long 47).

Model: DeepSeek V4.1 Flash 1017, chat 1794862262. Time: `stamps.txt`.

## Fixed now
- Plain release build `/tmp/ds6/build-release/forge` (sha256 `7c4e1aee…33622`), S14, Threads 1, Hash 16,
  OwnBook false, `go depth 10`, one fresh process per (position, k). 200 positions x 3 k = **600 searches**.
- The check reads the **last complete iteration** that carries exactly k lines, so a partial iteration cannot be
  mistaken for a result. Scores are compared with mate scores ranked above any cp score and by magnitude.
- Legality of every PV move via python-chess 1.11.2.

## Predictions, each with the range that kills it

**P1 — zero violations of all three properties across all 600 reads**: k distinct moves, non-increasing scores,
every move legal. Kill range: any violation — it is the item's headline and the position is named.

**P2 — the first line under MultiPV 3 and 5 equals MultiPV 1's bestmove on at least 170 of 200 positions** (85 %).
MultiPV does not change the top line's move on most positions; where it does, the engine's tie-breaking or the
helper-off path changed the search. Kill range: fewer than 150 of 200 kills P2.

**P3 — MultiPV 5 differs from MultiPV 1 MORE often than MultiPV 3 does.** More lines means more internal
re-search, so more chances for the top move to change. Kill range: the reverse ordering kills P3.

**P4 — the k=5 run's first line NEVER scores lower than the k=1 run's score on the same position.** The best move
of a restricted-to-5-lines search cannot be worse than the overall best (it is a subset). Kill range: any position
where k=5's first-line score is below k=1's score kills P4 — that would mean the MultiPV path is not searching the
same move set, a real defect.

**P5 — budget.** 600 depth-10 searches on O: about 10–20 minutes. Kill range: over 40 minutes I report the
positions done and name the rest.

## What would make me report "not done"
A refused option (MultiPV is in the plain build, so this would mean the wrong binary), a hang, or a run that does
not finish: then the report names how many positions have all three k values and quotes no global count.
