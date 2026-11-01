# R13 Phase 6 - Syzygy on the lock tree - IN PROGRESS (CR R13: port PASS)

Branch `opus-r13-p6-syzygy` (from main). UNPROVEN: no Elo claim.
- Source: Opus C1 (3fd235c8 + aa0b0a83; identical to the final opus-r3-stack / forge-bundle-int b7c17722 versions): the own
  Syzygy WDL/DTZ prober, the search glue and the options SyzygyPath / SyzygyProbeDepth / Syzygy50MoveRule only
  (IntendedThreefold and HardDeadline left out: one change per gate line).
- Port: tools/port_syzygy.py (anchored, each anchor exactly once) on a fresh lock copy -> p6/syzygy_port.patch
  (6 files, +1796 -6): include/forge/syzygy.hpp (only change: forge/search_types.hpp -> forge/search.hpp), src/syzygy.inc,
  src/tablebase.inc (unchanged, included at the end of search.cpp as in R3), hooks in search.cpp / search.hpp / uci.cpp.
- Next (needs CPU after the P3 SPSA): plain build, OFF pins, ON bench with SyzygyPath=D:\syzygy345 (read only), WDL/DTZ check on
  200 known 5-man positions against python-chess's prober as an oracle (test tool only), 50-move cases, kit pc1/pc2, checks.
Gate lines (planned): `SyzygyPath D:\syzygy345`; `SyzygyPath D:\syzygy345` + `SyzygyProbeDepth 4`.

## Checks (plain build of the port, 6d74e0f5, 0 warnings, vfmadd 0)
| check | result | evidence |
|---|---|---|
| OFF (SyzygyPath empty): bench d11-d22, perft 5 | 312866/862329/3024920/12389307/34048354, 4865609/193690690 = lock pins | logs/off.json |
| **ON `SyzygyPath D:\syzygy345`** (145 WDL + 145 DTZ, read only) | **313631/866959/2460490/11465604/31972996 = the R5C-N3 ON pins of the original prober** (exact port proof) | logs/tb.json |
| ON + `SyzygyProbeDepth 4` | 312794/847340/2563760/9925508/28519443 (differs from SyzygyPath alone: live) | logs/tb_pd4.json |
| WDL / DTZ vs an independent prober (python-chess chess.syzygy as test oracle): 200 random legal 5-man positions from 110 materials + 20 with WDL +-1 (cursed / blessed), seed 13601 | WDL 220/220 equal, DTZ 220/220 exact, 0 rejected tables | logs/tb200.*, tools tb_probe.cpp + check_tb.py |
