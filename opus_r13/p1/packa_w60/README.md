# packa_w60 - NonPawnCorr + PawnHist, NonPawnCorrWeight=60 (old gate 34) on the lock tree, LTO+PGO -Expose - UNPROVEN

Gate-ready candidate for the crew gate vs the lock FD3A5190 (UHO book first; 8moves_v3 second, never pooled).
No Elo claim. Same exe as packa_w50 (one build, two gate lines).

## Exe (not in git)
- `C:\o13\handoff\packa_w60\forge_ltopgo_pka.exe` (built at `C:\o13\w\pka_pc1\src_copy\forge_ltopgo_pka_pc1.exe`)
- sha256 **07cc2393934528272d3114e3d664a3165fabc3614f2eba9a2782ca919e4b8146** (pc1 = pc2, kit v2.3 md5 729fe727, -Expose, workload v1)
- Source: lock d4f4312 (= src_al1s198_clean) + `../packa_w50/packa_port.patch` (`patch -p1` on a clean lock copy).

## Gate line (engine A = this exe; engine B = lock FD3A5190, no options)
```
setoption name NonPawnCorr value 1
setoption name PawnHist value 1
setoption name NonPawnCorrWeight value 60
```
## PC precondition (check before game 1)
- exe sha256 as above; OFF bench (no setoption) d11..d22 = 312866/862329/3024920/12389307/34048354.
- With the gate line: **bench 13 = 676197 nodes** (d11..d22 = 268049 / 676197 / 2377430 / 13677030 / 32934550).

## Checks (evidence in ../logs/)
| check | result | evidence |
|---|---|---|
| pc1 = pc2 exe sha256 | PASS (07cc2393…) | logs/kit_pka/SUMMARY_pc1.txt, SUMMARY_pc2.txt |
| OFF pins d11-d22, perft 4865609/193690690, per-FEN d13 nodes (plain = LTO+PGO) | ALL OK | logs/kit_pka/off.compare.txt |
| ON bench with this line, plain = LTO+PGO, differs from OFF (live) | 268049 / 676197 / 2377430 / 13677030 / 32934550 | logs/kit_pka/opt2.compare.txt |
| real -Wmissing-profile warnings / vfmadd | 0 / 0 | SUMMARY |
| uci lists NonPawnCorr, PawnHist, LmrCorrThreshold (default 0 = OFF); parameters NonPawnCorrWeight 100, NonPawnKeyIncludesKing 1, PawnHistDivisor 2 (original defaults) | PASS | logs/packa.json |
| T1/T4 go movetime 1000, 4 positions, OFF/w50/w60: bestmove legal (engine's own go perft 1) | 24/24 | logs/packa.json |
| CI ASan+UBSan self-play (Linux g++ 13.3), default / w50 / w60 / max / active: 0 sanitizer lines, 0 illegal | PASS (run 41209065763) | logs/ci_san_41209065763.txt |
| mate probe (22 forced mates, 3M nodes): mates found OFF 19, w50 22, w60 20 | see note | logs/packa.json, logs/lost1_*.json |
| port proof: line set = packa.patch minus its CMakeLists hunk (no CMake in the lock tree) | EQUAL | logs/packa_lineset.txt |
| tests/nonpawn_key_tests.cpp (hand-built, asserts on) | passed | logs/packa_nonpawn_key_tests.out |

Mate-probe note: w60 reports cp 573 where OFF reports mate 15 in one deep KRK ending (3k4/8/8/8/7r/8/8/6K1 b) at 3M and
10M nodes, and finds that mate at 30M nodes. It finds two mates OFF does not find at 3M (M17, M14). These are horizon effects
of a changed search, not a lost mate line.
ON bench vs the original: packa was only benched on the old h256e12 base (other net), so its ON numbers cannot match here.
