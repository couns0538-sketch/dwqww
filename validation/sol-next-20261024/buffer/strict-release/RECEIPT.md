# Strict buffer Release qualification

**PASS for the requested flags and node/perft closure.** Both engines were
built from released `forge-buffer-source.zip` (SHA256
`e05e75180a6e9b2c390fb7711aa6f686b51ac172333ab65670347bbce852fb51`),
source commit `30e703edc90976b9c59fb22912ddabb3b690658f`, in fresh H-only
directories. All 99 source hashes match the embedded manifest and remain
unchanged after both builds; the network remains `74c4009d...275b1b`.

Both profiles use GCC14.2, C++20, H256, `-O3 -DNDEBUG -ffp-contract=off
-fno-fast-math -march=znver5`, explicit compile **and** link `-pthread`, and
`-static`. `FORGE_COMPLETE_ITERATION_ONLY=0` is explicit. Configure, build and
engine commands were pinned to CPU3; each build used `--parallel 1`.

| Profile | Explicit AVX512 / ALIGN64 | Verification |
| --- | --- | --- |
| OFF | 0 / 0 | First engine process: d11=308972. Engine and core archive exactly byte-identical to the original Release artifacts; remaining original gates reused by byte proof. |
| ON Release | 1 / 1 | First engine process: d11=308972. Then all remaining depths and both perft5 positions freshly checked. |

Both profiles' recorded complete matrix is:

| Depth | Nodes |
| --- | ---: |
| 11 | 308972 |
| 13 | 745494 |
| 16 | 2460422 |
| 20 | 11901452 |
| 22 | 31111774 |

Startpos perft5=4865609; kiwipete perft5=193690690. All new engine commands
exit0 with empty stderr. Their first stdin is exactly the original d11
precondition stream; no earlier engine command was run on either new build.

- OFF engine: `dbc2df7403b20f3a767e22e1d53e11716a7ecac702f846bad666973d02306ac4`
- OFF core: `7f942d0d29bc357859d990ba20bbd8d7713e2fffecc341963caa3b942b31ab9e`
- ON engine: `e69695843a43927882dc1826c7ae27ce36288942f44bffe7ca3b1810ee65ffaf`
- ON core: `0d0efb38e526cf42eb2bc63f4230513d2eee596b63db20ffbea322201eaf77fb`

The OFF hashes and direct byte comparisons match the original engine/core
before and after this task, allowing reuse of its all-depth/perft and full
CTest receipts. No full CTest was rerun. The original Release,
assertions-ON and ASan/UBSan-ON suites remain **14/15**, with the four existing
FAIL lines inside `forge_tests`; the new ON Release profile adds bench/perft
coverage only. Both new builds emit the same six `int`-to-`uint16_t`
`-Wconversion` warnings in unchanged TT calls; exact build stderr is retained.

`PROVENANCE.json` contains exact flags, link commands, binary/core hashes,
source hashes, old-artifact byte proofs, gate results and receipt references.
SHA256: `38f1ff033e03c4045b62849372d37d39362f7b99d8afe7a98d7ebee852a8d6b1`.
Per-command argv/stdin/stdout/stderr and actual exits are retained under
`off/` and `on/`. No repository/Git/index/ref changes, sanitizer rerun, timing
comparison or speed/Elo claim is introduced.
