long 52 prediction (the IirAtRoot patch) -- own commit before the counted runs

The reduction: search.cpp line 1784 of the plain tree
`if (mate_moves_ == 0 && !in_check && depth >= tune::IirDepth && tt_move.is_none() && (pv_node || cut_node)) --depth;`
-- the root is recognised by `ss->ply == 0` (root_node, set at the function's top, line ~1553).
The patch adds a UCI check option `IirAtRoot` (default true) and extends the condition with
`&& !(root_node && !tune::IirAtRoot)`.

1. Pins at the default: 312866 / 862329 / 3024920 / 4865609. Kill: otherwise.
2. The S14 identity at the default on O and G: 200/200 and 353/353 vs my long-1 rows. Kill: any
   differing row.
3. On the first 50 of O at depth 12: (a,true) = 2,150,681 and (b,true) = 1,483,521 EXACTLY (my
   long-47 numbers, now from the patched build). Kill: otherwise.
4. (a,false) == (a,true) on all 50 (the unrestricted root has a hash move from the second
   iteration on, so the root IIR rarely fires -- my prior run's long-6 measured the inertness).
   Kill: any differing row.
5. (b,false) is MUCH larger than (b,true): about +55 percent (2,300,000) -- the root's IIR tax
   removed. Kill: within 10 percent of (b,true).
6. (b,false) still differs from (a) on most positions (the restricted root's missing TT store is
   independent of the IIR option). Kill: exact equality on all 50.
7. The full sets with IirAtRoot false: O and G sums within 0.5 percent of S14's (the inertness
   without searchmoves). Kill: either outside.
