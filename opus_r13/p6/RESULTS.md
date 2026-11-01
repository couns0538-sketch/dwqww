# R13 Phase 6 - Syzygy on the lock tree - IN PROGRESS

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
