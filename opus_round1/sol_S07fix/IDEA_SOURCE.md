# IDEA_SOURCE — S07fix

- Harness: Sol's S07 tool `forge_sol_S07_screen_sweep_20261026.py` (branch `forge/sol-pack31-20261025` @ 17aa0cae,
  sha256 `7262dcf8259781396849c217e8713868d8f37736e63ec6015ff99c845b57baf7`), used unchanged (copy in this folder),
  and its WAC300 suite (`forge_sol_S07_wac300_20261026.epd`, sha256 `9bfb7b42...`, identical to opus-C3
  `tools/wac300.epd`). Each screen = one call of its `wac300` mode, i.e. exactly the harness that produced the
  official 271.
- Fix-up items: `SOL_LEFTOVERS_FOR_CLAUDE.md` section 3, S07-1 (lock vs real candidate interleaved, 100 ms and
  1000 ms, mean + range, 1-3 points = noise) and S07-2 (lock 3x at 1000 ms with load/CPU logged; explain 271 vs
  283-286; keep the official 271).
- 271 vs 283 evidence base: Sol's native evidence archive `forge_sol_S07_native_evidence_20261026.tar.gz` (his raw
  UCI stdout of the 271 run: per-position nodes/nps/depth) and his comparability audit
  `forge_sol_S07_WAC_comparability_audit_20261026.json` (historical 283/284 lock controls, 286/287 = different-net
  candidates, harness differences).
- Engines: the PC's h256_e12 lock exe (`forge_h256_e12.exe`, sha256 `456743d9...`, bench d11 308972 = the reference
  of Sol's tool and of the 271 run) and the most recent real gate candidate, gate38 `cand_packa_w55`
  (`forge_packa_h256.exe`, sha256 `c98ee238...`, options NonPawnCorr=1 PawnHist=1 NonPawnCorrWeight=55, from its
  RUN_INFO.json). Copies in `F:\opus_scratch\sol_S07fix\bin`.
- Driver, load sampler (GetSystemTimes / GlobalMemoryStatusEx) and analysis: original.
- No engine code changed; no Elo or speed claim.
