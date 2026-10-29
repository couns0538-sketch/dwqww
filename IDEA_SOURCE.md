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

## Astra R2 B1 — protected SmpV2 selection
IDEA_SOURCE: user-requested proven-result preservation; original Forge FB2-J5 (`bf6839e9e65108db76f028532dc15f9587a41fe7`) helper diversification, adapted to the bundle snapshot. No code or tuned constants copied from another engine.
