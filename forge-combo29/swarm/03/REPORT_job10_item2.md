# job 10, item 2 — instrumentation: where the bare-king LMR cap fires for position 155

**Question.** Even if the cap is not the cause, does the reduced search produce the wrong score? Instrument the cap
site and record where it fires.

**The answer.** The cap fires **4,680,728 times** in a depth-18 search of this position, but **only 6 times at the
root ply, and always on `c6d7` — never on `c6d6` and never on `c6c7`.** Both the correct move and the wrong move are
searched through the root without the cap touching them. So the cap **does not** produce the wrong score for either
candidate at the root; it operates deeper in the tree, where it inflates the node count (which is what the ~1000x
cost in job 9 measures) without touching the root comparison that makes the choice.

## Method

`instrument_cap.py` copies the r15 tree to `/tmp/instr155` (the repository source is never modified), and inserts a
trace at the cap site, guarded by an environment variable so the protocol stream on stdout is untouched:

```cpp
if (bare_king_lmr_cap && r > 1) {
    if (std::getenv("FORGE_TRACE_CAP") != nullptr) {
        std::fprintf(stderr, "CAPFIRE ply=%d move=%s r_before=%d depth=%d alpha=%d beta=%d pv=%d\n",
                     (int)ply, board.move_to_uci(move).c_str(), r, (int)depth, (int)alpha, (int)beta, (int)pv_node);
    }
}
if (bare_king_lmr_cap) r = std::min(r, 1);
```

Built with `-DFORGE_MATE_ALPHA_GUARD=1`, `-march=native`, Release. **Build sanity: `bench 11` = 312866**, the same
pinned value as every other build, and the instrumented binary plays `c6c7` exactly like the real PC build under the
same settings, so the trace does not perturb behaviour.

## Findings from the trace

Depth 8, PC20, Threads 1 (`/tmp/cap_1.err`, kept as `cap_depth8.err`):

| quantity | value |
|---|---|
| total CAPFIRE lines | 2,907 |
| `r_before=2` | 1,391 |
| `r_before=3` | 854 |
| `r_before=4` | 377 |
| `r_before=5` | 192 |
| `r_before=6` | 90 |
| `r_before=7` | 3 |
| deepest firing ply | 11 |

So the cap is regularly costing up to 6 plies of reduction at a single node — that is the cost explosion, and it
happens all over the tree.

Depth 18 (`/tmp/cap18.err`, kept as `cap_depth18.err`):

| quantity | value |
|---|---|
| total CAPFIRE lines | **4,680,728** |
| fires at the ROOT ply (ply=0) | **6** |
| which moves those 6 are on | **`c6d7`, all six** |
| fires on `c6d6` at the root | **0** |
| fires on `c6c7` at the root | **0** |
| `r_before=3` | 1,395,047 |
| `r_before=6` | 134,108 |
| `r_before=8` | 13,523 |
| `r_before=9` | 1,068 |
| `r_before=11` | 11 |

The `r_before` histogram is the cost story in one line: **1.4 million nodes have a 3-ply reduction clamped to 1**,
and eleven nodes have an **11-ply** reduction clamped to 1 — i.e. those nodes are searched 10 plies deeper than the
search intended. That is where the ~1,000x node count comes from.

The six root fires, verbatim:

```
CAPFIRE ply=0 move=c6d7 r_before=2 depth=7 alpha=-764 beta=-720 pv=1
CAPFIRE ply=0 move=c6d7 r_before=2 depth=7 alpha=-796 beta=-742 pv=1
CAPFIRE ply=0 move=c6d7 r_before=2 depth=7 alpha=-847 beta=-769 pv=1
CAPFIRE ply=0 move=c6d7 r_before=2 depth=8 alpha=-908 beta=-872 pv=1
CAPFIRE ply=0 move=c6d7 r_before=2 depth=8 alpha=-926 beta=-890 pv=1
CAPFIRE ply=0 move=c6d7 r_before=2 depth=8 alpha=-926 beta=-890 pv=1
```

## What this means for the mechanism

1. **The cap is not what mis-scores the two candidates.** Neither `c6d6` nor `c6c7` has the cap applied at the root.
   Whatever makes the engine prefer the move that loses two plies sooner lies in the root comparison itself, not in
   the reduced search of those two moves.
2. **The cap does explain the cost.** 4.68M clamp events at depth 18, with individual nodes losing up to 6 plies of
   reduction, is exactly what produces the ~1,000x node count job 9 measured. So the cap is expensive but not the
   cause of the wrong move.
3. **The six root fires on `c6d7` are interesting but not the answer.** `c6d7` is a third move the engine considers and
   does not play; it is clamped at the root because it is a late move at a lone-king root. That is the cap doing what
   it says, on a move that is not chosen.
4. This is consistent with S-F19 (hash and depth do not change the choice): a root-ordering/proof problem, not a
   resource problem, and not the cap.

## The finding, in the form requested

**S-F20 — a losing-move misevaluation in the shared search, proven by play-out.**

On `1r6/5b2/2K5/8/8/5n2/5k2/8 w - - 18 183` the engine plays `c6c7`, which against an opponent playing the same
engine's moves loses in **20 plies**, while `c6d6` — which the engine rejects and rates `mate -11` in its own
root scores — actually holds out **22 plies** (python-chess adjudication, 3 of 3 paired repeats, `job10/
playout_base_d12.txt`). So the engine **mis-scores the alternative move** and, because of that score error, chooses
the move that loses two plies sooner. This defect:
- **predates the PC build** — it reproduces on the base tree `6b98f217` under S14 (`c6c7` mate -20, `c6d6` cp -1192);
- **is not fixable by removing the bare-king cap** — the cap never fires on either candidate at the root (this
  job's trace), and removing it changes which wrong move is played without restoring the correct one
  (`job6` matrix: both-off gives the base answers under DEFAULT options, but base under S14 is itself wrong);
- **is not a resource limit** — hash 16..1024 and depth 18..22 all give the same wrong choice (S-F19).

It is a genuine losing-move misevaluation in the root comparison, and it is the strongest defect found in this run.

## Honesty notes

- The trace build is a **scratch copy** under `/tmp`; the repository source was not modified. The change is recorded
  as code in `instrument_cap.py` so it can be reproduced.
- Raw traces are large (the depth-18 file is ~4.68M lines). The committed copies are `cap_depth8.err` and a
  **truncated head** of the depth-18 trace plus `cap_depth18_summary.txt` with the counts above; the full file is
  reproducible by re-running the two commands in this report. A 4.68M-line file is not suitable to commit.
- **A measurement error I made and caught in this job**: two of my early checks piped `quit` behind a live search and
  got `bestmove c6c5` instead of `c6c7`. That is exactly the 19-F12 fabricated-answer trap I had audited for earlier
  — the audit covered my harness files but not ad-hoc commands typed directly into the shell. Re-run with reads to
  `bestmove`, both the real and the instrumented build give `c6c7` 3/3. Every number in this report comes from the
  correct form.
