# REPORT_job14 — does the PC build actually repair the drawn-root defect? (verified)

## What was asked
Nothing specific. FABLE file 6 makes a headline claim that the owner cares about: on the base tree
6b98f217 a **drawn root** (halfmove counter ≥ 100, or a third occurrence of a position) is scored 0 and
the engine searches **0 nodes**, playing its first legal move even with a mate on the board; and on the
owner's PC this is **REPAIRED** since 15 November, so such a root is searched like any other — only
insufficient material is still answered at once.

That is worth verifying independently rather than accepting: it is the difference between the engine the
owner was measuring and the engine he plays.

## The answer: every part of the claim holds

| case | base 6b98f217 | PC r15 |
|---|---|---|
| mate-in-1 at **halfmove 100** | **0 nodes, `bestmove a1b1`, no score — mate MISSED** | 144 nodes, `score mate 1`, `bestmove a1a8` — mate found |
| mate-in-1 at **halfmove 150** | **0 nodes, `bestmove a1b1` — mate MISSED** | 144 nodes, `mate 1`, `a1a8` — found |
| mate-in-1 at halfmove **0** (control) | 144 nodes, `mate 1`, `a1a8` | 144 nodes, `mate 1`, `a1a8` |
| mate-in-1 at halfmove **99** (control) | 144 nodes, `mate 1`, `a1a8` | 144 nodes, `mate 1`, `a1a8` |
| **third occurrence** of the position, mate available | **0 nodes, `bestmove a1b1` — mate MISSED** | 144 nodes, `mate 1`, `a1a8` — found |
| **two** occurrences, mate available (control) | 144 nodes, `mate 1`, `a1a8` | 144 nodes, `mate 1`, `a1a8` |
| K vs K (insufficient material) | 0 nodes, `e2d1` | 0 nodes, `e2d1` |

Verdict on each of file 6's claims:

| claim | verdict |
|---|---|
| the base tree has the halfmove-100 defect | **HOLDS** — 0 nodes at 100 and 150, mate missed |
| the PC build repairs it | **HOLDS** — mate found at 100 and 150 |
| the defect also fires on a third occurrence | **HOLDS on the base tree** — 0 nodes, mate missed |
| the repair covers third occurrence too | **HOLDS** — mate found |
| only insufficient material is still answered at once | **HOLDS** — K vs K gives 0 nodes on both builds |

The controls are what make this credible: at halfmove 0 and 99 **both** builds find the mate (so the
harness can see a mate), and with **two** occurrences of the repetition position **both** builds find it
(so the third-occurrence result is specifically about the count, not about the position).

## The two mistakes I made getting case E right (which is why I trust it now)
My first version of the third-occurrence case passed the position as a bare `position fen`. **That case
tested nothing:** a FEN carries no occurrence history — the engine can only know about repetitions from a
`position ... moves` move list — so it reported "both builds find the mate", which looked like a clean
pass and was a vacuum.

My second version used `position ... moves` but keyed the repetition count on the **full FEN string**.
The halfmove/fullmove counters change on every shuffle, so the full-FEN dict reported **1 occurrence for a
genuine three-fold repetition** and my own guard fired: `FAIL: repetition built 1 occurrences, wanted 3`.
The engine's repetition key is pieces + side to move + castling + en passant, **not** the move counters;
keying the check the same way made it correct.

Both mistakes were caught by asserting the construction rather than the result — the guard refuses to run
the case unless the position is genuinely on the board three times. Lesson, stated for the next person: a
test that **passes for the wrong reason** is harder to notice than one that fails, because the expected
and observed answers agree. Assert the *input construction*, not just the outcome.

The guard is now permanent: `repetition_position_cmd()` raises unless the walk produces the required
occurrence count and the halfmove clock did not reset, so this case cannot silently become vacuous again.

## Settings and build
Base: `forge-combo29` at 6b98f217, release, g++ 13.3.0, x86-64-v4. PC: r15 patch applied with
`-DFORGE_MATE_ALPHA_GUARD=1`. Both: Threads 1, Hash 16, OwnBook false, fresh process per case,
`go depth 8`. Option names validated against each exe's `uci` list.

## Findings
- S-F17: FABLE file 6's drawn-root claims are **confirmed independently on both builds**: the base tree
  at 6b98f217 scores a halfmove-≥100 root and a third-occurrence root as 0 and searches **0 nodes**,
  missing a mate-in-1 (playing `a1b1` instead of `a1a8`), while PC r15 finds the mate in 144 nodes at
  both; both builds still answer K vs K at once (0 nodes), and both find the mate at halfmove 0, 99 and
  at two occurrences, so the difference is specifically the drawn-root condition.
  Reproduce: `cd forge-combo29/swarm/13/job14 && python3 drawroot.py ~/b/rel/forge ~/b/pc/forge /tmp/dr`.

## Suspicions, not proven
- The base tree's 0-node answer plays `a1b1` rather than `a1a8`, i.e. the first legal move in generation
  order. That is consistent with "no search happened", but I did not instrument the engine to prove the
  move comes from generation order rather than a 0-node search that happens to pick it.

## What I did NOT do
- Did not test the "halfmove ≥ 100 with insufficient material" interaction beyond K vs K at halfmove 0.
- Did not test whether the third-occurrence repair behaves the same at four or five occurrences.
- Did not measure any strength consequence of the repair (that is a match question).

## What I am NOT sure about
- `go depth 8` is enough to find a mate-in-1 and to expose a 0-node root, but I did not test whether the
  repaired PC build's search of a drawn root is *correct* in deeper cases — only that it searches and
  finds an immediate mate.
- The repetition test uses one shuffling sequence; a different one could in principle interact
  differently with the engine's repetition detection.

## Files
`drawroot.py` (self-checking: it raises if the repetition is not genuinely three-fold), `out2/drawroot.json`
(per-case rows for both builds, including the two-occurrence control and the `position_cmd` used for every
case), `stamps.txt`. `out/` holds the earlier run from before the repetition key was fixed — kept so the
difference between a vacuous pass and a real one can be inspected.

## Last command output

```
$ ls
drawroot.py
out
out2
REPORT_job14.md
stamps.txt
```
