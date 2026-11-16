cross-1 prediction (reproducing kimi5's job-10 quiescence counters) -- own commit before the first counted run

Scope: the four STEPS runs (defaults-O, S14-O, S14-G, defaults-G) with FORGE_QS_STEPS=1; the
REGRET probe runs and their missed tables are left for a later cross (stated scope cut).

1. Pins on my flag build: 312866 / 862329 / 4865609. Kill: otherwise.
2. The four runs' rows equal the plain rows for the same settings on every position (O defaults =
   my long-1 O_none.rows; O S14 = O_S14.rows; G likewise). Kill: any differing row.
3. My aggregated tables (agg_qs.py over my captured QSTEPS lines) equal kimi5's agg_k1_def_O,
   agg_k2_s14_O, agg_k3_s14_G, agg_k4_def_G on EVERY labeled line except the file-name lines:
   the IDENTITY VIOLATIONS line (all six zeros, searches 200/353), the TOTALS line (including
   q0 = 5,643,723 / 4,629,887 / ... and nodes(engine) = the run's own node sum), the CALL SITES
   matrix and its I1, the EXITS line and its I3 + the X_tt bounds split, the STAND PAT classes
   and both identities, the S_tt line, the MOVES lines and their I4, the P_fut/P_see/CUT splits,
   and the Q0 by-class lines. Kill: ANY differing number anywhere.
4. The K2 COMPARISON sections inside kimi5's aggs compare its runs against Fable's counters; my
   numbers must equal those same constants (they appear as the right-hand "vs" values) -- covered
   by item 3's equality.
