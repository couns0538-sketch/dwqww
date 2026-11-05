# T05B-01: pawn-king terms cached in the pawn entry (shelter, storm, open file, king-pawn distance)
Status: PARTIAL (every unfinished field says PENDING)

## Source
Own code: lock src/eval.cpp:198-228 (shelter loop), :250 (shelter mg sum used by king danger), :269-272 (king-pawn
distance), :397-415 (pawn cache), include/forge/eval.hpp:52-65 (40 B entry, 32,768 entries). Own profile: R7 J3
(opus-r7-nps `opus_r7/j3/logs/ci_prof1_base/perf_self_off.txt`: HCE 14.43 % self time). Other engines: PENDING.

## Licence
Own code. Other engines: PENDING.

## Mechanism
PENDING (draft): the shelter / storm / open-file loop and the king-pawn distance depend only on the two pawn sets
and on the own king square. Store, per colour, the king square they were computed for, the summed packed Score,
and the summed middlegame part (the `shelter` integer that king danger divides) in the pawn entry. On a pawn-cache
hit with the same king square, add the stored Score and use the stored integer; otherwise compute and store.

## Forge fit
PENDING

## Expected gain
PENDING

## Effort
PENDING

## Test plan
PENDING

## OFF-by-default design
PENDING
