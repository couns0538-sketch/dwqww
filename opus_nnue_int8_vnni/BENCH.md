# NnueInt8Vnni - builds, pins, ON nodes (step 2e, 2026-11-06 17:00-17:04 PC clock)

**UNPROVEN. No Elo claim and no speed claim.** ON changes eval and nodes, so it needs an SPRT. QA queues it after Code
Review; nothing was queued here.

## Builds
- **Recipe:** `build_variants.ps1 -Variant lp_v1 -Twice -Work D:\opus_5h\int8_vnni\builds`. This is the QA kit v2.3
  LTO+PGO recipe, workload v1, with g++ 15.2.0 and -march=znver5.
- **Trees:** made by `tools/port_controls.sh` from `D:\opus_5h\int8_vnni\src\int8v2` (= the patch on trial_w6). The six
  lock switches are flipped in the source.

| build | macro | pc1 sha256 | pc2 sha256 | result |
|---|---|---|---|---|
| identity `int8v2_id` | FORGE_NNUE_INT8_VNNI 0, no new UCI | 4181a5893f15e732... | 4181a5893f15e732... | **= live lock trial_w6 byte for byte** (also for the 2b source `int8_id`) |
| gate `int8v2_gate` | FORGE_NNUE_INT8_VNNI 1, UCI `NnueInt8Vnni` spin 0-1 default 0 | 81741f2b0f5ae1be... | 81741f2b0f5ae1be... | pc1 = pc2 |

- **Gate exe:** `D:\opus_5h\int8_vnni\pack\forge_nnue_int8_vnni_gate_81741f2b.exe`, sha256
  81741f2b0f5ae1be2e8647f2f886e0bcaa800108cc7f1c3b929f8167296d06a3.

## Gate exe nodes (forge-uci pin_check, Idle, mask 0x3; net-off by UCI pipe, affinity 0xF Idle)

| bench | lock pin (net on) | gate OFF (default) | gate ON `NnueInt8Vnni=1` | lock pin (net off) | gate OFF net off |
|---|---|---|---|---|---|
| d11 | 312866 | 312866 | 326976 | 375354 | 375354 |
| d13 | 862329 | 862329 | **760289** (!= 862329: live) | 907205 | 907205 |
| d16 | 3024920 | 3024920 | 3282449 | 2448617 | 2448617 |
| d20 | 12389307 | 12389307 | 11638305 | 13573040 | 13573040 |
| d22 | 34048354 | 34048354 | 27267033 | 24506465 | 24506465 |

- **Perft 5:** startpos 4865609 and kiwipete 193690690 match the pins, with the option OFF and ON (pin_check PASS / LIVE).
- **The option has no effect when the net is off:** `NnueInt8Vnni=1` + `UseNNUE=false` gives bench d13 907205, the
  net-off pin.
- **d20 / d22 are recorded honestly.** ON searches fewer nodes there than OFF (-6 % at d20, -20 % at d22). There is no
  node inflation of the kind the int16 pack showed. That says nothing about strength.

## Advisory nps (one process, OFF/ON alternated twice, bench 16; PC not quiet, live trainer on 0xF; NOT an ABBA)
| exe | OFF nps | ON nps | ON / OFF |
|---|---|---|---|
| LTO+PGO gate 81741f2b | 2,309,099 / 2,493,751 | 1,184,571 / 1,198,411 | **about 0.50** |
| plain -O3 build of the same gate tree (0b6622bb) | 2,219,310 / 2,252,360 | 2,061,839 / 2,303,472 | about 0.97 (within the noise) |

- **CR / QA item, blocking a fair SPRT.**
  - Cause: the kit's workload v1 trains the OFF path only, so with `-fprofile-use` GCC treats the int8 code as never
    executed (cold) and optimizes it for size. In the plain build ON runs at OFF's speed, so the kernel itself is not
    slow.
  - Consequence: an SPRT of the LTO+PGO gate exe as built would measure a cold-path exe.
  - The recipe change is QA's call; the kit lines were not changed here. QA can either:
    - build the gate with a workload that also runs `setoption name NnueInt8Vnni value 1` + the same benches; or
    - build it with partial training (`-fprofile-partial-training`, kit v2.4) for the gate exe only. The identity
      build must stay lp_v1 = 4181a589.
- Same lesson as the earlier v2-net path: v2.3 leaves an option-only code path cold.
