# T05E: where the HalfKA (npt K32H3^ 1024 x 32 x 32) time goes - a model from own measurements, and what is missing

Every number below is an own measurement or arithmetic on one; nothing new was run (research only). All Forge-side
estimates are **UNPROVEN**.

## Inputs (own records, read-only)
| input | value | where |
|---|---|---|
| bench nps OFF vs ON (npt w4 s10 final ftp1 net, same exe, d11-d22) | OFF 1.95-2.17 Mnps, ON 1.02-1.21 Mnps, ON / OFF 0.47-0.58 per depth | card T02-04 (QA run 20261101_121847) |
| nodes to depth 20 | ON 19.8M vs OFF 12.4M | card T02-04 |
| HalfKA stage costs, v2 kernels, L1 1024 (halfka_tool speed, 12,000 positions x 50, one random legal move each) | refresh 626.5 ns per perspective, update from the parent 124.5 ns per perspective, forward (pairwise, l1, l2, output) 279.2 ns | r10fix1 docs/OPUS_R10_HALFKA.md "Where the time goes" |
| same at L1 256 | refresh 189.4, update 31.4, forward 218.8 ns | same |
| refresh share | 2,259 of 24,000 perspective-moves = 9.4 % (king move, mirror flip, queen / rook state change) | same |
| lock eval in the same tool | FORGENN2 update 55-58 ns (both perspectives), evaluate 46-49 ns, HCE 243-249 ns (public evaluate, an upper bound of the search path) | same |
| evaluations per node | about 0.55 (lock path, 30-h counters; the ON path was never counted) | notes/T05/SPEED_LIST.md item 5 |
| npt net shape | 1024 x 32 x 32 (file 70,334,820 B by the loader's size rule); FT table 67,584 x 1024 = 69,206,016 B int8 = 16,896 pages of 4 KB or 33 pages of 2 MB | forge_push/bin npt_*_ftp1.nnue; include/forge/nnue_halfka.hpp:19-29 |
| when no row is built | TT entry has an eval (src/search.cpp:864, :992), in check (:858-860 qsearch, :987-988 main search), singular-excluded nodes (:989-990, eval reused), null move (record_null_move :638-646) | r10fix1 src/search.cpp |

## Per-evaluation split at L1 1024 (tool costs; warm caches: each position is measured 50 times)
| part | ns per evaluation | share |
|---|---|---|
| forward: pairwise (AVX2 only), l1 block kernel (VNNI zmm, NQ = 2), activations (scalar), l2, output | 279 | 45 % |
| incremental updates, 2 perspectives x 0.906 x 124.5 | 226 | 36 % |
| refreshes, 2 perspectives x 0.094 x 626.5 | 118 | 19 % |
| total ON | about 622 | |
| total OFF (FORGENN2 update + evaluate + HCE upper bound) | about 344-356 | |

The forward grows little with L1 (219 ns at 256, 279 at 1024); updates and refreshes grow linearly (31.4 -> 124.5 ns,
189 -> 627 ns for 4x the width). The tool has no split of the forward into pairwise / l1 / l2 / output (PENDING).

## Per node: the tool explains about a third of the gap
- OFF 460-513 ns per node, ON 826-980 ns per node: gap 366-467 ns per node.
- Tool model: 0.55 evaluations per node x (622 - 350) ns = about 150 ns per node, i.e. ON / OFF about 0.76 predicted
  vs 0.47-0.58 measured. About 215-320 ns per node (55-70 % of the gap) is not in the stage table.
- Candidates for the rest, each with the card or existing card that attacks it:
  (a) more refreshes in search than the tool's 9.4 %: each evaluated child of an unevaluated king-move node refreshes
      on its own -> T05E-02 (backward fill), T05E-01 (cache);
  (b) lazy walks over 2+ plies (TT-eval and in-check gaps): one more full 2-KB pass per ply and perspective -> T05E-04;
  (c) cold rows in search: the 69 MB table on 4 KB pages (16,896 pages) while the TT, histories and stacks compete for
      L2 / L3; the tool re-uses each position 50 times -> evidence for T05-03 (2 MB pages) and T05-04 (prefetch at
      record_move);
  (d) more evaluations per node in the ON tree (it is about 60 % bigger to the same depth; qsearch share unknown) ->
      a tree-shape question, card T02-04 (H1 / H3);
  (e) a cold forward: 32 layer stacks x about 33 KB of l1 weights (about 1 MB) plus l2 / output.

## The one measurement that splits the residue (counter build, no behaviour change)
Per 1M nodes, Threads 1, bench positions and 200 game positions, OFF exe vs ON with e19 and an npt net:
evaluate() calls, TT-eval skips, in-check skips; per perspective: updates by walk length (1, 2, 3+ plies) and
refreshes by cause (king move, mirror flip, state change, no valid ancestor, parent row missing); rdtsc totals per
stage (update, refresh, pairwise, l1, l2 + output) in a counting build only (never the timed exe); plus halfka_tool
speed with shuffled positions and no repeats (cold rows). This fixes the inputs of T05E-01 / -02 / -04 and says
whether large pages (T05-03) or prefetch (T05-04) should come first.

## What would close the gap (bit-exact levers only; the npt deficit is -86 to -116 Elo, so speed alone may not)
| lever | attacks | Forge estimate (nps, L1 1024) |
|---|---|---|
| T05E-01 refresh cache | refreshes (19 % of eval + residue a) | +3 to +8 % UNPROVEN |
| T05E-02 backward fill | residue a | +1 to +4 % alone, +0.5 to +1.5 % on top of T05E-01, UNPROVEN |
| T05-03 2 MB pages for the 69 MB FT table (existing card / 30-Oct S1; not in any stack yet) | residue c | not sized here; PENDING the counter build |
| T05-04 prefetch the rows at record_move (existing card) | residue c, updates | not sized here; PENDING |
| T05E-03 split VNNI chains | forward | +1 to +3 % UNPROVEN |
| T05E-04 one pass over plies and perspectives | residue b | +0.5 to +2 % UNPROVEN |
Not bit-exact, out of scope here: a narrower net (L1 512 / 256) - the FT costs scale with L1, the forward barely does
(R10 "next speedups" item 5); needs training and an SPRT.
