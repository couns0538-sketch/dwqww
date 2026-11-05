# T12B-01-bad-captures-overflow: the lock's 64-entry bad-capture buffer overflows on a legal FEN; merge the node-identical fix
Status: PARTIAL (every unfinished field says PENDING)

## Source
Own: lock src/search.cpp:361 (unguarded write), :453 (std::array<Move, 64>); fable-review-buffix 8632e8ab (fix
a9cea71f, fixture tests/bad_capture_tests.cpp:141). External fix history: PENDING.

## Licence
Own code. External: PENDING.

## Mechanism
PENDING

## Forge fit
PENDING

## Expected gain
No Elo (correctness). PENDING.

## Effort
PENDING

## Test plan
PENDING

## OFF-by-default design
PENDING
