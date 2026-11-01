# R13 Phase 3 - Sf26 bundle split (bits 2 / 4 / 8) - IN PROGRESS
Branch `opus-r13-p3-sf26split` (from main). UNPROVEN: no Elo claim. Background: Sf26Bundle=14 (bits 2/4/8) capped with no
decision on both books (8moves -3.94, UHO -3.47 at 1500 games); bit 1 (razor) has its own gate.

## Step 1 - split
- Source: lock d4f4312 + sf26bundle_al1.patch (-F0) + tools/port_sf26split.py -> sf26/sf26split_port.patch (applies with
  -p1 on a clean lock copy; sf26split_only.patch = the split on top of the bundle).
- New switches (default 0): Sf26NmpPrior (= bit 2), Sf26LmrGap (= bit 4), Sf26MulticutCorr (= bit 8); new margin tunable
  Sf26NmpPriorCap (1-8, default 3 = the original constant). Existing margins unchanged: Sf26NmpPriorBonus 16, Sf26LmrAlphaGap 260.
- Plain build 1156ebe9 (0 warnings, vfmadd 0). Equivalence vs the original AL1 benches (handoff logs/bench_cand_expose_on*.txt): RUNNING.
