# REPORT - deepseek job 4

Branch `for-fable-and-opus/deepseek-work`. The branch's `src` and `include` are
untouched; for part A I built a private copy with tracing and committed the diff as
`tests_deepseek_job4/trace_patch.txt`.

## 1. Table

| part | done / partly / not done | evidence files | result in one line |
|---|---|---|---|
| A the mechanism of F1 | done | `logs/A1-trace-summary.txt`, `trace_patch.txt`, `a_drive.py` | the node after `Kd8` is entered at **depth 1** and leaves through **`qsearch` (line 1557)** with `depth 0`, so the move loop never runs and `Kf7` is never tried |
| B how often, and switch costs | done | `logs/B-*.json`, `logs/B-bench.txt`, `b_setting.py`, `b_bench.py` | with a clean table: mate2 **1000/1000** all settings; mate3 **975/1000** default, **999/1000** with `RfpDepth 0`, **954** with `SoundMatePruning true`; bench 13 nodes 862329 (default) to 1260718 (`RfpDepth 0`) |
| C what to change | done (text only) | `proposal.diff.txt` | add a fourth `sound_mate_case` arm behind a new default-off switch `MateWindowGuard`; **not measured** - see below |
| D1 en passant / castling / promotion mates | **partly** | `logs/D1-special.json`, `logs/D1-D2-results.txt`, `d1_special.py` | en passant **20/20**, promotion **20/20**; **castling: 0 positions built, not tested** |
| D2 depth-16 retry of job 3's B6 misses | done | `logs/D2-run.json`, `logs/D1-D2-results.txt` | **18/18 correct at depth 16** with a clean table (16/18 already at depth 12) |
| D3 the 11 job-3 B1 misses | done | `logs/D3-results.txt`, `logs/D3-tt-effect.txt`, `d3_misses.py` | 10 of 11 report the correct `mate 2` at depth 12 with a clean table; F1 still reports mate 4 at depth 12 and mate 2 at 18 |

## 2. Findings, most costly in a real game first

**F1 (new, and it corrects my own job 3 report). The mate distance the engine reports
depends on the transposition table.** The same position, same depth, same binary gives
a different mate distance depending only on what was searched before it:

```
2Q3KR/4k3/8/8/8/8/8/8 w - - 0 1   (truth: mate in 2 moves)
  isolated, fresh process    : score mate 4
  after 5 other positions    : score mate 3
  after 5 others + ucinewgame: score mate 4
```

`ucinewgame` clears the table and restores the value, so entries from unrelated
positions are changing the answer. This is why job 3's B1 reported 11 misses and B6
18 misses: **that harness ran 100-250 positions in one process without `ucinewgame`
between them.** With `ucinewgame` before each search, 10 of the 11 B1 misses report
the correct `mate 2` and 16 of the 18 B6 misses are correct at the same depth. So the
job 3 numbers overstated the defect; the surviving defect is F2 below. I did not
investigate *how* a foreign entry changes the reported distance, only that it does.

**F2 (the real one, reproduced and unchanged). The one position that is wrong even
with a clean table** is `2Q3KR/4k3/8/8/8/8/8/8 w`: `mate 4` at depths 12-16, `mate 2`
only at depth 18. Its mechanism is part A: the node after `Qc6 Kd8` is searched at
depth 1 and the search drops into quiescence without ever trying the quiet mating move
`Kf7`. That is a genuine horizon defect and it is what Fable reproduced on the PC.

**F3. `SoundMatePruning true` makes mate3 *worse*, not better** (954/1000 vs 975
default), while `RfpDepth 0` makes it much better (999/1000). Since
`SoundMatePruning` is the switch that skips move-loop pruning on PV/in-check/mate-alpha
nodes, this says the mate3 misses at 20,000 nodes are mostly **not** caused by that
pruning block; switching reverse futility off is the effective lever.

**F4. Special moves are handled correctly**: en passant 20/20 and promotion 20/20,
each being the *only* mating move.

**F5 (process finding). My job 3 harness was wrong** in a way that mattered: it did not
clear the transposition table between positions, so its per-position results were
contaminated by earlier positions. Job 3's Part A numbers are unaffected (a separate
process per net via `b2_compare.py`), but B1, B3, B6 and B4's 50-position sets are all
affected. This is the third harness bug across these jobs that I have had to correct
in public; the pattern is that I test the engine and not the harness.

