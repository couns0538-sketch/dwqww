# Question 3: is the draw-boundary mate miss reachable in real play?

Answer: **legal and constructible, but it did not occur once in 792,081 plies of
real engine play.** Five independent searches, all with literal denominators.
Every number is the pasted output of a committed script.

## Line A: every real game in the repository, narrow band (the band the brief named)

`scan_pgn.py`, all 13 PGN files at 6b98f217 -- real engine-vs-engine tournament
games -- every ply replayed and checked:

    games scanned                       : 5689
    plies scanned                       : 792081
    plies in band (hm 98 or 99)         : 798
    band plies with no clock reset      : 503
    distinct such FENs with a forced mate: 1
    EXPOSED (engine must answer 0)      : 0
    FOUND   (engine must answer mate)   : 1

## Line B: wide band, firing on the CORRECT condition (`p > 100 - H`)

`scan_pgn_wide.py`, same corpus, with cheap pre-filters whose funnel is printed:

    games scanned                        : 5689
    plies scanned                        : 792081
    clock >= 93                          : 3825
    of those, <= 6 pieces                : 2305
    of those, no clock-resetting move    : 1673
    distinct FENs tested for a mate      : 1220
    with a forced mate (p in 2,4,6)      : 3
    IN BAND (H > 100-p), engine MUST miss: 0

So **1,220 distinct real positions were tested for a forced mate at clock >= 93,
and zero of them were in the exposed cell.**

## The three real positions that DID have a mate, and what they show

All three are the tail of ONE game (EvasionOn vs EvasionOff, the final
conversion). Measured on the base engine at depth 16:

    K2k4/5Q2/8/8/8/8/8/8 b - - 94 103   oracle p=6, j0=6  -> mate -3,  45487 nodes
    2k5/K4Q2/8/8/8/8/8/8 b - - 96 104   oracle p=4, j0=4  -> mate -2,   1524 nodes
    3k4/5Q2/1K6/8/8/8/8/8 b - - 98 105  oracle p=2, j0=2  -> mate -1,     54 nodes

Every one sits EXACTLY on the boundary (`p == j0`) and every one is answered
correctly. That is not luck: it is what a real conversion does. The winning side
mates as soon as it is able, so the clock is only high when the mate is short,
which is precisely the `p == j0` cell that works. To land in the exposed cell the
mating move has to fall one ply LATER than the clock crossing -- i.e. the winner
must dither for exactly one extra ply at the end, after already having had the
mate available one ply earlier.

That single-ply dither is what the real corpus never does, and it is why the
exposed cell is empty here.

## Line C: engine self-play into the band

`selfplay_game.py`, engine playing both sides, movetime 30:

    games                          : 2
    positions at clock >= 93       : 11
    of those, a forced mate exists : 0
    of those, in band (must miss)  : 0

Reaching the clock band is easy (11 positions in 2 games). Reaching it with a
forced mate available is what does not happen.

## Line D: hand-constructed game search

`construct_game.py` and an earlier `realplay.py` (random quiet walks from real
openings): 20 + 30 attempted games. All reached the band; none had a mate
available there. Both scripts print attempts/reached/hits rather than only hits.

## Line E: the direct construction, which DOES work

The defect is trivially constructible as a position (job3/BAND_TABLE.md: 80
measured cells, 32 misses, all reproduced). What cannot be produced from real
play in this corpus is a game whose loser has a mate hanging one ply past the
crossing.

## The honest answer, stated so it cannot be over-read

* **Reachable?** Yes in the rules sense: every fixture in job3 is a legal
  position reachable by a legal move sequence, and `construct_game.py` shows real
  games reach clock 93+ routinely.
* **Seen in real play?** Not once in 792,081 plies of real games, nor in 52
  generated games. 0 exposed, denominator 1,220 tested FENs (wide) / 503 (narrow).
* **Why not:** a real converter mates at the earliest opportunity, which puts it
  on the `p == j0` boundary cell that the engine answers correctly. The defect
  needs a winner that delays the mate by exactly one ply past the clock crossing,
  and no game in this corpus did that.

The realistic carrier is therefore not "a normal game" but a specific pathology:
a winner that has the mate available, does not play it, and shuffles across the
100-ply boundary. A weak or time-scrambling engine in a won endgame is exactly
that pathology -- which is why the report should describe the trigger as
"a winning side that misses the fastest mate for one ply", not as "a rare position".
