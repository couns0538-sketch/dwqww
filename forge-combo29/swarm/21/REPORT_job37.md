# REPORT job37 — the drawn-root change loses the DRAW SCORE on the PC build

**What was asked.** (File 6's complement.) File 6 says a draw by repetition or the fifty-move rule
scored 0 is not a defect, and that a mate ending by half-move 100 outranks it. job36 tested the mate
case. This job tests the other side: at a drawn root with **no mate available**, does the engine
score it 0?

**The answer.** On the **base build, yes** (`cp 0`, 0 nodes). On the **PC build, NO** — it searches and
reports a **winning score**: `cp 199` at depth 10 on a K+P vs K board at halfmove 100, and
`cp 207–298` on the repetition case. That is a real behavioural difference introduced by the patch's
`FORGE_FIX_ROOT_DRAWN`, and it is the opposite of what file 6 describes: the drawn root is no longer
scored a draw.

**How sure.** High on the measurement; the score appears in the raw engine line, on two fresh
processes, with and without PC20 options.

```
base, no options:  info depth 10 seldepth 10 score cp 0   nodes 0    pv
pc,   no options:  info depth 10 seldepth 17 score cp 199 nodes 6221 pv e2e3 e5d5 e1e2 d5e4 ...
pc,   PC20:        info depth 10 ...                (same shape, cp 207-298)
```

## Table (pasted from `job37/run2.log`)

| build | case | go | nodes | score | bestmove |
|---|---|---|---|---|---|
| base | rep3_nomate | `go depth 10` | 0 | **`cp 0`** | `e2e3` |
| base | rep3_nomate | `go nodes 100000` | 0 | **`cp 0`** | `e2e3` |
| base | hm100_nomate | `go depth 10` | 0 | **`cp 0`** | `e2e3` |
| base | hm100_nomate | `go nodes 100000` | 0 | **`cp 0`** | `e2e3` |
| pc | rep3_nomate | `go depth 10` | 7,734 | **`cp 238`** | `e1f2` |
| pc | rep3_nomate | `go nodes 100000` | 93,148 | **`cp 298`** | `e2e3` |
| pc | hm100_nomate | `go depth 10` | 5,602 | **`cp 207`** | `e2e3` |
| pc | hm100_nomate | `go nodes 100000` | 99,293 | **`cp 258`** | `e2e3` |
| base & pc | kvk, knvk, kbvk (insufficient material) | both forms | 0 | `cp 0` | legal |

The insufficient-material roots are correctly 0 on **both** builds — the patch kept that part
(`root_drawn = ... board.is_insufficient_material()`).

## Why this happens (a code read, labelled as such)

In the PC tree, `src/search.cpp:2571-2582`:

```
#if FORGE_FIX_ROOT_DRAWN
    const bool root_drawn = !legal.empty() && board.is_insufficient_material();
#else
    const bool root_drawn = !legal.empty() && (board.is_repetition() || board.halfmove_clock() >= 100 ||
                                               board.is_insufficient_material());
#endif
```

So with the fix, a repetition or fifty-move root is **searched** rather than adjudicated. That is
what file 6 describes and is deliberate. But the search does not then apply the draw rule at the
ROOT: it returns an ordinary evaluation (+199 for a pawn up), because the fifty-move/repetition
condition is now only tested inside the tree, not at the root. The result is that a root the rules
call drawn is reported as won.

## What this means

- **For the owner's matches**: if the match program adjudicates by its own rules (file 6 says it
  ends the game at the third occurrence and the 100th half-move), the SCORE does not change the
  result — the game is already over. So this may be harmless in match play.
- **For self-play and for any analysis**: the engine's reported score at such a root is wrong by
  about 2 pawns. A training loop that records the search score, or an analysis tool that shows it,
  will see a "winning" evaluation for a drawn position.
- **For the base tree**, the old behaviour (`cp 0`) is correct but has the flaw file 6 named (it also
  suppressed a real mate). The PC's version fixes the mate case and loses the draw score. Neither
  build does both at the root.

## Prediction outcome

| prediction | outcome |
|---|---|
| P1 base: drawn root with no mate answers `cp 0`, 0 nodes | **held** |
| P2 PC: the same root answers `cp 0` | **FAILED** — it answers `cp 199–298` |
| P3 base: hm100 with no mate answers `cp 0`, 0 nodes | **held** |
| P4 PC: the same hm100 root answers `cp 0` | **FAILED** — `cp 207–258` |
| P5 insufficient-material roots `cp 0` on both | **held** |
| P6 legal moves, 0 crashes | **held** |

## Two errors of mine in this job, both recorded

1. My **first version of the boards had a mate in 1** (`6k1/5ppp/…/3R2K1` mates with `d1d8`), so the
   "no mate" premise was false and the PC build finding the mate was correct. I fixed the boards and
   added **assertions that the boards really have no mate**, so the test cannot silently go void again.
2. My **first repetition cycle was illegal** (`e3e2` after the pawn had moved), which crashed the
   script. The final cycle (`e1f1 e5d5 f1e1 d5e5`, twice) is verified by python-chess to give a real
   threefold with no mate at the root.

## Findings

`21-F19 | NEW` — on the PC build, a drawn root (threefold repetition, or halfmove 100) with **no
mate available** is reported as a **win**: `cp 199` on K+P vs K at halfmove 100 (depth 10), and
`cp 238–298` on the repetition case, where the base build reports `cp 0` with 0 nodes. Insufficient
material is still correctly 0 on both. Cause (code read): with `FORGE_FIX_ROOT_DRAWN` the root-draw
test shrinks to insufficient material only, and the search does not re-apply the fifty-move or
repetition rule at the root.

`21-C16` (job36, mate outranks a drawn root) stands and is the complement of this: the PC build is
right to find the mate, and wrong to report a win when there is no mate.

## Suspicions, not proven

- Whether the owner's match program reads the score at all. If it adjudicates on its own rules, this
  costs nothing in match results. I did not see the match program.
- Whether a root at exactly halfmove 100 with a *forced* mate in, say, 3 would be found (job36
  tested mate in 1 and it was). Not tested for longer mates.

## What I did NOT do

- Did not test the score's effect on actual games.
- Did not propose a patch: the right fix is to search the root (so a mate is found) and then fall back
  to the draw score when no mate is available — that is a design change for the owner, not something I
  should patch unasked.

## What I am NOT sure about

- Whether the +199 is stable across positions or specific to my pawn-up board. I tested one drawn
  board and one repetition case; both show a win, but the size varied with the material, which is what
  makes me think it is "ordinary search score with no draw rule at the root" rather than a fixed bug.

## Times

see `job37/stamps.txt`.
