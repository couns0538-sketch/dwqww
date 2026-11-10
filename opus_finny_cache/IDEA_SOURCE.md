# opus_finny_cache — IDEA_SOURCE

| idea | source | licence | how it is used here |
|---|---|---|---|
| "Finny tables": keep, per (perspective, king bucket), the last accumulator and the board it represents, and refresh by applying the piece difference | Stockfish (described in its source and development history) | GPL-3.0 | **idea only**: no source, constants, tables or weights copied. The SPEC wording and the design in SPEC §3 are this job's own |
| refresh cache keyed (perspective, bucket, flip) with 12 piece bitboards | this repository, branch `fable-nnue-arch` (FB1, `src/nnue_v3.cpp`) | the project's own code | read as prior art for the ownership map; nothing copied into this pack |
| lazy accumulator walk-back + dirty pieces | this repository (parent P `src/search.cpp`, `src/nnue.cpp`) | own code | analysed and measured, not changed |
| exactness of float accumulation with weights int/4096 | arithmetic fact (24-bit float mantissa; values are multiples of 2^-12) | — | SPEC §3.3 exactness rule |

Tools: `tools/o2_uci_lib.ps1` is a re-pathed copy of `opus-speed-20261105@1ad0d295:opus_speed/tools/uci_lib.ps1` (the project's own code, md5 a9c8f6aa…; the header says what changed). `rc_make.ps1`, `rc_measure.ps1`, `run_pinned.ps1` and `kit_build.ps1` are this job's own.
