# T05B: where the lock's hand-crafted eval spends its time (from reading the code), and what is cached today

Lock FD3A5190 source, read-only: `C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/src_al1s198_clean`.
All file:line below are in that tree. No engine was built or run for this note; measured numbers are the crew's own
(S37 microbench, R7 J3 profile), everything else is counted from the code and labelled as an estimate.

## 1. Measured shares (own records)
| what | number | conditions | source |
|---|---|---|---|
| HCE `evaluate_position<false>` self time | **14.43 %** of all samples | perf cpu-clock, bench 16, Linux GitHub runner, g++ -O3 (not LTO+PGO), engine with the lock's bench pins | R7 J3 `logs/ci_prof1_base/perf_self_off.txt` (opus-r7-nps) |
| same, instructions | 10.93 % (eval.cpp) + 4.11 % (bitboard.hpp inlined) + ~1.8 % (board.hpp, `<bit>`, stl) = **~15-17 %** of Ir; `evaluate_runtime` inclusive 17.39 % | callgrind bench 13 (totals include bench start-up: memset 6.9 %, magic init 7.7 %) | R7 J3 `profile_self_off.txt`, `profile_incl_off.txt` |
| `Worker::corrected_eval` self time | **2.76 %** | perf, as above | R7 J3 perf_self_off.txt line 12 |
| `update_runtime_psqt` / `static_evaluate` / `scale_factor` | 1.03 % / 0.49 % / 0.42 % | perf, as above | R7 J3 |
| NNUE `update` / `evaluate` | 8.28 % / 4.91 % | perf, as above | R7 J3 |
| search-case static eval (HCE + net, lazy accumulator path) | **403.1 ns**: HCE ~232 ns (57 %), net update + output ~97 ns (24 %), rest ~74 ns | PC Zen 5, TSC 4.70 GHz, CPU time per region, Idle under gate + training load (advisory), plain -O3 lock recipe | S37 REPORT.md section 3 |
| HCE `evaluate_uncached` (no pawn cache, full PSQT loop) | 396.1 ns | same | S37 cost table |
| pawn-cache prefetch after make_move (R7EvalPrefetch) | -0.60 % [-2.36, +1.18] d16 wall nps, 5 runs; callgrind +0.08 % Ir | PC, loaded (73 %) | R7 J3 NPS table -> no gain, kept OFF |

Derived (estimates, not measured): bench 13 has 862,329 nodes; at ~0.55 evaluations per node (30-h counters, game
positions) that is ~474k HCE calls for ~0.78-0.89 G Ir -> **~1,650-1,900 instructions per HCE call**. S37's 232 ns at
4.70 GHz is ~1,090 cycles -> IPC ~1.5-1.7: branch mispredictions and dependent table loads, not ALU width, set the pace.
The HCE is the largest single hotspot of the lock and about 1.4x the residual net (S37: 232 vs ~97 ns; perf: 14.4 % vs
13.2 %). A node-identical change that removes X % of the HCE's time moves nps by about 0.14-0.17 X % (if the
removed work is average work; branchy work is worth more per instruction).

## 2. What is cached or incremental today
| state | how | where |
|---|---|---|
| Zobrist key, **pawn key** (XOR of pawn zobrists only; 0 = no pawns) | incremental in make_move, restored from Undo | src/board.cpp:729, 743-762, 818, 1048-1056 |
| piece bitboards, occupancy, squares, king squares, checkers | incremental (checkers recomputed by one attackers_to per move) | src/board.cpp:180-200, 763, 786 |
| **PSQT sum + phase** (RuntimePsqt) | incremental per search-stack frame from the NNUE dirty-piece list, lazy walk-back with the accumulator | src/eval.cpp:486-517, src/search.cpp:599-621, 623-636 |
| **pawn structure** (score of evaluate_pawn_structure + both passed-pawn sets) | per-worker pawn cache, 32,768 entries, index pawn_key & 32767, full 64-bit key check + valid flag | include/forge/eval.hpp:52-65, src/eval.cpp:397-415, 471-480, 519-522 |
| static eval of a TT position | the TT entry stores the raw eval (HCE + net); qsearch and search reuse it before calling static_evaluate | src/search.cpp:807-808, 935-936, 817, 868 |
| NNUE accumulators | incremental, lazy, per stack frame | src/search.cpp:602-616 |
NOT cached / NOT incremental: everything else in evaluate_position (below), the **material key** (recomputed from 10
popcounts in a serial multiply chain at every corrected_eval and update_correction, src/search.cpp:588-596, 642, 655,
with MaterialCorrectionWeight = 100 by default, src/search.cpp:50), any material-config table (none exists), any
king-square-dependent pawn term.

