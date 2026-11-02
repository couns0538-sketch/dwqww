---
name: eval-exact-simd-port
description: Use when porting or reviewing Forge evaluation to SIMD, AVX2, AVX-512 or VNNI, changing NNUE accumulator arithmetic or refresh paths, or qualifying an exact evaluation optimization against the pinned fens12k suite before benchmarking.
---

# Eval Exact SIMD Port

Establish bit-identical evaluation on the exact current fens12k **before collecting any timing**. A rounded UCI centipawn score is insufficient for float evaluation. Use existing `cpp-chess-engineering` arithmetic guidance. Exact SIMD work must retain ON as well as OFF search identity when that is the reviewed contract; **do not force an ON bench difference**. The strict ON-different `forge-lock-proof-set` is for behavior-changing gates, so use the crew-reviewed exact-identity qualification protocol for this port before timing.

1. Recover the accepted source/net and authoritative fens12k path plus independently supplied SHA-256. Do not substitute another 12k file, a sliced/truncated suite or a newer branch name. Record compiler, ISA flags and scalar/candidate executable hashes. Freeze inputs; no live network replacement. Confirm the Windows CPU supports the selected instruction set.
2. Inspect the actual eval entry points and write or reuse a native probe adapter. Compare the same full engine evaluation boundary, including residual HCE, scaling and accumulator state where applicable. Emit exact IEEE bit patterns or exact quantized integer bits, never rounded cp. Match source/net/features/options and arithmetic order. Preserve no-FMA/no-fast-math requirements.
3. Prove integer bounds across every supported net and transient update order. VNNI operand signedness, dot-product accumulation width, clipping and saturation require explicit checks. Sampling is not an overflow proof. Compare fresh versus incremental refresh, make/unmake and scalar versus every enabled path, including king buckets, promotions, en passant and castling.
4. Run all 12,000 FENs in order on scalar and candidate paths. Bind each trace header to the actual executable/net/options/suite hashes and every row to its index and full six-field FEN hash. Capture a native implementation marker/counter showing the candidate path executed for all evaluations. Preserve original adapter transcripts, exit statuses and source hashes. A flag alone does not demonstrate SIMD execution.
5. In an isolated copy of the frozen net, change exactly one identified weight, capture its tensor/index/byte range, and rerun the probe. Its trace must produce an actual mismatch. Preserve this negative control; never alter the accepted network. A changed header or unrelated byte is not a weight test.
6. Run the bundled checker and review its original native evidence. Missing/malformed rows, changed hashes, inactive candidate, nonfinite float outputs or any bit mismatch block timing. Report FAIL or UNVERIFIED with the first mismatch. A clean fixture test is not native fens12k qualification.

PowerShell, after the probe adapter has produced the record described in [record-format.md](record-format.md):

```powershell
python "$SkillDir\scripts\check_eval_parity.py" "$RunDir\eval-parity.json"
if ($LASTEXITCODE -ne 0) { throw 'Exact evaluation gate failed; do not time this candidate.' }
```

Set `$SkillDir` to this installed skill directory and `$RunDir` to a new approved evidence directory. Invoke `grok-pc-safe-run` for any native work on that PC. The checker reads files only; it does not run the probe or verify hardware activity. Only after trace/hash checks **and native evidence review** pass may `abba-nps-timing` begin. Publish raw traces, input hashes, counter evidence and 0/12000 mismatch count with scope; claim no Elo.

## Multi-component and embedded-weight probes

Use `encoding: "components-v1"` with ordered named component encodings when the exact boundary includes multiple raw lane/output values and integer evaluation components. Every component is mandatory and float components must be finite. Every root row also records zero OFF activation or one ON activation; the checker validates these values in addition to the total counter.

For embedded weights, explicitly select `network_storage: "embedded"` and supply a complete documented weight image, hash-bound source/build provenance and the separate negative-control binary. The checker compares the negative trace against the good OFF trace and requires the negative binary hash to differ. It does not infer the compiler's source consumption; original compile commands, source manifests and native invocation evidence must be reviewed. External-network records retain their original requirement that the negative run use the candidate binary. See the expanded [record format](record-format.md).
