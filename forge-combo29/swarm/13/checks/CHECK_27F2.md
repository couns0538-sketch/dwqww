# CHECK of seat 27's finding 27-F2 — seat 13, own build, own interactive harness

## Verdict
**CONFIRMS 27-F2.**

Seat 27 claimed: `go nodes N` with N below one root iteration (N < 26 at startpos) answers the
first legal move in generation order (`a2a3`) with **no info line at all**, while N = 26 answers
`d2d4`. Both halves hold exactly on my build.

## Evidence
Raw: `out_27f2/fresh_nodes_<N>.txt`, `out_27f2/warm_nodes_<N>.txt`, each holding the exe path,
sha256, every line sent, every info line received, and the bestmove. Summary `out_27f2/VERDICT.md`.

| N | info lines | deepest depth | nodes on last info | bestmove |
|---|---|---|---|---|
| 0, 1, 10, 24, 25 | 0 | — | — | `a2a3` |
| 26 | 1 | 1 | 26 | `d2d4` |
| 27 | 1 | 1 | 26 | `d2d4` |
| 30 | 1 | 1 | 26 | `d2d4` |
| 100 | 2 | 2 | 54 | `d2d4` |
| 100000 | 13 | 13 | 72062 | `e2e4` |

## Controls I added (so this cannot be a blind-runner artefact)
1. **Runner sanity, N = 100000:** 13 info lines and 72,062 nodes. If my runner could not see info
   lines, this control would have been silent too. It is not, so "0 info lines" below 26 is a real
   absence, not a parser that finds nothing.
2. **Boundary both ways:** N = 24 and 25 are silent; N = 26 and 27 each give exactly one info line
   at depth 1 with 26 nodes. The switch is at 26, as the finding states, not 25 or 27.
3. **State control:** N = 25/26/27 were repeated in ONE process after a completed `go depth 10`
   (with `ucinewgame` and a fresh `position startpos`). The answers are identical to the fresh-process
   runs, so this is a budget effect and not a warm/cold state effect.
4. **No stdin close mid-search:** the harness writes one command, reads to `bestmove`, and only then
   sends the next. This matters because of 19-F12 (a `quit` during a running search yields a
   fabricated `bestmove` with 0 nodes) — the two symptoms look similar and I wanted them separated.

## Why this finding matters to other seats
This is the trap that can make an unrelated check look like a bug: any harness that uses a small
`go nodes` budget, or that pipelines `quit`, gets `a2a3` with no info line, which is
indistinguishable at a glance from 19-F12's fabricated move. The two are different: 19-F12 needs a
search to be *cut short*, this one happens with a fully finished search under a tiny budget. My
`S-C1` and all perft work are unaffected because perft is synchronous and prints `nodes`.

## Beyond the finding
Nothing beyond it. I did not test other positions (the finding states startpos, and I checked
startpos only), so I am not claiming the N = 26 boundary is universal — at another position the
boundary would differ with the branching factor.
