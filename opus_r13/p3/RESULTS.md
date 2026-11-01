# R13 Phase 3 - Sf26 bundle split (bits 2 / 4 / 8) - IN PROGRESS
Branch `opus-r13-p3-sf26split` (from main). UNPROVEN: no Elo claim. Background: Sf26Bundle=14 (bits 2/4/8) capped with no
decision on both books (8moves -3.94, UHO -3.47 at 1500 games); bit 1 (razor) has its own gate.

## Step 1 - split
- Source: lock d4f4312 + sf26bundle_al1.patch (-F0) + tools/port_sf26split.py -> sf26/sf26split_port.patch (applies with
  -p1 on a clean lock copy; sf26split_only.patch = the split on top of the bundle).
- New switches (default 0): Sf26NmpPrior (= bit 2), Sf26LmrGap (= bit 4), Sf26MulticutCorr (= bit 8); new margin tunable
  Sf26NmpPriorCap (1-8, default 3 = the original constant). Existing margins unchanged: Sf26NmpPriorBonus 16, Sf26LmrAlphaGap 260.
- Plain build 1156ebe9 (0 warnings, vfmadd 0). **Equivalence vs the original AL1 benches** (Engine Strength handoff
  logs/bench_cand_expose_on*.txt), d11/13/16/20/22, all EXACT:
| config | this port | original | |
|---|---|---|---|
| OFF | 312866/862329/3024920/12389307/34048354 (+ perft, per-FEN) | lock pins | = |
| Sf26NmpPrior=1 | 331582/931568/2928565/10949103/18597001 | Sf26Bundle=2 | = |
| Sf26LmrGap=1 | 333008/936607/3350442/14519686/32147378 | Sf26Bundle=4 | = |
| Sf26MulticutCorr=1 | 313902/849753/2830920/11586538/29775014 | Sf26Bundle=8 | = |
| Sf26Bundle=14 | 335098/727853/2415447/9334814/29426126 | Sf26Bundle=14 | = |
  Evidence: logs/sf26_plain_*.json. LTO+PGO pc1/pc2 build (tag sfs): RUNNING.
