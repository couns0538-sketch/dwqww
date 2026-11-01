# R13 Phase 3 - Sf26 bundle split (bits 2 / 4 / 8) - DONE (CR R13 PASS; the 3 singles are queued as gates)
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

### SPSA result, bit 2 (run 2026-11-01 09:07-09:56, 160 pairs = 320 games, seed 13002)
| parameter | start | end | int | noise sigma | z | verdict |
|---|---|---|---|---|---|---|
| Sf26NmpPriorBonus | 16 | 17.77 | 18 | 3.68 | +0.48 | noise |
| Sf26NmpPriorCap | 3 | 1.93 | 2 | 0.92 | -1.16 | noise |
plus vs minus +57 -42 =221 (69.1% draws); 0 of 2 parameters beyond 2 sigma (about 0.1 expected by chance).
Proposal (optional, noise-level - gate the default line first): `setoption name Sf26NmpPrior value 1`,
`Sf26NmpPriorBonus value 18`, `Sf26NmpPriorCap value 2`. (The R9 report tool prints `R9Tune=true` in its option lines:
that is R9-specific and not an option of this exe; the switch here is Sf26NmpPrior.) Evidence: spsa/run_bit2/, spsa/report_bit2/.

### SPSA result, bit 4 (run 2026-11-01 09:56-10:45, 160 pairs = 320 games, seed 13004)
| parameter | start | end | int | noise sigma | z | halves | verdict |
|---|---|---|---|---|---|---|---|
| Sf26LmrAlphaGap | 260 | 310.63 | 311 | 34.83 | +1.45 | mixed | noise |
plus vs minus +44 -44 =232 (72.5% draws); 0 of 1 parameter beyond 2 sigma.
Proposal (optional, noise-level): `setoption name Sf26LmrGap value 1` + `Sf26LmrAlphaGap value 311`. Bit 8: no margin, no SPSA.
Evidence: spsa/run_bit4/, spsa/report_bit4/.

## Summary for the gate queue
Primary lines (default margins) as in README.md: Sf26NmpPrior 1 / Sf26LmrGap 1 / Sf26MulticutCorr 1, exe 029d58e8; combined
line only if 2+ singles reach H1. SPSA proposals (both noise-level, not recommended over the defaults): bit 2 Bonus 18 + Cap 2,
bit 4 Gap 311. Everything UNPROVEN.
