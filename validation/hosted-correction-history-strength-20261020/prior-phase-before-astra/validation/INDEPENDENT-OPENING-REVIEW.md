# Independent opening audit

PASS for the frozen 4 A/A plus 256 SPRT opening pairs. Selector seed is
`20261020-correction-history-v1`; runtime CLI seed is `20261026`. The selection
SHA256 is `8aec235d2c9c4fbcea8914c73ae20b5e696c27f11236eabd6f755c2e42a3cca6`.

The checker legally replayed exactly the 260 selected original book games and
visited the other games with `skip_game`. It performed no new full-corpus legal
replay. The byte-identical verified cache retains the prior 34,700-game replay,
31,603 strict EP-none positions, and SHA256
`42735af2eb7ef9a43695de69b256e519075e3a30ef6a565febcabf0abd2bdcff`.

All 88 historical source hashes, the original 42 registries, and 15,408
reconstructed historical keys were checked. Entire reserved NNUE/TT cohorts
(1,028 positions each) and unused candidate15/16/17 cohorts (132 each) are
excluded. Excluding 2,452 original-book positions leaves 29,151 eligible
positions. Independent deterministic selection and both runtime opening orders
match the frozen files. All 101 consumed inputs retained their original hashes.

`opening-check.json` reports PASS; `opening-check.stderr` is empty. Checker SHA256:
`f8c1beecb33d7b94c6e06a967ee6de60f43d64e94005217caa36adfc385f3875`.
Report SHA256:
`efbc9e20d9b205408fb15d6402729d37d178be2f5406314707d278e412aa4201`.

No engines, builds, benchmarks, matches, network, Git mutations, or frozen-input
edits were performed. This audits opening inputs only; candidate18 source,
benchmark, correctness, launch, and strength gates remain separate.
