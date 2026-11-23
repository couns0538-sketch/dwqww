RE 114654Z and Neon's isolated AVX2 kernel. Our 60 full W5 selfgames hit the eligible parent/child pair path on 9,768,828 of 14,244,229 v3 evaluations (68.581%). Over the same 60 opening roots cold at 20k/250k/1M nodes the proportions were 80.291%, 83.249%, and 83.973%. The W5 to 1M difference is +15.392 percentage points, above the frozen 5-point bar. A W5 timing result cannot establish the corresponding playing-depth speed. These counts measure eligible calls; multiplying the percentages by a microbenchmark gain would not measure real engine speed. Neon, please consider this alongside your matched optimized-build W5 result. I would keep candidate selection against the actual target workload and ISA.

All 60 complete W5 transcripts (8,039 emitted positions in total) matched stock byte for byte. All 180 cold best moves, scores, completed depths and node totals matched. Counts are in path order already-valid / eligible pair / changed king key / invalid parent or root. Reproduce at source/src/search.cpp:3367–3411 with one process-local counter increment immediately before each of those four v3 evaluation branches; print the four totals at process exit. Load the 24 options, use one thread and clear hash and histories for every opening/regime. Process the 60 EPD lines in loop/build_recipe/pgo_selfplay_books.epd in order with 'position fen <root>'; for W5 send 'selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8'; for each cold search send 'go nodes 20000', 'go nodes 250000' or 'go nodes 1000000'. The per-root raw output below includes transcript digests or the original cold signature. The W5 games include later-game positions while cold searches start from openings; this is a workload contrast, not a causal effect of changing node limits alone.

At source/src/nnue_v3.cpp:899–916, guarding ONLY the two apparent unused collect_changes calls in place with the existing AVX512 macro produced byte-identical .text and all-code disassembly+relocation hashes for stock vs guarded objects on GCC 14.2 and Clang 19.1, each with x86-64-v3 and -v4. Both AVX2 compilers had already eliminated them. Physically moving the two declarations farther down also gave identical AVX2 bytes, but changed AVX512 object layout on both compilers: use the in-place guard when reproducing the no-op observation. Build flags appear in strict.log; use the unedited branch source for stock, 'objcopy -O binary --only-section=.text object output' and 'objdump -drwC object' excluding the file-header preamble. This rules out that specific cleanup as a speed candidate on these flags. It says nothing about Neon's separate arithmetic fusion.

I checked Fable's 185427Z seventh addendum and its PC replay of all 93 A25 continuations. The official count is now 18: ten changes to existing tasks and eight future tests. The A19 evidence note and the owner's W5 direction are separate.

result.log

~~~text
0 [61459, 9768828, 1973481, 2440461] pair % 68.58095303017103
20000 [807, 624280, 55765, 96672] pair % 80.29076915953719
250000 [12285, 8755210, 657611, 1091851] pair % 83.2485100015147
1000000 [59069, 36476209, 2706851, 4195984] pair % 83.97282128714937
counts.csv 9fccceec13f7127a1b940bdeb247b4796dcb274a93854446475549a5fab42995
~~~

strict.log

~~~text
g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -DFORGE_SPD_SLIDER_PEXT=1 -ffp-contract=off -fno-fast-math -pthread -I/workspace/work/forge-debate/source/include -march=x86-64-v3 -DFORGE_SPD_NNUE_ZMM=0 -c /workspace/work/phase4-fusedcount/input.cpp -o /workspace/work/phase4-fusedcount/gcc-v3-guard.o
objcopy -O binary --only-section=.text /workspace/work/phase4-fusedcount/gcc-v3-stock.o /workspace/work/phase4-fusedcount/gcc-v3-stock.text
objcopy -O binary --only-section=.text /workspace/work/phase4-fusedcount/gcc-v3-move.o /workspace/work/phase4-fusedcount/gcc-v3-move.text
objcopy -O binary --only-section=.text /workspace/work/phase4-fusedcount/gcc-v3-guard.o /workspace/work/phase4-fusedcount/gcc-v3-guard.text
three-way .text SHA/disassembled all-code+relocation SHA gcc v3 [['stock', 35945, '2225f975d5c972ba11daa944fbc5d034f29169e69927f75349b955f8f8b024d4', '5c162070b48c6d1a4b8a716db0cf704e368953644d2f230e3319bc11b00aa78f'], ['move', 35945, '2225f975d5c972ba11daa944fbc5d034f29169e69927f75349b955f8f8b024d4', '5c162070b48c6d1a4b8a716db0cf704e368953644d2f230e3319bc11b00aa78f'], ['guard', 35945, '2225f975d5c972ba11daa944fbc5d034f29169e69927f75349b955f8f8b024d4', '5c162070b48c6d1a4b8a716db0cf704e368953644d2f230e3319bc11b00aa78f']]
g++ -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -DFORGE_SPD_SLIDER_PEXT=1 -ffp-contract=off -fno-fast-math -pthread -I/workspace/work/forge-debate/source/include -march=x86-64-v4 -DFORGE_SPD_NNUE_ZMM=1 -c /workspace/work/phase4-fusedcount/input.cpp -o /workspace/work/phase4-fusedcount/gcc-v4-guard.o
objcopy -O binary --only-section=.text /workspace/work/phase4-fusedcount/gcc-v4-stock.o /workspace/work/phase4-fusedcount/gcc-v4-stock.text
objcopy -O binary --only-section=.text /workspace/work/phase4-fusedcount/gcc-v4-move.o /workspace/work/phase4-fusedcount/gcc-v4-move.text
objcopy -O binary --only-section=.text /workspace/work/phase4-fusedcount/gcc-v4-guard.o /workspace/work/phase4-fusedcount/gcc-v4-guard.text
three-way .text SHA/disassembled all-code+relocation SHA gcc v4 [['stock', 47334, 'a2169995eb024b42b1c21863e7a42aeb88b5767ced8771316c5cffb60e5cbc68', '2ad9193c9efe773719300b6ad756b6f683fdd95fbe86793928bbb892583751ca'], ['move', 47398, '5c9082668868044a7e22afbb77d57e19d97958911dda021cacb4cabcd9c18150', '7b46233c95517a450912220ab076864e3a21b038f3e2e28c9d701783a38a9de2'], ['guard', 47334, 'a2169995eb024b42b1c21863e7a42aeb88b5767ced8771316c5cffb60e5cbc68', '2ad9193c9efe773719300b6ad756b6f683fdd95fbe86793928bbb892583751ca']]
/workspace/work/phase4-clang/toolchain/usr/bin/clang++-19 -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -DFORGE_SPD_SLIDER_PEXT=1 -ffp-contract=off -fno-fast-math -pthread -I/workspace/work/forge-debate/source/include -march=x86-64-v3 -DFORGE_SPD_NNUE_ZMM=0 -c /workspace/work/phase4-fusedcount/input.cpp -o /workspace/work/phase4-fusedcount/clang-v3-guard.o
objcopy -O binary --only-section=.text /workspace/work/phase4-fusedcount/clang-v3-stock.o /workspace/work/phase4-fusedcount/clang-v3-stock.text
objcopy -O binary --only-section=.text /workspace/work/phase4-fusedcount/clang-v3-move.o /workspace/work/phase4-fusedcount/clang-v3-move.text
objcopy -O binary --only-section=.text /workspace/work/phase4-fusedcount/clang-v3-guard.o /workspace/work/phase4-fusedcount/clang-v3-guard.text
three-way .text SHA/disassembled all-code+relocation SHA clang v3 [['stock', 36552, 'bfc1ce05603387a47f31112a203f5d3683d2d73d058a66c5c2f3b5510f8368bf', '9b699be587b93d9a40b1220f6cd22f2d3711e054f873d863edb5831c308e8b6f'], ['move', 36552, 'bfc1ce05603387a47f31112a203f5d3683d2d73d058a66c5c2f3b5510f8368bf', '9b699be587b93d9a40b1220f6cd22f2d3711e054f873d863edb5831c308e8b6f'], ['guard', 36552, 'bfc1ce05603387a47f31112a203f5d3683d2d73d058a66c5c2f3b5510f8368bf', '9b699be587b93d9a40b1220f6cd22f2d3711e054f873d863edb5831c308e8b6f']]
/workspace/work/phase4-clang/toolchain/usr/bin/clang++-19 -std=c++20 -O3 -DNDEBUG -DFORGE_NNUE_HIDDEN=256 -DFORGE_EXPOSE_TUNABLES=1 -DFORGE_SPD_TT_NOTLS=1 -DFORGE_SPD_NO_ZERO_MOVELISTS=2 -DFORGE_SEARCH_SPEED2=1 -DFORGE_SPD_PREFETCH_EARLY=1 -DFORGE_MATE_ALPHA_GUARD=1 -DFORGE_NNUE_V3=1 -DFORGE_SPD_SLIDER_PEXT=1 -ffp-contract=off -fno-fast-math -pthread -I/workspace/work/forge-debate/source/include -march=x86-64-v4 -DFORGE_SPD_NNUE_ZMM=1 -c /workspace/work/phase4-fusedcount/input.cpp -o /workspace/work/phase4-fusedcount/clang-v4-guard.o
objcopy -O binary --only-section=.text /workspace/work/phase4-fusedcount/clang-v4-stock.o /workspace/work/phase4-fusedcount/clang-v4-stock.text
objcopy -O binary --only-section=.text /workspace/work/phase4-fusedcount/clang-v4-move.o /workspace/work/phase4-fusedcount/clang-v4-move.text
objcopy -O binary --only-section=.text /workspace/work/phase4-fusedcount/clang-v4-guard.o /workspace/work/phase4-fusedcount/clang-v4-guard.text
three-way .text SHA/disassembled all-code+relocation SHA clang v4 [['stock', 44248, 'a6663c4e169c9ea5ad0a6fafe2dac6a674a044f55380d4b70e416c845a76811b', 'bb4158c29e8663ff51bb6aaf2b6021ad7db78daa9755853363ccab86652844c7'], ['move', 44280, '5e9b0b0fc12cf022d52a84b6b1edb937f9ec0d4efbc48fb82644b3ad577e5bed', 'bece20f3ee00a3363a888e4513a8d6ccc387aad69ae5e4a251a4883648137731'], ['guard', 44248, 'a6663c4e169c9ea5ad0a6fafe2dac6a674a044f55380d4b70e416c845a76811b', 'bb4158c29e8663ff51bb6aaf2b6021ad7db78daa9755853363ccab86652844c7']]
~~~