## 3. Part A in plain sentences, then the evidence
**In plain sentences.** Walking down the principal variation of the depth-4 search
from the position after `Qc6`, the root move is `Kd8` and the search then plays
`Qd6`. The node that matters is white-to-move after `Kd8`, i.e.
`3k2KR/8/2Q5/8/8/8/8/8 w - - 2 2`, where `Kf7` is mate in one. That node is reached at
**depth 1**, with alpha/beta `-31999/31998` (a full window, and it *is* a PV node:
`pv 1`). Before its move loop starts, `HindsightDepth` recomputes the depth from the
mover's static-eval loss; the depth becomes **0** and the function returns
`qsearch(...)` at line 1557. Quiescence search only looks at captures, promotions and
checks that arise *from those*, so a quiet king move like `Kf7` is not in its move set
and the mate is never seen at this node. `gives_check` is not at fault: I compiled a
small test against `Board` from the branch source and `gives_check(Kf7) = 1`, and after
the move black has zero legal replies. The move is not pruned as a quiet non-check; it
is simply never generated, because the node never enters the move loop.

**Why `SoundMatePruning true` makes the mate appear.** It changes which nodes skip the
move-loop pruning block: PV nodes, nodes in check, and nodes whose alpha is already a
mate score are no longer pruned (`src/search.cpp:1833-1843`). More nodes are searched,
so the depth-4 tree reaches the mate. This is an indirect effect on tree shape, not a
direct "this rule was dropping the mating move" - the mating node is not in the move
loop at all (it returns through `qsearch`), which is why switching a *move-loop* rule
on can still help: the extra nodes change the reduction decisions above it.

**Why `RfpDepth 0` and `QuietExtinction true` do not reproduce here.** Fable reported
that `RfpDepth 0` or `QuietExtinction true` makes `mate -1` appear at depth 4 from
this root. On my build at this root they do not: default, `RfpDepth=0` and
`QuietExtinction=true` all report a centipawn score (`cp -1509`, `cp -1463`,
`cp -1509`), and **only `SoundMatePruning=true` gives `mate -1`**. So I confirm the
`SoundMatePruning` result and cannot confirm the other two. It is possible Fable's
depth-4 root was the game position rather than the after-`Qc6` position (the two
searches differ); I did not check that, so I record the disagreement as a
disagreement and not as a refutation. In part B, `RfpDepth 0` is the setting that
improves the mate3 score most, so it does matter - just not at this root at depth 4.

**Evidence.** `logs/A1-trace-summary.txt` holds the two decisive trace lines:

```
NODE ply 1 depth 1 a -31999 b 31998 pv 1 chk 0 eval 1166 mv e7d8 fen 3k2KR/8/2Q5/8/8/8/8/8 w - - 2 2
RET qsearch_depth0 line 1557 ply 1 depth 0 a -32001 b 32001 pv 1 fen 3k2KR/8/2Q5/8/8/8/8/8 w - - 2 2
```

and the `gives_check`/mate test output. The `HindsightDepth` block that reduces the
depth is `src/search.cpp:1610-1634` at commit `6b98f217`.

## 4. Which files of the repository I opened

- `src/search.cpp` (the `FORGE_NNUE_V3_VERIFY` block in job 3; in this job the reverse
  futility rule, the `SoundMatePruning` block, the `HindsightDepth` block, the move
  loop, and the `Worker::search` signature)
- `include/forge/search.hpp` (the `SoundPruneArm` helpers, tunable declarations)
- `src/uci.cpp` (the `eval` handler and the option table)
- `include/forge/nnue_v3.hpp`, `src/nnue_v3.cpp` (job 3, for the reference evaluator)
- `CMakeLists.txt` (unchanged)
- On the handoff branch: `FABLE_TO_deepseek_1..4.md`
- Not opened: any other implementation of the net (job 2 rule), `ci/fable-opus-checks`

## 5. Start and end of each part, recorded stamps

