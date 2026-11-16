# REPORT — seat 03, job 12: does the wrong choice survive at the owner's MATCH budget, `go nodes 20000`?

**What was asked.** Take the four positions where the engine's choice was worse by play-out and check whether the
same wrong choice appears at `go nodes 20000` — the owner's match budget. If it does, S-F20 stops being a deep-search
curiosity and becomes something his matches can hit.

**The answer: yes — 4 of 4.** The wrong choice is identical at `go nodes 20000` and at `go depth 16` in **all seven**
positions tested (four positive-cost cases, three controls). It is deterministic, 3 of 3 repeats on each of the four.
Node-limited and depth-limited search therefore agree, which means S-F20 is reachable in the owner's matches and is
not an artefact of deep iteration.

**How sure.** High. Every answer was read to `bestmove` with a fresh process, PC20, Threads 1, Hash 16; the harness
refuses an answer with no preceding `info depth` line; and the four positive-cost positions were repeated three times
each, identically.

## Results (`nodes20k.txt`)

| idx | role | play-out cost | free at `nodes 20000` | free at `depth 16` | same? | chosen score (nodes) | alt score (nodes) |
|---|---|---|---|---|---|---|---|
| 6 | positive | +21 | e3f3 | e3f3 | **SAME** | cp 0 (18,422) | cp −944 (14,293) |
| 16 | control | +2 | h7g6 | h7g6 | SAME | cp −1907 (10,587) | cp −2045 (15,430) |
| 22 | positive (also d16) | +23 | g5f6 | g5f6 | **SAME** | cp 0 (19,503) | cp −953 (14,731) |
| 30 | control | −32 | c7d7 | c7d7 | SAME | cp −490 (17,668) | mate −2 (3,709) |
| 36 | control | −26 | c4d5 | c4d5 | SAME | cp −432 (14,865) | cp −915 (12,728) |
| 37 | positive | +23 | f6f7 | f6f7 | **SAME** | cp 0 (17,339) | cp −725 (5,228) |
| 44 | positive | +38 | c7d6 | c7d6 | **SAME** | cp 0 (3,798) | cp −439 (12,595) |

Determinism, `go nodes 20000`, three fresh processes each:

```
idx 6   e3f3 e3f3 e3f3
idx 22  g5f6 g5f6 g5f6
idx 37  f6f7 f6f7 f6f7
idx 44  c7d6 c7d6 c7d6
```

## What this means, stated carefully

The important thing is **not** the score column — it is that at 20,000 nodes the engine picks exactly the move the
deeper search picks, on all four positions where play-out says that move is worse. So:

1. **S-F20 is reachable in the owner's matches.** A 20,000-node search is what his match files use; the wrong move is
   not something only a depth-16 search produces.
2. **The budget does not explain it.** If this were merely "not enough search", the node-limited run would be the
   wrong one and the deeper run would correct it. Instead both budgets agree — the choice is stable across a 10x
   difference in effort, which points at the ordering/comparison rather than at resources, consistent with S-F19
   (hash and depth did not change it either) and S-F21 (the cap does not touch either candidate).
3. **A caveat I will not hide:** in three of the four positive-cost rows the chosen move scores **cp 0** at 20,000
   nodes while the alternative scores −725 to −953. cp 0 in a bare-king endgame is the drawn-root/insufficient-material
   answer (FABLE_TO_swarm_3, and S-F24 below), not a genuine evaluation. So the engine is very likely choosing on the
   strength of a "this is a draw" adjudication that the play-out contradicts. That is a concrete, testable hypothesis
   for the cause of S-F20 and I name it as a hypothesis, not a result.

## Prediction against result

| # | predicted | killed? | measured |
|---|---|---|---|
| 1 | 2-3 of the 4 positive-cost positions keep the wrong move at `nodes 20000` | no (exceeded) | **4 of 4** |
| 2 | 2-3 of 3 controls keep the same move | no (exceeded) | **3 of 3** |
| 3 | 0 missing/illegal bestmoves | no | 0 |
| 4 | determinism 7 of 7 | no | 7 of 7 (and 3/3 twice more on the four) |
| 5 | every run reports >= 20,000 nodes and under 200,000 | **no — killed in spirit** | the *last info line* shows 3,798-19,503 nodes because `go nodes` stops mid-iteration; the reported total is the last completed info line, not the budget. Recording this rather than calling it a pass. |

Prediction 1 and 2 were exceeded in the direction that strengthens the finding; prediction 5 is stated honestly as
not what I expected — `go nodes N` reports the node count of the last *completed* iteration, so the visible count can
be below N.

## Findings

| id | one sentence | reproduce |
|---|---|---|
| S-F25 | **The S-F20 wrong move reproduces at the owner's match budget**: on all 4 positions where play-out says the engine's choice is worse, `go nodes 20000` picks the same move as `go depth 16` (and 3/3 deterministic), with the three controls also agreeing — so the defect is reachable in his matches and is not a deep-search artefact. Build: PC r15; settings: PC20, Threads 1, Hash 16, `go nodes 20000` and `go depth 16`, fresh process per search. | `cd forge-combo29/swarm/03/job12 && python3 nodes_budget.py /tmp/n.txt` |
| S-F26 | In 3 of those 4 positions the engine's chosen move scores **cp 0** at 20,000 nodes while the alternative scores −725 to −953, in bare-king endgames where cp 0 is the drawn-root/insufficient-material answer rather than an evaluation — a concrete hypothesis for S-F20's cause: the engine chooses on a "drawn" adjudication that play-out contradicts. | same command; see `nodes20k.txt` score columns |

## Suspicions, not proven

- That the cp 0 adjudication is what drives the choice (S-F26). Testable: rebuild with `FORGE_FIX_ROOT_DRAWN`
  disabled, or with the material check relaxed, and re-run these four. Not done here.

## What I did NOT do

- Did not test the other match budgets (`go nodes 50000`, `250000`). The owner's files use all three; 20,000 was the
  one asked for.
- Did not build a variant to isolate the cp 0 hypothesis.
- No sanitizer runs.

## What I am NOT sure about

- Whether "same move at both budgets" holds for positions beyond these seven. Seven is what I had with play-out
  evidence; a wider sweep would need play-out adjudication for every position, which is the expensive part.

## Times

`job12/stamps.txt`.
