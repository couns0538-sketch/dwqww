# T05B-02: exact material key without the serial multiply chain (closed form, or incremental in Board)
Status: COMPLETE

## Source
Own: lock src/search.cpp:588-596 (material_key, Horner form), :638-645 (corrected_eval), :647-656 (update_correction),
:50 (MaterialCorrectionWeight = 100). Own profile: R7 J3 perf bench 16, corrected_eval 2.76 % self time
(opus-r7-nps `opus_r7/j3/logs/ci_prof1_base/perf_self_off.txt`). Own static disassembly of the lock exe
(forge_ltopgo_x_al1s198_v23.exe, sha256 fd3a5190...): three inlined copies, each 10 popcnt + 9 dependent imul by
0x100000001b3 + lea, then imul $0x3c15 and $0x3fff before the material-correction load (search 0x1400ee33e,
0x1400ef925; qsearch 0x1400fae4d). Precedent: Stockfish keeps its material key incrementally and feeds a material
correction history: https://github.com/official-stockfish/Stockfish/commit/ddc9f48bc3e0b1d22b2d1259d5d45d4640e0374d ,
/commit/e9aa20ad132b569c7a9e60322a25aeef94a3375a , and the bug + fix PRs https://github.com/official-stockfish/Stockfish/pull/6891 ,
https://github.com/official-stockfish/Stockfish/pull/6894 .

## Licence
Own code and own exe. Stockfish 86f1df7134: GPL-3.0, ideas only - commit messages and PR text only, no source.

## Mechanism
The lock's key is G * sum_j (c_j + 1) * P^(9-j) mod 2^64 (c_j = count of the 10 pawn..queen kinds, P and G the two
literals at :592 and :595). That is a constant K0 plus sum_j c_j * K_j with K_j = G * P^(9-j) mod 2^64, exactly,
because unsigned arithmetic mod 2^64 is a ring. (a) Closed form, no Board change: compute K0 and K_j at compile time
from the same literals; the key is K0 plus 10 independent products (or 10 small table entries indexed by the counts),
summed as a tree: same 64-bit value, latency ~10 cycles instead of ~40. (b) Incremental: Board keeps the value
(set_fen from (a); make_move subtracts K_j for a capture or en passant, swaps pawn for piece on a promotion; unmake
restores it from Undo); corrected_eval and update_correction read one field. Only bits 0-13 are ever used (both
callers mask with CorrectionSize - 1, CorrectionSize = 1 << 14 at include/forge/search.hpp:257; the lock exe already
narrows the last multiply to imul $0x3c15), so K0 and K_j can be kept mod 2^14 and summed in 32 bits: same index.

## Forge fit
`forge_has.sh 'material_key|materialKey|material_table|MaterialEntry'`: only search.cpp:588, :642, :655 - no material
key in Board, no material table. Runs at every non-check node that reaches the eval step (TT-eval reuse included)
and at each correction update. More keys (card T04-04 minor / major correction keys) would add more such chains, so
(b) is also the base for those. Overlap: T05C-04 (one-line, same target; design = recompute with the same formula
only after a capture or promotion, restore from Undo; no number) (corrected by verify: T05C-04 has since been merged
into notes/T05C/TABLE.md row 18, which marks it a duplicate of this card - this is the only card); this card adds the
closed form (a), the 14-bit index, the disassembly, the unit test and the planted mutant.

## Expected gain
Source numbers: none for this exact change (Stockfish's key is incremental since at least 2009; no nps logged).
Forge: bounded by corrected_eval's 2.76 % self time; the key is 31 of its ~56 instructions and ~40-50 of its
~70-80-cycle dependent path (disassembly); out-of-order execution may hide part. (b) also saves ~30 instructions.
Forge estimate: **+0 to +1.5 % nps UNPROVEN** (~1 % if half of corrected_eval's time is the chain).

## Effort
(a) crew ~1-2 h, (b) ~3-4 h (Board, Undo, set_fen, debug check, CTest); CPU ~1 h (kit build, pins, identity, probe).
No SPRT; GPU 0.

## Test plan
1. Unit test: closed form == lock Horner function on every count vector 0..10 per kind (or 10^6 random vectors) and
   on every node of bench 13; for (b) a debug-build check board key == recomputed at every make / unmake (the
   Stockfish PR 6894 lesson: an incremental material key broke silently in a do_move reorder).
2. Static check: objdump of the ON exe shows no imul chain by 0x100000001b3 at the corrected_eval sites.
3. ON exe with the kit (pc1 = pc2): bench d11-d22 + perft pins, 12k-FEN exe identity; planted mutant (drop one K_j
   term) must change bench nodes.
4. Gate route: node-identical = nps ABBA only (standard probe, protocol T12-02, fresh copies, A/A arm), timed in one
   speed exe with T05B-01 (alone it is below the PC's per-file effect).

## OFF-by-default design
Build switch FORGE_MATKEY_FAST (0 = lock source, lock pins by construction; 1 = closed form (a); 2 = incremental (b)).
Not a UCI option (hot path; cold OFF paths under the kit's PGO workload). OFF / ON identity as above.
