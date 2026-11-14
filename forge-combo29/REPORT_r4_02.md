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

grok47/r3-01-eval-rule-50-damp c0aaf80df402 200 identical
grok47/r3-02-threat-history f29db79a4e87 200 identical; e7f5bc837eb7 200 identical
grok47/r3-03-lmr-signed-correction 1ecc1d33156d 200 identical
grok47/r3-04-lmr-late-parent-relief ae2cc041e24b 200 identical; feccf387e16a 200 identical
grok47/r3-05-hindsight-depth 4ce2b8b18fd9 200 identical
grok47/r3-08-asp-capped-reopen dc2e25b54d7c 20 identical
grok47/r3-21-mate-score-tt af1c998304db 200 identical
grok47/r3-24-tt-duplicate-shadow 0ca8cb1009df 200 identical

## Commands and hashes

grok47/r3-01-eval-rule-50-damp c0aaf80df402 kind nodes pgn forge-combo29/tests_r3fu_01/chunk_1.pgn
build flags: -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DFORGE_MARCH=x86-64-v4 -DFORGE_PORTABLE=OFF
engine source sha256: c0aaf80df402:c01288122f80fc10ab3efd8439e62c5a27057d7531b48b00ae57f6f967c3338b c0aaf80df402:c01288122f80fc10ab3efd8439e62c5a27057d7531b48b00ae57f6f967c3338b
engine binary sha256: c0aaf80df402:778ba5bd02273550e7fc600768ec0f8913354b9039a3f310b59b0179eb19e9e6 c0aaf80df402:778ba5bd02273550e7fc600768ec0f8913354b9039a3f310b59b0179eb19e9e6
fastchess command: /home/ubuntu/r4-verify/fastchess-src/fastchess -engine cmd=/home/ubuntu/r4-verify/build/c0aaf80df40213f867038d2280abbc954d8b9e98-37997d042e39/forge name=EvalRule50DampOn restart=on option.EvalRule50Damp=true option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 -engine cmd=/home/ubuntu/r4-verify/build/c0aaf80df40213f867038d2280abbc954d8b9e98-37997d042e39/forge name=EvalRule50DampOff restart=on option.EvalRule50Damp=false option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 -rounds 100 -games 2 -concurrency 3 -openings file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-01-eval-rule-50-damp/f3217e57bbc8/openings.epd format=epd order=sequential -pgnout file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-01-eval-rule-50-damp/f3217e57bbc8/replay.pgn append=false nodes=true notation=san -ratinginterval 0 -scoreinterval 0

grok47/r3-02-threat-history f29db79a4e87 kind nodes pgn forge-combo29/tests_r3fu_02/chunk001.pgn
build flags: -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DFORGE_MARCH=x86-64-v3 -DFORGE_PORTABLE=ON
engine source sha256: f29db79a4e87:b57150d279362aa6eb622a205ae08a30a951590ee36a34f08fc98548ca23b5b9 f29db79a4e87:b57150d279362aa6eb622a205ae08a30a951590ee36a34f08fc98548ca23b5b9
engine binary sha256: f29db79a4e87:af091e30e0cbe0de2ab0dfdbe0bfde609bec3f3bab7c5d6d76a4def478837361 f29db79a4e87:af091e30e0cbe0de2ab0dfdbe0bfde609bec3f3bab7c5d6d76a4def478837361
fastchess command: /home/ubuntu/r4-verify/fastchess-src/fastchess -engine cmd=/home/ubuntu/r4-verify/build/f29db79a4e873309bad06bbc2606c7876ca995a8-87d04443a779/forge name=ThreatHistoryOn restart=on option.Threads=1 option.Hash=16 option.OwnBook=false option.ThreatHistory=true nodes=50000 -engine cmd=/home/ubuntu/r4-verify/build/f29db79a4e873309bad06bbc2606c7876ca995a8-87d04443a779/forge name=ThreatHistoryOff restart=on option.Threads=1 option.Hash=16 option.OwnBook=false option.ThreatHistory=false nodes=50000 -rounds 100 -games 2 -concurrency 2 -openings file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-02-threat-history/31a83bc0803b/openings.epd format=epd order=sequential -pgnout file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-02-threat-history/31a83bc0803b/replay.pgn append=false nodes=true notation=san -ratinginterval 0 -scoreinterval 0

