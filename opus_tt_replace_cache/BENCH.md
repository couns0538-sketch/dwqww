# TtReplaceCache - builds and pins (2026-11-06 17:00-17:07 PC clock)

## Builds
- **Recipe:** `build_variants.ps1 -Variant lp_v1 -Twice -Work D:\opus_5h\tt_replace_cache\builds`. This is the QA kit
  v2.3 LTO+PGO recipe, workload v1.
- **Trees:** made by `tools/port_controls.sh` from `D:\opus_5h\tt_replace_cache\src\trc` (= the patch on trial_w6). The
  six lock switches are flipped in the source.

| build | macro | pc1 sha256 | pc2 sha256 | result |
|---|---|---|---|---|
| identity `trc_id` | FORGE_SPD_TT_REPLACE_CACHE 0, no new UCI | 4181a5893f15e732... | 4181a5893f15e732... | **= live lock trial_w6 byte for byte** |
| gate `trc_gate` | FORGE_SPD_TT_REPLACE_CACHE 1, UCI `TtReplaceCache` spin 0-1 default 0 | ec1cb55e5220991b... | ec1cb55e5220991b... | pc1 = pc2 |

- **Gate exe:** `D:\opus_5h\tt_replace_cache\pack\forge_tt_replace_cache_gate_ec1cb55e.exe`, sha256
  ec1cb55e5220991ba19727cc79e883a0e2c878d8b1b6ba506c316537ac153361.
- **Preprocessor identity:** `tools/pp_identity.sh` at macro 0 gives IDENTICAL for all 8 units.
- **Compile check:** macro 1 compiles warning-free (-Wall -Wextra) in both TT paths (FORGE_SPD_TT_NOTLS 1 and 0).

## Gate exe nodes (pin_check full, Idle, mask 0x3; net off by UCI pipe)
| bench | lock pin net on | gate OFF | gate ON `TtReplaceCache=1` | lock pin net off | gate OFF net off | gate ON net off |
|---|---|---|---|---|---|---|
| d11 | 312866 | 312866 | 312866 | 375354 | 375354 | 375354 |
| d13 | 862329 | 862329 | 862329 | 907205 | 907205 | 907205 |
| d16 | 3024920 | 3024920 | 3024920 | 2448617 | 2448617 | 2448617 |
| d20 | 12389307 | 12389307 | 12389307 | 13573040 | 13573040 | 13573040 |
| d22 | 34048354 | 34048354 | 34048354 | 24506465 | 24506465 | 24506465 |

- **Perft 5:** startpos 4865609 and kiwipete 193690690 match the pins with the option OFF and ON.
- **The option is advertised, and `value 2` is refused** ("info string invalid value for option TtReplaceCache").
- **ON is node-identical to the identity / lock path** at every bench depth, net on and net off. This is the expected
  result: the selection is the same.
  - The forge-uci pin_check "on-line" mode says FAIL "dead option" for exactly this reason. Its rule is for options that
    should change nodes, so here that verdict is the expected outcome, not a defect.
- **Not shown:** that the ON branch actually runs. Nodes cannot show it, and there was no counter build. The code reads
  `tt_replace_cache` only in the two new branches.
- **No speed claim.** QA owns any quiet ABBA of ON vs OFF / trial_w6.
