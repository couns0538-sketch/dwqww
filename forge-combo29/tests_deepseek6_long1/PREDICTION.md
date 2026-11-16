# PREDICTION — deepseek6, long 1

Written before the first measuring command of long 1. Never edited after this commit.

Exe: Release CMake build with g++ 13.3.0 of commit 6b98f2170a3210e71beed04bbd2553972c253ed7,
folder forge-combo29, no FORGE_PORTABLE (this CPU has AVX-512F and BMI2),
build dir /agent/repos/work/build-base, binary /agent/repos/work/build-base/forge.

Protocol: `go depth 12` per position; `ucinewgame` + `isready` before every `go`;
Threads 1, Hash 16, OwnBook false; wait for `bestmove`; one row per position.

## Honesty check (4 numbers, 4 fresh processes)

| line | predicted | killed by |
|---|---|---|
| `bench 11` | nodes 312866 | any other integer |
| `bench 13` | nodes 862329 | any other integer |
| `bench 16` | nodes 3024920 | any other integer |
| `go perft 5` (startpos) | nodes 4865609 | any other integer |

## The four known sums

| set | options | predicted sum | predicted first three rows | killed by |
|---|---|---|---|---|
| O (200) | none | 12,573,318 | 18407 / 25756 / 64000 | sum differs at all |
| O (200) | S14 | 9,500,069 | 41311 / 24872 / 28574 | sum differs at all |
| G (353) | none | 22,128,265 | not predicted | sum differs at all |
| G (353) | S14 | 18,466,239 | not predicted | sum differs at all |

A sum that differs is reported with the first position that differs; the report then says the
known answer was NOT met for that row of the table.

Why I expect exactly these numbers: the honesty check already reproduced the four pins of this
commit on this exact machine with this exact compiler, and the four sums are published for the
plain build at this commit. My only new variable is the harness; a harness that differs would show
up as a difference in the first three rows of the O/no-options run (18407 / 25756 / 64000), which
are published separately from the sum. If the sum matches but those three do not, the harness is
wrong in the position ordering and I will say so rather than call the sum met.

## Harness self-check (a known answer that must stop it)

Setting an option the plain build does not advertise, e.g.
`setoption name NoSuchOptionDeepseek6 value 1`, must make the run STOP: the rows file gets no
data rows and a `# STOPPED` line, the process exit is 2. Killed by: the run completing 200 rows.

## S14 as I will send it

```
setoption name LmrQuietBase value 93
setoption name LmrQuietDivisor value 205
setoption name LmrNoisyBase value 13
setoption name LmrNoisyDivisor value 333
setoption name LmrHistoryDivisor value 5643
setoption name NullMoveBase value 5
setoption name LmpBase value 8
setoption name HistoryPruneMultiplier value 2220
setoption name HistoryBonusQuadratic value 24
setoption name HistoryBonusLinear value 54
setoption name HistoryBonusMax value 2212
setoption name SingularDepth value 6
setoption name IirDepth value 2
setoption name NonPawnCorrection value true
```
each after the fixed `Threads 1` / `Hash 16` / `OwnBook false`, in this order, before the first
`ucinewgame`.
