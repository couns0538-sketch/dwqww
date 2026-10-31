# R13 Phase 1 - near-miss ports onto the lock tree (LTO+PGO -Expose) - IN PROGRESS

Branch `opus-r13-p1-nearmiss-ports` (from main). All results UNPROVEN: no Elo claim, the crew gate decides (UHO book first).
Lock = FD3A5190 (AL1 s198, kit v2.3 -Expose). Lock source = git d4f4312 (byte-identical to `src_al1s198_clean`, 20 files).
Scratch/builds on C:\o13 (F: had 45 GB < 50 GB floor at start). Handoff exes: `C:\o13\handoff\<item>\` (not in git).

## Ranking (prompt order)
| rank | item | state | gate line(s) | exe sha256 (pc1 = pc2) |
|---|---|---|---|---|
| 1 | b1 BundlePreset=B1 | PORTING | BundlePreset=B1 | - |
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

## Next
B1 port (reference ON bench 280182/758456/3357587/11208630/20560049): A1 HistRework + C6 board cuckoo applied (no fuzz); CorrHistPlus, CuckooRep search instance, TtPruneV2, BundlePreset being ported.