grok47/r3-02-threat-history e7f5bc837eb7 kind nodes pgn forge-combo29/tests_r3fu_02/chunk001.pgn
build flags: -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=ON -DFORGE_MARCH=x86-64-v3 -DCMAKE_CXX_COMPILER=g++
engine source sha256: e7f5bc837eb7:b57150d279362aa6eb622a205ae08a30a951590ee36a34f08fc98548ca23b5b9 e7f5bc837eb7:b57150d279362aa6eb622a205ae08a30a951590ee36a34f08fc98548ca23b5b9
engine binary sha256: e7f5bc837eb7:af091e30e0cbe0de2ab0dfdbe0bfde609bec3f3bab7c5d6d76a4def478837361 e7f5bc837eb7:af091e30e0cbe0de2ab0dfdbe0bfde609bec3f3bab7c5d6d76a4def478837361
fastchess command: /home/ubuntu/r4-verify/fastchess-src/fastchess -engine cmd=/home/ubuntu/r4-verify/build/e7f5bc837eb7461c21779dc182eda5b9cfc4b1c7-87d04443a779/forge name=ThreatHistoryOn restart=on option.Threads=1 option.Hash=16 option.OwnBook=false option.ThreatHistory=true nodes=50000 -engine cmd=/home/ubuntu/r4-verify/build/e7f5bc837eb7461c21779dc182eda5b9cfc4b1c7-87d04443a779/forge name=ThreatHistoryOff restart=on option.Threads=1 option.Hash=16 option.OwnBook=false option.ThreatHistory=false nodes=50000 -rounds 100 -games 2 -concurrency 2 -openings file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-02-threat-history/6be54c788bac/openings.epd format=epd order=sequential -pgnout file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-02-threat-history/6be54c788bac/replay.pgn append=false nodes=true notation=san -ratinginterval 0 -scoreinterval 0

grok47/r3-03-lmr-signed-correction 1ecc1d33156d kind nodes pgn forge-combo29/screen_r3fu_03/chunk-01.pgn
build flags: -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DFORGE_MARCH=x86-64-v4 -DFORGE_PORTABLE=OFF
engine source sha256: 1ecc1d33156d:47cb047708db6294e74b1cbe280ceff6a7ec194f64425aa6d232dad72d656221 1ecc1d33156d:47cb047708db6294e74b1cbe280ceff6a7ec194f64425aa6d232dad72d656221
engine binary sha256: 1ecc1d33156d:c91a68b5e05822f312df0547d162e551d30c98250201e77452938ece4e41c31a 1ecc1d33156d:c91a68b5e05822f312df0547d162e551d30c98250201e77452938ece4e41c31a
fastchess command: /home/ubuntu/r4-verify/fastchess-src/fastchess -engine cmd=/home/ubuntu/r4-verify/build/1ecc1d33156d1833701b98586f9c17bd4f67da91-37997d042e39/forge name=LmrSignedCorrectionOn restart=on option.LmrSignedCorrection=true option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 -engine cmd=/home/ubuntu/r4-verify/build/1ecc1d33156d1833701b98586f9c17bd4f67da91-37997d042e39/forge name=LmrSignedCorrectionOff restart=on option.LmrSignedCorrection=false option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 -rounds 100 -games 2 -concurrency 4 -openings file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-03-lmr-signed-correction/60ab30b56428/openings.epd format=epd order=sequential -pgnout file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-03-lmr-signed-correction/60ab30b56428/replay.pgn append=false nodes=true notation=san -ratinginterval 0 -scoreinterval 0

