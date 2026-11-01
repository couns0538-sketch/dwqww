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

## Step 2 - SPSA (local, short; values are proposals only)
Budget fixed BEFORE the runs: **160 game pairs (320 games) per bit**, tc 5+0.05, Threads 1, Hash 16, OwnBook false,
8moves_v3 openings (sequential from a seeded start), concurrency <= 2 on CPUs 2-3 at BelowNormal (run_pinned 0xC).
Seeds (fresh, logged): bit 2 = 13002, bit 4 = 13004. Engine = the LTO+PGO split exe, the bit's switch on in both engines.
| run | switch on | tuned (start = original) | c_end | r_end |
|---|---|---|---|---|
| bit 2 | Sf26NmpPrior=1 | Sf26NmpPriorBonus 16 (0-100), Sf26NmpPriorCap 3 (1-8) | 4, 1 | 0.06 |
| bit 4 | Sf26LmrGap=1 | Sf26LmrAlphaGap 260 (50-1000) | 40 | 0.06 |
| bit 8 | - | no margin parameter in the code: nothing to tune | - | - |
Tuner: R9's r9_spsa.py (opus-r9-spsa) copy with one change (fixed_options from the config instead of option.R9Tune=true):
spsa/r9_spsa.py, spsa/patch_tuner.py; configs spsa/sf26_bit*.json. The governor caps are set above the PC's own ~90% load
(gate + trainer) because the games are pinned to CPUs 2-3; max 2 games. Runs end by --max-pairs (no STOP files).
Noise expectation (R9: 832 pairs moved 0 of 16 parameters beyond 2 sigma): at 160 pairs only a clearly mis-set margin can move.
