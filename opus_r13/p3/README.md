# P3 Sf26 split - three single-bit gate lines (+ a combined line) on the lock tree, LTO+PGO -Expose - UNPROVEN

Background: Sf26Bundle=14 (bits 2/4/8 together) capped with no decision on both books (8moves -3.94, UHO -3.47 at 1500
games). Bit 1 (razor) has its own gate. This splits bits 2, 4, 8 into their own switches so each can be gated alone.

## Exe (not in git) - one exe for all lines
- `C:\o13\handoff\p3_sf26\forge_ltopgo_sfs.exe`, sha256 **029d58e8036aafa18849fef4c32cdf1a02385cc96208692d5fa366dad8e401ce**
  (pc1 = pc2, kit v2.3 md5 729fe727, -Expose, workload v1). Source: lock d4f4312 + `sf26/sf26split_port.patch` (-p1).

## Gate lines (engine A = this exe; engine B = lock FD3A5190, no options), UHO book first
| line | setoption | PC precondition: bench 13 (d11..d22) |
|---|---|---|
| sf26_nmp (bit 2) | `Sf26NmpPrior value 1` | 931568 (331582/931568/2928565/10949103/18597001) |
| sf26_lmr (bit 4) | `Sf26LmrGap value 1` | 936607 (333008/936607/3350442/14519686/32147378) |
| sf26_mc (bit 8) | `Sf26MulticutCorr value 1` | 849753 (313902/849753/2830920/11586538/29775014) |
| combined - ONLY if 2+ singles reach H1 | `Sf26NmpPrior 1`, `Sf26LmrGap 1`, `Sf26MulticutCorr 1` (= Sf26Bundle 14) | 727853 (335098/727853/2415447/9334814/29426126) |
Margins at their original defaults (Sf26NmpPriorBonus 16, Sf26NmpPriorCap 3, Sf26LmrAlphaGap 260). SPSA proposals (if any
move beyond noise) are listed in RESULTS.md as optional extra setoption lines; the default lines above are the primary ones.
OFF (no setoption) must bench 312866/862329/3024920/12389307/34048354 before game 1.
SPSA proposals (160 pairs each; noise-level, gate the defaults first): sf26_nmp + `Sf26NmpPriorBonus 18`,
`Sf26NmpPriorCap 2` (z +0.48 / -1.16); sf26_lmr + `Sf26LmrAlphaGap 311` (z +1.45). Details: RESULTS.md.

## Checks (evidence in logs/)
| check | result | evidence |
|---|---|---|
| each switch = its original Sf26Bundle bit on AL1, d11-d22 exact (and Sf26Bundle=14 = original 14) | PASS | RESULTS.md, logs/sf26_plain_*.json |
| pc1 = pc2; OFF pins + perft + per-FEN (plain = LTO+PGO); each line live, plain = LTO+PGO; 0 missing-profile, vfmadd 0 | PASS | logs/kit_sfs/ |
| uci: Sf26Bundle / Sf26NmpPrior / Sf26LmrGap / Sf26MulticutCorr default 0; margins 3 / 16 / 260 / 60 | PASS | logs/sf26_checks.json |
| T1/T4 movetime smoke, OFF + 3 lines, 4 positions: legal bestmoves | 32/32 | logs/sf26_checks.json |
| mate probe 22 mates @3M: OFF 19, nmp 20, lmr 20, mc 19; the deep KRK M15 (3k4/8/8/8/7r/8/8/6K1 b) is cp for all three at 3M, mate 11 for OFF and all three at 30M (horizon) | PASS | logs/sf26_checks.json, logs/sf26_lost1_30M.json |
| CI ASan+UBSan self-play default / nmp / lmr / mc / max: 0 sanitizer lines, 0 illegal | PASS (run 41286830769) | logs/ci_san_41286830769.txt |
| R14 combined line on this exe (kit lp_check.py, frozen bench_fens): the three singles together = `Sf26Bundle=14` in every bench d11-d22, perft and per-FEN node / bestmove number; differs from OFF; OFF = lock pins | PASS (NODE IDENTITY ALL OK) | logs/comb_r14/run_comb.log, off/b14/comb.json |
| R14 combined line: uci defaults 0, T1/T4 movetime smoke 16/16 legal, mate probe OFF 19 / combined 21 mates (none lost) | PASS | logs/comb_r14/cand_checks_comb.json |
| R14 CI ASan+UBSan config `comb` (the combined line), run 41422747717 on c8486179: default / nmp / lmr / mc / comb / max, 4 games each | PASS: 0 illegal, 0 sanitizer lines | logs/comb_r14/ci_san_41422747717.txt |
