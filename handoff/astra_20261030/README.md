# Astra handoff 2026-10-30: where each Forge file lives

Repo: https://github.com/couns0538-sketch/dwqww (PUBLIC). Work branch base: `astra-a1-data` (110f0c4a).

1. Forge lock source AL1_s198: commit 294dbed3a15dfd821aaf9d4edc6e5f62832fd460 ("[BASE] AL1 s198 lock source tree (verbatim)"),
   root tree 480db9286c2e1fccde37ab7e195042c4c02bdbaf, byte-identical to the lock tree. It is an ancestor of astra-a1-data,
   qa-r10v2-fix1 and opus-r11-nnue-pipeline. NNUE code: src/nnue.cpp, include/forge/nnue.hpp.
   Lock exe forge_h256_s198.exe sha256 833C47F3209DCEECF662E8B1D4587435E44702FBD3AB9DDF278A49172D9122B3;
   bench 312866 / 862329 / 3024920 / 12389307 / 34048354.
2. R10 HalfKAv2_hm fix1 loader: branch qa-r10v2-fix1 @ 7f79c34901fdd118bc4bf904f4bcaec4006047c6
   (parent bb6175b1 = opus-r10-halfka head; tree aeab5a36). Files: src/nnue_halfka.cpp, include/forge/nnue_halfka.hpp, docs/OPUS_R10_HALFKA.md.
3. fens_12k: qa-r10v2-fix1:opus_r10/parity/fens_12k.txt (12,000 lines, sha256 c01c0e6a49fb9aaab535058bd7280c33b8735e0f8bd40834f1c029843a75a265).
4. Lock net: 294dbed3:src/nnue_weights.inc (embedded net, md5 22b4b9e2c61b37c0450f13a3a92c19b3 = CURRENT_LOCK net_md5,
   sha256 a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638).
5. Self-play sample: release data-sample-10m-20261030, asset forge_sample_10M.tar.gz
   (shard 003, 10M rows, .pos + .pos.info + .txt; sha256 1d6160dd859740fe617c8dc6c6e6ad8fbcdd0ba40b59ee9cee84342f9202cca5).
   Only one shard is on GitHub; more shards were not uploaded because the repo is public. Layout: see HOLDOUT_LIST.md.
6. QA_ASTRA_A1_20261030.md: this folder.
7. Holdout list: HOLDOUT_LIST.md in this folder.
