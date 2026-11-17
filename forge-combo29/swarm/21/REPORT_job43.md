# REPORT job43 — the drawn-root design note as a RUNNABLE acceptance spec

**What was asked.** (My own next job.) `DESIGN_drawn_root.md` states a rule for drawn roots. A rule that
cannot be checked in one command will not be used, so this job turns it into an executable acceptance
test and runs it against both builds.

**The answer — and it is the cleanest result of the session.** The spec is expressible, runs in under a
minute, and **neither build passes it, each failing a different half**: the base build misses the mates
(S1, S4) because it refuses to search drawn roots; the PC build reports winning scores at drawn roots
with no mate (S2, S5). All four honesty pins stay exact on both. So the design note's rule — search the
root, then fall back to the draw score — is the unique rule that would pass all five cases.

## The spec, and what each build answers

| case | root | must answer | base build | PC build |
|---|---|---|---|---|
| S1 | halfmove 100 **with** a mate in 1 | a mate score | `cp 0`, `f2f3` — **FAIL** | `mate 1`, `e1e8` — **PASS** |
| S2 | halfmove 100, **no** mate | `cp 0` | `cp 0` — **PASS** | `cp 368` — **FAIL** |
| S3 | insufficient material (K v K) | `cp 0` | `cp 0` — **PASS** | `cp 0` — **PASS** |
| S4 | threefold **with** a mate in 1 | a mate score | `cp 0`, `f2f3` — **FAIL** | `mate 1`, `e1e8` — **PASS** |
| S5 | threefold, **no** mate | `cp 0` | `cp 0` — **PASS** | `cp 292` — **FAIL** |

| build | spec | pins |
|---|---|---|
| base (`~/b/release/forge`) | **FAILED** (S1, S4) | 4/4 exact |
| PC (`~/b/pc/forge`, PC20) | **FAILED** (S2, S5) | 4/4 exact |

## How to use it

```
python3 forge-combo29/swarm/21/job43/acceptance.py <engine-exe> <outdir> <label>
```

Exit code **0** only when all five cases pass and the four pins are exact, so it drops straight into a
patch check. `label` decides the settings: anything containing `pc` gets PC20, otherwise default options.
Every case asserts its own premise with python-chess before asking the engine (a mate really is
available for S1/S4, really is not for S2/S5, the S4/S5 roots really are threefolds), so a wrong premise
cannot pass as a pass.

## Prediction outcome

| prediction | outcome |
|---|---|
| P1 base passes S2/S3/S5 and fails S1/S4 | **held exactly** |
| P2 PC passes S1/S4 and fails S2/S5 | **held exactly** |
| P3 both pass S3 | **held** |
| P4 spec runs quickly and prints PASS/FAIL per case | **held** — under a minute per build |
| P5 pins exact on both | **held** — 312866 / 862329 / 3024920 / 4865609 |

## Findings

`21-C20 | the drawn-root rule is a discriminating spec, and neither build passes it` — the five-case
acceptance test above passes on base for the draw cases and fails its mate cases, and the reverse on the
PC build, with all pins exact. This is the check a fix should be judged by.

## Four errors of mine in this job, all recorded

1. `pass=ok)` — `pass` is a Python reserved word; the script did not parse.
2. Inverted the S4 premise assertion (`assert not premises["S4"]`), which fired and stopped the run. The
   threefold root **does** have a mate; my assertion text was the opposite of my intent.
3. My bench pin reader let a `Timeout` escape instead of reading one line, killing the run.
4. The perft pin was routed through the bench reader, which stops at `bestmove` — perft has none.

Each was caught by the script failing loudly rather than by the numbers looking wrong, which is the
behaviour the premise assertions are there to produce.

## Suspicions, not proven

- Whether "the search finds a win for the side to move" is the right threshold, or whether it should be
  "finds a win that does not rely on the opponent declining a draw". Under the owner's match rules (file
  6: the match program ends the game at the third occurrence and the 100th half-move) the simpler form
  is correct, and I used it.
- Whether S2's `cp 368` and S5's `cp 292` are stable across positions — they are single measurements on
  my two boards; 21-F19 measured `cp 199–298` on other boards, so the size varies with material, which is
  consistent.

## What I did NOT do

- Did not patch the engine (deliberate: the design note stays a note).
- Did not add a case for a drawn root where the mate is longer than 1 (S1/S4 use mate in 1 only). A
  longer-mate case is the obvious extension and would need a verified mate-N board.

## What I am NOT sure about

- Whether the owner's match program would ever ask for a score at a drawn root in a way that matters. If
  it adjudicates on its own rules, S2/S5 cost nothing in results, which is what 21-F19 already said.

## Times

see `job43/stamps.txt`.
