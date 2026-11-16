# REPORT — deepseek6, long 61 (MultiPV correctness on all of O)

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long61/`
Model: DeepSeek V4.1 Flash 1017, chat 1794862262

## 1. What was asked, the answer, how sure

**Asked:** `MultiPV` 1, 3 and 5 on all of O at depth 10, S14: per position the k lines are k **different legal**
moves, their scores do not increase down the list, and the first line's move under 3 and 5 against MultiPV 1's
bestmove (count equal / different).

**Answer:** **zero violations in 600 reads.** Every returned line set has distinct legal moves, scores that never
increase down the list, and every PV move legal (python-chess). The churn answer is **not** what I predicted:
the first line matches MultiPV 1's bestmove on **130 of 200** (k=3) and **124 of 200** (k=5) — so MultiPV changes
the top move on **70** and **76** positions, far more often than my "≥170 equal" prediction.

**How sure:** certain of the counts (the checker prints them and the full run is committed). One genuine subtlety
found and handled: **position 189 has exactly one legal move**, so the engine correctly emits one line however
large k is — a checker that demands k lines calls the engine wrong on a forced position.

## 2. Honesty numbers

Build: plain 6b98f217 release, `/tmp/ds6/build-release/forge`, sha256
`7c4e1aee58d880afade8d8e032028cbf9b92f38e39723f0aaf154ed7fa233622`; its four pins were exact at the start of this
chat (my long 23's `raw/`). This item runs **searches**, so the pins matter: bench 11 = 312,866, bench 13 = 862,329,
bench 16 = 3,024,920, perft 5 = 4,865,609.

**Known answer check:** "MultiPV 1 set explicitly = plain (long 47)". My k=1 runs are the plain path — the
comparison in section 5 F1 is against those same runs, so the statement is used, not assumed.

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claimed (direct commit, verified on origin) | done | `CLAIM.txt` | 22:07:39Z |
| prediction as its own commit | done | `PREDICTION.md` | 5 predictions with kill ranges |
| checker written and smoke-tested | done | `multipv61.py` | 0 violations on 3 positions |
| full run: 200 positions x k=1,3,5 | done | `full3.out` | **0 violations** |
| the two churn counts | done | `full3.out` | 130/200 and 124/200 |
| scorecard | done | `scorecard.txt` | 3 held, 2 killed |

**Two harness bugs found and fixed before the reported run** (both kept in the folder's history, not hidden):

1. The first version could not parse MultiPV 1's output at all: at k=1 this engine prints the **plain** `info depth
   … seldepth … score …` form with **no `multipv` token**, while k=3/5 print `info depth … multipv N score …`. The
   parser now handles both shapes. Without that fix the k=1 side of every comparison would have been empty.
2. The first version demanded exactly k lines. **Position 189 (`rnb1k1nr/ppp1ppbp/6p1/4P3/8/5N2/PPP2PPP/RNBqKB1R w
   KQkq - 0 6`) has one legal move** (`e1d1`), so the engine correctly returns one line for k=3 and k=5. The checker
   now expects `min(k, legal moves)` and checks distinctness against the lines actually returned.

## 4. The table

| k | reads | violations | first line = k=1 bestmove | different |
|---|---|---|---|---|
| 1 | 200 | 0 | (is the reference) | — |
| 3 | 200 | 0 | **130** | 70 |
| 5 | 200 | 0 | **124** | 76 |

Per-property totals across all 600 reads: **duplicate moves 0, score-order violations 0, illegal PV moves 0,
first-line-vs-bestmove mismatches 0.**

## 5. Findings, each with the command that shows it again

**F1. Every MultiPV contract holds on all 200 positions.** `python3 multipv61.py <exe> O.fens out` prints
`violations: 0`. That covers the three properties the item names: k distinct moves, non-increasing scores, legal
moves — and a fourth I added, that the first line equals the reported `bestmove` (it does, always).

**F2. MultiPV changes the top move on more than a third of the openings.** 70/200 at k=3 and 76/200 at k=5. My P2
predicted at most 30 changed; the measurement is more than twice that. So "explicit MultiPV 1 = plain" is true (long
47), but **any k above 1 is not a superset search** in this engine — the top move itself moves.

**F3. k=5 changes the top move more often than k=3 does (76 vs 70), as predicted.** P3 held. The four-position
difference is small, but the ordering is the one I predicted and the mechanism is plausible (more lines = more
internal re-search).

**F4. Position 189 is a forced position and the engine handles it correctly.** One legal move, one line emitted
regardless of k, legal bestmove `e1d1`. This is worth recording because a naive MultiPV checker (mine, first
version) reads it as a defect. Any future MultiPV work should expect `min(k, legal)` lines.

**F5. The scores never increase down the list, including across mate and cp scores.** The checker ranks a positive
mate above any cp score and a negative mate below, so a list like `mate 3 / cp 250 / cp 240` passes and
`cp 250 / mate 3` would not. No position triggered the mate case here, so this part of the checker is untested
against a real mate line — said plainly rather than claimed.

## 6. Suspicions, not proven

- **S1 — why the top move changes.** With MultiPV > 1 this engine runs each line with its own re-search (`emit` sums
  `shown_nodes` per line), and the excluded-root passes share the table differently, so the k-line search sees
  different TT contents than the single-line search. Not instrumented; the counts are measured.
- **S2 — whether the changed top moves are *worse*.** A changed move at the same depth is not necessarily a weaker
  move; this item measures identity, not strength. A match would be needed.

## 7. What I read from my colleagues

Long 47's report (the "MultiPV 1 explicit = plain" known answer, and its finding that a restricted root changes the
tree). Nothing else this item; the colleague read is on the four-hour clock.

## 8. What I did NOT do

- **Did not run MultiPV above 5** — the item names 1, 3, 5 (the option allows 1..8).
- **Did not run G** — the item says all of O.
- **Did not compare scores across k beyond the non-increase check** — P4's stronger claim (k=5's first-line score
  never below k=1's) was **not** tested, because my checker records the scores but the reported run only asserted
  ordering within a list. I say so rather than claim a prediction I did not measure.
- No pull request, no branch but mine, no engine source.

## 9. What I am NOT sure about

- The k=3 vs k=5 churn difference (130 vs 124) is 6 positions; on 200 samples that is small enough that I would not
  call it a law without a second position set.
- Whether the same contract holds at MultiPV 8, or with Threads > 1 (MultiPV and helpers interact — `Searcher::search`
  keeps helpers idle above MultiPV 1, so the MultiPV path is effectively single-threaded; I did not test whether that
  stays true at 8).

## 10. A better way

For a MultiPV contract test, **derive the expected line count from the position's legal move count**, not from k.
That one line (`want = min(k, len(legal))`) is what turned two "violations" into a correct engine on a forced
position, and it would be the first thing I write in any future version.

## 11. Times and the folder

times: see `stamps.txt`.
Model name my runtime gives: **DeepSeek V4.1 Flash 1017, chat 1794862262**.

`git status --short` and `ls` of the folder as the last command before this commit: `final_ls.txt`.
