# BENCH - SingularNonCut identity and gate builds (2026-11-06, PC clock)

All runs at Idle. Builds and bitexact_check on CPUs 0-1 (the tools pin themselves to 0x3); MCP forge-uci benches on
CPUs 0-1. Bench = the engine's 8-FEN `bench`, Threads 1, Hash 16, cleared per FEN; perft = `go perft 5`.
Pin tables = `opus_speed/tools/uci_lib.ps1` (the old lock FD3A5190's pins; trial_w6 searches the same nodes).

## Parent
- Branch point 277a8f90 = final tip of `opus-speed-20261105`.
- Parent exe = the live lock trial_w6, sha256 4181A5893F15E732D08A2F4FCFBAFFB23618B2567B9F30F9ACD58BE2E69B6FB0
  (`C:\Users\Administrator\grok-pc\forge_push\bin\forge_ltopgo_x_al1s198_trial_w6.exe`). It is the base of the gate
  that the crew started 00:08 (RUN_INFO `base.sha256`).
- The hunt's H1-H9 switches (H5 MOVE_STORE32 = the only screening WIN) were never merged into a lock, so trial_w6 is
  the parent exe.

## Identity build (FORGE_SINGULAR_NONCUT 0, no new option): PASS
- Source `D:\opus_singular_noncut\src\snc_id` = trial_w6 source + `singular_noncut_after_w6.patch`, with the six
  trial_w6 defaults flipped in the source (the hunt_identity "six" route).
- Build: `build_variants.ps1 -Variant lp_v1` (QA kit v2.3 lines, -Expose), 01:32:53-01:33:52.
- Exe `D:\opus_singular_noncut\build\snc_id_lp_v1\src_copy\forge_lp_v1.exe`, sha256
  4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0, md5 331ea9bf077cbf9c4c823125baa80bcc.
- **sha256 = trial_w6's, and `cmp` says byte-identical.** So the parent still builds that exact exe, and macro 0 adds
  nothing. Before the build, all 8 units preprocessed (`g++ -E -P`, kit flags) to trial_w6's token stream
  (`logs/pp_neutrality.txt`).
- bitexact_check `-Quick -SkipSan` (01:34:07-01:37:41, `logs/bx_id.log`): **BIT-EXACT** L1-L3.

| check | identity exe | pin |
|---|---|---|
| bench d11 net on | 312866 | 312866 |
| bench d13 net on | 862329 | 862329 |
| bench d16 net on | 3024920 | 3024920 |
| bench d20 net on | 12389307 | 12389307 |
| bench d22 net on | 34048354 | 34048354 |
| bench d11 net off | 375354 | 375354 |
| bench d13 net off | 907205 | 907205 |
| bench d16 net off | 2448617 | 2448617 |
| bench d20 net off | 13573040 | 13573040 |
| bench d22 net off | 24506465 | 24506465 |
| perft 5 startpos | 4865609 | 4865609 |
| perft 5 kiwipete | 193690690 | 193690690 |
| L3 2,000 FENs go depth 13 (fens_12k_v2, md5 e7dbf2c8) | 2000 / 2000 identical | trial_w6 cache |

- `uci`: no SingularNonCut option. The exe is the same bytes as trial_w6.

## Gate build (FORGE_SINGULAR_NONCUT 1, option SingularNonCut default 0)
- Source `D:\opus_singular_noncut\src\snc_gate` = `snc_id` + `#define FORGE_SINGULAR_NONCUT 1`.
- `build_variants.ps1 -Variant lp_v1 -Twice` (01:32:53-01:34:46): **REPRO pc1 = pc2**.
- sha256 5f6be7c55ba318790c26690b0a96edec678aab786334247a8e7a630c5610d117, md5 e71c1b18d09186cb745e023398395a60.
- vfmadd 0, gcda 8, 0 missing-profile warnings, quick pins 312866 / 862329 / 3024920 OK at the default 0.
- Handoff copy `D:\opus_singular_noncut\pack\forge_singular_noncut_gate_5f6be7c5.exe` (same sha256).
- `uci` (MCP uci_options): `option name SingularNonCut type spin default 0 min 0 max 1`, listed after
  FailLowContinuationBonus. 62 options.

### Runtime 0 (default) = trial_w6 node for node
- bitexact_check **full 12k** `-SkipSan` started 01:35 (`logs/bx_gate_off_12k.log` when done).
- L1 (net on + off d11-d22 = pins) and L2 (perft = pins) PASS. L3 on 12,000 FENs: running.

### Runtime 1 (`setoption name SingularNonCut value 1`): LIVE
- MCP pin_check `-Full`, 01:38:30-01:39:07: advertised, accepted and live; perft = pins.

| bench | ON (SingularNonCut=1) | OFF = pin | ON / OFF |
|---|---|---|---|
| d11 net on | 368386 | 312866 | 1.177 |
| d13 net on | 863236 | 862329 | 1.001 |
| d16 net on | 3254758 | 3024920 | 1.076 |
| d20 net on | **10207303** | 12389307 | 0.824 |
| d22 net on | 28667881 | 34048354 | 0.842 |
| d13 net off | 873459 | 907205 | 0.963 |
| d20 net off | 12554284 | 13573040 | 0.925 |
| perft 5 startpos / kiwipete | 4865609 / 193690690 | same | - |

- Repeat: ON d20 net on of the pc2 exe = 10207303 (separate process, same nodes).
- The spec's sanity band (d22 ON within 0.7x-1.5x of OFF): 0.842, inside it.
- Fewer nodes at d20 / d22 do NOT mean stronger or faster play. Node counts at fixed depth are no Elo evidence; the
  SPRT decides.