grok47/r3-04-lmr-late-parent-relief ae2cc041e24b kind nodes pgn forge-combo29/tests_r3fu_04/chunk-0001.pgn
build flags: -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DFORGE_MARCH=x86-64-v4 -DFORGE_PORTABLE=OFF
engine source sha256: f3ecae11d4cd:223845227cb2248c6b4c9843b416bfcdee8a0d9fb891303b27180cdd83cd5a1d ae2cc041e24b:223845227cb2248c6b4c9843b416bfcdee8a0d9fb891303b27180cdd83cd5a1d
engine binary sha256: f3ecae11d4cd:8919bd97dd07407c40e2d3f14793b691da7b672f4878d366af4e374363e2f7ac ae2cc041e24b:8919bd97dd07407c40e2d3f14793b691da7b672f4878d366af4e374363e2f7ac
fastchess command: /home/ubuntu/r4-verify/fastchess-src/fastchess -engine cmd=/home/ubuntu/r4-verify/build/f3ecae11d4cdf9fb58925853e25a340f921b53ba-37997d042e39/forge name=LmrLateParentReliefOn restart=on option.LmrLateParentRelief=true option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 -engine cmd=/home/ubuntu/r4-verify/build/ae2cc041e24b5805d04fd4a0d95fcf88f20fdb84-37997d042e39/forge name=LmrLateParentReliefOff restart=on option.LmrLateParentRelief=false option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 -rounds 100 -games 2 -concurrency 2 -openings file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-04-lmr-late-parent-relief/02d819ff1e60/openings.epd format=epd order=sequential -pgnout file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-04-lmr-late-parent-relief/02d819ff1e60/replay.pgn append=false nodes=true notation=san -ratinginterval 0 -scoreinterval 0

grok47/r3-04-lmr-late-parent-relief feccf387e16a kind nodes pgn forge-combo29/tests_r3fu_04/chunk-0001.pgn
build flags: -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DFORGE_MARCH=x86-64-v4 -DFORGE_PORTABLE=OFF
engine source sha256: f3ecae11d4cd:223845227cb2248c6b4c9843b416bfcdee8a0d9fb891303b27180cdd83cd5a1d f3ecae11d4cd:223845227cb2248c6b4c9843b416bfcdee8a0d9fb891303b27180cdd83cd5a1d
engine binary sha256: f3ecae11d4cd:8919bd97dd07407c40e2d3f14793b691da7b672f4878d366af4e374363e2f7ac f3ecae11d4cd:8919bd97dd07407c40e2d3f14793b691da7b672f4878d366af4e374363e2f7ac
fastchess command: /home/ubuntu/r4-verify/fastchess-src/fastchess -engine cmd=/home/ubuntu/r4-verify/build/f3ecae11d4cdf9fb58925853e25a340f921b53ba-37997d042e39/forge name=LmrLateParentReliefOn restart=on option.LmrLateParentRelief=true option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 -engine cmd=/home/ubuntu/r4-verify/build/f3ecae11d4cdf9fb58925853e25a340f921b53ba-37997d042e39/forge name=LmrLateParentReliefOff restart=on option.LmrLateParentRelief=false option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 -rounds 100 -games 2 -concurrency 2 -openings file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-04-lmr-late-parent-relief/dfcdfb2fd396/openings.epd format=epd order=sequential -pgnout file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-04-lmr-late-parent-relief/dfcdfb2fd396/replay.pgn append=false nodes=true notation=san -ratinginterval 0 -scoreinterval 0

grok47/r3-05-hindsight-depth 4ce2b8b18fd9 kind nodes pgn forge-combo29/tests_r3fu_05/chunk-001.pgn
build flags: -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++ -DFORGE_MARCH=x86-64-v4 -DFORGE_PORTABLE=OFF
engine source sha256: 4ce2b8b18fd9:ddef1ee036558f512c1bcd23720a33977d72db5f726b23679b23a35776262136 4ce2b8b18fd9:ddef1ee036558f512c1bcd23720a33977d72db5f726b23679b23a35776262136
engine binary sha256: 4ce2b8b18fd9:453e4757662bf45230623455f63da64657e6a7cee0120f49fe0ee0eb3e8d8a02 4ce2b8b18fd9:453e4757662bf45230623455f63da64657e6a7cee0120f49fe0ee0eb3e8d8a02
fastchess command: /home/ubuntu/r4-verify/fastchess-src/fastchess -engine cmd=/home/ubuntu/r4-verify/build/4ce2b8b18fd9490fb07cd7f6be2fb6d81f8c9a6e-37997d042e39/forge name=HindsightOn restart=on option.HindsightDepth=true option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 -engine cmd=/home/ubuntu/r4-verify/build/4ce2b8b18fd9490fb07cd7f6be2fb6d81f8c9a6e-37997d042e39/forge name=HindsightOff restart=on option.HindsightDepth=false option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 -rounds 100 -games 2 -concurrency 4 -draw movenumber=40 movecount=8 score=10 -resign movecount=4 score=800 -maxmoves 200 -openings file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-05-hindsight-depth/ce71a2d4c861/openings.epd format=epd order=sequential -pgnout file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-05-hindsight-depth/ce71a2d4c861/replay.pgn append=false nodes=true notation=san -ratinginterval 0 -scoreinterval 0