Pawn-cache entry layout: `{uint64 key; Score score; 4 B padding; Bitboard passed[2]; bool valid; 7 B padding}` =
40 B; 32,768 x 40 B = **1.25 MiB per worker** (> the 1 MiB L2 of a Zen 5 core); with a 40 B stride **half of all
entries straddle two 64-B lines** (4 of every 8, for any 16-B-aligned base). For TODAY's contents `valid` is
redundant: a zeroed entry (key 0, score 0, passed 0) is the correct entry for key 0 (no pawns -> score 0, no
passers). That stops being true as soon as king terms join the entry (T05B-01): with no pawns the shelter loop still
adds ShelterDistance + 0 and KingFileOpen per file, so king slots need their own sentinel.

Static disassembly of the lock exe (forge_ltopgo_x_al1s198_v23.exe, sha256 fd3a5190..., objdump -d, no run):
`evaluate_position<false>.constprop.0` = 2,968 static instructions (79 imul, 69 popcnt, 331 branches, 63 cmov);
material_key survives LTO+PGO as 10 popcnt + 9 dependent imul by 0x100000001b3 + lea, then imul $0x3c15 and
and $0x3fff, inlined three times (search: corrected_eval 0x1400ee33e, update_correction 0x1400ef925; qsearch
0x1400fae4d); the material-correction load issues only after the chain.

