# IDEA_SOURCE — fc_nnue_h256_e12_ep12_ep10base  (REAL H256 net on the locked ep10 source base; UNPROVEN)

Forge 6.4.24 (1ab50b2d), same source as the locked ep10 tree `/workspace/forge-coder/fc_nnue_ep10_1ab50b2d` (net-a md5 da65098c…). The ONLY source change is `src/nnue_weights.inc`, replaced by Engine NNUE's own trained H256 residual net:
- file: /workspace/chess-tools/nnue/forge_resid/resid_h256_e12_e_ep12.inc ("run e", epoch 12)
- md5: 6d22f612c855e17c62d396d32da99ea4  sha256: 74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b  (size 1126753 bytes, stable)
- Engine NNUE reported export parity 10000/10000 exact with HID=256.
- Replaced baseline (ep10 tree) nnue_weights.inc: md5 da65098ce0612b7f18706547b0a57c84

Build configuration (not a source change): `-DFORGE_NNUE_HIDDEN=256` in CMAKE_CXX_FLAGS (macro default is 128; it must reach every translation unit). The .inc carries FORGE_NNUE_RESIDUAL 1 and static_asserts (InputCount 768, HiddenSize 256, SigmoidK 2.25, WeightScale/OutputScale 4096).

Idea source: our own NNUE training (Engine NNUE, train_resid.py): residual 768 -> 256x2 SCReLU on Forge's own self-play data. No code, tables, tuned constants or comments from any other engine or project; no source code written for this build (no source edit at all). The net's holdout-loss numbers (teacher 0.004679, b0.6 0.014534 vs ep10 0.004701 / 0.014740) are Engine NNUE's claims, not verified here and NOT strength evidence.

Status: UNPROVEN. No Elo/strength claim. Only games (1000-game SPRT run by QA, no pooling) can decide.

## Open provenance item (carried over unchanged from fc_nnue_ep10_1ab50b2d/IDEA_SOURCE.md)
- /workspace/chess-tools/nnue/forge_resid/train_resid.py (md5 fe1d12817a250baa86bcbb9362fda3e4) states in its header: "Own code, derived in structure from the supplied train_nnue.py (md5 5A161C70...)". NETS.md line 1187 repeats this.
- The supplied train_nnue.py (md5 5a161c70bb8b7675ba56c916947f546a, sha256 cb8fa7b6a1654022a6d62c162994800d4672b54b5b6cc8e454370c8514f5a22a) is identical in three places: chess-tools/nnue/forge_datagen_pkg/unzipped/forge-nnue-tools/, the PC preserve copy (pc_preserve_20261023/extracted/tier2/grok-pc/nnue/forge-nnue-tools/) and the zip 3feee8758e49....zip. It belongs to a "forge-nnue-tools" bundle targeting Forge's own 768 SCReLU format.
- What the evidence does NOT show: the bundle has no author line, copyright header, SPDX tag or LICENSE file; no record on the box says who wrote it or under what terms it was supplied. A later revision exists at chess-tools/nnue/chatgpt_kit/forge-nnue-tools-grok/ (train_nnue.py md5 921c6e004c40be7997ae7882f97cce2c, also no licence file). It imports only generic libraries (python-chess, numpy, PyTorch, stdlib) and references no other engine's trainer. Author and licence of train_nnue.py: could not be determined from the box. The Forge repo (1ab50b2d) carries an MIT LICENSE ("Copyright (c) 2026 OpenAI"), but nothing ties the supplied bundle to it.
- Conclusion: the net weights come from our own training run; the trainer is our derivative of a user-supplied script of undetermined authorship/licence. Open provenance item for CR/Couns; no code from other chess engines was identified, but this was not verified line by line.

## Provenance note (QA, 2026-10-24 ~10:00 Vienna, recorded at lock)
- CORRECTED 2026-10-24 10:04 Vienna (QA, after Coder check): tools/nnue/train_nnue.py has NO MIT, copyright or SPDX header in any box copy (md5 5a161c70, 921c6e00, 483e7b2c). The "Copyright (c) 2026 OpenAI" MIT text is only in the Forge repo LICENSE. e12 was trained with train_resid_v2.py (md5 7640ffe6), derived from train_nnue.py. The trainer is a training-side tool, not compiled into the Forge binary. Authorship and licence of train_nnue.py are still undetermined, as above. The 8-0 lock vote (09:46) stands, recorded on this corrected basis.
- Engine NNUE reports that the e12 net was trained with train_resid_v2.py (not verified here by QA).
- h256_e12 was LOCKED 2026-10-24 09:46 Vienna by crew vote 8-0 (Couns delegated). See /workspace/forge-hashes/LOCK_CHECK_h256_e12.md.
- 2026-10-24 10:05 Vienna (QA): git log --follow for tools/nnue/train_nnue.py and tools/nnue/train_resid_v2.py in the box clone of couns0538-sketch/dwqww (/workspace/forge-sol-teacher/repo) shows no history, and neither file is tracked. So the repo MIT LICENSE does not cover them for now, and their licence is unknown. This matters only if the trainer is ever published; the weights are unaffected. A remote fetch was not re-run this time.

## Appended 2026-10-25 (QA merge): buffix = h256_e12 + Sol bad-capture buffer fix (b425207a buffer_only.patch code hunks)
- Bug fix from Sol commit b425207a (forge/sol-next-20261024), applied as buffer_only.patch only (sha256 32967232…, md5 5b7bf5c8), minus its IDEA_SOURCE.md hunk. This file was written by hand by Coder.
- What: MovePicker `bad_captures_` (deferred SEE-losing captures) goes from `std::array<Move,64>` to `std::array<Move,MoveList::Capacity>` (256), plus a `static_assert` that the deferred buffer holds the full generated noisy list. A new ctest (tests/bad_capture_tests.cpp) and its CMakeLists entry come with it.
- Why: the GoodCaptures stage writes `bad_captures_[bad_count_++]` with no bound, so a node with more than 64 SEE-losing captures would write past the array (UB). Not shown reachable from legal play (QA fixtures max 50). This is a defensive fix: no behaviour or node change expected, and no speed or Elo claim.
- Idea origin: QA REVIEW_3afd230 finding 3 and Couns's prompt to Sol. Sol is an AI model; Couns ruled Sol's work usable (2026-10-24). Ideas only: no code, tables or constants from any other engine. No license text, and none of Sol's README/AGENTS/.agents/SOURCE_MANIFEST/FORGE_* flag files or source zips were used.
- Status: UNPROVEN. CR_PASS (forge-hashes/CR_PASS_sol_buffix_b425207a.txt) covers buffer_only.patch only.
- Merged by QA per CR LOW finding: the lock text above is kept unchanged; this section is appended. Patch fc_sol_buffix_h256e12_vs_lock.patch sha256 9ce56b3d9b5291e450679209ac991c4d560bf40f64aa0281492c53ad37d96a5c; src/search.cpp md5 9553f697fa7bed500f945bc247d70dbf. CR note: forge-hashes/CR_PASS_sol_buffix_h256e12_samediff.txt.
