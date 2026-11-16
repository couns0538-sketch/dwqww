# deepseek6 long 53 — PREDICTION (written before the first measuring command)

Item (file 14, long 53): **CARRIED HASH ON GAMES.** Long 48's last part (the positions searched in ONE process
without `ucinewgame`, Hash 16, against the fresh-process rows) on the **first 100 positions of G**, at **depth 12
and depth 14**. Question: do carried entries make the tree bigger on game positions too (long 48 measured **+1.50 %**
on O)?

Model: DeepSeek V4.1 Flash 1017. Time: `stamps.txt`, first line `claim.sh`'s output.

## Fixed now

- Build: the plain 6b98f217 release build, `/tmp/ds6/build-release/forge`, sha256
  `7c4e1aee58d880afade8d8e032028cbf9b92f38e39723f0aaf154ed7fa233622`. The four pins are re-run before the first
  counted run, not quoted from memory.
- **Five runs, all on the first 100 positions of G (in file order):**
  | tag | process model | depth |
  |---|---|---|
  | G100_S14_d12_fresh | one fresh process per position, `ucinewgame` before each | 12 |
  | G100_S14_d12_carried | ONE process, NO `ucinewgame` between positions | 12 |
  | G100_S14_d14_fresh | fresh per position | 14 |
  | G100_S14_d14_carried | one process, no `ucinewgame` | 14 |
  | (the two fresh runs are the baseline for their own depth) |
  That is four runs and two comparisons (d12: carried vs fresh; d14: carried vs fresh). Options S14 + Threads 1,
  Hash 16, OwnBook false in every run.
- The **carried** harness is a different program path from `rows.py` (which is fresh-per-position by design): it
  keeps one engine alive, sends `position fen ...` + `go depth N` for each of the 100, and never sends
  `ucinewgame`. It still sends `isready` and reads every line, and it stops on a refusal.

## Predictions, each with the range that kills it

**P1 — the fresh depth-12 baseline for these 100 positions is between 5.0 M and 5.8 M nodes.** G's full 353 at
depth 12 is 18,466,239 (known); the first 100 are not necessarily proportional, and the positions are game
positions with long trees. Kill range: outside 4.5–6.5 M.

**P2 — carried entries make the G tree BIGGER at depth 12, by +0.5 % to +4 %.** Long 48 measured +1.50 % on O;
game positions have more transpositions *and* more stale-entry mismatches, so I predict the effect survives but
does not explode. Kill range: a NEGATIVE ratio (carried smaller) kills P2; above +4 % also kills it.

**P3 — the effect is LARGER at depth 14 than at depth 12.** Reasoning: a deeper search writes more entries per
position, so the next position starts with a fuller — and staler — table. Kill range: the depth-14 ratio being at
or below the depth-12 ratio kills P3.

**P4 — the carried run changes at least 60 of the 100 best moves at depth 12** (long 48 changed 14 of 50 on O at
depth 12, i.e. 28 %; on G I predict a similar or higher fraction). Kill range: below 30 of 100 kills it.

**P5 — at depth 14 the carried run changes at least as many best moves as at depth 12.** Kill range: fewer.

**P6 — budget.** Two fresh runs (100 positions each at depth 12 and 14) plus two carried runs: I predict
15–30 minutes. Kill range: a single run over 1800 s gets killed and reported as "timeout".

## What would make me report "not done"
A depth-14 run I cannot finish, or a carried run whose process dies mid-way (then the comparison names the number
of positions completed and no ratio is quoted from a partial run). A carried run is compared only against a fresh
run over the SAME positions in the SAME order.
