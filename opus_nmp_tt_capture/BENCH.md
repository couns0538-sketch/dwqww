# NmpTtCaptureMin - numbers

All runs on CPUs 0-1 at Idle (tools pin themselves). Pins = the live lock trial_w6 4181A589 (net-on bench
312866 / 862329 / 3024920 / 12389307 / 34048354; net-off 375354 / 907205 / 2448617 / 13573040 / 24506465; perft 5
startpos 4865609, kiwipete 193690690).

## Identity build (macro FORGE_NMP_TT_CAPTURE_MIN = 0, tree `ntc_id`)
| check | result |
|---|---|
| exe sha256 | 4181a5893f15e732d08a2f4fcfbaffb23618b2567b9f30f9acd58be2e69b6fb0 = trial_w6, `cmp` byte-identical |
| build quick pins | 312866 / 862329 / 3024920 OK |
| bitexact_check -Quick -SkipSan vs trial_w6 (`logs/bx_id.log`) | **BIT-EXACT** L1-L3: net on + off d11-d22 = pins, perft 5 startpos + kiwipete = pins, 2,000 / 2,000 FENs identical at depth 13 |

## Gate build (macro = 1, tree `ntc_gate`), runtime NmpTtCaptureMin = 0, NmpTtCaptureSee = 0 (defaults)
| check | result |
|---|---|
| exe sha256 (pc1 = pc2) | 1c6e105ee74ff31b1343307b320dc88b48cef6faa2879bdf97f9be43c3feaa87 |
| advertised (MCP pin_check) | `NmpTtCaptureMin type spin default 0 min 0 max 5`, `NmpTtCaptureSee type spin default 0 min 0 max 900` |
| build quick pins | 312866 / 862329 / 3024920 OK |
| bitexact_check -Quick -SkipSan vs trial_w6 (`logs/bx_gate_off.log`, started 03:39:50) | **BIT-EXACT** L1-L3: net on + off d11-d22 = pins, perft = pins, 2,000 / 2,000 FENs identical -> runtime defaults = the lock path |

## Gate build, runtime NmpTtCaptureMin = 4, NmpTtCaptureSee = 0 (the gate ON line, form A)
MCP `pin_check -Full NmpTtCaptureMin=4;NmpTtCaptureSee=0`, 2026-11-06 03:39:47-03:40:22, priority Idle, mask 0x3:
verdict **LIVE**.

| bench (net on) | ON nodes | OFF = lock pin | ON / OFF |
|---|---|---|---|
| d11 | 329842 | 312866 | 1.054 |
| d13 | **936622** | 862329 | 1.086 |
| d16 | 3034926 | 3024920 | 1.003 |
| d20 | 12816428 | 12389307 | 1.034 |
| d22 | 34919651 | 34048354 | 1.026 |

- perft 5: startpos 4865609 and kiwipete 193690690, both = the pins.
- d13 != 862329, so the term is wired and live.
- Fewer null moves give slightly more nodes at every depth (1.00-1.09x). Bench totals are no strength evidence.
- Variant B (NmpTtCaptureSee 300) ON bench, net-off ON benches and the counter box tests (null_tries_ / null_cutoffs_
  per 1M nodes) were not run (not in this brief).
