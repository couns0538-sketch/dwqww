# IDEA_SOURCE - Opus 30-h job (branch opus-30h-20261103)

All engine code written for this job is own code. No other engine's code, constants, tables or weights are used.

| item | idea source | code source | licence note |
|---|---|---|---|
| A: FORGENN2 v2 net path on the lock tree | Forge's own v2 net design (crew, R3 tree b7c17722 `include/forge/nnue_v2.hpp`, own code) | ported from Forge's own R3 tree | Forge code |
| A: residual target (HCE + net) | Forge's own lock net design (`FORGE_NNUE_RESIDUAL 1`, AL1 s198) | own code | - |
| A: king buckets with horizontal mirroring, output buckets by piece count | general NNUE practice, already in Forge's R3 design (C4 / C5) | own code | - |
| A: trainer `forge-v2-bullet` | own R13/R14 trainer configuration on the bullet trainer library (tool only, never linked into Forge) | own code + a small patch to a private copy of the trainer library (residual base input) | trainer library: MIT, tool only |
| A: holdout scorer, data audit, reader | the crew's S31 holdout metric (b0.6 / b1.0 MSE on holdout 013/014 subset s16) | own code | - |
| B: SPSA tuner | public SPSA literature (Spall); R9's own tuner `opus_r9/tuner/r9_spsa.py` | own code (port of R9) | - |
| B: new tunable options | Forge's own literals in the lock search (R9 list of former literals) | own code | - |
| tools | R13-R15 own tools (fresh_lock, kit wrapper, pin_check, smoke2m, cleanroom_lint, pc_gate, abba) | own code | - |