grok47/r3-08-asp-capped-reopen dc2e25b54d7c kind nodes pgn forge-combo29/tests_r3fu_08/chunk-001.pgn
build flags: -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=clang++ -DFORGE_MARCH=x86-64-v4 -DFORGE_PORTABLE=OFF
engine source sha256: dc2e25b54d7c:e3397b5a3b2a673ce6b30163d531bd851813a43279027ea30f502e376f455327 dc2e25b54d7c:e3397b5a3b2a673ce6b30163d531bd851813a43279027ea30f502e376f455327
engine binary sha256: dc2e25b54d7c:1e647eead4e6ee779673c3463d897c06d9727ea66cc918a7a1f9762641abd480 dc2e25b54d7c:1e647eead4e6ee779673c3463d897c06d9727ea66cc918a7a1f9762641abd480
fastchess command: /home/ubuntu/r4-verify/fastchess-src/fastchess -engine cmd=/home/ubuntu/r4-verify/build/dc2e25b54d7ce176090fd439d1b4df2d5fbcefc4-7e389295b5ee/forge name=on restart=on option.Threads=1 option.Hash=16 option.OwnBook=false option.AspCappedReopen=true nodes=50000 -engine cmd=/home/ubuntu/r4-verify/build/dc2e25b54d7ce176090fd439d1b4df2d5fbcefc4-7e389295b5ee/forge name=off restart=on option.Threads=1 option.Hash=16 option.OwnBook=false option.AspCappedReopen=false nodes=50000 -rounds 10 -games 2 -concurrency 2 -openings file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-08-asp-capped-reopen/d4da1cf2a088/openings.epd format=epd order=sequential -pgnout file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-08-asp-capped-reopen/d4da1cf2a088/replay.pgn append=false nodes=true notation=san -ratinginterval 0 -scoreinterval 0

grok47/r3-21-mate-score-tt af1c998304db kind nodes pgn forge-combo29/tests_r3fu_21/chunk1.pgn
build flags: -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=OFF -DFORGE_MARCH=x86-64-v4 -DCMAKE_CXX_COMPILER=g++
engine source sha256: af1c998304db:2cb78b8c476020dda94a09873fc523bd61352cb7b89c5a6b50e698c2dec33f60 e04556ddc3a4:b0949c1ea74050643e14972b9d27b8d62aa568466e0e28e78587efa2c0060e16
engine binary sha256: af1c998304db:e12981d3667fc4319920388621a591763a2ebc58c5da1c7552ed5f8f211bb197 e04556ddc3a4:4a624cf990c057c9a5d7847916b2d537a38ab6b95be4339dbec30a187f7ec984
fastchess command: /home/ubuntu/r4-verify/fastchess-src/fastchess -engine cmd=/home/ubuntu/r4-verify/build/af1c998304dbfbcb997b757a7ce43af7cdf6e933-37997d042e39/forge name=r3-21 restart=on option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 -engine cmd=/home/ubuntu/r4-verify/build/e04556ddc3a430b2e751159b0d46111ef56c8b89-37997d042e39/forge name=base restart=on option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 -rounds 100 -games 2 -concurrency 4 -openings file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-21-mate-score-tt/nr100/openings.epd format=epd order=sequential -pgnout file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-21-mate-score-tt/nr100/replay.pgn append=false nodes=true notation=san -ratinginterval 0 -scoreinterval 0