## 3. Per-call work of evaluate_position<false> (cache-hit path), counted from the code
Middlegame example: per side 8 pawns, 2 N, 2 B, 2 R, 1 Q. "op" = one x86 instruction, rough.
| block | lines | depends on | ops / call (est.) | cacheable without changing a value? |
|---|---|---|---|---|
| EvalInfo zero-init (~200 B) | eval.cpp:377 | - | ~5 | n/a |
| PSQT + phase | :382-395 | given by RuntimePsqt | ~5 | done (incremental) |
| pawn-cache probe + hit | :397-400 | pawn key | ~10 + 1-2 line loads | done |
| per-colour setup: pawn attacks, king attacks, double pawn attacks, king zone, mobility area | :417-439 | pawns, kings, occupancy | ~50 | pawn parts only (shifts: not worth a load) |
| evaluate_pieces x2: one magic lookup per N/B/R, two per Q (mobility), attack-map ORs, mobility, king-zone hits, outposts, behind-pawn, same-colour pawns, long diagonal (extra bishop lookup on pawn occupancy), open files, rook behind passers (extra rook lookups, rare), 7th rank, queen development, WeakQueen (**two more lookups with the same square and occupancy as the queen's mobility attacks**, :190-191 vs :131) | :99-196 | all pieces | ~550-650 (14 pieces x ~40) | attack reuse for the queen (2 lookups per queen); pawn-only masks (attack span :109, open files :167-168, pawns per square colour :158-159, long-diagonal centre view :161) |
| evaluate_king x2: **shelter / storm / open file over 2-3 files** (:207-228), king danger (2 lookups + popcounts when >= 2 attackers or queen + 1, :230-253), space (:255-267), **king-pawn distance** (:269-272) | :198-273 | shelter + KPD: own + enemy pawns + own king square only; danger: everything | ~250-320, of which shelter + KPD **~175-205** | **YES: shelter Score, shelter mg sum, KPD Score per colour, valid while the king square is unchanged** |
| evaluate_threats x2: minor / rook target loops with piece_at loads, hanging, pawn threats, safe pushes, restricted | :275-316 | everything | ~100-150 | no |
| evaluate_passed x2: per passer rank term, king distances x scale, blocked / path / push | :318-344 | PassedRank: pawns only; king distances: pawns + both kings; rest: occupancy + attacks | ~25 per passer | PassedRank sum could fold into the cached pawn score (small); king-distance part if both king squares match |
| bishop pair, tempo | :450-453 | material | ~10 | material-config table (tiny) |
| scale_factor: 8 popcounts + 8 multiplies for non-pawn material, OCB test, pawn counts | :346-372 | material + bishop square colours + strong pawns | ~40 | material table only with bishop colours in the key; perf 0.42 % -> not worth it alone |
| taper + side flip | :455-466 | - | ~15 | n/a |
| **total** | | | **~1,100-1,400 counted; ~1,650-1,900 by callgrind** | |

Branches that depend on the data (and so mispredict): the piece loops (count varies), king-zone hits, outposts,
rook files, the shelter loop (own / enemy pawn present, storm distance <= 3, open file), king-danger trigger, the
threat target loops, passer loops. The shelter loop alone has 2-3 data-dependent branches per file.

## 4. Search-side eval cost outside evaluate_position
- `corrected_eval` (src/search.cpp:638-645) runs at every non-check node that reaches the eval step (also on TT-eval
  reuse), and `update_correction` (:647-656) at every search node that updates correction history. Each computes
  `material_key(board)`: 10 popcounts and a **serial chain of 10 multiply-adds** (Horner form, :590-595) plus a final
  multiply -> ~40 ops and ~35-40 cycles of dependent latency before the material-correction load can even issue. The
  pawn-correction load uses the incremental pawn key and starts at once. perf: corrected_eval 2.76 % self.
- `static_evaluate` (:599-621): the lazy walk-back of the accumulator and RuntimePsqt, then HCE + net + clamp.

## 5. Node-identical options that follow from this (cards / table)
1. T05B-01: pawn-king terms in the pawn entry (shelter / storm / open file + the shelter mg sum used by king danger
   + king-pawn distance, per colour, valid for the stored king square); 64-B aligned entries. Removes ~175-205 of
   ~1,650-1,900 instructions on most calls, plus the shelter loop's mispredictions. Estimate **+0.5 to +1.5 % nps
   UNPROVEN**.
2. T05B-02: material key without the multiply chain - incremental in Board (exactly the lock's value, the key is
   linear in the piece counts mod 2^64) or a closed-form table sum. Estimate **+0 to +1.5 % nps UNPROVEN** (bounded by
   corrected_eval's 2.76 %; out-of-order execution may hide part of the chain).
   Both are below the PC's per-file effect alone (BH-8 up to 3-5 %): time them in ONE speed exe; the microbench
   (HCE / corrected_eval ns per call, same binary) is the primary go / no-go evidence.
3. Below +1 % each (TABLE.md, no card): queen attack reuse, pawn-only masks in the entry, PassedRank folded into the
   pawn score, 32-B pawn entries without the valid flag, material-config table for scale_factor, pawn-entry prefetch
   (measured: no gain, R7EvalPrefetch).

## 6. How to measure before any gate (proposal; no run in this job)
- Counters build (not for gating): count HCE calls, pawn-cache hits / misses, king-square hits per colour, bench 13
  and 200 game positions at movetime 200; gives the hit rates the estimates above assume (none are logged today).
- Microbenchmark: extend S37's `forge_nnue_microbench` (opus-sol-S37 `tools/nnue_microbench.cpp`, links forge_core) with
  a region that times `evaluate_runtime` on the same 10,000 positions + 346,182 children with the old and the new
  code in one binary; checksum of every eval must be equal (the tool already prints per-position FNV-1a of HCE and
  total eval).
- Identity: bench pins d11-d22 + perft, 12k-FEN exe identity (eval + bestmove per FEN) with the kit; then the
  standard nps probe (T05 SPEED_LIST header) with fresh exe copies and an A/A arm.
