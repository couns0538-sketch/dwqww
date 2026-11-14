# Screen verification

Node-limited screening and no-regression matches on grok47/r3-* and grok47/r4-03, grok47/r4-04, and grok47/r4-05 are checked against the pushed games.
A node limit is replayed for the first 100 openings, 200 games when each opening is played twice, of the first chunk.
The replay uses that commit, the recorded flags and options, the recorded openings, and a fresh engine for every game.
A clock match is not replayed move by move. The recorded configuration, the legality of every game, the results, and the time losses are checked.

## Toolchain

fastchess version: fastchess alpha 1.8.3 20261113-3d7a4db
fastchess source: 3d7a4db2493fc85a05ef010fd7e13a3884667aa2
fastchess binary sha256: 936811dcaea97a853a762d3f1e6fb600610c1be3c1f759f2f2fefa2e6500b21e
book file: UHO_Lichess_4852_v1.epd
book lines: 2632036
book sha256: 7a7f6470615a69c6cf23d565417701d38732876f480af90d67b42abade35644a
Fastchess and the book were fetched locally and are not in this branch.
Self-check at e04556dd, portable x86-64-v3, 20000 nodes, one opening, two games, fresh engines: a second run matched the first move by move and node count by node count.

## Results

grok47/r3-04-lmr-late-parent-relief ae2cc041e24b 200 identical
grok47/r3-08-asp-capped-reopen dc2e25b54d7c 20 identical

## Commands and hashes

grok47/r3-04-lmr-late-parent-relief ae2cc041e24b kind nodes pgn forge-combo29/tests_r3fu_04/chunk-0001.pgn
build flags: -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=OFF -DFORGE_MARCH=x86-64-v4 -DCMAKE_CXX_COMPILER=g++
engine source sha256: f3ecae11d4cd:223845227cb2248c6b4c9843b416bfcdee8a0d9fb891303b27180cdd83cd5a1d ae2cc041e24b:223845227cb2248c6b4c9843b416bfcdee8a0d9fb891303b27180cdd83cd5a1d
engine binary sha256: f3ecae11d4cd:8919bd97dd07407c40e2d3f14793b691da7b672f4878d366af4e374363e2f7ac ae2cc041e24b:8919bd97dd07407c40e2d3f14793b691da7b672f4878d366af4e374363e2f7ac
fastchess command: /home/ubuntu/r4-verify/fastchess-src/fastchess -engine cmd=/home/ubuntu/r4-verify/build/f3ecae11d4cdf9fb58925853e25a340f921b53ba-37997d042e39/forge name=LmrLateParentReliefOn restart=on option.LmrLateParentRelief=true option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 -engine cmd=/home/ubuntu/r4-verify/build/ae2cc041e24b5805d04fd4a0d95fcf88f20fdb84-37997d042e39/forge name=LmrLateParentReliefOff restart=on option.LmrLateParentRelief=false option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 -rounds 100 -games 2 -concurrency 2 -openings file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-04-lmr-late-parent-relief/02d819ff1e60/openings.epd format=epd order=sequential -pgnout file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-04-lmr-late-parent-relief/02d819ff1e60/replay.pgn append=false nodes=true notation=san -ratinginterval 0 -scoreinterval 0

grok47/r3-08-asp-capped-reopen dc2e25b54d7c kind nodes pgn forge-combo29/tests_r3fu_08/chunk-001.pgn
build flags: -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=clang++ -DFORGE_MARCH=x86-64-v4 -DFORGE_PORTABLE=OFF
engine source sha256: dc2e25b54d7c:e3397b5a3b2a673ce6b30163d531bd851813a43279027ea30f502e376f455327 dc2e25b54d7c:e3397b5a3b2a673ce6b30163d531bd851813a43279027ea30f502e376f455327
engine binary sha256: dc2e25b54d7c:1e647eead4e6ee779673c3463d897c06d9727ea66cc918a7a1f9762641abd480 dc2e25b54d7c:1e647eead4e6ee779673c3463d897c06d9727ea66cc918a7a1f9762641abd480
fastchess command: /home/ubuntu/r4-verify/fastchess-src/fastchess -engine cmd=/home/ubuntu/r4-verify/build/dc2e25b54d7ce176090fd439d1b4df2d5fbcefc4-7e389295b5ee/forge name=on restart=on option.Threads=1 option.Hash=16 option.OwnBook=false option.AspCappedReopen=true nodes=50000 -engine cmd=/home/ubuntu/r4-verify/build/dc2e25b54d7ce176090fd439d1b4df2d5fbcefc4-7e389295b5ee/forge name=off restart=on option.Threads=1 option.Hash=16 option.OwnBook=false option.AspCappedReopen=false nodes=50000 -rounds 10 -games 2 -concurrency 2 -openings file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-08-asp-capped-reopen/d4da1cf2a088/openings.epd format=epd order=sequential -pgnout file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-08-asp-capped-reopen/d4da1cf2a088/replay.pgn append=false nodes=true notation=san -ratinginterval 0 -scoreinterval 0