| part | start | end | wall |
|---|---|---|---|
| reading job 4, tracing copy, first trace build | 11:50:48 | 11:52:06 | ~1 min |
| A: instrumenting returns, tracing, `gives_check` test | 11:52:06 | 12:01:00 | ~9 min |
| B: generating 1,000+1,000 mate positions | 11:53:34 | 11:57:00 | ~3.5 min (background) |
| B: six settings x 2 classes, and bench 13 | 12:00:37 | 12:01:26 | ~1 min |
| C: proposal written | 12:01:00 | 12:05:00 | ~4 min |
| D1: en passant/castling/promotion generator + run | 12:06:06 | 12:07:37 | ~1.5 min |
| D3: per-position retry, then the TT discovery | 12:01:30 | 12:10:00 | ~8 min |
| D2: depth-16 retry, with and without a clean table | 12:07:48 | 12:10:30 | ~3 min |
| writing this report | 12:10:30 | 12:22:00 | ~11 min |

**Total: about 31 minutes of the 60 allowed.** (Job clock start 11:50:48.)

## 6. What I did not do

- **Part C's proposal is not measured.** The job asks for "its part-B row measured
  with your private build". I did not implement `MateWindowGuard` in the tracing copy,
  so there is no row for it. The diff is a design, not a result.
- **D1 castling: nothing.** The generator placed the enemy king first and could not
  produce a legal pre-castling position (228 of 228 reconstructions failed
  `is_valid()`, because the stepped-back rook gave check to a king that was
  supposed to be un-checkable). I did not get 20 castling mates.
- **Part B's mate positions come from 3-10 pieces as asked**, but I did **not**
  cross-check them against a second brute-force implementation in this job; I used the
  corrected search from job 3, which was cross-checked on 300 positions there.
- **`QuietExtinction` does not reproduce here** (see part A); I did not chase why.
- I did not test what a *stale* table does with the `SoundMatePruning` or
  `RfpDepth 0` settings; all B numbers are with `ucinewgame` before every search.
- I did not run the PC's 20,000-position VERIFY campaign, nor re-run job 3's Part A.
- I did not change the branch's engine source.

## 7. What I am not sure about

- **The TT effect (F1) might be a symptom of something worse.** A foreign entry
  changing a mate distance means the entry is being used where it should not be
  (`halfmove_clock < 90` and the mate-score guards are the obvious suspects). I have
  only shown that the answer changes, not which stored field leaks into the answer.
  If Fable can make a stale entry turn `mate 4` into `mate 3`, it may also make a
  losing position look won, which would be much more costly than a slow mate.
- **Part A's mechanism is established for the depth-4 search only.** I traced that
  search; I did not trace the depth-12/18 searches where the same position behaves
  differently. The HindsightDepth reduction could be doing something different there.
- **My part A conclusion has already been revised once** (I first thought
  `gives_check` was wrong and that `g_f7` mated from the wrong node). The two
  corrections are in the transcript and both were caught by checking rather than by
  reasoning.
- **Part B's "exact distance" and "shortest-mate move" columns are identical for every
  setting.** That is suspicious: it could be true (when the engine's score is the
  right mate distance it is also looking at a mating move) or it could be that my
  `keeps_shortest_mate` is too lenient. I did not test the function against a position
  where the score is right and the move is wrong.
- **`bench 13` node counts are deterministic here** (862329 three times), which makes
  the cost column trustworthy, but the node *counts* under a switch are not a measure
  of strength.

## 8. A better way

**8.1 Clear the table between measured positions, and say so in every job text.** My
job 3 and job 4 numbers disagree because the harness cached across positions. A job
that measures per-position search behaviour should require `ucinewgame` before each
`go` (or a fresh process per position) and should say which. Cheap check that it is
better: run one 100-position set both ways and see whether the pass rate moves; if it
does, the harness was measuring the table as much as the search.

**8.2 Ask for the transposition-table effect directly.** The finding above only
surfaced by accident. A small job: take 50 positions with a known mate distance, search
each in a fresh process, then search them again in one process in 50 different orders,
and tabulate the distance per position per order. If the distance depends on order,
the table is being used unsoundly, which is a correctness question rather than a depth
question.

**8.3 For D1, build castling mates by stepping back from the finished pattern but
placing the *attackers* last.** My generator put the enemy king first, so once the
castled rook stepped back to a1/h1 it was giving check in the pre-position and the
position was illegal. Placing the enemy king after choosing the attackers, and
rejecting any pre-position where the side not to move is in check, should give a hit
in a few hundred attempts rather than none.
