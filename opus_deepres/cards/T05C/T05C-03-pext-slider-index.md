# T05C-03-pext-slider-index: smaller slider attack tables on Zen 5 (PEXT index, 16-bit PDEP entries)
Status: COMPLETE (verify 2026-11-05: all source numbers confirmed, see notes/T05C/VERIFY.md; one unit slip corrected in Forge fit; minor caps VIOLATION: the W5 Caissa Bitboard.cpp fetch exceeded the ~300-line cap, self-reported in sources.md, MIT so no licence impact)

## Source
Stockfish PR 6845 "HQ attacks for AVX2" (https://github.com/official-stockfish/Stockfish/pull/6845), commits e17725f445
(PR 6706), 99489f57dd (PR 6939), ee72cf49fe (PR 6998) at https://github.com/official-stockfish/Stockfish/commit/SHA.
Caissa src/backend/Bitboard.cpp @57cae7ef71, commit https://github.com/Witek902/Caissa/commit/7ed119c7b9; chess-library
src/attacks_fwd.hpp @430266434a. Zen 5 timing: https://uops.info/html-instr/PEXT_R64_R64_R64.html.

## Licence
Caissa @57cae7ef71 MIT, chess-library @430266434a MIT: source read (copy with notice). Stockfish GPL-3.0: only PR text
and commit messages read, never source (ideas only). uops.info: measurement table (facts).

## Mechanism
The lock indexes its slider tables with a 64-bit multiply magic: per square a 32-B record {mask, magic, table*,
shift}, index = ((occ & mask) * magic) >> shift, 841 KiB of 8-B entries built at start-up. On Zen 3 and later PEXT is
one fast instruction, so the index can be pext(occ, mask) (16-B record {mask, offset}, no magic search). The table
can also shrink 4x: a rook (bishop) attack set is a subset of its 14 (13) ray squares including the edges, so each
entry can be stored as the 16-bit pext of the attack set over that ray mask and expanded with pdep at lookup time
(rook 102,400 x 2 B = 200 KiB, bishop 5,248 x 2 B = 10 KiB). With PEXT the layout is a plain function of the square,
so the tables can be built at compile time (read-only image pages that the gate's engine processes running the same exe
share). Later, larger step: table-free hyperbola quintessence (bit reversal for files / diagonals, small rank table).

## Forge fit
NO. Lock include/forge/bitboard.hpp:143-171 (Magic struct, index, bishop / rook / queen), src/bitboard.cpp:23-24
(tables 0x19000 + 0x1480 entries), :63-108 (runtime magic search). forge_has.sh 'pext|pdep|bmi2': 0 real hits (4
false hits on RfpDepth); the -march=znver5 lock exe contains 0 pext / 0 pdep, 487 imul (objdump). Lookups per node:
board.cpp has 27 call sites (movegen, is_legal, gives_check, checkers, SEE), the HCE in eval.cpp 10 (mobility and
x-rays at every static eval). One search thread's hot set (841 KiB attack tables + 768 KiB (786 KB) float w1 (corrected by verify: 768 x 256 x 4 B = 786,432 B = 768 KiB, not 786 KiB) + ~1.55 MiB
histories) exceeds Zen 5's 1 MiB L2.

## Expected gain
Sources: Stockfish PR 6845 (AVX2 build, hyperbola quintessence + small rank table vs magics): local 100-run speed test
1,136,025 -> 1,171,370 nps, +3.11 %, P(speedup > 0) = 1.0; STC SPRT [0,2] LLR 2.93, 29,792 games W 7759 L 7465
D 14568. Stockfish e17725f445 (compile-time PEXT tables, PDEP 4x smaller): STC [0,2] LLR 2.97, 38,400 games W 10057
L 9749 D 18594 (~+2.8 Elo computed here from W/L/D; the gain is said to come mostly from tables shared between
fishtest's processes, "gains a little outside of fishtest as well"). Stockfish 99489f57dd: PEXT lookups are "slower or
equal to parallel-hyperbola attacks" (non-regression <-1.75,0.25> passed on avx512icl, 81,632 games, and bmi2, 78,112).
Caissa 7ed119c (hardware pext / pdep instead of a software fallback, no functional change): +3.01 +- 1.84, 5+0.05
Threads=1, [0,2], LLR 2.95, N=37,274. Zen 5 PEXT: latency 3, throughput 0.33 c (Zen 2: 18 / 19.00 microcoded).
Forge estimate: PEXT index on the lock layout 0 to +1 %; PEXT + 16-bit PDEP tables +0.5 to +3 % single-process
nps; more under gate concurrency only if the tables are compile-time constant - **UNPROVEN**, microbench first.

## Effort
Crew 3-4 h (switch, table builder, exhaustive test, kit build pc1 = pc2), +3-4 h for a compile-time table variant;
hyperbola quintessence 6-10 h (not first). CPU: < 2 h of one core for the ABBA set. No GPU.

## Test plan
Pre-gate: exhaustive identity, every square x every subset of its relevant mask (102,400 rook + 5,248 bishop cases)
vs the lock's sliding_attack and vs the lock tables; bits outside the mask are ignored by both index functions, so
this covers all occupancies. Then the shared recipe in notes/T05C/BOARD_COST.md: bench pins d11-d22, perft 5 =
4,865,609, kiwipete 5 = 193,690,690 + suite, 12k-FEN identity. Microbench: perft nps (startpos d6, kiwipete d5) and
bench d16 + the 200-position probe, ABBA with fresh copies and an A/A arm, one logical CPU with its SMT sibling idle
(T12-02). Gate route: node-identical speed change = nps ABBA only; for the shared-table claim one extra ABBA with 8
copies of each exe running at once (gate-like load), still no SPRT.

## OFF-by-default design
Build switch FORGE_SLIDER_ATTACKS: 0 = lock magics (default, same exe), 1 = PEXT index on the lock layout, 2 = PEXT +
16-bit PDEP entries (3 = 2 built at compile time). Every value returns the same attack bitboard for every square and
occupancy (exhaustive test), so bench and perft pins stay equal; values 1-3 need BMI2 (Zen 3+, never Zen 1 / 2).
