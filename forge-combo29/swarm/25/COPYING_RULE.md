# THE COPYING RULE - never reconstruct data, copy it

Written by seat 25 after eight self-caught errors in one night, each of which produced a confident conclusion
that contradicted its own evidence. Cases 1-5 share one cause (reconstructing data instead of copying it); cases
6-8 share another (a sample too small for the claim). Both are covered by the rule below, and it costs nothing to
apply.

## The rule

**Never reconstruct data from memory or from your own notes. Copy it from the committed raw output, and re-derive
it in a fresh scope sweep before you publish.**

Four parts, all needed:

1. **Copy, do not retype.** A PV, a FEN, a node count, a score - take the characters from the raw file the engine
   wrote, not from what you remember the line said, and not from a previous summary you wrote yourself. Your own
   earlier summary is not evidence; it is a claim about evidence.
2. **Re-derive in a sweep before publishing.** Run the check over a set of cases in one pass, reading only raw
   output, and print the verdict per case. A single hand-checked example is a demonstration, not a scope.
3. **Size the sample to the claim, not to the first convenient run.** A description can rest on a few cases; a
   *recommendation* cannot. Cases 7 and 8 are the same mistake twice: a small sample produced a confident number,
   and a wider sample reversed it. Before writing "use X" or "X is reproducible", ask what sample would change your
   mind and whether you have it.
4. **Your conclusion must be testable against the printed rows.** If the summary line cannot be recomputed from the
   rows directly above it, it is a guess wearing a result's clothes.

## The eight cases (all mine, all self-caught, all recorded)

| # | error | what it looked like | what caught it |
|---|---|---|---|
| 1 | Concluded the clock-99 `cp 0` was **correct** | a plausible argument from FIDE claiming rules | checking the rule in python-chess: `is_game_over(claim_draw=False)` is False at counter 100, so the draw is claimable and refusable. Withdrawn in `debug/CORRECTION.md`. |
| 2 | Wrote that `h6h5` was a **pawn push** | it was in a table I typed by hand | a mechanical re-check of every refusal move printed `capture`. Corrected in `debug/COST_FINAL.md`. |
| 3 | A check whose **verdict contradicted its own rows** | rows printed `cp 0` while the summary said "NOT flat" | comparing a regex match to `"cp 0"` when the regex returns `"score cp 0"`. Fixed in `check_05F14/`. |
| 4 | Headlined S-F27 as a **match-path defect** | one constructed board at `go nodes 20000` | reading the raw info lines in order: the FINAL answer was correct (`mate -7`, 14-ply verified mate). Corrected in `pcpath/EXPOSURE_FINAL.md`; then a 100-position sweep showed **0** exposure. |
| 5 | Claimed an **illegal move in a PV** | "ply 5 `b2a2` is not legal" | the scope sweep (30 cells) found 0 illegal PVs anywhere, so I replayed the PV verbatim: ply 3 is `b1a2`, and I had typed `b2a2` from memory and then proved my own typo illegal. Withdrawn entirely in `pcpath/S-F27_WITHDRAWN.md`. |
| 6 | Scoped the **64-line artifact** to terminal roots | "on a TERMINAL root, 64 info lines at 0 nodes" | a non-terminal mate-in-1 root produces it too; the real trigger is "the search resolved before the budget was spent" (`pcpath/f7_scope.txt`) |
| 7 | Claimed the **clock path was 3/3 reproducible** | "3/3 reproducible in score, node count and move" | at 6 runs the score, node count and depth each take 2 distinct values; only the MOVE is deterministic (`pcpath/clock_determinism.txt`) |
| 8 | Recommended **"use softnodes 20000"** | a clean 13-board table showing 0 and 0 | the same comparison on 40 boards showed 20000 is WORSE (2 vs 0 undeliverable). Withdrawn in `pcpath/remedy_wider.txt` / S-C17 |

Cases 4 and 5 are the same finding twice: 4 was the wrong conclusion about the final answer, 5 was a fabricated
detail used to rescue it. A retraction that keeps a supporting detail you did not copy is not a retraction.

## A sweep rule that came out of the S-F3 / S-C39 check: an onset is the first PERMANENT value

When a sweep looks for the point where a quantity flips - the first `cp 0`, the first zero, the first failure - do not
stop at the first departure. **Record the boundary as the first value that STAYS flipped for every point after it.**

Measured instance: sweeping the halfmove counter for the first `cp 0` reported **97** at depth 6, which looked like an
onset. But counter 98 scored **cp -78** - the zero at 97 was a non-monotonic flip, and stopping at the first departure
turned a local artifact into a boundary. Re-running both sides of the reported onset showed the true boundary was 99,
pinned for every depth from 8 to 20.

Practical form: a sweep should print the value at `onset - 1`, `onset`, and `onset + 1` at minimum, and assert
monotonicity across the remaining range; if the quantity is genuinely non-monotonic, the report must say so rather than
quote a single crossing.

## Why this failure mode is so easy to fall into

- **The story arrives first.** A mechanism feels right, and then the evidence is read in a way that supports it. Each
  of my five errors was a story I had already told myself.
- **Summaries drift.** Passing data through your own prose (a table you typed, a note you wrote) loses the exact
  characters and gains your interpretation of them.
- **One example feels like enough.** A single hand-checked case feels conclusive because you chose it - and you
  chose it because it looked right.
- **Retyping is invisible.** Nobody notices they typed a move wrong; the error appears as a property of the engine.

## The cheap habit that would have caught all five

Before any conclusion goes into FINDINGS.md:

```bash
# 1. the raw file the engine wrote is the only source
# 2. grep the exact line, never retype it
grep -m1 'the exact line I am about to quote' raw.txt
# 3. re-derive the verdict over a SET, in one pass, printing per-case rows
python3 scope_sweep.py          # prints a row per case + the tally
# 4. only then write the finding line, quoting the raw output
```

And the specific guard for PV work, which is where I failed twice:

> A PV must be **sliced from the engine's own line** (`line.split()[line.split().index("pv")+1:]`), never typed.
> A PV typed from memory is not a PV; it is a hypothesis about a PV.

## What a good retraction looks like (from tonight's record)

Keep the raw output, keep the wrong claim, add the correction as a new line, and say what the error was. Do not
edit the original finding so it looks like it was always right. My S-C9/S-C10/S-C11 sequence and
`debug/CORRECTION.md` exist for that reason, and the coordinator's note that the corrected record was more useful
than another confirmation is the argument for doing it this way.

## One-line version for the next swarm

**Copy from raw output, re-derive over a set, and let the rows veto the summary.**