grok47/r3-24-tt-duplicate-shadow 0ca8cb1009df kind nodes pgn forge-combo29/tests_r3fu_24/chunk1.pgn
build flags: -DCMAKE_BUILD_TYPE=Release -DFORGE_PORTABLE=OFF -DFORGE_MARCH=x86-64-v4 -DCMAKE_CXX_COMPILER=g++
engine source sha256: 0ca8cb1009df:7028cd9889652ee6fb17adc9c5843b47632756e12f39c3a78eb84c4cc36dedb7 e04556ddc3a4:b0949c1ea74050643e14972b9d27b8d62aa568466e0e28e78587efa2c0060e16
engine binary sha256: 0ca8cb1009df:16f789f896392b646cac0ac54c311ed552d55e2624a616f7352caa0c468571f1 e04556ddc3a4:4a624cf990c057c9a5d7847916b2d537a38ab6b95be4339dbec30a187f7ec984
fastchess command: /home/ubuntu/r4-verify/fastchess-src/fastchess -engine cmd=/home/ubuntu/r4-verify/build/0ca8cb1009dfd1c8e58dc793c3e760d1c88628f3-37997d042e39/forge name=r3-24 restart=on option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 -engine cmd=/home/ubuntu/r4-verify/build/e04556ddc3a430b2e751159b0d46111ef56c8b89-37997d042e39/forge name=base-e04556dd restart=on option.Threads=1 option.Hash=16 option.OwnBook=false nodes=50000 -rounds 100 -games 2 -concurrency 4 -openings file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-24-tt-duplicate-shadow/nr100/openings.epd format=epd order=sequential -pgnout file=/agent/repos/dwqww/forge-combo29/tests_r4_02/r3-24-tt-duplicate-shadow/nr100/replay.pgn append=false nodes=true notation=san -ratinginterval 0 -scoreinterval 0

## Still open

grok47/r3-06-null-threat-verify e0c1252e4 2026-11-14 17:12:31 +0000 Update in-progress UHO chunk 1.
grok47/r3-07-null-see-veto 06b49fd5a 2026-11-14 17:05:12 +0000 Add the fourth NullSeeVeto screen chunk.
grok47/r3-09-asp-arm-late 97b51960d 2026-11-14 17:17:17 +0000 Add UHO screen chunk 005 for AspArmLate.
grok47/r3-10-evasion-ordering 70aa54740 2026-11-14 17:04:52 +0000 Add EvasionOrdering screen chunk 007.
grok47/r3-11-dead-material b27a351b7 2026-11-14 17:23:14 +0000 Add UHO screen chunk 004.
grok47/r3-12-soft-nodes 6d8717d28 2026-11-14 15:53:19 +0000 Record the 10000-position nodes and softnodes label totals
grok47/r3-13-quiet-extinction a17b76e14 2026-11-14 17:15:53 +0000 Record UHO screen chunks 7 and 8.
grok47/r3-14-draw-jitter c37741517 2026-11-14 17:16:30 +0000 Finish UHO chunk 3 for DrawJitter 8 against 0.
grok47/r3-15-tm-finish-iteration 24fc1d9c0 2026-11-14 16:40:37 +0000 Push the latest clock-screen PGN and progress.
grok47/r3-16-tm-node-share 4bb15fdbe 2026-11-14 17:07:06 +0000 Checkpoint clock screen chunk 1 in progress.
grok47/r3-17-merge-legal-node-limit 02674044d 2026-11-14 15:28:41 +0000 Record the owner-build node budget follow-up.
grok47/r3-18-lazy-net-accumulator 820784220 2026-11-14 15:36:04 +0000 Record the AVX-512 fused-pass identity checks.
grok47/r3-19-faster-hce 528ccdf1c 2026-11-14 15:33:17 +0000 Record the shared-slider follow-up measurements.
grok47/r3-20-faster-search-plumbing decec3775 2026-11-14 15:37:05 +0000 Add the depth-8 and perft comparison tests.
grok47/r3-22-time-safety 143f3c5c6 2026-11-14 16:47:41 +0000 Record the empty-clock follow-up and the 1+0.01 match
grok47/r3-23-sound-mate-pruning 1c76659e0 2026-11-14 17:15:02 +0000 Add UHO slice 4, openings 1200-1599
grok47/r4-03-screen-lds ca20d7f52 2026-11-14 17:15:41 +0000 r4-03: chunk 501 PGN and screen summary
grok47/r4-04-screen-ch4 51fb0b120 2026-11-14 17:11:45 +0000 r4-04: ContHist4PlyRead screen chunk001
grok47/r4-05-screen-npc 697f52ee8 2026-11-14 17:20:41 +0000 r4-05: NonPawnCorrection screen chunk 003 (1001-1500)

Last check: 2026-11-14T17:34:14Z
Deadline: 2026-11-15T01:52:00Z
