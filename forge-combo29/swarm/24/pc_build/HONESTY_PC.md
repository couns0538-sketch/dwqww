# PC r15 build — honesty check (FABLE_TO_swarm_5.md)

Built from base 6b98f217 in a SEPARATE copy (~/work/pcsrc), patch applied with `patch -p1` (11 files, no fuzz,
`patch_rc=0`), CMake Release, GCC 13.3.0, `-DCMAKE_CXX_FLAGS=-DFORGE_MATE_ALPHA_GUARD=1`.

patch sha256 **d6bd72c531f785f40421be1cc542743922a944fb0973d05831788440309c1a1a** — matches the prefix
`d6bd72c531f785f4` that file 5 states.

exe /home/ubuntu/work/pcsrc/forge-combo29/build-pc/forge
sha256 068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4
`id name Chess Engine Forge 6.4.24 candidate`

## Result: every published number matches

Each line below is a FRESH engine process (file 4: the pins are default-option numbers, so they are checked with no
setoption at all, and the S14/PC20 rows are separate regimes). `bad=` counts `unknown option` / `invalid value` /
`ERROR` lines in that run — 0 everywhere.

| regime | command | engine says | expected (file 5) | match |
|---|---|---|---|---|
| none  | bench 11 | nodes 312866  | 312866  | yes |
| none  | bench 13 | nodes 862329  | 862329  | yes |
| none  | bench 16 | nodes 3024920 | 3024920 | yes |
| none  | perft 5  | nodes 4865609 | 4865609 | yes |
| S14   | bench 11 | nodes 242796  | 242796  | yes |
| S14   | bench 13 | nodes 656517  | 656517  | yes |
| PC20  | bench 11 | nodes 278024  | 278024  | yes |
| PC20  | bench 13 | nodes 587276  | 587276  | yes |

Unpublished regimes (measured, not pinned by file 5, recorded for completeness):
S14 bench 16 = 2155620; PC20 bench 16 = 2343893; perft 5 = 4865609 in all three regimes.

## A mistake I made in this check, and how it was caught

The FIRST version of honesty_pc.sh emitted `setoption name LmrQuietBase 93` — no `value` keyword. The engine
answered `info string unknown option LmrQuietBase 93` for every setting, so the S14 and PC20 rows were really
DEFAULT-option runs (all three regimes printed 312866 / 862329 / 3024920). I saw that the three regimes agreed
perfectly, which is exactly the signature of "the options were never applied", and checked the raw file instead of
believing the table. The broken output is kept in /tmp/pcout_broken (not committed); the script now prints a `bad=`
count per line and no line may pass with bad>0.

## Settings used for everything after this

PC20 = the 14 S14 settings + `CuckooRep true`, `HistRework 2`, `TtPruneV2 true`, `CorrHistV2 true`,
`MateAlphaGuard true`, `OwnBook false`, with **Threads 1** and Hash 16.

**Threads rule in force (swarm rule, seat 04's measurement):** every score I report is from Threads 1. Scores and
node counts at Threads > 1 are not reproducible (seat 04: +2576 / mate 13 / mate 18 / mate 16 on four runs of one
position at Threads 4, versus +2207 four times at Threads 1). Where a result of mine used Threads > 1 it is labelled
and its scores are PROVISIONAL — this applies to my whole job-1 family (Threads 2/4/8/16), whose purpose was the
sanitizer question, not scores.

Also now applied everywhere: `OwnBook false` (file 3: the default is true and can answer book moves with no search).
My earlier job-1/job-2/job-3 runs did NOT send OwnBook false. Their positions are mid-game or from random games and
no book move appeared (every bestmove was judged legal on its own board and each line carries real `info depth`
lines), but the omission is recorded here rather than glossed over.
