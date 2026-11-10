# PROVENANCE of imported files (byte-exact)

Every file below is byte-identical to the named blob of `opus-r9-spsa` 73eb280a5506ea0d093c4e675984e34fbaccfde9 (checked with `git hash-object` after extraction). The four `spsa/` files are R9's tuner, kept unmodified as the reference implementation; `spsa/opus3_spsa.py` and its modules extend it. The `tests/fixtures/r9/` files are R9's own saved run records, used for replay regression tests; the PGN is R9's saved fastchess smoke output, used for replay parsing tests.

| pack path | source | git blob | sha256 |
|---|---|---|---|
| `spsa/r9_spsa.py` | `73eb280a:opus_r9/tuner/r9_spsa.py` | 74ed44f2b412526a5b094015fa4bbdf7ce607724 | dcedd3790da5b88fa763a1d490d4d5905071b96049b4caef879fd54bf2b8aeab |
| `spsa/r9_spsa_report.py` | `73eb280a:opus_r9/tuner/r9_spsa_report.py` | fb60114c8571701037e4b001ec90299854e2386c | 1dfe80071a23c8ebfd4d3c74e759323b932876017fcc376951352abb5db61485 |
| `spsa/r9_spsa_svg.py` | `73eb280a:opus_r9/tuner/r9_spsa_svg.py` | c25a9941d3fe6b21d87af41e0a29fc88717cad5b | d9748dcfb54f4cc8ec74424711690beceffc7680219b7dec9cb12bfcaeb6cd29 |
| `spsa/test_r9_spsa_sim.py` | `73eb280a:opus_r9/tuner/test_r9_spsa_sim.py` | 6632bd8481731ebbbb1964bbccbdd737168b6e30 | 6356a54f14d3b2c7a6c1d79bd8b406d0b133ede30d8e6e15b4b4e16a27f59dc5 |
| `tests/fixtures/r9/stc_main.json` | `73eb280a:opus_r9/configs/stc_main.json` | 564b9f6b596f717da4fd912bb924c141f0b67a6b | 56060479f12235f41ea5629bb539ac413208370b5aef227c3a0d771925f63c8b |
| `tests/fixtures/r9/stc1_config.json` | `73eb280a:opus_r9/runs/stc1/config.json` | ef8073641e777912a83ae265c41b0319e6d72f21 | 4f5148a4b52b5e9af68358e21b348f73a300f685fb8b6d4cca1c06dee5c40e12 |
| `tests/fixtures/r9/stc1_iterations.jsonl` | `73eb280a:opus_r9/runs/stc1/iterations.jsonl` | c493242c4f33119ffadba7f939a9889e64d5a1e1 | fa1f5c06690a09aaa04ced179e36275316801d59ab3c6cc24a444cfb41567037 |
| `tests/fixtures/r9/sanity3_config.json` | `73eb280a:opus_r9/runs/sanity3/config.json` | 92bb60f3aaa86ead0adcf5f8e7b0d1e2f93a1482 | 5bd26f44e6d6bf56c436f17c21c79957b252938c33e7070a65c6eb907ca80c43 |
| `tests/fixtures/r9/sanity3_iterations.jsonl` | `73eb280a:opus_r9/runs/sanity3/iterations.jsonl` | 7e95ced16c303ac117c1cff30586ad9a4f6e4297 | 7053af55edcb385bffe0a30eeeef85bc89facb7a0eb81ff42a70e35c4bbaf1d1 |
| `tests/fixtures/pgn/r9_fastchess_smoke_2games.pgn` | `73eb280a:opus_r9/logs/fastchess_smoke_2games.pgn` | 96f06423070459e410d402384ae13a702ad8ce4b | 9d781cc945af46427360dc871841a7f2789e33bf0622bbfb666f65912957bf84 |
