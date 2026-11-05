# T05C-01-check-info-legality: one per-node pin / check-square cache for is_legal, gives_check, has_legal_move, checkers
Status: PARTIAL (every unfinished field says PENDING)

## Source
chess-library movegen.hpp checkMask / pinMask / seenSquares (MIT, @430266434a). PENDING: more sources.

## Licence
PENDING

## Mechanism
PENDING

## Forge fit
Lock src/board.cpp:577-598 is_legal = full king-attack test per move; :671-701 gives_check recomputes direct and
discovered checks; :558-575 has_legal_move (called by is_draw at every node, src/search.cpp:692-702, 780, 893);
:786 make_move recomputes checkers with attackers_to. No pinned / king-blocker cache (forge_has.sh 'pinned|blockers_for'
-> only see_ge-local pinner scans). PENDING: details.

## Expected gain
PENDING. Forge estimate: PENDING **UNPROVEN**.

## Effort
PENDING

## Test plan
PENDING

## OFF-by-default design
PENDING
