# Characterising the lone-king divergences — my eyeball impression was WRONG — seat 08

After confirming that PC-vs-base divergence is exclusive to lone-king roots (08-C25), I wrote that "several turn a
probing move into a waiting move". The coordinator asked me to test that as a mechanism signature. **I tested it, and
it is not true.** This file records the refutation of my own impression.

## Definitions used (computed in python-chess, before any engine ran)
- **PROBING**: the move gives check, captures, or newly attacks an enemy piece.
- **WAITING**: none of those.

## The 11 divergences classified

| base move | class | PC move | class | pattern |
|---|---|---|---|---|
| e6d6 | PROBING | e6e7 | WAITING | base probes, PC waits |
| e2d3 | WAITING | h1c1 | PROBING | **reverse** |
| c7d8 | WAITING | c7c6 | WAITING | both wait |
| e7d7 | WAITING | e7d6 | WAITING | both wait |
| a6a7 | PROBING | a6a5 | WAITING | base probes, PC waits |
| a3a4 | WAITING | c1c2 | WAITING | both wait |
| d2e3 | WAITING | d2e1 | WAITING | both wait |
| b2b3 | WAITING | b2c2 | WAITING | both wait |
| a6a5 | WAITING | a1d4 | WAITING | both wait |
| h3g4 | WAITING | h3g2 | WAITING | both wait |
| a6a5 | WAITING | g5f6 | WAITING | both wait |

| pattern | boards |
|---|---|
| **both WAITING** | **8 of 11** |
| base PROBING → PC WAITING | 2 of 11 |
| base WAITING → PC PROBING | 1 of 11 |

## Verdict: the "probing becomes waiting" signature is NOT the rule

**Only 2 of 11 divergences fit it, 8 of 11 have both moves waiting, and one goes the opposite way.** So the repair
does not uniformly convert a concrete threat into a waiting move: in most cases it changes **which** waiting move is
played. Any statement that the bare-king repair "turns probing moves into waiting moves" would be wrong on this
sample, and I withdraw my own sentence to that effect from the 08-C25 discussion.

## Why this is worth a file rather than a quiet edit
I looked at three or four of the eleven boards and generalised. The test took ten minutes and refuted it. That is the
**fifth or sixth** time tonight that a claim I formed by looking rather than measuring did not survive being measured
— and the pattern is consistent enough to name: **claims about WHY something happens are the ones that need the test,
more than claims about WHAT happens.** The boundary (0 of 60 outside the class) was measured and held. The mechanism
story I attached to it was eyeballed and failed.

## What the data does suggest, without claiming it
The divergences are all in K+material vs bare-king endings and all involve king or rook repositioning, which is
consistent with the `BARE_KING_LMR_CAP` / `ONE_THREAD` switches changing move ORDER rather than move choice — an
ordering change would explain "both moves are waiting, but a different one is picked". **That is a hypothesis, not a
result**: testing it would need the build variants seat 03 already made (their S-F11/S-F14), and I have not run them.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s03f13_mechanism.py /tmp/m.txt