## Still open

grok47/r3-01-eval-rule-50-damp b009da42b 2026-11-14 15:29:24 +0000 Record the EvalRule50Damp screen command, hashes, and bench rates.
grok47/r3-02-threat-history e01cad043 2026-11-14 15:30:53 +0000 Record the occupancy-fix bench and the screening command.
grok47/r3-03-lmr-signed-correction 4c1dd7ac5 2026-11-14 15:30:56 +0000 Record the one-ply LMR fraction and the owner-build bench.
grok47/r3-05-hindsight-depth 4ce2b8b18 2026-11-14 15:50:54 +0000 Add the first HindsightDepth screening chunk.
grok47/r3-06-null-threat-verify 5afe0de5d 2026-11-14 15:36:37 +0000 Record the owner-build bench sample and screen setup.
grok47/r3-07-null-see-veto f3bcd9a05 2026-11-14 15:43:06 +0000 Add the first NullSeeVeto screen chunk and bench rates.
grok47/r3-09-asp-arm-late a8a175f09 2026-11-14 15:50:46 +0000 Add the first UHO screen chunk for AspArmLate.
grok47/r3-10-evasion-ordering 692004da0 2026-11-14 15:45:07 +0000 Add EvasionOrdering screen chunk 001.
grok47/r3-11-dead-material 83f38f489 2026-11-14 15:41:37 +0000 Add KBNK mate tests for both sides at 200000 nodes.
grok47/r3-12-soft-nodes eaa3fca7f 2026-11-14 15:30:11 +0000 Record the fixed-seed self-play positions for the label run
grok47/r3-13-quiet-extinction 20d889a12 2026-11-14 15:49:12 +0000 Add the QuietExtinction on-versus-off UHO screen harness.
grok47/r3-14-draw-jitter ccbb229af 2026-11-14 15:29:14 +0000 Clear the hash when DrawJitter changes.
grok47/r3-15-tm-finish-iteration 962119265 2026-11-14 15:30:42 +0000 Record the clock-screen command, versions, and sha256s.
grok47/r3-16-tm-node-share 08d4b7ea4 2026-11-14 15:34:02 +0000 Add the 10+0.1 clock screen driver.
grok47/r3-17-merge-legal-node-limit 02674044d 2026-11-14 15:28:41 +0000 Record the owner-build node budget follow-up.
grok47/r3-18-lazy-net-accumulator 820784220 2026-11-14 15:36:04 +0000 Record the AVX-512 fused-pass identity checks.
grok47/r3-19-faster-hce 528ccdf1c 2026-11-14 15:33:17 +0000 Record the shared-slider follow-up measurements.
grok47/r3-20-faster-search-plumbing decec3775 2026-11-14 15:37:05 +0000 Add the depth-8 and perft comparison tests.
grok47/r3-21-mate-score-tt caa1c4bad 2026-11-14 15:52:08 +0000 Record finished chunk 1 of the no-regression match.
grok47/r3-22-time-safety b8d47952f 2026-11-14 15:38:05 +0000 Add the short-clock match against the base engine
grok47/r3-23-sound-mate-pruning 3d903f6ae 2026-11-14 15:44:11 +0000 Prove the mate against every defence and test each prune arm
grok47/r3-24-tt-duplicate-shadow d546561dd 2026-11-14 15:52:19 +0000 Add UHO chunk 1: 1000 games, r3-24 253-253-494.
grok47/r4-03-screen-lds 626479273 2026-11-14 15:45:37 +0000 r4-03: drop generated bytecode from the screen snapshot
grok47/r4-04-screen-ch4 67c2a7ea6 2026-11-14 15:41:10 +0000 r4-04: record ContHist4PlyRead screen setup
grok47/r4-05-screen-npc b68b815c1 2026-11-14 15:43:00 +0000 r4-05: start NonPawnCorrection screen

Last check: 2026-11-14T16:02:57Z
Deadline: 2026-11-15T01:52:32Z
