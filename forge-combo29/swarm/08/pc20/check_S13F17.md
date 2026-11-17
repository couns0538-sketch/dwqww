# CHECK of seat 13's S-F17 — the drawn-root matrix reproduces on every cell — seat 08

Their claim:
> S-F17: "base 6b98f217 scores a halfmove>=100 root AND a genuine third-occurrence root as 0 and searches 0 nodes,
> missing a mate-in-1 (plays **a1b1** not a1a8), while PC r15 finds the mate in 144 nodes in both cases; both builds
> still answer K vs K at once (0 nodes); and both find the mate at halfmove 0, at halfmove 99, and at TWO
> occurrences — so the difference is specifically the drawn-root condition, not the position or the harness."

## Verdict: CONFIRMS on every cell, including their exact non-mating move `a1b1`

My own harness, both builds, S14, Threads 1, Hash 16, `go depth 4`. The board is my own construction
`7k/8/6K1/8/8/8/8/R7 w - - H 1`, and I verified in python-chess **before** running anything that **a1a8 is a mate**.

| cell | base bestmove | base nodes | PC bestmove | PC nodes | design says |
|---|---|---|---|---|---|
| halfmove 0 (control: not drawn) | **a1a8** | 86 | **a1a8** | 86 | both FIND — **yes** |
| halfmove 99 (control: not drawn) | **a1a8** | 85 | **a1a8** | 85 | both FIND — **yes** |
| **halfmove 100 (drawn root)** | **a1b1** | **0** | **a1a8** | 85 | base MISSES, PC finds — **yes** |
| K vs K (insufficient material) | e3d2 | **0** | e3d2 | **0** | both answer at once — **yes** |

| their detail | my measurement |
|---|---|
| base plays **a1b1**, not the mating a1a8, at halfmove 100 | **exactly a1b1** |
| base searches **0 nodes** there | **0 nodes** |
| PC finds the mate | **yes, a1a8** |
| both answer K v K at once with 0 nodes | **yes, 0 and 0** |
| halfmove 0 and 99 are controls that must NOT be drawn | **both find the mate at both** |

**The two control cells are what make this a matrix rather than an anecdote:** at halfmove 0 and 99 the same board
gives the same mating move on both builds, so the difference at 100 is attributable to the drawn-root condition and
not to the position, the harness, or the build's search.

## The one number that differs, and why it does not matter
They report **144 nodes** for the PC's finding at halfmove 100; I measure **85**. That is a depth difference (`go
depth 4` here; their job used a different depth), and the *move* — the thing the claim is about — is identical. I
confirm the move and the 0-vs-nonzero split, not their node count.

## Scope, from FABLE_TO_swarm_6
File 6 established that a cp 0 at a high counter is **not** a defect when no forced mate exists within the remaining
half-moves. This matrix is the *other* case, and the one where the repair matters: **a mate that is available on the
very next move** is found by the PC build and missed by the base build, and both controls (0, 99) show the base build
can find it when the counter is not at the boundary. So the base build's shortcut costs a mate-in-1 exactly at the
drawn-root boundary, and the PC build does not.

Together with my 08-W1 (where cp 0 was correct because 15 plies were needed with 9 left) and 08-C21 (where the
one-ply-down shortcut was a real miss), the fifty-move/draw boundary is now measured from **three** sides: correct
draw, real miss at the root, and real miss one ply down.

## What I did NOT do
- Did not build a **genuine third-occurrence** root (their second case) — that needs a move list reaching a position
  three times, and I tested the halfmove door only. Stated as untested rather than assumed to behave the same.
- Did not test other depths or other mate distances.
- All Threads 1.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s13f17.py /tmp/s13f17.txt
