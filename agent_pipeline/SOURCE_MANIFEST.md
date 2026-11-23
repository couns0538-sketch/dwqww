# Forge 6.5 pinned source inventory

Baseline branch: `forge6.5`
Immutable baseline SHA: `d4651aeac344b9d838c63406abb95053cd968f9a`
Baseline tree SHA: `c2a19acd8be3d253b33f9cf7f4a8051e5422c8a9`
Listing verified: GitHub Git tree (recursive, truncated=false).
Each row: git blob SHA, source-byte length, relative path.
This manifest is an index, **not a replacement for reading and verifying every source file**. Read `source/**`, `loop/source/**`, build scripts, README, SHA256 manifests, config, and relevant test notes. Fetch pinned blob bytes; verify SHA-256 where supplied. Binary assets may require authenticated archive/download and must never be interpreted as text.

```text
fa1385d99a319b43c06f5309d1aae9fdd3adea46           8 .gitattributes
cdb6356605a04107cff1d6227729afbc6ef454c1    11863040 Forge65.exe
50377189ea748cb52db6d2631b9ebe70ba112751       11841 Forge65_build/build_clang.log
37e1b04f591bc438a5681cafcab53b1bbac30542        1639 Forge65_build/build_forge65_clang_pgo.sh
3c1ffe072994cb8f828b31020eac0e1e94b227b8        8448 HASHES.sha256
906769d28423eb3fd9e94549ea7fcd97c7ed31df        6364 README.txt
f096a359a03f9cefc99607ab9186b2de9759be8a         959 loop/LOOP_OPTIONS.txt
990708e7810d88d5127ef48b9d530ca9a88eb315        9796 loop/build_clang.log
4d5aaf13dbacb1db62913cf13c4eafbb98928122        6233 loop/build_recipe/build_forge_clang_pgo.sh
8986299df9b59604de64d92aec0e8f9eed1cbf9a         754 loop/build_recipe/build_forge_v3_clang_pgo.sh
207d531d1b31f42bdf3c155b84ff950ec464a49a         836 loop/build_recipe/build_forge_v3r15d_clang_pgo.sh
aed1ecb3e414be51ed1297d07f7d36ccd13945a3        1390 loop/build_recipe/build_forge_v3r15dsg_sp_clang_pgo.sh
c6b89817bf059efb187e473959a7727189b65d9d        4188 loop/build_recipe/pgo_selfgame.py
08c062357ef0709eedadf6344aa7a6bd0fbeefce        3935 loop/build_recipe/pgo_selfplay_books.epd
7492ffe4aee43af9c098cc4dd522f99e350015b4     2390528 loop/forge.exe
101df6fdb4dc38b9bd907ba2cd49287f483970ff     9463528 loop/forge65_r0067.fnn3
18967a3f50df1b1e460b37c8c5984d11bb0a2283       12825 loop/source/CARBON2_E1_legal_check_evasions.patch.txt
17217643a8b93f7a04d8fa6df85331f8fa0520ec       15763 loop/source/CARBON2_selfgame_v3.patch.txt
d9dd678606c4adf5dc0c167fd1e1fc0a6b299dbf        2170 loop/source/CMakeLists.txt
c4c575c8c134416cccfbca1f5d77005c036f4765        6756 loop/source/R15DSG_NOTE.txt
fe03c78023492236124d786a1b017294de33f0e4        3282 loop/source/R15D_NOTE.txt
3975a2a7151771d79aff2b0fa52ed4213ced95e8        2539 loop/source/SOURCE_INPUTS.sha256
fe7bcab110126f6609fda8e5d17f595c8ae0f881        5862 loop/source/include/forge/b4.hpp
b1d660ba5d73010fc00446a48a6eb3c294186fa8        9867 loop/source/include/forge/bitboard.hpp
e9623d7763d4aadd3fe9c1237385abdde3f1e0b3       16117 loop/source/include/forge/board.hpp
a350cbb363b42cfaf5811af29ab09b3b88197b8f        1994 loop/source/include/forge/book.hpp
06cd760c5a84decc9ed37ccd63e25c6ab00b2ce4        2392 loop/source/include/forge/clock_plan.hpp
6e152993d70ab0df056ad6e2cb19a2a47a7528f8        3321 loop/source/include/forge/eval.hpp
2bfe24a35c63f95feb227934506f5f588c3cb64a        3282 loop/source/include/forge/eval_params.hpp
3ff913a473ace1a37677c1553eee8297d7bb369a        4863 loop/source/include/forge/nnue.hpp
8765fcf1538dde830fb82d240118d7a5f31c04e3       15525 loop/source/include/forge/nnue_v3.hpp
6e1ce1f01ee6a0310b403d7d3c263db49bb5814b       33146 loop/source/include/forge/search.hpp
1a287fc1a3e1413f7154f976478c6cd4d5827495        1982 loop/source/include/forge/tm_finish.hpp
c5509165d096a7e5e0f0f6f1425381ce286ad487        2880 loop/source/include/forge/tm_node_share.hpp
f7f7e6f467ee86bffc591afe850e99756288a92f         262 loop/source/include/forge/uci.hpp
6d29c5df25d2ac0fb14653eb88e0dd670663f89b        1847 loop/source/include/forge/uci_clock.hpp
b0e4c1e6efb41c3d3dab781d033b5a92922aab60         162 loop/source/include/forge/uci_output.hpp
fea4808843c40380e940c8c79ac6702c0668de79        8791 loop/source/src/bitboard.cpp
7716d4826616f025616db157c859de63e78e074a       81283 loop/source/src/board.cpp
5f79f022f65a524dcc5b15059c5e8b33b26f321a        7492 loop/source/src/book.cpp
9b9671eeb47c994e5ef8d6ea91d44bc971986fa3       91623 loop/source/src/book_data.inc
208ab2a00585ac48055fd33ed92293611a04bafb       32752 loop/source/src/eval.cpp
2146b7cf9a5afb0d727728b33bf57c572f79f75e        4168 loop/source/src/eval_params.cpp
6f2634ba788d3624a739304c30611ee0ce13e9c2       23556 loop/source/src/eval_params_table.inc
99eb9eb455f8ed199a646dc94fb7fddf3f5ac848       25855 loop/source/src/nnue.cpp
5c79ffc9a4d2b9abb3a46bab5d7de1c71c3ddeec       49795 loop/source/src/nnue_v3.cpp
c17ccca5f157d07c65eff76aac510a99490c6fcc     1123870 loop/source/src/nnue_weights.inc
1f5703d1c39ae76253e79ce0740ce3a79223726e       18859 loop/source/src/polyglot_keys.inc
620c0c2b39329bac6e0a4b379f64795abebc559b      167417 loop/source/src/search.cpp
a775055f694de37ab1a17337b595b4d7917bf45e       57105 loop/source/src/uci.cpp
18967a3f50df1b1e460b37c8c5984d11bb0a2283       12825 source/CARBON2_E1_legal_check_evasions.patch.txt
17217643a8b93f7a04d8fa6df85331f8fa0520ec       15763 source/CARBON2_selfgame_v3.patch.txt
d9dd678606c4adf5dc0c167fd1e1fc0a6b299dbf        2170 source/CMakeLists.txt
c4c575c8c134416cccfbca1f5d77005c036f4765        6756 source/R15DSG_NOTE.txt
fe03c78023492236124d786a1b017294de33f0e4        3282 source/R15D_NOTE.txt
4c0a202b1c458663f388e9a9f90db0fe01108f4b        5482 source/R65_NOTE.txt
f0551c6d6597369303cca19a7af4686cd1e0d1da        2800 source/SOURCE_INPUTS.sha256
fe7bcab110126f6609fda8e5d17f595c8ae0f881        5862 source/include/forge/b4.hpp
b1d660ba5d73010fc00446a48a6eb3c294186fa8        9867 source/include/forge/bitboard.hpp
e9623d7763d4aadd3fe9c1237385abdde3f1e0b3       16117 source/include/forge/board.hpp
a350cbb363b42cfaf5811af29ab09b3b88197b8f        1994 source/include/forge/book.hpp
06cd760c5a84decc9ed37ccd63e25c6ab00b2ce4        2392 source/include/forge/clock_plan.hpp
6e152993d70ab0df056ad6e2cb19a2a47a7528f8        3321 source/include/forge/eval.hpp
2bfe24a35c63f95feb227934506f5f588c3cb64a        3282 source/include/forge/eval_params.hpp
4728d6f2ea37ea8f87f5da13d48848280a65b89e         806 source/include/forge/forge65.hpp
3ff913a473ace1a37677c1553eee8297d7bb369a        4863 source/include/forge/nnue.hpp
8765fcf1538dde830fb82d240118d7a5f31c04e3       15525 source/include/forge/nnue_v3.hpp
6e1ce1f01ee6a0310b403d7d3c263db49bb5814b       33146 source/include/forge/search.hpp
1a287fc1a3e1413f7154f976478c6cd4d5827495        1982 source/include/forge/tm_finish.hpp
c5509165d096a7e5e0f0f6f1425381ce286ad487        2880 source/include/forge/tm_node_share.hpp
f7f7e6f467ee86bffc591afe850e99756288a92f         262 source/include/forge/uci.hpp
6d29c5df25d2ac0fb14653eb88e0dd670663f89b        1847 source/include/forge/uci_clock.hpp
b0e4c1e6efb41c3d3dab781d033b5a92922aab60         162 source/include/forge/uci_output.hpp
fea4808843c40380e940c8c79ac6702c0668de79        8791 source/src/bitboard.cpp
7716d4826616f025616db157c859de63e78e074a       81283 source/src/board.cpp
5f79f022f65a524dcc5b15059c5e8b33b26f321a        7492 source/src/book.cpp
9b9671eeb47c994e5ef8d6ea91d44bc971986fa3       91623 source/src/book_data.inc
208ab2a00585ac48055fd33ed92293611a04bafb       32752 source/src/eval.cpp
2146b7cf9a5afb0d727728b33bf57c572f79f75e        4168 source/src/eval_params.cpp
6f2634ba788d3624a739304c30611ee0ce13e9c2       23556 source/src/eval_params_table.inc
86c8d491307f4dcc49ad1d52bddab2c3c5caa11d        2268 source/src/forge65.cpp
101df6fdb4dc38b9bd907ba2cd49287f483970ff     9463528 source/src/forge65_net.fnn3
99eb9eb455f8ed199a646dc94fb7fddf3f5ac848       25855 source/src/nnue.cpp
c74bf1e10d24d96d3984db9e8efdff4f5c9ccbc6       50437 source/src/nnue_v3.cpp
c17ccca5f157d07c65eff76aac510a99490c6fcc     1123870 source/src/nnue_weights.inc
1f5703d1c39ae76253e79ce0740ce3a79223726e       18859 source/src/polyglot_keys.inc
620c0c2b39329bac6e0a4b379f64795abebc559b      167417 source/src/search.cpp
eba7f64bf31a7c22dad11d3959de4dad5cf4ee23       62541 source/src/uci.cpp
```

Source subtree SHA `da01f98eb2678383d20dc3b49ed876ee36147f21` (at baseline). Shared source files are not assumed independent of their build flags. Key expected benchmark from baseline README: bench depth 11 226187 nodes, depth 13 616966 nodes when loop options and built-in net are active; perft depth 5 4865609 for different baseline defaults. These are **historical claims in README**, not independently replicated by this pipeline.
