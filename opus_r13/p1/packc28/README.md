# packc28 - Pack C gate-28 line (AspFailHighReduce, EvalSwing history) on the lock tree, LTO+PGO -Expose - UNPROVEN

Gate-ready candidate for the crew gate vs the lock FD3A5190 (UHO book first; 8moves_v3 second, never pooled). No Elo claim.

## Exe (not in git)
- `C:\o13\handoff\packc28\forge_ltopgo_pkc.exe`
- sha256 **cf617e671069d32ba6eb5ce452b56e193af41442a5db39388a19005a04b22351** (pc1 = pc2, kit v2.3 md5 729fe727, -Expose, workload v1)
- Source: lock d4f4312 (= src_al1s198_clean) + `packc28_port.patch` (`patch -p1` on a clean lock copy).

## Gate line (engine A = this exe; engine B = lock FD3A5190, no options)
```
setoption name AspFailHighReduce value 1
setoption name AspFailHighMaxReduce value 3
setoption name EvalSwingMult value 24
setoption name EvalSwingMax value 200
```
## PC precondition (check before game 1)
- exe sha256 as above; OFF bench (no setoption) d11..d22 = 312866/862329/3024920/12389307/34048354.
- With the gate line: **bench 13 = 690187 nodes** (d11..d22 = 277906/690187/2273374/8834244/17379405).

## Checks (evidence in ../logs/)
| check | result | evidence |
|---|---|---|
| pc1 = pc2 exe sha256 | PASS | logs/kit_pkc/SUMMARY_pc*.txt |
| OFF pins d11-d22, perft, per-FEN d13 nodes (plain = LTO+PGO) | ALL OK | logs/kit_pkc/off.compare.txt |
| ON with the gate line (plain = LTO+PGO, differs from OFF) | 277906/690187/2273374/8834244/17379405 | logs/kit_pkc/opt1.compare.txt |
| real -Wmissing-profile warnings / vfmadd | 0 / 0 | SUMMARY |
| uci: AspFailHighReduce 0, EvalSwingMult 0, TtCutoffHistory 0, AspFailHighMaxReduce 3, EvalSwingMax 200 | PASS | logs/packc28.json |
| T1/T4 go movetime 1000, 4 positions, OFF and gate line: bestmove legal (engine's own go perft 1) | 16/16 | logs/packc28.json |
| mate probe (22 forced mates, 3M nodes): mates found OFF 19, AspFailHighReduce=1;AspFailH 22 | PASS | logs/packc28.json |
| CI ASan+UBSan self-play (Linux g++ 13.3), configs default/gate/max: 0 sanitizer lines, 0 illegal | PASS | logs/ci_san_41212623622.txt |

- Port = packc.patch with patch -p1 -F0; line set EQUAL (logs/packc28_lineset.txt). Gate line from gate28 RUN_INFO.json. Old result +9.27 LLR 1.83 (h256e12 base).
