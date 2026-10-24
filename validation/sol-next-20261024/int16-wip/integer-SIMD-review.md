# Integer NNUE emitted-code review

**PASS: required integer SIMD operations and groupwise signed widening are
present; FMA count is zero across all 18 `forge::nnue::*` function symbols.**
This is a static review of the existing complete disassembly. No compiler,
objdump, engine, benchmark or input generator was run.

Binary SHA256:
`61f3753f8f66ec5b9ee2d43d0f3156b3bc1fedf32fc7da46582354a04c49e509`.
Disassembly SHA256:
`c605a3ff6abe3b5c1a6a82df11cc26e862590b565e3288fa5e2eb21fb09efe4e`.
Both match the existing `int16-FMA/forge.receipt.json` before/after bindings.

Actual kernel: `forge::nnue::int16_detail::evaluate_integer(...)`, symbol
interval `[0x41bc70,0x41bde0)`, disassembly line 28012.

| Static instruction | Count | Addresses |
| --- | ---: | --- |
| `vpmulhrsw` | 2 | `41bcf7`, `41bd17` |
| `vpmaddwd` | 2 | `41bcfc`, `41bd1c` |
| `vpmovsxdq` | 2 | `41bd29`, `41bd35` |
| `vpaddq` | 5 | `41bd3a`, `41bd3e`, `41bd4a`, `41bd55`, `41bd66` |

The sole `vpaddd` (`41bd25`) combines the current group's two perspectives.
Both halves are sign-extended before the loop-carried 64-bit additions at
`41bd3a/41bd3e`. The back edge at `41bd48` returns to `41bce0`. Final horizontal
addition uses `vpaddq`, followed by `vmovq` into 64-bit RAX (`41bd6a`) and
64-bit integer-to-double conversion (`41bd73`). There is no final int32
horizontal reduction. Source `src/nnue_int16.inc:123–141` agrees.

Public `forge::nnue::evaluate(...)` occupies `[0x41d190,0x41d340)`. Its flag
test at `41d1a5` takes the float body when zero and otherwise tail-jumps at
`41d1b6` to the integer kernel. The kernel is separately emitted, not inlined
into the public symbol. Thus a checker requiring the integer instructions
directly inside the public float/integer dispatcher would misclassify this
runtime design.

All 18 anchored NNUE symbols, including cold/partial clones, contain zero FMA.
The whole binary's 46 FMA instructions belong to the two libm log symbols,
matching the original receipt; none belong to Forge NNUE.

Source hashes match `int16-agent/SCRATCH_SOURCE_SHA256.json`:

- `src/nnue_int16.inc`: `38ef63379551c8bee318a93a6aaccd56cf4369b530dcd89093082af40a3279fc`
- `src/nnue.cpp`: `735f01df92331342305d1d87f77fec217218615b3e664e5453708b96ba7bc946`
- Network: `74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b`

The existing bound analysis gives at most 247,578,624 in magnitude per full
16-unit group, within int32. The full positive bound is 2,510,422,016, beyond
int32; widening before the cross-group/final sum addresses that design limit.
No speed or Elo conclusion follows. This YMM integer-kernel review also does
not qualify a combined AVX-512 profile.

`INT16-SIMD-REVIEW.json` retains every NNUE symbol range, exact instruction
rows, source/receipt hashes and bounds references. Symbol intervals use the
next disassembly header and may include alignment padding. An independent
read-only reviewer confirmed the counts, dispatch and widening sequence.
