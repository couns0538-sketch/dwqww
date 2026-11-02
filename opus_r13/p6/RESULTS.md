# R13 Phase 6 - Syzygy on the lock tree - READY: CR PASS both lines, gates queued by the crew (exe 150374ff); R14 evidence complete - UNPROVEN

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
| 50-move rule cases (check50.py, 20 cursed / blessed positions, Syzygy50MoveRule true / false) | 20/20 handled as expected | logs/check50.out |

## LTO+PGO build check (kit v2.3 -Expose, tag syz, 2026-11-01 11:02-11:12 PC clock, CPUs 2-3) - PASS
| check | result | evidence |
|---|---|---|
| two clean rebuilds (fresh exports C:\o13\src\syz_pc1 / syz_pc2) | **pc1 = pc2 = 150374ff4b9132b99b48e9ba6a51b36b89e22014c61cec3053d1f4f17b87d99f** (md5 ecec73fc), RESULT PASS both | logs/kit_syz/SUMMARY_pc1.txt, SUMMARY_pc2.txt, syz_kit.log |
| OFF (no options): bench d11-d22, perft, 8 FENs, plain = LTO+PGO = pins | ALL OK (312866 / 862329 / 3024920 / 12389307 / 34048354; 4865609 / 193690690) | logs/kit_syz/pc1_off.compare.txt |
| ON `SyzygyPath=D:\syzygy345`: plain = LTO+PGO | 313631 / 866959 / 2460490 / 11465604 / 31972996, differs from OFF (live) | logs/kit_syz/pc1_opt1.compare.txt |
| ON `SyzygyPath` + `SyzygyProbeDepth=4`: plain = LTO+PGO | 312794 / 847340 / 2563760 / 9925508 / 28519443, differs from OFF (live) | logs/kit_syz/pc1_opt2.compare.txt |
| load line (LTO+PGO exe, after `setoption name SyzygyPath value D:\syzygy345`) | `info string Syzygy: 145 WDL and 145 DTZ tables, up to 5 pieces` | logs/kit_syz/pc1_opt1.ltopgo.uci_excerpt.txt |
| bench 16 on the LTO+PGO exe: OFF / SyzygyPath / SyzygyPath + PD4 | 3024920 / 2460490 / 2563760 | logs/kit_syz/pc1_*.ltopgo.uci_excerpt.txt |
| warnings, codegen | compiler warning lines plain 0, LTO+PGO 1; real missing-profile / coverage warnings 0; -flto on the link line; vfmadd 0 | logs/kit_syz/kit_result_pc1.txt, kit_result_pc2.txt |
| plain exes | pc1 8f1ac76c, pc2 88ae1406: same size, exactly 4 bytes differ = the PE header TimeDateStamp (file offset 136) and the PE CheckSum (offset 216) - a link timestamp, no code difference; not binding (the binding rule is the LTO+PGO exe) | SUMMARY_pc*.txt, `cmp -l` (R14 review) |

## R14 checks on exe 150374ff (2026-11-02, cand_checks.py, CPUs 2-3, BelowNormal)
| check | result | evidence |
|---|---|---|
| uci: SyzygyPath (string, default `<empty>`), SyzygyProbeDepth (spin 1-10, default 1), Syzygy50MoveRule (check, default true) advertised with the OFF defaults | PASS | logs/cand_checks_syz_r14.json |
| T1 + T4 `go movetime 1000`, 4 positions x (OFF, path, path + PD4), bestmove in the engine's own `go perft 1` list | 24 / 24 legal | same |
| mate probe, 22 positions (R5D KRK/KQK + 2 mate-in-1), `go nodes 3000000`, Threads 1 | OFF 19 mates + 3 cp; each Syzygy line 19 mates + 3 TB-win scores (`cp 31870`, above MateInMaxPly 31743): all 22 decisive positions recognised as won | logs/mate_probe_compare_r14.txt |
| the tool's FAIL rule ("OFF mate, line not") | flags 3k4/8/8/8/7r/8/8/6K1 b (OFF mate 15, ON cp 31870 = TB win): a TB-win score instead of mate notation, not a lost mate; ON also turns OFF's cp 474 into mate 14 (8/1r6/8/8/8/4K2k/8/8 b) | same |
| CI ASan+UBSan self-play (run 41295841377, 73c2d139): default 4 games, tb / tb_pd4 / tb_no50 6 games each from 3-4 piece starts | 0 illegal moves, 0 sanitizer lines, PASS | logs/ci_san_41295841377.txt |
| CI at the option's max (R14: `SyzygyProbeDepth=10`, config tb_pd10 added to opus-r13-san-p6.yml), run 41420554076 on 2ba7c923 | default 4 games + tb / tb_pd4 / tb_no50 / **tb_pd10** 6 games each: 0 illegal moves, 0 sanitizer lines, PASS (green) | logs/ci_san_41420554076.txt |

## Code Review / QA (crew) - read, nothing to apply on this branch
- `CR_PASS_p6syzygy_path_al1_ltopgo_150374ff.ok` and `CR_PASS_p6syzygy_pd4_al1_ltopgo_150374ff.ok` (grok-pc\forge_push,
  2026-11-01 12:12 PC clock): Code Review PASS-notes for both lines (CR_OPUS_R13_P6_SYZYGY_DELTA_20261101.md md5 5c792d46,
  CI 41295841377 green, check_tb 211/211, syzygy_port.patch md5 4342d24f = this branch's patch); QA precheck OFF = lock pins,
  perft OK, ON = the benches above, uci = lock 61 options + the 3 Syzygy lines, 4-game smoke OK; GATE_EXE
  `forge_ltopgo_x_syzygy_al1_150374ff.exe` (same sha256). Gates `uhoP6syz_path_1503_vs_AL1lp` and `uhoP6syz_pd4_1503_vs_AL1lp`
  on UHO, each with a HELD 8moves_v3 40+0.4 confirm, never pooled.
- CR's LOW crfix `p6_checks_crfix.patch` (md5 4b537823, test tooling only) is not on the PC (not in
  `C:\Users\Administrator\qa_crfix_astra_r10\r13_patches\`, not on GitHub): not applied. CR counts check_tb 211/211; this
  branch's run counts 220/220 (200 random + 20 cursed / blessed) - CR's own selection, cause not visible without the patch.

### Review milestone R14-P6-1 (structured self-review, NOT independent - no sub-agents in R14)
- Reviewed: the kit evidence (both SUMMARY files, compares, warning lines), the R14 smoke / mate-probe output, CI log;
  candidate = exe 150374ff (unchanged since the CR PASS; nothing rebuilt).
- Findings: (1) cand_checks' mate rule reports a TB-win score as a "lost mate" - documented here and in the skill
  forge-candidate-checks (count decisive results for TB lines); (2) CI had no run at SyzygyProbeDepth's max (10) - config
  tb_pd10 added; (3) plain exes differ between pc1 / pc2 - expected (paths), not binding.
- Checks after: CI run 41420554076 (2ba7c923, tb_pd10 included) green. Next: nothing on P6 until the crew's gates report.

### Review milestone R14-P6-2 (20-minute review pass, structured self-review, NOT independent)
- Found + fixed: the first R14 text said the plain pc1 / pc2 exes differ by "build-path strings" - a guess. Measured with
  `cmp -l`: 4 bytes, the PE TimeDateStamp + CheckSum fields only; text corrected. No other finding in this file.
