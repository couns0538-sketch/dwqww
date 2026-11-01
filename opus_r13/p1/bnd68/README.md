# bnd68 - gate-68 bundle g43+g33+g49 (NonPawnCorr + PawnHist w50, ContHist4Pct 45, EvalOnlyStore + MinDepth 2) on the lock tree, LTO+PGO -Expose - UNPROVEN

Gate-ready candidate for the crew gate vs the lock FD3A5190 (UHO book first; 8moves_v3 second, never pooled). No Elo claim.

## Exe (not in git)
- `C:\o13\handoff\bnd68\forge_ltopgo_bnd.exe`
- sha256 **8dc93b38b7513de629e4854748f593b6d42a51bd4922a5c16d2a54b130866f69** (pc1 = pc2, kit v2.3 md5 729fe727, -Expose, workload v1)
- Source: lock d4f4312 (= src_al1s198_clean) + `bnd68_port.patch` (`patch -p1` on a clean lock copy).

## Gate line (engine A = this exe; engine B = lock FD3A5190, no options)
```
setoption name NonPawnCorr value 1
setoption name PawnHist value 1
setoption name NonPawnCorrWeight value 50
setoption name ContHist4Pct value 45
setoption name EvalOnlyStore value 1
setoption name EvalOnlyStoreMinDepth value 2
```
## PC precondition (check before game 1)
- exe sha256 as above; OFF bench (no setoption) d11..d22 = 312866/862329/3024920/12389307/34048354.
- With the gate line: **bench 13 = 776194 nodes** (d11..d22 = 365135/776194/2534121/11294400/32210117).

## Checks (evidence in ../logs/)
| check | result | evidence |
|---|---|---|
| pc1 = pc2 exe sha256 | PASS | logs/kit_bnd/SUMMARY_pc*.txt |
| OFF pins d11-d22, perft, per-FEN d13 nodes (plain = LTO+PGO) | ALL OK | logs/kit_bnd/off.compare.txt |
| ON with the gate line (plain = LTO+PGO, differs from OFF) | 365135/776194/2534121/11294400/32210117 | logs/kit_bnd/opt1.compare.txt |
| real -Wmissing-profile warnings / vfmadd | 0 / 0 | SUMMARY |
| uci: NonPawnCorr 0, PawnHist 0, LmrCorrThreshold 0, ContHist4Pct 0, EvalOnlyStore 0, EvalOnlyStoreMinDepth 0, NonPawnCorrWeight 100, NonPawnKeyIncludesKing 1, PawnHistDivisor 2 | PASS | logs/bnd68.json |
| T1/T4 go movetime 1000, 4 positions, OFF and gate line: bestmove legal (engine's own go perft 1) | 16/16 | logs/bnd68.json |
| mate probe (22 forced mates, 3M nodes): mates found OFF 19, NonPawnCorr=1;PawnHist=1;Non 22 | PASS | logs/bnd68.json |
| CI ASan+UBSan self-play (Linux g++ 13.3), configs default/gate/max: 0 sanitizer lines, 0 illegal | PASS | logs/ci_san_41212623622.txt |

- Port = packae2r's board/search files (byte-equal); src/include line set = packa (item 2) + packe2r (item 5) exactly: logs/bnd68_lineset.txt. Old result: H1 on the old h256e12 base.
