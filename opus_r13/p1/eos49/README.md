# eos49 - EvalOnlyStore=1 EvalOnlyStoreMinDepth=2 (gate-49 line) on the lock tree, LTO+PGO -Expose - UNPROVEN

Gate-ready candidate for the crew gate vs the lock FD3A5190 (UHO book first; 8moves_v3 second, never pooled). No Elo claim.

## Exe (not in git)
- `C:\o13\handoff\eos49\forge_ltopgo_eos.exe`
- sha256 **a4e7f24cbb7334e1d203e92bfa71d4edbf8d10a6a5836ad702978dee32dddbdc** (pc1 = pc2, kit v2.3 md5 729fe727, -Expose, workload v1)
- Source: lock d4f4312 (= src_al1s198_clean) + `eos49_port.patch` (`patch -p1` on a clean lock copy).

## Gate line (engine A = this exe; engine B = lock FD3A5190, no options)
```
setoption name EvalOnlyStore value 1
setoption name EvalOnlyStoreMinDepth value 2
```
## PC precondition (check before game 1)
- exe sha256 as above; OFF bench (no setoption) d11..d22 = 312866/862329/3024920/12389307/34048354.
- With the gate line: **bench 16 = 3033426 nodes** (d11..d22 = 312866/862329/3033426/12953506/41008668).

## Checks (evidence in ../logs/)
| check | result | evidence |
|---|---|---|
| pc1 = pc2 exe sha256 | PASS | logs/kit_eos/SUMMARY_pc*.txt |
| OFF pins d11-d22, perft, per-FEN d13 nodes (plain = LTO+PGO) | ALL OK | logs/kit_eos/off.compare.txt |
| ON with the gate line (plain = LTO+PGO, differs from OFF) | 312866/862329/3033426/12953506/41008668 | logs/kit_eos/opt1.compare.txt |
| real -Wmissing-profile warnings / vfmadd | 0 / 0 | SUMMARY |
| uci: ContHist4Pct 0, EvalOnlyStore 0, EvalOnlyStoreMinDepth 0 | PASS | logs/eos49.json |
| T1/T4 go movetime 1000, 4 positions, OFF and gate line: bestmove legal (engine's own go perft 1) | 16/16 | logs/eos49.json |
| mate probe (22 forced mates, 3M nodes): mates found OFF 19, EvalOnlyStore=1;EvalOnlyStor 20 | see note | logs/eos49.json |
| CI ASan+UBSan self-play (Linux g++ 13.3), configs default/gate/max: 0 sanitizer lines, 0 illegal | PASS | logs/ci_san_41212623622.txt |

- Bench d11 / d13 with the gate line equal OFF (312866 / 862329); the line is live from d16, so the precondition uses bench 16.
- Mate probe: at 3M nodes the gate line reports cp 583 where OFF reports mate 15 in one deep KRK ending (3k4/8/8/8/7r/8/8/6K1 b); at 30M nodes both report mate 11 (logs/eos49_lost1_30M.json): horizon effect, not a lost mate line. The line finds 20 of 22 mates vs OFF 19.
- Port = packe2r's search files (byte-equal). The two OFF-path ValueNone guards keep OFF node-identical (pins ALL OK). Old result +8.57 LLR 1.76 (h256e12 base).
