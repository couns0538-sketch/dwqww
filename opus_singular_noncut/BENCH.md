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

### Runtime 0 (default) = trial_w6 node for node: BIT-EXACT on the full 12k
- bitexact_check **full 12k** `-SkipSan`, 01:35:16-01:45:55 (`logs/bx_gate_off_12k.log`): **VERDICT BIT-EXACT (L1-L3;
  L3 on 12000 FENs)**.
  - L1: net on d11-d22 = 312866 / 862329 / 3024920 / 12389307 / 34048354; net off = 375354 / 907205 / 2448617 /
    13573040 / 24506465. Cand = trial_w6 = pins.
  - L2: perft 5 startpos 4865609, kiwipete 193690690 = pins.
  - L3: fens_12k_v2.txt (md5 e7dbf2c8) go depth 13, OwnBook false, ucinewgame per FEN: 12000 / 12000 identical
    (depth, score, nodes, bestmove; 12000 distinct reference rows; reference = the cached trial_w6 rows in
    `F:\ospd\ref\4181a589`, read only).
- The tool's closing `LOCK PROOF INCOMPLETE` line is its generic speed-lock note. This exe is a search candidate for
  an SPRT, not a speed lock.

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

## L4 sanitizers (gate source `snc_gate`), 02:32:51-02:34:58
- `bitexact_check -OnlyL4 -SanSrc D:\opus_singular_noncut\src\snc_gate` (`logs/bx_gate_l4.log`): **L4 PASS** at the
  default (OFF). Builds are in `D:\opus_singular_noncut\out\bx_gate_l4\san`; the MSVC reference nodes of the lock
  source come from the existing cache, read only.
  - MSVC ASan: bench 16 = 2587341 (= the reference source under MSVC ASan), exit 0, 0 reports.
  - g++ UBSan-trap: bench 16 = 3024920 (= the candidate's d16 = pin), exit 0, 0 reports.
- ON path, the same two exes with `setoption name SingularNonCut value 1` + `bench 16` (`logs/san_on/`): UBSan-trap
  3254758 (= the gate exe's ON d16), MSVC ASan 2505351 (MSVC orders equal scores differently; differs from its
  OFF 2587341, so the option is live there too). Both: exit 0, 0 sanitizer lines.

## Box test (the spec's counter build), 02:34-02:35
- Counter build, test only and never a gate exe: `singular_noncut_counters_test.patch` on `snc_gate` adds
  `FORGE_SPEC_COUNTERS` (default 0).
  - Built as `build_variants -Variant o3 -Define FORGE_SPEC_COUNTERS=1` (sha256 5ffd4e04..., quick pins OK).
  - Plain globals, valid at Threads 1; one `info string spec_counters` line at process exit.
- Counters do not touch the tree: the counter build's bench nodes equal the gate exe's in all four runs (OFF d16
  3024920 / d20 12389307 = pins; ON d16 3254758 / d20 10207303).
- 8 bench FENs, one process per run (`logs/box/`):

| run | tries | at cut nodes | +1 | +2 | multicut return | -2 | -1 | 0 | nodes in verifications | per try |
|---|---|---|---|---|---|---|---|---|---|---|
| OFF d16 | 15645 | 13819 (88.3 %) | 3364 | 3195 | 3577 | 2127 | 2789 | 593 | 296975 | 19.0 |
| ON d16 | 12622 | 10540 (83.5 %) | 2830 | 2380 | 3071 | 1872 | 1857 | 612 | 263551 | 20.9 |
| OFF d20 | 92597 | 84976 (91.8 %) | 14929 | 16464 | 21770 | 15420 | 21705 | 2309 | 1735132 | 18.7 |
| ON d20 | 52478 | 46515 (88.6 %) | 9272 | 8845 | 13314 | 8993 | 10364 | 1690 | 1166879 | 22.2 |

- Readings (box facts, no strength claims):
  - Live share: 88-92 % of all singular tries are at cut nodes, so OFF -> ON changes most verifications.
  - ON spends more nodes per verification (d20 22.2 vs 18.7, d16 20.9 vs 19.0). That matches the card's reasoning
    (no cut-node LMR penalty inside the verification).
  - The extension share per try hardly moves: +1 / +2 together are 34.5 % ON vs 33.9 % OFF at d20, 41.3 % vs 41.9 %
    at d16. The +2 share drops a little at both depths (d20 16.9 % vs 17.8 %, d16 18.9 % vs 20.4 %).
  - So the card's "fewer +1 / +2" holds only for the +2 part. The spec says to report this; it is no stop.
  - Tries per 1M nodes drop at d20 (5141 ON vs 7474 OFF). The tree shape changes (d20 total 0.82x), not only the
    verifications.
