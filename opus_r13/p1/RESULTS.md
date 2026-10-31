# R13 Phase 1 - near-miss ports onto the lock tree (LTO+PGO -Expose) - IN PROGRESS

Branch `opus-r13-p1-nearmiss-ports` (from main). All results UNPROVEN: no Elo claim, the crew gate decides (UHO book first).
Lock = FD3A5190 (AL1 s198, kit v2.3 -Expose). Lock source = git d4f4312 (byte-identical to `src_al1s198_clean`, 20 files).
Scratch/builds on C:\o13 (F: had 45 GB < 50 GB floor at start). Handoff exes: `C:\o13\handoff\<item>\` (not in git).

## Ranking (prompt order)
| rank | item | state | gate line(s) | exe sha256 (pc1 = pc2) |
|---|---|---|---|---|
| 1 | b1 BundlePreset=B1 | READY (handoff b1/README.md) | BundlePreset=B1 | e950c77e7832e7f32d701bf1424d65553957ca8486e8bd1d29d922f9b1e25900 |
| 2 | packa_w50 | READY (handoff packa_w50/README.md) | NonPawnCorr=1 PawnHist=1 NonPawnCorrWeight=50 | 07cc2393934528272d3114e3d664a3165fabc3614f2eba9a2782ca919e4b8146 |
| 2 | packa_w60 | READY (handoff packa_w60/README.md) | NonPawnCorr=1 PawnHist=1 NonPawnCorrWeight=60 | same exe as w50 |
| 3 | bnd68 | TODO (next plan) | | |
| 4 | packc28 | TODO (next plan) | | |
| 5 | eos49 | TODO (next plan) | | |

## packa (items packa_w50 / packa_w60: one exe, two gate lines)
| check | result | evidence |
|---|---|---|
| source | `D:\grok-pc-data\opus30h_inputs\packa.patch` sha256 909d9bfb… (old base h256e12) | - |
| port = packa.patch minus its CMakeLists.txt hunk (no CMake in the lock tree), `patch -p1 -F0`, no fuzz | PASS | packa_w50/packa_port.patch (sha256 624f3643…) |
| line set: port vs original | EQUAL except the 4 CMakeLists '+' lines; EQUAL with CMakeLists excluded | logs/packa_lineset.txt |
| plain build (lock g++ line + Expose) OFF bench d11-d22 / perft / per-FEN d13 nodes | 312866/862329/3024920/12389307/34048354, 4865609/193690690, fen nodes = kit README lock values: PASS | logs/packa_plain_off.json |
| plain ON w50 bench d11/d13 | 284907 / 744597 (live) | logs/packa_plain_w50.json |
| plain ON w60 bench d11/d13 | 268049 / 676197 (live) | logs/packa_plain_w60.json |
| ON bench vs original | not comparable: packa was benched on the h256e12 base (other net), never on the AL1 tree | - |
| tests/nonpawn_key_tests.cpp (hand build, asserts on) | passed | logs/packa_nonpawn_key_tests.out |
| LTO+PGO kit pc1 = pc2 (07cc2393…), OFF pins + perft + per-FEN ALL OK, ON w50 d11-d22 284907/744597/2764319/14536259/25311735, ON w60 268049/676197/2377430/13677030/32934550 (plain = LP, live), 0 missing-profile, vfmadd 0 | PASS | logs/kit_pka/ |
| uci: switches NonPawnCorr/PawnHist/LmrCorrThreshold default 0; parameters keep original defaults (100/1/2) | PASS | logs/packa.json |
| T1/T4 movetime 1000 smoke, 24 runs, bestmove legal | 24/24 PASS | logs/packa.json |
| CI ASan+UBSan self-play: default/w50/w60/max/active, 0 sanitizer lines, 0 illegal (+ lock control) | PASS run 41209065763 | logs/ci_san_41209065763.txt |
| mate probe 22 forced mates @3M nodes: OFF 19 / w50 22 / w60 20; w60's one miss (OFF M15, KRK) is found at 30M nodes | PASS (horizon note) | logs/packa.json, logs/lost1_*.json |

## b1 (item 1)
| check | result | evidence |
|---|---|---|
| port: A1 a8b63aae + C6 2cb0babd by `patch -p1 -F0`; C6 search part, C2, TtPruneV2, BundlePreset by tools/port_b1.py (all anchors asserted once) | DONE | b1/b1_port.patch, tools/port_b1.py |
| **ON nodes = forge-bundle-int b7c17722 (binding port proof)**: B1 280182/758456/3357587/11208630/20560049, TtPruneV2 309157/736967/2960397/12062561/34293668, CorrHistPlus=1 d11 318363 | EQUAL (plain and LTO+PGO) | logs/b1_plain_*.json, logs/kit_b1k/opt1.compare.txt |
| line set vs original commits | layout differences only (listed) | logs/b1_lineset_vs_original_commits.txt |
| LTO+PGO pc1 = pc2 e950c77e…, OFF ALL OK, ON live (B1, CorrHistPlus=7), 0 missing-profile, vfmadd 0 | PASS | logs/kit_b1k/ |
| uci defaults OFF / params 100, smoke 16/16 legal, mate probe OFF 19 B1 21 (none lost) | PASS | logs/b1.json |
| CI ASan+UBSan self-play default/B1/max | PASS run 41210111829 | logs/ci_san_41210111829_b1.txt |

## Handoff verification (fresh, 2026-10-31)
- Each committed port patch, applied with `patch -p1 -F0` to a fresh `git archive d4f4312` lock copy, equals the kit's
  built source `C:\o13\w\<tag>_pc1\src_copy` (diff -rq, build products excluded): packa IDENTICAL, b1 IDENTICAL
  (logs/verify_patch_*.diff are empty). Handoff exes hash to the pc1 = pc2 values (b1 e950c77e…, packa 07cc2393…).

## Next
Block 1 of the plan is done for P1 (items 1-2). P1 items 3-5 (bnd68, packc28, eos49) go into the next short plan after P2 steps 1/1a/1b.
