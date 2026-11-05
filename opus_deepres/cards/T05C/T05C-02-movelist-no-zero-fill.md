# T05C-02-movelist-no-zero-fill: stop zero-filling ~3-4 KiB of move arrays per node; quiets-only generation
Status: COMPLETE

## Source
chess-library README perft table and comparison/comparison.md, src/movelist.hpp, src/move.hpp
(https://github.com/Disservin/chess-library/blob/430266434aeb42f19bb5baa84597d671824889ff/README.md). Own: static
disassembly of the lock exe forge_ltopgo_x_al1s198_v23.exe (sha256 fd3a5190..., notes/T05C/sources.md L5).

## Licence
chess-library @430266434a MIT (copy with notice): README, comparison file and two headers read. The lock code and
its disassembly are own.

## Mechanism
Every MovePicker (main search and qsearch) value-initialises a 256-entry scored array (2 KiB), a 64-entry
bad-capture array and a MoveList whose Move elements carry default member initialisers; a main node adds
quiets_tried{} and captures_tried{} (768 B). The compiler cannot prove each slot is written before it is read, so
the lock exe calls the CRT memset twice per picker (0x800 and 0x400 bytes, through the import thunk) plus inline
64-B zero stores. Every read is of a slot written first (index < count_), so the fill is dead work. Fix: (a) the
arrays are default-initialised and Move gets a trivial default constructor (`Move{}` and Move::none() stay zero by
value-initialisation; every bare `Move x;` must be assigned before use - search.cpp:827 and :1044 are); (b)
generate_quiets asks generate_pseudo_legal for quiets only (same loop order, piece targets & empty, no promotion-push,
pawn-capture or ep loops) instead of the full list plus a filter; (c) has_legal_move's fallback list and perft lose
their fill too. Trap: (b) must emit the IDENTICAL quiet subsequence, because pick_best does selection swaps and then
an unstable std::sort; for the same reason an evasion-only or legal-only generator is NOT node-identical (removing
illegal entries changes the swap / sort input and can reorder equal scores) and is excluded here.

## Forge fit
NO. Lock src/search.cpp:450 moves_{}, :453 bad_captures_{}, :456 MoveList buffer_ (include/forge/board.hpp:34-39
Move initialisers, :49-73 MoveList), :459 check_squares_{}, :1034-1035 quiets_tried{} / captures_tried{}; :523-536
generate_quiets = full list + filter. Codegen: Worker::search and Worker::qsearch each `mov $0x800,%r8d; call memset`
and `mov $0x400,%r8d; call memset` per picker, plus 19 (search) / 4 (qsearch) zmm zero stores; has_legal_move
fallback memset 0x408; perft rep stos 0x102 dwords per node.

## Expected gain
Source: chess-library perft on a Ryzen 9 5950X, kiwipete d5 (193,690,690 nodes): 430 ms = 449.4 Mnps "with movelist
preallocation" (README) vs 538 ms = 359.4 Mnps with "no movelist preallocation" (comparison.md; its machine is not
stated, so this +25 % is not a controlled A/B). No logged search-nps number for removing a zero fill was found
(missing). Forge estimate: the fill is ~3.3 KiB (qsearch) / ~4.3 KiB (main) plus two CRT calls per picker, roughly
70-120 cycles of ~2,200 per node (static count) -> +1 to +3 % search nps; quiets-only generation +0 to +1 %; perft
nps more (perft is not a gate) - **UNPROVEN**.

## Effort
Crew 1-2 h code (five declarations, the Move constructor, a captures/quiets/all mode flag), 1-2 h proofs. CPU < 1 h of
one core for the ABBA set. No GPU.

## Test plan
Pre-gate: (1) poison verify build: the same arrays filled with 0xA5 bytes instead of zeros - bench pins d11-d22
(312866 / 862329 / 3024920 / 12389307 / 34048354), perft 4,865,609 / 193,690,690 and 12k-FEN identity must hold (no
read depends on the fill); (2) valgrind memcheck on a Linux CI runner, bench d8 + perft 4: no uninitialised-value
report; (3) verify build asserts quiets-only list == filtered full list element by element at every call (bench + 12k
FENs); (4) the shared recipe in notes/T05C/BOARD_COST.md and the ASan + UBSan self-play row. Microbench: bench d16 +
the 200-position probe, ABBA with fresh copies and an A/A arm on one logical CPU with its SMT sibling idle (T12-02);
perft nps as a side check. Gate route: node-identical speed change = nps ABBA only, no SPRT.

## OFF-by-default design
Build switch FORGE_NO_ZERO_MOVELISTS, default 0 = the lock source unchanged. 1 removes the five `{}`, makes Move
trivially default-constructible and turns on the quiets-only mode. Node-identical because every slot read is written
first (poison build) and the quiet list is element-identical (assertion), so bench and perft pins are equal both ways.
