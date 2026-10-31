# R13 Phase 1 - near-miss ports onto the lock tree (LTO+PGO -Expose) - IN PROGRESS

Branch `opus-r13-p1-nearmiss-ports` (from main). All results UNPROVEN: no Elo claim, the crew gate decides (UHO book first).
Lock = FD3A5190 (AL1 s198, kit v2.3 -Expose). Lock source = git d4f4312 (byte-identical to `src_al1s198_clean`, 20 files).
Scratch/builds on C:\o13 (F: had 45 GB < 50 GB floor at start). Handoff exes: `C:\o13\handoff\<item>\` (not in git).

## Ranking (prompt order)
| rank | item | state | gate line(s) | exe sha256 (pc1 = pc2) |
|---|---|---|---|---|
| 1 | b1 BundlePreset=B1 | TODO (after packa) | BundlePreset=B1 | - |
| 2 | packa_w50 | BUILDING | NonPawnCorr=1 PawnHist=1 NonPawnCorrWeight=50 | - |
| 2 | packa_w60 | BUILDING | NonPawnCorr=1 PawnHist=1 NonPawnCorrWeight=60 | same exe as w50 |
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
| LTO+PGO kit pc1 = pc2, OFF pins, ON per line, perft | RUNNING | - |
| uci option list / T1+T4 smoke / mate probe / CI ASan+UBSan self-play | TODO | - |

## Next
packa kit builds -> checks -> handoff READMEs; then B1 port (reference ON bench 280182/758456/3357587/11208630/20560049).
