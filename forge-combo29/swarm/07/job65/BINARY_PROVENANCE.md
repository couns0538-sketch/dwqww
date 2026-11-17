# BINARY PROVENANCE for this seat's jobs (raises 20-S-F63's rule against my own record)

Every behavioural number this seat produced came from one of these two executables.
Recorded 2026-11-17 (date -u in stamps.txt), after seat 20's S-F63 pointed out that a
citation of settings without a binary is half a citation.

## base 6b98f217 (no options beyond Hash/Threads/OwnBook as stated per job)
```
e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83  /agent/repos/base/forge-combo29/build-rel/forge
id name Chess Engine Forge 6.4.24 candidate
id author OpenAI
```

## PC r15 (base + pc_r15.patch sha256 d6bd72c5..., -DFORGE_MATE_ALPHA_GUARD=1)
```
068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4  /agent/repos/pcbase/forge-combo29/build-pc/forge
id name Chess Engine Forge 6.4.24 candidate
id author OpenAI
```

## Other executables this seat used, for completeness
```
775fb0f61e6ce73f602ce6635255e93c09f6c0764f018289c849e9e80db016e0  /tmp/mirord/build2/forge          (07-C74: mirror-order, -DFORGE_EXPERIMENT_MIRROR_ORDER=1)
2db028fa9ade74d7c80110d6ab23c73bd06e43333305a10ec32615682b345939  /tmp/sharedv2/build/forge         (07-C78 v2)
2db028fa9ade74d7c80110d6ab23c73bd06e43333305a10ec32615682b345939  /tmp/revcheck/forge-combo29/build/forge   (07-C79 clean rebuild, byte-identical)
2db028fa9ade74d7c80110d6ab23c73bd06e43333305a10ec32615682b345939  /tmp/v3final/forge-combo29/build/forge    (07-C79)
2db028fa9ade74d7c80110d6ab23c73bd06e43333305a10ec32615682b345939  /tmp/vfinal/forge-combo29/build/forge     (third independent clean build)
96eda98a7ea046e42802175c12ee7d621854d66f26599ae93e072c5560f5aa01  /tmp/sharedverify/build/forge     (07-F1 patch v1, superseded)
70892782538b24fb57dfb4cbc95d7e308990f4bebb54315d03837b0f0fb4db5c  /tmp/patched/build-rel/forge
378c1d9c8662a6f8f10c0783e390a370d991cb950a57dc845453e4ebb4ec01ef  /tmp/pcverify/build-pc/forge
96eda98a7ea046e42802175c12ee7d621854d66f26599ae93e072c5560f5aa01  /tmp/sharedverify/build/forge
95e438941b51b6fb33f78151a9617039a7c933daad262a9b87ce73409bf6e3e4  /tmp/hl_off/build/forge
f4d44fb5ee9f781a5ac76205a3f120015b6e1029e4a719432fec83f357dffd2d  /tmp/var_ROOT_DRAWN/build-pc/forge
62a7efad06366a60124b0081a2c072e31136c2e54d8eda63dd35f7bef06897be  /tmp/var_HARD_LIMIT_EMERGENCY/build-pc/forge
32e178667f0e92c7319aec4dda751adf62f84a677ccb13ceed6a2da8bb479e24  /tmp/var_BARE_KING_LMR_CAP/build-pc/forge
```

## The 07-F1 deliverable's binary (added at the final consistency pass)

The recommended patch, `job73/07f1_shared_report_v3.patch.txt`, produces
`2db028fa9ade74d7c80110d6ab23c73bd06e43333305a10ec32615682b345939` — and it produced that
**same hash from three independent clean checkouts** (`/tmp/revcheck`, `/tmp/v3final`,
`/tmp/vfinal`), each from a fresh copy of PC r15 with the patch applied by
`patch -p1 --fuzz=0` and built from scratch with g++-13. That is the point of the check: the
patch alone determines the binary, so the eight pin results and the seven zero-node-path
results are reproducible by anyone with the patch and the base commit, without any of my
scratch trees.