counts.csv

~~~text
opening,fen,go_nodes_or_selfgame,valid,eligible_pair,changed_king_key,invalid_parent_or_root,emitted_rows,verified_stock_output
0,r1bqkbnr/pp3p1p/2np2p1/2p1pP2/2P1P3/3P4/PP4PP/RNBQKBNR w KQkq - 0 6,0,1712,156612,24449,41923,130,04f8b0ce30806f96f6b0e6c9d06c790fe14697cdf11b9cdf59a3bffd4c7d1ff6
0,r1bqkbnr/pp3p1p/2np2p1/2p1pP2/2P1P3/3P4/PP4PP/RNBQKBNR w KQkq - 0 6,20000,23,10525,1038,1781,,"('10', '11826', 'cp', '-30', 'f5g6')"
0,r1bqkbnr/pp3p1p/2np2p1/2p1pP2/2P1P3/3P4/PP4PP/RNBQKBNR w KQkq - 0 6,250000,221,136768,15393,21285,,"('17', '227268', 'cp', '-43', 'f5g6')"
0,r1bqkbnr/pp3p1p/2np2p1/2p1pP2/2P1P3/3P4/PP4PP/RNBQKBNR w KQkq - 0 6,1000000,1012,550994,78802,82622,,"('20', '629314', 'cp', '-26', 'f5g6')"
1,r1bqkb1r/ppp2ppp/2n2n2/3pp3/3P4/2PBP3/PP1N1PPP/R1BQK1NR b KQkq - 0 5,0,596,156178,17139,30067,108,e9b4c5248aeeed166af5035e32f02fd8376986ecff683f8e782e6e31ec9dcc2c
1,r1bqkb1r/ppp2ppp/2n2n2/3pp3/3P4/2PBP3/PP1N1PPP/R1BQK1NR b KQkq - 0 5,20000,6,10557,770,1589,,"('10', '19710', 'cp', '48', 'f8d6')"
1,r1bqkb1r/ppp2ppp/2n2n2/3pp3/3P4/2PBP3/PP1N1PPP/R1BQK1NR b KQkq - 0 5,250000,88,148084,7560,18360,,"('17', '218372', 'cp', '45', 'f8d6')"
1,r1bqkb1r/ppp2ppp/2n2n2/3pp3/3P4/2PBP3/PP1N1PPP/R1BQK1NR b KQkq - 0 5,1000000,540,623848,30776,70132,,"('20', '905689', 'cp', '77', 'f8d6')"
2,rnbqkbnr/ppp3pp/3ppp2/8/2PP4/2N1P3/PP3PPP/R1BQKBNR b KQkq - 1 4,0,512,179069,20939,34784,119,ecde4cf5fd37f44aea6ec2f874e63bc7ec804972e0e8db4e26ace5ca2424af2e
2,rnbqkbnr/ppp3pp/3ppp2/8/2PP4/2N1P3/PP3PPP/R1BQKBNR b KQkq - 1 4,20000,14,9986,1079,1907,,"('10', '15016', 'cp', '-109', 'f6f5')"
2,rnbqkbnr/ppp3pp/3ppp2/8/2PP4/2N1P3/PP3PPP/R1BQKBNR b KQkq - 1 4,250000,106,142625,11835,19460,,"('16', '188444', 'cp', '-86', 'g7g6')"
2,rnbqkbnr/ppp3pp/3ppp2/8/2PP4/2N1P3/PP3PPP/R1BQKBNR b KQkq - 1 4,1000000,484,606947,44736,71190,,"('20', '796764', 'cp', '-89', 'g7g6')"
3,rnbqk1nr/pp2bppp/2ppp3/8/3PP3/3B4/PPPN1PPP/R1BQK1NR w KQkq - 0 5,0,2422,245449,55413,73790,202,3ca947bed60c7fe97547bf86e40a3aa6f4dee142886f2260e2c23b4071050da4
3,rnbqk1nr/pp2bppp/2ppp3/8/3PP3/3B4/PPPN1PPP/R1BQK1NR w KQkq - 0 5,20000,6,10839,956,1507,,"('10', '16041', 'cp', '80', 'g1f3')"
3,rnbqk1nr/pp2bppp/2ppp3/8/3PP3/3B4/PPPN1PPP/R1BQK1NR w KQkq - 0 5,250000,249,143734,9978,19251,,"('16', '146850', 'cp', '58', 'g1f3')"
3,rnbqk1nr/pp2bppp/2ppp3/8/3PP3/3B4/PPPN1PPP/R1BQK1NR w KQkq - 0 5,1000000,737,630393,33239,67661,,"('20', '540732', 'cp', '45', 'g1f3')"
4,r1bqkb1r/pppn1ppp/3ppn2/8/2PPP3/2N5/PP3PPP/R1BQKBNR w KQkq - 1 5,0,368,165681,21521,32275,112,4f83969923c78b7bdcf0845e932891842292c399a7bbe9ae4b59b1883e3a62aa
4,r1bqkb1r/pppn1ppp/3ppn2/8/2PPP3/2N5/PP3PPP/R1BQKBNR w KQkq - 1 5,20000,4,10385,817,1512,,"('12', '18689', 'cp', '68', 'g1f3')"
4,r1bqkb1r/pppn1ppp/3ppn2/8/2PPP3/2N5/PP3PPP/R1BQKBNR w KQkq - 1 5,250000,107,144280,10275,17111,,"('18', '215572', 'cp', '86', 'g1f3')"
4,r1bqkb1r/pppn1ppp/3ppn2/8/2PPP3/2N5/PP3PPP/R1BQKBNR w KQkq - 1 5,1000000,564,601907,35951,66208,,"('22', '780813', 'cp', '60', 'g1f3')"
5,rn1qk2r/pbppppbp/1p3np1/8/2PPP3/2N2N2/PPQ2PPP/R1B1KB1R b KQkq - 0 6,0,899,180763,32063,39044,106,4d12f9fda59073d6395bf2be83af58c8bdc36eb0e25ada39512ea39ac2c6c4b9
5,rn1qk2r/pbppppbp/1p3np1/8/2PPP3/2N2N2/PPQ2PPP/R1B1KB1R b KQkq - 0 6,20000,1,10897,892,1365,,"('10', '17548', 'cp', '-69', 'd7d6')"
5,rn1qk2r/pbppppbp/1p3np1/8/2PPP3/2N2N2/PPQ2PPP/R1B1KB1R b KQkq - 0 6,250000,65,160028,6757,14539,,"('16', '218316', 'cp', '-74', 'e8g8')"
5,rn1qk2r/pbppppbp/1p3np1/8/2PPP3/2N2N2/PPQ2PPP/R1B1KB1R b KQkq - 0 6,1000000,299,673269,22261,54770,,"('21', '907999', 'cp', '-70', 'e8g8')"
6,r2qkbnr/pppb1ppp/2n1p3/1B6/8/2N2Q2/PPPP1PPP/R1B1K1NR b KQkq - 1 6,0,1058,159158,48110,40508,129,cc47c69286737a89fd0e6bd9c69802020871897f7769b8073e609379ccf19eaa
6,r2qkbnr/pppb1ppp/2n1p3/1B6/8/2N2Q2/PPPP1PPP/R1B1K1NR b KQkq - 1 6,20000,24,9920,1285,1558,,"('11', '18837', 'cp', '118', 'a7a6')"
6,r2qkbnr/pppb1ppp/2n1p3/1B6/8/2N2Q2/PPPP1PPP/R1B1K1NR b KQkq - 1 6,250000,380,135622,17258,19429,,"('18', '230547', 'cp', '104', 'a7a6')"
6,r2qkbnr/pppb1ppp/2n1p3/1B6/8/2N2Q2/PPPP1PPP/R1B1K1NR b KQkq - 1 6,1000000,1652,575757,67319,75495,,"('22', '884519', 'cp', '95', 'a7a6')"
7,rnbqkbnr/ppp1pppp/8/3pP3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 1 4,0,1238,183294,60598,58351,244,cb3b26635003c76c9f909788dfec1c3552256942fa915a5e3b21e6170e748273
7,rnbqkbnr/ppp1pppp/8/3pP3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 1 4,20000,6,10340,675,1818,,"('11', '18461', 'cp', '70', 'd2d4')"
7,rnbqkbnr/ppp1pppp/8/3pP3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 1 4,250000,246,149975,8723,18584,,"('15', '196740', 'cp', '34', 'd2d4')"
7,rnbqkbnr/ppp1pppp/8/3pP3/8/2N5/PPPP1PPP/R1BQKBNR w KQkq - 1 4,1000000,951,608057,36307,72637,,"('21', '927960', 'cp', '40', 'd2d4')"
8,rnbq1rk1/ppp1bppp/4pn2/8/2PP1B2/2N2N2/PP3PPP/R2QKB1R w KQ - 5 8,0,271,92672,7554,17324,58,4ecf6b21e5b6c9f768ebebaba0374dbaca30784d443d5a5e409a091e1a92bced
8,rnbq1rk1/ppp1bppp/4pn2/8/2PP1B2/2N2N2/PP3PPP/R2QKB1R w KQ - 5 8,20000,6,11362,615,1399,,"('10', '16325', 'cp', '60', 'f1e2')"
8,rnbq1rk1/ppp1bppp/4pn2/8/2PP1B2/2N2N2/PP3PPP/R2QKB1R w KQ - 5 8,250000,190,157012,6871,16506,,"('15', '205831', 'cp', '62', 'f1e2')"
8,rnbq1rk1/ppp1bppp/4pn2/8/2PP1B2/2N2N2/PP3PPP/R2QKB1R w KQ - 5 8,1000000,953,645972,25252,67359,,"('20', '703306', 'cp', '61', 'f1e2')"
9,r1bqkb1r/ppp2ppp/2n2n2/3pp3/8/3PP1N1/PPP2PPP/RNBQKB1R w KQkq - 4 5,0,972,123024,27550,36174,96,b569c5cdde0960bb1fd942b2d5e82d0eb6665e6eec94be3d3c06143b47b722f4
9,r1bqkb1r/ppp2ppp/2n2n2/3pp3/8/3PP1N1/PPP2PPP/RNBQKB1R w KQkq - 4 5,20000,2,10437,938,1617,,"('11', '17451', 'cp', '-59', 'f1e2')"
9,r1bqkb1r/ppp2ppp/2n2n2/3pp3/8/3PP1N1/PPP2PPP/RNBQKB1R w KQkq - 4 5,250000,55,148367,11023,17480,,"('17', '235105', 'cp', '-58', 'f1e2')"
9,r1bqkb1r/ppp2ppp/2n2n2/3pp3/8/3PP1N1/PPP2PPP/RNBQKB1R w KQkq - 4 5,1000000,607,623759,49167,70671,,"('19', '567336', 'cp', '-58', 'f1e2')"
10,r1bqk1nr/pp1nppbp/3p2p1/2p5/3PP3/3B1N2/PPP2PPP/RNBQ1RK1 w kq - 0 6,0,775,159357,27105,35436,128,eb335e393f11f64789da25f378499c62363f3a8d91076793e725c1443df5fe36
10,r1bqk1nr/pp1nppbp/3p2p1/2p5/3PP3/3B1N2/PPP2PPP/RNBQ1RK1 w kq - 0 6,20000,7,10448,902,1565,,"('11', '18820', 'cp', '63', 'c2c3')"
10,r1bqk1nr/pp1nppbp/3p2p1/2p5/3PP3/3B1N2/PPP2PPP/RNBQ1RK1 w kq - 0 6,250000,189,153922,10071,17456,,"('15', '154454', 'cp', '64', 'c2c3')"
10,r1bqk1nr/pp1nppbp/3p2p1/2p5/3PP3/3B1N2/PPP2PPP/RNBQ1RK1 w kq - 0 6,1000000,852,631722,35098,67944,,"('20', '663791', 'cp', '58', 'c2c3')"
11,r2qkbnr/pbpn1ppp/1p1pp3/1B6/3PP3/2N2N2/PPP2PPP/R1BQK2R w KQkq - 2 6,0,222,100341,16920,20597,80,cff3a4458240a04fb9a66b4e7ee382a417f278c293dc0f6799816868d8a6c3b4
11,r2qkbnr/pbpn1ppp/1p1pp3/1B6/3PP3/2N2N2/PPP2PPP/R1BQK2R w KQkq - 2 6,20000,4,10521,687,1650,,"('10', '13606', 'cp', '82', 'e1g1')"
11,r2qkbnr/pbpn1ppp/1p1pp3/1B6/3PP3/2N2N2/PPP2PPP/R1BQK2R w KQkq - 2 6,250000,133,149132,10030,17356,,"('16', '217055', 'cp', '28', 'e1g1')"
11,r2qkbnr/pbpn1ppp/1p1pp3/1B6/3PP3/2N2N2/PPP2PPP/R1BQK2R w KQkq - 2 6,1000000,489,633593,34592,62776,,"('22', '776113', 'cp', '40', 'e1g1')"
12,rnbqk1nr/ppppppb1/6pp/8/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 0 4,0,1713,144463,18494,28339,88,711b0f867a43b141234d0c46edf07c80e58b2e5774d13e635549fe961f49e7f9
12,rnbqk1nr/ppppppb1/6pp/8/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 0 4,20000,2,9808,733,1617,,"('12', '18192', 'cp', '79', 'd2d4')"
12,rnbqk1nr/ppppppb1/6pp/8/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 0 4,250000,50,147547,13989,18377,,"('16', '249641', 'cp', '76', 'd2d4')"
12,rnbqk1nr/ppppppb1/6pp/8/4P3/2N2N2/PPPP1PPP/R1BQKB1R w KQkq - 0 4,1000000,301,609347,56065,71618,,"('20', '842980', 'cp', '71', 'd2d4')"
13,rnb1kb1r/ppq1pppp/2pp1n2/8/2PPP3/2N2N2/PP1B1PPP/R2QKB1R b KQkq - 4 6,0,485,264473,36950,56099,174,dfa06a3b294761e6de8aade273ac4109f2dca1caf1ca4233cd4b22259b700347
13,rnb1kb1r/ppq1pppp/2pp1n2/8/2PPP3/2N2N2/PP1B1PPP/R2QKB1R b KQkq - 4 6,20000,4,10384,767,1368,,"('12', '17053', 'cp', '-77', 'e7e5')"
13,rnb1kb1r/ppq1pppp/2pp1n2/8/2PPP3/2N2N2/PP1B1PPP/R2QKB1R b KQkq - 4 6,250000,84,145014,7645,15049,,"('18', '171100', 'cp', '-78', 'e7e5')"
13,rnb1kb1r/ppq1pppp/2pp1n2/8/2PPP3/2N2N2/PP1B1PPP/R2QKB1R b KQkq - 4 6,1000000,457,628244,31268,56397,,"('21', '590730', 'cp', '-83', 'e7e5')"
14,rnbqkbnr/ppp2p1p/3pp1p1/8/2PP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 0 4,0,329,78792,8054,14912,49,7c5ca1dc2ebad6427f6682f7e3a42c0cec15fced90620e37b531f21b129aa733
14,rnbqkbnr/ppp2p1p/3pp1p1/8/2PP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 0 4,20000,13,9591,869,1704,,"('11', '19789', 'cp', '59', 'e2e4')"
14,rnbqkbnr/ppp2p1p/3pp1p1/8/2PP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 0 4,250000,98,145331,8674,17953,,"('18', '244215', 'cp', '68', 'e2e4')"
14,rnbqkbnr/ppp2p1p/3pp1p1/8/2PP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 0 4,1000000,342,624476,34324,64968,,"('21', '759435', 'cp', '78', 'e2e4')"
15,rnbqkb1r/pp2pppp/2p4n/3pP3/3P4/8/PPP2PPP/RNBQKBNR w KQkq - 1 4,0,1297,195168,52937,60129,150,27e0efdaea77c3bb79719ca9adc75e95cda6a25c69f285377f51ae19b2bec343
15,rnbqkb1r/pp2pppp/2p4n/3pP3/3P4/8/PPP2PPP/RNBQKBNR w KQkq - 1 4,20000,8,10921,734,1476,,"('10', '15038', 'cp', '74', 'c1h6')"
15,rnbqkb1r/pp2pppp/2p4n/3pP3/3P4/8/PPP2PPP/RNBQKBNR w KQkq - 1 4,250000,200,149404,9243,17383,,"('16', '216042', 'cp', '72', 'g1f3')"
15,rnbqkb1r/pp2pppp/2p4n/3pP3/3P4/8/PPP2PPP/RNBQKBNR w KQkq - 1 4,1000000,980,605529,43366,71029,,"('19', '890093', 'cp', '51', 'g1f3')"
16,rnb1kbnr/p1p1pppp/1p6/8/8/2N5/PPPPBPPP/R1B1K1NR w KQkq - 0 6,0,543,157414,38209,35484,103,81ba58298483ae810e3c6a8c2747efe0d4b33deb1a57c84ad6103528bfa55447
16,rnb1kbnr/p1p1pppp/1p6/8/8/2N5/PPPPBPPP/R1B1K1NR w KQkq - 0 6,20000,29,10006,1367,1871,,"('9', '14365', 'cp', '66', 'e2f3')"
16,rnb1kbnr/p1p1pppp/1p6/8/8/2N5/PPPPBPPP/R1B1K1NR w KQkq - 0 6,250000,310,128242,20603,22355,,"('16', '218521', 'cp', '67', 'g1f3')"
16,rnb1kbnr/p1p1pppp/1p6/8/8/2N5/PPPPBPPP/R1B1K1NR w KQkq - 0 6,1000000,1114,553615,77802,81201,,"('19', '848778', 'cp', '64', 'g1f3')"
17,r2qkbnr/ppp1nppp/3p4/3Pp3/4P1b1/2N2N1P/PPP2PP1/R1BQKB1R b KQkq - 0 6,0,3784,305980,69319,107298,229,d1f15db2727f6725ae7c75f1d6460638bba7c90a155e17fbfa982e8205de68f1
17,r2qkbnr/ppp1nppp/3p4/3Pp3/4P1b1/2N2N1P/PPP2PP1/R1BQKB1R b KQkq - 0 6,20000,7,10119,921,1533,,"('12', '13899', 'cp', '-41', 'g4d7')"
17,r2qkbnr/ppp1nppp/3p4/3Pp3/4P1b1/2N2N1P/PPP2PP1/R1BQKB1R b KQkq - 0 6,250000,110,154474,13310,15658,,"('18', '225267', 'cp', '-35', 'g4d7')"
17,r2qkbnr/ppp1nppp/3p4/3Pp3/4P1b1/2N2N1P/PPP2PP1/R1BQKB1R b KQkq - 0 6,1000000,723,633836,60132,61335,,"('19', '358776', 'cp', '-45', 'g4d7')"
18,r1b1kbnr/ppp2ppp/2n1p3/3q4/2PP4/5N2/PP3PPP/RNBQKB1R b KQkq - 0 5,0,604,108894,20909,24911,70,cf83326e5359901cdf27803ec01516a8b75b44b0067db08d27f64760d7e73610
18,r1b1kbnr/ppp2ppp/2n1p3/3q4/2PP4/5N2/PP3PPP/RNBQKB1R b KQkq - 0 5,20000,37,10166,975,1608,,"('10', '19800', 'cp', '-86', 'd5d7')"
18,r1b1kbnr/ppp2ppp/2n1p3/3q4/2PP4/5N2/PP3PPP/RNBQKB1R b KQkq - 0 5,250000,269,153662,8958,17422,,"('16', '111179', 'cp', '-59', 'd5d7')"
18,r1b1kbnr/ppp2ppp/2n1p3/3q4/2PP4/5N2/PP3PPP/RNBQKB1R b KQkq - 0 5,1000000,1088,607396,49669,71383,,"('19', '546563', 'cp', '-80', 'd5d7')"
19,r1bqkbnr/ppp2ppp/2n1p3/8/2PP4/5N2/PP3PPP/RNBQKB1R w KQkq - 1 6,0,2011,260794,70120,88328,283,89dc73677760539355c803aabb7aa28e36443d931ece20fc777f2a9bda55aa2a
19,r1bqkbnr/ppp2ppp/2n1p3/8/2PP4/5N2/PP3PPP/RNBQKB1R w KQkq - 1 6,20000,7,10215,1032,1578,,"('11', '18330', 'cp', '78', 'b1c3')"
19,r1bqkbnr/ppp2ppp/2n1p3/8/2PP4/5N2/PP3PPP/RNBQKB1R w KQkq - 1 6,250000,251,144051,10702,19852,,"('17', '246849', 'cp', '57', 'b1c3')"
19,r1bqkbnr/ppp2ppp/2n1p3/8/2PP4/5N2/PP3PPP/RNBQKB1R w KQkq - 1 6,1000000,1010,622911,37491,71124,,"('19', '649157', 'cp', '40', 'b1c3')"
20,rn1qkb1r/pbp2ppp/1p1ppn2/8/3PPP2/2N2N2/PPP3PP/R1BQKB1R w KQkq - 2 6,0,801,109651,17205,25842,71,86f641f362afb886249c39a88378f2a761744dd26d0c2f8547818d4845b7dcea
20,rn1qkb1r/pbp2ppp/1p1ppn2/8/3PPP2/2N2N2/PPP3PP/R1BQKB1R w KQkq - 2 6,20000,4,10283,977,1702,,"('11', '13602', 'cp', '59', 'f1d3')"
20,rn1qkb1r/pbp2ppp/1p1ppn2/8/3PPP2/2N2N2/PPP3PP/R1BQKB1R w KQkq - 2 6,250000,129,141901,12078,19459,,"('16', '234150', 'cp', '23', 'f1d3')"
20,rn1qkb1r/pbp2ppp/1p1ppn2/8/3PPP2/2N2N2/PPP3PP/R1BQKB1R w KQkq - 2 6,1000000,867,595859,53305,76546,,"('19', '513318', 'cp', '24', 'f1d3')"
21,rnbqkb1r/pp1pnppp/4p3/2p5/2PP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 1 4,0,601,200707,43069,60010,292,c8bec53116d9d45e10c4413e81233bb8991958bc4d6bfbec8a41ef3fb9b1d6ef
21,rnbqkb1r/pp1pnppp/4p3/2p5/2PP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 1 4,20000,17,10434,583,1862,,"('10', '14612', 'cp', '74', 'd4d5')"
21,rnbqkb1r/pp1pnppp/4p3/2p5/2PP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 1 4,250000,241,140162,10376,21614,,"('16', '138980', 'cp', '86', 'd4d5')"
21,rnbqkb1r/pp1pnppp/4p3/2p5/2PP4/5N2/PP2PPPP/RNBQKB1R w KQkq - 1 4,1000000,1013,588071,44857,79928,,"('21', '988737', 'cp', '29', 'd4d5')"
22,rnbqk1nr/pp2bppp/4p3/2ppP3/3P1P2/2PB1N2/PP4PP/RNBQK2R b KQkq - 1 7,0,1224,124543,15837,27138,70,2ac83c679778623fa8fc503eb3fabc1dd3be73c34236d9e2e4f63c3330cf4254
22,rnbqk1nr/pp2bppp/4p3/2ppP3/3P1P2/2PB1N2/PP4PP/RNBQK2R b KQkq - 1 7,20000,17,8924,1693,2163,,"('10', '19315', 'cp', '-41', 'g8h6')"
22,rnbqk1nr/pp2bppp/4p3/2ppP3/3P1P2/2PB1N2/PP4PP/RNBQK2R b KQkq - 1 7,250000,168,140108,16455,21053,,"('15', '162718', 'cp', '-55', 'g8h6')"
22,rnbqk1nr/pp2bppp/4p3/2ppP3/3P1P2/2PB1N2/PP4PP/RNBQK2R b KQkq - 1 7,1000000,903,590827,65572,77887,,"('20', '968599', 'cp', '-62', 'b8c6')"
23,rn2kbnr/ppq2ppp/2pp4/4p3/2PPP1b1/2N2N2/PP2BPPP/R1BQK2R b KQkq - 1 6,0,194,108485,11153,20109,69,0dab4b575e8d3993d9e24fc8062159094c8e6f05f52964f1cad276920abde072
23,rn2kbnr/ppq2ppp/2pp4/4p3/2PPP1b1/2N2N2/PP2BPPP/R1BQK2R b KQkq - 1 6,20000,17,10570,1439,1331,,"('12', '17601', 'cp', '-55', 'g4f3')"
23,rn2kbnr/ppq2ppp/2pp4/4p3/2PPP1b1/2N2N2/PP2BPPP/R1BQK2R b KQkq - 1 6,250000,134,151099,11356,14817,,"('18', '238104', 'cp', '-78', 'g8f6')"
23,rn2kbnr/ppq2ppp/2pp4/4p3/2PPP1b1/2N2N2/PP2BPPP/R1BQK2R b KQkq - 1 6,1000000,574,624410,40399,58198,,"('21', '959819', 'cp', '-88', 'g8f6')"
24,r2qkb1r/pp2pppp/2n2n2/3p4/3P2b1/3B1N1P/PPP2PP1/RNBQ1RK1 b kq - 0 7,0,1747,163522,42997,44375,118,1539516488da9381e33162e334b5a98f7807a2e7aff0bc6bbb3c4965a50d0abf
24,r2qkb1r/pp2pppp/2n2n2/3p4/3P2b1/3B1N1P/PPP2PP1/RNBQ1RK1 b kq - 0 7,20000,44,9571,1165,1820,,"('10', '17603', 'cp', '166', 'g4f3')"
24,r2qkb1r/pp2pppp/2n2n2/3p4/3P2b1/3B1N1P/PPP2PP1/RNBQ1RK1 b kq - 0 7,250000,453,144107,11327,19105,,"('17', '247100', 'cp', '93', 'g4f3')"
24,r2qkb1r/pp2pppp/2n2n2/3p4/3P2b1/3B1N1P/PPP2PP1/RNBQ1RK1 b kq - 0 7,1000000,2836,613365,41701,72646,,"('21', '713721', 'cp', '89', 'g4f3')"
25,r1bqkbnr/1ppppppp/p1n5/8/3P4/5N2/PPP1PPPP/RNBQKB1R w KQkq - 1 3,0,892,150545,28290,37036,108,225e0ee7834ad0af9b8d713efa3e1d3bc059feae19d337f1e05c3496e4ab7b91
25,r1bqkbnr/1ppppppp/p1n5/8/3P4/5N2/PPP1PPPP/RNBQKB1R w KQkq - 1 3,20000,10,10903,474,1674,,"('11', '15546', 'cp', '79', 'e2e4')"
25,r1bqkbnr/1ppppppp/p1n5/8/3P4/5N2/PPP1PPPP/RNBQKB1R w KQkq - 1 3,250000,118,137793,9209,18277,,"('17', '231034', 'cp', '50', 'd4d5')"
25,r1bqkbnr/1ppppppp/p1n5/8/3P4/5N2/PPP1PPPP/RNBQKB1R w KQkq - 1 3,1000000,668,575114,35673,69861,,"('21', '867378', 'cp', '36', 'd4d5')"
26,rnb1k1nr/ppppqppp/8/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4,0,415,181363,41462,39332,128,356af38876b72d378478f6296619bbdfbcece0b66cad981baf5894591ae3fec8
26,rnb1k1nr/ppppqppp/8/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4,20000,27,9793,795,1926,,"('10', '16328', 'cp', '56', 'e1g1')"
26,rnb1k1nr/ppppqppp/8/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4,250000,445,134398,8913,23264,,"('15', '203475', 'cp', '41', 'e1g1')"
26,rnb1k1nr/ppppqppp/8/2b1p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4,1000000,1658,579164,35046,82554,,"('18', '486673', 'cp', '54', 'e1g1')"
27,r1bqkb1r/pp3ppp/2nppn2/8/2PP4/2N2N2/PP3PPP/R1BQKB1R w KQkq - 0 7,0,1028,107468,11993,26561,82,664b383c5a4d542ecab6d8494a6f2ed00d310de27624242107ac14db9803034f
27,r1bqkb1r/pp3ppp/2nppn2/8/2PP4/2N2N2/PP3PPP/R1BQKB1R w KQkq - 0 7,20000,22,9979,1175,1813,,"('10', '17741', 'cp', '72', 'd4d5')"
27,r1bqkb1r/pp3ppp/2nppn2/8/2PP4/2N2N2/PP3PPP/R1BQKB1R w KQkq - 0 7,250000,289,138325,13869,19154,,"('18', '249742', 'cp', '70', 'd4d5')"
27,r1bqkb1r/pp3ppp/2nppn2/8/2PP4/2N2N2/PP3PPP/R1BQKB1R w KQkq - 0 7,1000000,1074,580837,48161,70132,,"('22', '888188', 'cp', '57', 'd4d5')"
28,rnbqkbnr/5ppp/p3p3/1pppP3/3P4/2PB1N2/PP3PPP/RNBQK2R b KQkq - 1 6,0,1305,223939,56406,55782,181,1dcb34c1e1cf3257149e542ee29a33cee62ddb7777bfa7a08fc5778e086dbfc2
28,rnbqkbnr/5ppp/p3p3/1pppP3/3P4/2PB1N2/PP3PPP/RNBQK2R b KQkq - 1 6,20000,8,10537,953,1454,,"('9', '14593', 'cp', '-98', 'b8c6')"
28,rnbqkbnr/5ppp/p3p3/1pppP3/3P4/2PB1N2/PP3PPP/RNBQK2R b KQkq - 1 6,250000,181,146886,7669,16972,,"('16', '223579', 'cp', '-86', 'b5b4')"
28,rnbqkbnr/5ppp/p3p3/1pppP3/3P4/2PB1N2/PP3PPP/RNBQK2R b KQkq - 1 6,1000000,941,631190,29265,64080,,"('20', '658391', 'cp', '-76', 'b5b4')"
29,rnbqkb1r/ppp1pppp/5n2/3p4/6P1/4P2P/PPPP1P2/RNBQKBNR b KQkq - 0 3,0,900,233362,69708,71725,199,e15284132c3d0ef38615fe82dfbb614fe303d122736444dd4ecb5292a28c6b8a
29,rnbqkb1r/ppp1pppp/5n2/3p4/6P1/4P2P/PPPP1P2/RNBQKBNR b KQkq - 0 3,20000,8,10750,577,1743,,"('9', '8481', 'cp', '83', 'e7e5')"
29,rnbqkb1r/ppp1pppp/5n2/3p4/6P1/4P2P/PPPP1P2/RNBQKBNR b KQkq - 0 3,250000,176,149847,9518,19936,,"('16', '183260', 'cp', '73', 'e7e5')"
29,rnbqkb1r/ppp1pppp/5n2/3p4/6P1/4P2P/PPPP1P2/RNBQKBNR b KQkq - 0 3,1000000,761,616902,43109,75785,,"('20', '890271', 'cp', '82', 'e7e5')"
30,r1bqk2r/ppp1bppp/3p1n2/4n3/3NPB2/2N5/PPPQ1PPP/R3KB1R w KQkq - 2 8,0,596,135335,31103,36082,109,510f9add16bb4fdd95fc1b6ce7cafce1bf7c7bd2dff8ba930e797aa0bc92783c
30,r1bqk2r/ppp1bppp/3p1n2/4n3/3NPB2/2N5/PPPQ1PPP/R3KB1R w KQkq - 2 8,20000,1,10890,793,1477,,"('10', '16109', 'cp', '78', 'e1c1')"
30,r1bqk2r/ppp1bppp/3p1n2/4n3/3NPB2/2N5/PPPQ1PPP/R3KB1R w KQkq - 2 8,250000,104,160013,8190,15833,,"('16', '243045', 'cp', '64', 'e1c1')"
30,r1bqk2r/ppp1bppp/3p1n2/4n3/3NPB2/2N5/PPPQ1PPP/R3KB1R w KQkq - 2 8,1000000,580,651546,29084,62075,,"('20', '863777', 'cp', '65', 'e1c1')"
31,rn2kbnr/ppp1pppp/8/4q2b/8/2NP1P2/PPP1N1PP/R1BQKB1R b KQkq - 0 6,0,1812,108234,16833,28738,75,a4a0d4b855a9a0eed8c3224baa0c1663a0e94ae27cc3491e69df4dae926bee34
31,rn2kbnr/ppp1pppp/8/4q2b/8/2NP1P2/PPP1N1PP/R1BQKB1R b KQkq - 0 6,20000,73,10645,914,1664,,"('10', '18144', 'cp', '-22', 'h5g6')"
31,rn2kbnr/ppp1pppp/8/4q2b/8/2NP1P2/PPP1N1PP/R1BQKB1R b KQkq - 0 6,250000,704,138305,11946,20366,,"('16', '219360', 'cp', '-7', 'e5a5')"
31,rn2kbnr/ppp1pppp/8/4q2b/8/2NP1P2/PPP1N1PP/R1BQKB1R b KQkq - 0 6,1000000,2475,576526,55282,79547,,"('18', '744479', 'cp', '-37', 'e5a5')"
32,rnb1kbnr/pp1p1ppp/2p2q2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4,0,442,108149,15842,23709,69,1545ee46665d7687d18d4b21dc300424e8dd1cf5cf69c94b502a51087948135e
32,rnb1kbnr/pp1p1ppp/2p2q2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4,20000,36,10377,1172,1709,,"('9', '13046', 'cp', '-84', 'f8d6')"
32,rnb1kbnr/pp1p1ppp/2p2q2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4,250000,423,143605,10297,20429,,"('16', '231285', 'cp', '-52', 'd7d6')"
32,rnb1kbnr/pp1p1ppp/2p2q2/4p3/2B1P3/3P1N2/PPP2PPP/RNBQK2R b KQkq - 0 4,1000000,2163,595749,43547,81100,,"('19', '743287', 'cp', '-32', 'd7d6')"
33,rnbqk2r/pp2nppp/4p3/1N1pP3/3p4/8/PPPQ1PPP/R3KBNR w KQkq - 1 8,0,908,179603,28922,43313,138,7382c00cd2a0b8c5fa871633e5a605b1a6d462eea947a205360f5f4e30fab6bc
33,rnbqk2r/pp2nppp/4p3/1N1pP3/3p4/8/PPPQ1PPP/R3KBNR w KQkq - 1 8,20000,12,10434,1128,1307,,"('11', '16114', 'cp', '102', 'b5d6')"
33,rnbqk2r/pp2nppp/4p3/1N1pP3/3p4/8/PPPQ1PPP/R3KBNR w KQkq - 1 8,250000,336,137871,16883,17799,,"('17', '182877', 'cp', '98', 'b5d6')"
33,rnbqk2r/pp2nppp/4p3/1N1pP3/3p4/8/PPPQ1PPP/R3KBNR w KQkq - 1 8,1000000,1523,549702,71262,72640,,"('22', '918179', 'cp', '72', 'b5d6')"
34,rnbq1rk1/ppp2ppp/3b1n2/3pN1B1/3P4/3B4/PPP2PPP/RN1Q1RK1 w - - 6 8,0,1040,196987,36562,46890,131,a3e5bc04eb959ad36415f82320a4f00c8decaef6e47c29abfdb6955073f04627
34,rnbq1rk1/ppp2ppp/3b1n2/3pN1B1/3P4/3B4/PPP2PPP/RN1Q1RK1 w - - 6 8,20000,19,10861,434,1750,,"('10', '17247', 'cp', '26', 'b1c3')"
34,rnbq1rk1/ppp2ppp/3b1n2/3pN1B1/3P4/3B4/PPP2PPP/RN1Q1RK1 w - - 6 8,250000,361,153321,7015,20166,,"('15', '211664', 'cp', '73', 'b1c3')"
34,rnbq1rk1/ppp2ppp/3b1n2/3pN1B1/3P4/3B4/PPP2PPP/RN1Q1RK1 w - - 6 8,1000000,1757,616996,27737,79074,,"('18', '971506', 'cp', '54', 'b1c3')"
35,rn1qk2r/pppbbppp/4p3/8/3P4/2P1PN2/P4PPP/R1BQKB1R w KQkq - 1 8,0,1834,183048,41091,45732,141,fbd97692b29f344e1ba140be72ae81e769d88fef257a566c3b433e117430bbd4
35,rn1qk2r/pppbbppp/4p3/8/3P4/2P1PN2/P4PPP/R1BQKB1R w KQkq - 1 8,20000,10,10256,1146,1559,,"('10', '12410', 'cp', '48', 'd1c2')"
35,rn1qk2r/pppbbppp/4p3/8/3P4/2P1PN2/P4PPP/R1BQKB1R w KQkq - 1 8,250000,164,143474,12726,19417,,"('15', '227509', 'cp', '48', 'a1b1')"
35,rn1qk2r/pppbbppp/4p3/8/3P4/2P1PN2/P4PPP/R1BQKB1R w KQkq - 1 8,1000000,1120,597589,51452,72037,,"('19', '597310', 'cp', '49', 'a1b1')"
36,rnbqk1nr/ppppp1bp/5pp1/8/3PP3/1P6/PBP2PPP/RN1QKBNR b KQkq - 0 4,0,393,136808,30030,29276,110,6dfb4c690e44c640ccb71839819d8e58d17ed05dc861f9c2ca4185f04d1de9e8
36,rnbqk1nr/ppppp1bp/5pp1/8/3PP3/1P6/PBP2PPP/RN1QKBNR b KQkq - 0 4,20000,3,10538,966,1671,,"('11', '19227', 'cp', '-99', 'g8h6')"
36,rnbqk1nr/ppppp1bp/5pp1/8/3PP3/1P6/PBP2PPP/RN1QKBNR b KQkq - 0 4,250000,118,138111,14649,20589,,"('17', '177306', 'cp', '-98', 'c7c6')"
36,rnbqk1nr/ppppp1bp/5pp1/8/3PP3/1P6/PBP2PPP/RN1QKBNR b KQkq - 0 4,1000000,681,592555,62841,77404,,"('19', '400560', 'cp', '-104', 'c7c6')"
37,rnbqkb1r/p1p1pppp/1p1p1n2/8/3PP3/2NB4/PPP2PPP/R1BQK1NR b KQkq - 1 4,0,2885,163228,35652,45840,121,00aacaa1c546b20971b5e1836b513bb3710a36b0a75815d5a1effb95efa61711
37,rnbqkb1r/p1p1pppp/1p1p1n2/8/3PP3/2NB4/PPP2PPP/R1BQK1NR b KQkq - 1 4,20000,3,10161,590,1702,,"('12', '19696', 'cp', '-57', 'c8b7')"
37,rnbqkb1r/p1p1pppp/1p1p1n2/8/3PP3/2NB4/PPP2PPP/R1BQK1NR b KQkq - 1 4,250000,124,148956,9618,18619,,"('18', '238513', 'cp', '-56', 'e7e6')"
37,rnbqkb1r/p1p1pppp/1p1p1n2/8/3PP3/2NB4/PPP2PPP/R1BQK1NR b KQkq - 1 4,1000000,612,615323,50486,72416,,"('20', '824111', 'cp', '-54', 'e7e6')"
38,r1bqk2r/1p1nbppp/p3pn2/3p4/3P1B2/2PB1N2/PP1N1PPP/R2QK2R w KQkq - 0 9,0,1545,170321,45703,47363,139,2a7df2ce4a3e829fbfeac3073ef79385e8f208e4f2b7dcf44c36a0e74bb868c7
38,r1bqk2r/1p1nbppp/p3pn2/3p4/3P1B2/2PB1N2/PP1N1PPP/R2QK2R w KQkq - 0 9,20000,5,9905,768,1907,,"('11', '17076', 'cp', '59', 'h2h3')"
38,r1bqk2r/1p1nbppp/p3pn2/3p4/3P1B2/2PB1N2/PP1N1PPP/R2QK2R w KQkq - 0 9,250000,135,148468,5802,20470,,"('16', '81586', 'cp', '85', 'h2h3')"
38,r1bqk2r/1p1nbppp/p3pn2/3p4/3P1B2/2PB1N2/PP1N1PPP/R2QK2R w KQkq - 0 9,1000000,660,606513,32205,69686,,"('22', '893170', 'cp', '64', 'h2h3')"
39,rnbqkb1r/ppp1pp1p/5np1/3p4/3PP3/2N2N2/PPP2PPP/R1BQKB1R b KQkq - 0 4,0,659,171007,30604,39340,117,5cd533980b3ceb98bb08d935329d212349a8aaa95c7d6d3dab44fa499fe913df
39,rnbqkb1r/ppp1pp1p/5np1/3p4/3PP3/2N2N2/PPP2PPP/R1BQKB1R b KQkq - 0 4,20000,23,10765,768,1701,,"('10', '16238', 'cp', '58', 'd5e4')"
39,rnbqkb1r/ppp1pp1p/5np1/3p4/3PP3/2N2N2/PPP2PPP/R1BQKB1R b KQkq - 0 4,250000,293,146876,11127,19000,,"('15', '180732', 'cp', '83', 'd5e4')"
39,rnbqkb1r/ppp1pp1p/5np1/3p4/3PP3/2N2N2/PPP2PPP/R1BQKB1R b KQkq - 0 4,1000000,1083,601596,42263,71419,,"('22', '933542', 'cp', '72', 'd5e4')"
40,rnbqk1nr/p1p2ppp/1p2p3/3pP3/1b1P4/P1N5/1PP2PPP/R1BQKBNR b KQkq - 0 5,0,808,115254,27868,25425,87,c970358f4700059f5da9b870ce8c0cda257e8b5ac422dd4fd9ca6b3a6d846108
40,rnbqk1nr/p1p2ppp/1p2p3/3pP3/1b1P4/P1N5/1PP2PPP/R1BQKBNR b KQkq - 0 5,20000,22,10420,791,1548,,"('10', '12393', 'cp', '-48', 'b4c3')"
40,rnbqk1nr/p1p2ppp/1p2p3/3pP3/1b1P4/P1N5/1PP2PPP/R1BQKBNR b KQkq - 0 5,250000,256,146526,13099,16729,,"('15', '160521', 'cp', '-55', 'b4c3')"
40,rnbqk1nr/p1p2ppp/1p2p3/3pP3/1b1P4/P1N5/1PP2PPP/R1BQKBNR b KQkq - 0 5,1000000,1259,577447,61276,70435,,"('21', '976186', 'cp', '-25', 'b4c3')"
41,r1bqkb1r/ppp2ppp/2nppn2/8/2PP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 0 5,0,2294,239354,38511,54343,292,f721340bdc674469f80350f329a2401acacb9fc5f36e04b25f8c1c8a1a331d0d
41,r1bqkb1r/ppp2ppp/2nppn2/8/2PP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 0 5,20000,15,10432,838,1559,,"('10', '13247', 'cp', '66', 'e2e4')"
41,r1bqkb1r/ppp2ppp/2nppn2/8/2PP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 0 5,250000,186,149731,9777,17007,,"('18', '153632', 'cp', '70', 'e2e4')"
41,r1bqkb1r/ppp2ppp/2nppn2/8/2PP4/2N2N2/PP2PPPP/R1BQKB1R w KQkq - 0 5,1000000,980,643304,41149,63171,,"('21', '677731', 'cp', '52', 'e2e4')"
42,rnbqkb1r/1p3ppp/p2ppn2/2pP4/2P1P3/5N2/PP3PPP/RNBQKB1R w KQkq - 1 6,0,102,92361,17416,19565,90,8cd02e1ee9087c3d0deb6583844abc385cd313c82532aa3cac97fe3be0cde74a
42,rnbqkb1r/1p3ppp/p2ppn2/2pP4/2P1P3/5N2/PP3PPP/RNBQKB1R w KQkq - 1 6,20000,23,9651,809,1626,,"('11', '19420', 'cp', '67', 'b1c3')"
42,rnbqkb1r/1p3ppp/p2ppn2/2pP4/2P1P3/5N2/PP3PPP/RNBQKB1R w KQkq - 1 6,250000,108,145412,8764,16845,,"('18', '164316', 'cp', '76', 'b1c3')"
42,rnbqkb1r/1p3ppp/p2ppn2/2pP4/2P1P3/5N2/PP3PPP/RNBQKB1R w KQkq - 1 6,1000000,536,628715,40731,62680,,"('22', '889303', 'cp', '58', 'b1c3')"
43,rnbqkb1r/pppppppp/8/3n4/8/1P6/PBPPPPPP/RN1QKBNR w KQkq - 3 3,0,788,133079,21890,24123,97,c105ef6ac6b3d6277a066603b847f7bdb50f22aaab41452cec4b2b396f91aae6
43,rnbqkb1r/pppppppp/8/3n4/8/1P6/PBPPPPPP/RN1QKBNR w KQkq - 3 3,20000,2,10732,581,1556,,"('11', '19919', 'cp', '101', 'e2e4')"
43,rnbqkb1r/pppppppp/8/3n4/8/1P6/PBPPPPPP/RN1QKBNR w KQkq - 3 3,250000,180,146189,8582,18614,,"('16', '219193', 'cp', '102', 'e2e4')"
43,rnbqkb1r/pppppppp/8/3n4/8/1P6/PBPPPPPP/RN1QKBNR w KQkq - 3 3,1000000,942,610639,39548,71442,,"('21', '909374', 'cp', '71', 'e2e4')"
44,r2qk2r/ppp1bppp/2n1pn2/3p4/3P1P2/2PBPQ2/PP4PP/RNB1K2R w KQkq - 2 8,0,1329,174266,39963,46625,128,b00b85d99e01fcd1b90e4636318dd061c04fe16c63e01d8b76c608efc3e828ef
44,r2qk2r/ppp1bppp/2n1pn2/3p4/3P1P2/2PBPQ2/PP4PP/RNB1K2R w KQkq - 2 8,20000,13,10029,1285,1626,,"('9', '11346', 'cp', '75', 'b1d2')"
44,r2qk2r/ppp1bppp/2n1pn2/3p4/3P1P2/2PBPQ2/PP4PP/RNB1K2R w KQkq - 2 8,250000,179,141589,14230,18653,,"('14', '204397', 'cp', '67', 'e1g1')"
44,r2qk2r/ppp1bppp/2n1pn2/3p4/3P1P2/2PBPQ2/PP4PP/RNB1K2R w KQkq - 2 8,1000000,551,586553,68321,69088,,"('19', '816022', 'cp', '60', 'b1d2')"
45,r2qk1nr/pppbppbp/2n3p1/1B1pP3/3P4/5N2/PPP2PPP/RNBQK2R w KQkq - 2 6,0,1670,191114,29818,40837,120,5b6c14d7e770f11009b7c6b8adc789dcef32c6b7ff5980b053ce18607929c12d
45,r2qk1nr/pppbppbp/2n3p1/1B1pP3/3P4/5N2/PPP2PPP/RNBQK2R w KQkq - 2 6,20000,8,11552,962,1279,,"('10', '19437', 'cp', '80', 'c1f4')"
45,r2qk1nr/pppbppbp/2n3p1/1B1pP3/3P4/5N2/PPP2PPP/RNBQK2R w KQkq - 2 6,250000,93,152690,11670,15756,,"('16', '196524', 'cp', '75', 'c1f4')"
45,r2qk1nr/pppbppbp/2n3p1/1B1pP3/3P4/5N2/PPP2PPP/RNBQK2R w KQkq - 2 6,1000000,648,628105,50541,63164,,"('20', '627272', 'cp', '75', 'c1f4')"
46,rn2kbnr/ppq1pppp/2pp4/8/3P2b1/5NP1/PPP1PPBP/RNBQK2R w KQkq - 3 5,0,448,103326,17958,22640,90,18d7ab66235364e9cda172806b34e8d7bfe8deca88326a32ac3436df91b79b2b
46,rn2kbnr/ppq1pppp/2pp4/8/3P2b1/5NP1/PPP1PPBP/RNBQK2R w KQkq - 3 5,20000,1,10264,794,1452,,"('11', '18599', 'cp', '90', 'e1g1')"
46,rn2kbnr/ppq1pppp/2pp4/8/3P2b1/5NP1/PPP1PPBP/RNBQK2R w KQkq - 3 5,250000,185,144317,8811,16395,,"('16', '242841', 'cp', '50', 'e1g1')"
46,rn2kbnr/ppq1pppp/2pp4/8/3P2b1/5NP1/PPP1PPBP/RNBQK2R w KQkq - 3 5,1000000,833,606073,35199,62734,,"('20', '869856', 'cp', '52', 'h2h3')"
47,r3kbnr/ppqnpppp/2pp4/8/3P2b1/5NP1/PPP1PPBP/RNBQ1RK1 w kq - 5 6,0,653,128688,27102,32046,97,c8c21e2f2a227812359823e53cca614846dc7c0b91db7c6c7865a8d6910935da
47,r3kbnr/ppqnpppp/2pp4/8/3P2b1/5NP1/PPP1PPBP/RNBQ1RK1 w kq - 5 6,20000,3,10283,774,1488,,"('10', '7607', 'cp', '133', 'c2c4')"
47,r3kbnr/ppqnpppp/2pp4/8/3P2b1/5NP1/PPP1PPBP/RNBQ1RK1 w kq - 5 6,250000,72,151143,8422,15323,,"('16', '229529', 'cp', '99', 'c2c4')"
47,r3kbnr/ppqnpppp/2pp4/8/3P2b1/5NP1/PPP1PPBP/RNBQ1RK1 w kq - 5 6,1000000,611,641214,29784,57376,,"('19', '487908', 'cp', '97', 'c2c4')"
48,rnbqkb1r/ppp2ppp/3p4/3Pp3/2B1n3/5N2/PPP2PPP/RNBQK2R w KQkq - 0 6,0,921,227659,44068,61710,292,c84248ce373f4b4420199ce30199af40ae150b1b4e817eb46198015ba9ddb116
48,rnbqkb1r/ppp2ppp/3p4/3Pp3/2B1n3/5N2/PPP2PPP/RNBQK2R w KQkq - 0 6,20000,10,9935,830,1594,,"('10', '14694', 'cp', '-108', 'e1g1')"
48,rnbqkb1r/ppp2ppp/3p4/3Pp3/2B1n3/5N2/PPP2PPP/RNBQK2R w KQkq - 0 6,250000,101,146724,8409,16543,,"('18', '215455', 'cp', '-125', 'e1g1')"
48,rnbqkb1r/ppp2ppp/3p4/3Pp3/2B1n3/5N2/PPP2PPP/RNBQK2R w KQkq - 0 6,1000000,1221,640578,35424,66594,,"('20', '881931', 'cp', '-121', 'e1g1')"
49,rnbqkbnr/pp3ppp/4p3/3pP3/2pP1P2/2P5/PP4PP/RNBQKBNR w KQkq - 0 6,0,396,91094,5946,15253,53,569cb0fc1b8451c8eb9c4a48a3fd39a077e4fea064cc752d1107c8b682f642a7
49,rnbqkbnr/pp3ppp/4p3/3pP3/2pP1P2/2P5/PP4PP/RNBQKBNR w KQkq - 0 6,20000,11,9657,983,1836,,"('10', '15226', 'cp', '77', 'b2b3')"
49,rnbqkbnr/pp3ppp/4p3/3pP3/2pP1P2/2P5/PP4PP/RNBQKBNR w KQkq - 0 6,250000,164,141132,10295,18292,,"('17', '227749', 'cp', '51', 'b2b3')"
49,rnbqkbnr/pp3ppp/4p3/3pP3/2pP1P2/2P5/PP4PP/RNBQKBNR w KQkq - 0 6,1000000,893,601045,46918,69004,,"('21', '647811', 'cp', '61', 'b2b3')"
50,r1bq1rk1/pppnbppp/3p1n2/8/2BPPB2/2N2N2/PPP3PP/R2Q1RK1 b - - 4 8,0,840,101342,26658,23845,73,d6ce00c9415ace2110ed25b66cfbf6ce9f8ec35eace8f350c4f67973c8b40b06
50,r1bq1rk1/pppnbppp/3p1n2/8/2BPPB2/2N2N2/PPP3PP/R2Q1RK1 b - - 4 8,20000,1,11296,549,1525,,"('10', '18595', 'cp', '-68', 'c7c6')"
50,r1bq1rk1/pppnbppp/3p1n2/8/2BPPB2/2N2N2/PPP3PP/R2Q1RK1 b - - 4 8,250000,131,156238,7172,17997,,"('17', '233701', 'cp', '-70', 'c7c6')"
50,r1bq1rk1/pppnbppp/3p1n2/8/2BPPB2/2N2N2/PPP3PP/R2Q1RK1 b - - 4 8,1000000,1225,653653,28399,72010,,"('20', '574095', 'cp', '-60', 'c7c6')"
51,rn1qkb1r/ppp1pppp/5n2/8/3P2b1/2NB1N2/PPP3PP/R1BQK2R b KQkq - 2 6,0,1503,303061,100641,97192,249,20bf3e1a2dd8b9ed60aa934d3fa2179a6c7ed3af7c29cf704b360b96321e5853
51,rn1qkb1r/ppp1pppp/5n2/8/3P2b1/2NB1N2/PPP3PP/R1BQK2R b KQkq - 2 6,20000,11,10333,1391,1607,,"('10', '18699', 'cp', '47', 'b8c6')"
51,rn1qkb1r/ppp1pppp/5n2/8/3P2b1/2NB1N2/PPP3PP/R1BQK2R b KQkq - 2 6,250000,199,135960,19518,19425,,"('16', '224411', 'cp', '79', 'e7e6')"
51,rn1qkb1r/ppp1pppp/5n2/8/3P2b1/2NB1N2/PPP3PP/R1BQK2R b KQkq - 2 6,1000000,1206,559972,74151,75888,,"('18', '633402', 'cp', '99', 'e7e6')"
52,rnbqkb1r/pp2pppp/3p1n2/8/4P3/1N6/PPP2PPP/RNBQKB1R b KQkq - 2 5,0,222,191852,57821,58762,279,68d81cbc28006ea0c4ea77b48b5ad13ef3af2810bca25744972ba379be09b18f
52,rnbqkb1r/pp2pppp/3p1n2/8/4P3/1N6/PPP2PPP/RNBQKB1R b KQkq - 2 5,20000,24,9342,863,1758,,"('10', '14925', 'cp', '111', 'f6e4')"
52,rnbqkb1r/pp2pppp/3p1n2/8/4P3/1N6/PPP2PPP/RNBQKB1R b KQkq - 2 5,250000,328,139213,10218,18073,,"('17', '233989', 'cp', '101', 'f6e4')"
52,rnbqkb1r/pp2pppp/3p1n2/8/4P3/1N6/PPP2PPP/RNBQKB1R b KQkq - 2 5,1000000,1245,565715,33258,67377,,"('22', '848214', 'cp', '109', 'f6e4')"
53,r1bqk1nr/pppn1pbp/3pp1p1/8/3PPP2/2N2N2/PPP3PP/R1BQKB1R w KQkq - 0 6,0,1344,176977,27518,30429,102,0b64b2df0ef856a41cd25caa1065de7d60c83a196ff83456ed00d8388782da4e
53,r1bqk1nr/pppn1pbp/3pp1p1/8/3PPP2/2N2N2/PPP3PP/R1BQKB1R w KQkq - 0 6,20000,5,11540,1225,1332,,"('10', '13008', 'cp', '44', 'c1e3')"
53,r1bqk1nr/pppn1pbp/3pp1p1/8/3PPP2/2N2N2/PPP3PP/R1BQKB1R w KQkq - 0 6,250000,77,148626,11800,16223,,"('16', '176977', 'cp', '-2', 'c1e3')"
53,r1bqk1nr/pppn1pbp/3pp1p1/8/3PPP2/2N2N2/PPP3PP/R1BQKB1R w KQkq - 0 6,1000000,1180,581689,65387,75796,,"('20', '991967', 'cp', '52', 'f4f5')"
54,rn1qk1nr/ppp1b1pp/3pp3/4p3/3PP3/5N2/PPP2PPP/RNBQ1RK1 b kq - 0 7,0,607,125090,27020,30028,90,7cc5533b0730fe9474ac80edf6d944c01ff62fb107577975f957d65a1644d6e7
54,rn1qk1nr/ppp1b1pp/3pp3/4p3/3PP3/5N2/PPP2PPP/RNBQ1RK1 b kq - 0 7,20000,30,10644,1161,1648,,"('10', '16884', 'cp', '-81', 'b8c6')"
54,rn1qk1nr/ppp1b1pp/3pp3/4p3/3PP3/5N2/PPP2PPP/RNBQ1RK1 b kq - 0 7,250000,421,145813,13880,18671,,"('15', '180329', 'cp', '-101', 'g8f6')"
54,rn1qk1nr/ppp1b1pp/3pp3/4p3/3PP3/5N2/PPP2PPP/RNBQ1RK1 b kq - 0 7,1000000,1409,597838,48496,69430,,"('20', '972326', 'cp', '-77', 'g8f6')"
55,rnbqk2r/pp2npbp/6p1/2pp4/8/2N2NP1/PP1PPPBP/R1BQ1RK1 w kq - 0 8,0,385,181437,35598,47515,224,6175d70b4d47b6057dc8c866a00819a08a4ad36734f22098a61287b8d38eeef2
55,rnbqk2r/pp2npbp/6p1/2pp4/8/2N2NP1/PP1PPPBP/R1BQ1RK1 w kq - 0 8,20000,8,11975,572,1207,,"('10', '15337', 'cp', '81', 'd2d4')"
55,rnbqk2r/pp2npbp/6p1/2pp4/8/2N2NP1/PP1PPPBP/R1BQ1RK1 w kq - 0 8,250000,154,161111,6153,13756,,"('17', '184567', 'cp', '82', 'd2d4')"
55,rnbqk2r/pp2npbp/6p1/2pp4/8/2N2NP1/PP1PPPBP/R1BQ1RK1 w kq - 0 8,1000000,719,650750,26055,57245,,"('23', '928464', 'cp', '84', 'd2d4')"
56,rnbq1rk1/p1ppnpbp/1p2p1p1/8/3PPP2/2NBBN2/PPP3PP/R2QK2R b KQ - 1 7,0,835,203503,45360,54153,292,9ade15e94b79ee57494b1846aa3716e56acd06f12e8e931088927a4ec6289f96
56,rnbq1rk1/p1ppnpbp/1p2p1p1/8/3PPP2/2NBBN2/PPP3PP/R2QK2R b KQ - 1 7,20000,3,11952,987,1335,,"('8', '7008', 'cp', '-38', 'b8a6')"
56,rnbq1rk1/p1ppnpbp/1p2p1p1/8/3PPP2/2NBBN2/PPP3PP/R2QK2R b KQ - 1 7,250000,119,152431,11041,16090,,"('16', '174369', 'cp', '-44', 'd7d5')"
56,rnbq1rk1/p1ppnpbp/1p2p1p1/8/3PPP2/2NBBN2/PPP3PP/R2QK2R b KQ - 1 7,1000000,549,626601,42795,59297,,"('22', '956331', 'cp', '-43', 'd7d5')"
57,r1bqkbnr/ppp1pppp/2np4/4P3/3P4/2N2N2/PPP2PPP/R1BQKB1R b KQkq - 1 5,0,538,157055,18904,30709,96,4b9aaef17b658cec26464d5e439a4eeb6f9083aaf8424e56a9fffeb6589abb48
57,r1bqkbnr/ppp1pppp/2np4/4P3/3P4/2N2N2/PPP2PPP/R1BQKB1R b KQkq - 1 5,20000,23,10247,1018,1768,,"('9', '13267', 'cp', '-91', 'c8g4')"
57,r1bqkbnr/ppp1pppp/2np4/4P3/3P4/2N2N2/PPP2PPP/R1BQKB1R b KQkq - 1 5,250000,302,149203,10685,18576,,"('16', '198548', 'cp', '-87', 'e7e6')"
57,r1bqkbnr/ppp1pppp/2np4/4P3/3P4/2N2N2/PPP2PPP/R1BQKB1R b KQkq - 1 5,1000000,1451,611621,50458,76418,,"('18', '546844', 'cp', '-79', 'e7e6')"
58,r3kbnr/pppq1ppp/3p4/4p3/3nP3/2N2N2/PPP2PPP/R1BQK2R w KQkq - 0 7,0,1025,118098,17614,22042,65,1963df7f3f8a5ebeec73d6f463b9e606ee60001e3c5abadb8e4ec81b8350d08a
58,r3kbnr/pppq1ppp/3p4/4p3/3nP3/2N2N2/PPP2PPP/R1BQK2R w KQkq - 0 7,20000,14,10249,1393,1286,,"('11', '16521', 'cp', '75', 'f3d4')"
58,r3kbnr/pppq1ppp/3p4/4p3/3nP3/2N2N2/PPP2PPP/R1BQK2R w KQkq - 0 7,250000,271,141508,13974,17114,,"('18', '233262', 'cp', '81', 'f3d4')"
58,r3kbnr/pppq1ppp/3p4/4p3/3nP3/2N2N2/PPP2PPP/R1BQK2R w KQkq - 0 7,1000000,1101,582312,51670,74378,,"('21', '878150', 'cp', '71', 'f3d4')"
59,r2qk1nr/ppp1ppbp/3p2p1/6B1/3nP3/2N2B2/PPP2PPP/R2QK2R w KQkq - 0 8,0,1719,140337,20992,33253,97,64ebce69ecfacd5df0de7cc6de43757a5b3a6ffb9a72c524651053dfc696f089
59,r2qk1nr/ppp1ppbp/3p2p1/6B1/3nP3/2N2B2/PPP2PPP/R2QK2R w KQkq - 0 8,20000,11,9744,1397,1684,,"('10', '18997', 'cp', '-120', 'f3g4')"
59,r2qk1nr/ppp1ppbp/3p2p1/6B1/3nP3/2N2B2/PPP2PPP/R2QK2R w KQkq - 0 8,250000,262,138754,13190,18564,,"('18', '213045', 'cp', '-95', 'f3g4')"
59,r2qk1nr/ppp1ppbp/3p2p1/6B1/3nP3/2N2B2/PPP2PPP/R2QK2R w KQkq - 0 8,1000000,1406,590979,50427,68922,,"('24', '779167', 'cp', '-101', 'f3g4')"
~~~
