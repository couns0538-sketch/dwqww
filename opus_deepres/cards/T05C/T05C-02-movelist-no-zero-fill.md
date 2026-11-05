# T05C-02-movelist-no-zero-fill: stop zero-filling ~3-4 KiB of move arrays per node; quiets-only generation
Status: PARTIAL (every unfinished field says PENDING)

## Source
chess-library README perft table (with vs without move-list preallocation) and movelist.hpp / move.hpp (MIT,
@430266434a). PENDING: more sources.

## Licence
PENDING

## Mechanism
PENDING

## Forge fit
Lock src/search.cpp:450-459 MovePicker arrays value-initialised ({}), :456 MoveList buffer_ (Move has default member
initialisers, include/forge/board.hpp:34-39), :1034-1035 quiets_tried{} / captures_tried{}; :523-536 generate_quiets
regenerates the full pseudo-legal list. PENDING: details.

## Expected gain
PENDING. Forge estimate: PENDING **UNPROVEN**.

## Effort
PENDING

## Test plan
PENDING

## OFF-by-default design
PENDING
