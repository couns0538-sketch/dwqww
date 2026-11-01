# Frozen exact-evaluation record

`python scripts/check_eval_parity.py RECORD.json` uses Python3.10+ stdlib, reads nominated files and prints JSON. Exit0/PASS means the artifact-bound trace contract passed; exit1/FAIL means demonstrated evidence inconsistency/parity failure; exit2/INVALID means malformed or incomplete record. No files, processes or timings are created.

Top-level schema1:

- `schema`: integer1; `encoding`: `f32-bits`, `f64-bits` or `i32-bits`.
- `candidate_path`: object with native implementation `name` and integer `active_evaluations >= 12000` from the original probe's actual counter. A declared value cannot authenticate execution; review the native log and adapter source.
- `fens`, `scalar_binary`, `candidate_binary`, `network`, `scalar_options`, `candidate_options`, `native_log`, `scalar_trace`, `candidate_trace`: each a reference `{"path":"relative/file","sha256":"64 hexadecimal characters"}`. Paths resolve relative to RECORD.json, use forward slashes and may include `../` only for explicitly authorized inputs. No absolute/drive/UNC paths.
- `negative_control`: `network` and `trace` references; `tensor` nonempty name; `offset` nonnegative byte offset; `width`1/2/4/8. The net length must match, bytes must actually differ and every differing byte must lie within that single range. Confirm through the real net schema that it identifies one weight, not a header or metadata. The helper cannot infer a native architecture's tensor layout.

FEN file: UTF-8, exactly12,000 lines, each full six-field FEN. CRLF/LF line terminators are excluded from each row hash; the whole-file SHA includes original bytes. Other whitespace is not normalized. The checker verifies six fields and hash/order, not legal chess semantics. The native probe must parse and validate every FEN successfully. Supplied authoritative file SHA is a prerequisite; count alone does not identify the accepted suite.

Each JSONL trace begins with a header object containing `schema:1`, `kind:"eval-trace"`, `encoding`, `implementation`, `binary_sha256`, `network_sha256`, `fens_sha256` and `options_sha256`. The scalar header's implementation is `scalar`; candidate and negative-control use `candidate_path.name`. Bind scalar/candidate executable and options to their respective record references. The negative-control header binds the **candidate executable, candidate options and corrupted network**. All headers bind the exact fens file SHA. Native adapters must obtain these identities from the files they actually used, rather than inserting hashes from a later rebuild. Swapping the recorded binary while retaining an older trace is rejected.

Options references contain the effective accepted configuration frozen for that invocation, including enabled feature, thread/hash settings and relevant evaluation mode. The helper binds their bytes but does not interpret UCI option semantics.

After its header, each JSONL trace row:

```json
{"row":0,"fen_sha256":"full SHA-256 of UTF-8 FEN without newline","eval_bits":"3f800000"}
```

`row` is consecutive zero-based integer. `eval_bits` has exactly8 hex digits for f32/i32 or16 for f64, representing one documented full-evaluation scalar. Floating NaN/infinity encodings are rejected; signed zero remains bit-distinct. If the real evaluator produces multiple components or multiple output scalars, extend the adapter/checker with tests instead of dropping components silently. Emit the accepted full-evaluation boundary, not an unrepresentative internal subtotal.

Scalar, candidate and negative-control traces each contain exactly12,000 rows with identical FEN IDs/order. Positive scalar/candidate bits must match everywhere; negative control must differ at least once. Hashes are checked before and after validation. This is ordinary immutable-artifact checking, not a defense against all malicious concurrent rewrites.

No runtime setting or existing binary format is guessed. Before writing the adapter, inspect the exact current Forge probe and loader. Unsupported native output/ISA or missing fens12k means UNVERIFIED; preserve the blocker and complete independent static tests. Never produce fabricated traces to satisfy this schema.

Structured evidence is limited to 32 MiB per file. The helper hashes the exact bytes it parses, with file identity checked across the read; initial/final separate hash checks alone are not trusted. This rejects transient rewrite-and-restore substitution. Network negative-control comparisons also hash their consumed bytes.
