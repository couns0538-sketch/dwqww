# FINDINGS — swarm/netfuzz: the v3 net loader on malformed input

**The answer first.** The v3 loader **rejects 53 of 60 mutants** and the 7 that load are
**exactly the 7 that must load**. No mutant is accepted that shouldn't be. **Zero
sanitizer lines** under ASan+UBSan across all 60 hand-built cases and 1,096 swept
header mutations. The one thing it does wrong is **not a corruption bug but a
resource one**: it slurps the whole file into memory *before* it examines a single
header field, so an 8 GiB file costs 8.0 GiB of RSS to refuse.

## Which binary, which hashes

This is a **v3 loader** measurement, and it is **not** the audited default binary.

| what | value |
|---|---|
| option that reaches this loader | `NNUEArch` / `NNUEArchFile` |
| present in a **default** build? | **no** — `NNUEArch_occurrences 0`, `UseNNUE_occurrences 1` |
| why | `FORGE_NNUE_V3` defaults to 0 (`include/forge/nnue.hpp:10-12`) |
| binary fuzzed (release) | `forge` built with `-DFORGE_NNUE_V3=1`, sha256 `a1d0c0254e73776721b96bf1b5c24cf13f375c5675b57bc008f2d26599d3fcb1` |
| binary fuzzed (ASan+UBSan) | `forge` `-DFORGE_NNUE_V3=1 -fsanitize=address,undefined`, sha256 `041f834a64034d910fc5db52f8c60b4e34e2eb502394306f65055c02c4aa9740` |
| loader probe (release) | sha256 `6c22c6abd5b10edab3cd2925b8a1423e11bab8bf4eb89847ddf8b37a9dca53c3` |
| loader probe (ASan+UBSan) | sha256 `70103b04fb2e04b71e1c9aa64a54cf90de85e2ab38f92d01077b3edf1f98133d` |
| test net (the "real net") | `test_v3.fnn3`, 6,309,096 bytes, sha256 `1db8525e4eeb3c4cf425faf89a5dbb7e5aec0a9d00fd7de2c7cd25a7673ffd4a` |
| default-build binary (for the absence claim) | sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83` |

`FORGE_NNUE_V3=1` is the **only** difference between the fuzzed build and the audited
one. The four honesty pins are unchanged on it, so the flag does not move the search.

**So: this work says nothing about the compiled-in (v2) net loader.** That loader was
not touched here; it is a different code path (`src/nnue.cpp`) with a different magic
(`FORGENET`) and its own 2 MB size cap (cited in the slurp section).

## Honesty gate (release build, `-DFORGE_NNUE_V3=1`)

| pin | want | got |
|---|---|---|
| bench 11 | 312,866 | **312,866** |
| bench 13 | 862,329 | **862,329** |
| bench 16 | 3,024,920 | **3,024,920** |
| `go perft 5` | 4,865,609 | **4,865,609** |

All four PASS, and `bench N` was sent **on stdin**, not argv (brief: argv exits 0 and
prints nothing). `evidence/pins-release.log`. The default build was pinned separately
and also matches all four.

## The matrix: 60 mutants, every one derived from the real net

Each mutant differs from the pristine file in **exactly the field under test**.
Header mutants are **re-checksummed**, so the FNV layer cannot be what refuses them —
whatever refuses them is the field guard itself. Only the `ck_*` family and the
single `rechecksummed` case are not resealed, because those are the checksum layer.

| mutant | class | field changed | verdict | loader message | engine | ASan+UBSan lines |
|---|---|---|---|---|---|---|
| `ctrl_pristine` | control | none (pristine file) | loaded | — | loaded | 0 |
| `ctrl_kingmap_permuted` | control | king_bucket_map (in-range permutation) | loaded | — | loaded | 0 |
| `ctrl_outputmap_rotated` | control | output_bucket_map (in-range rotation) | loaded | — | loaded | 0 |
| `ctrl_flags_residual_cleared` | control | flags 2 -> 0 (mirror off) | loaded | — | loaded | 0 |
| `ctrl_weight_inrange` | control | w1[0] 1 -> 2 (checksum resealed) | loaded | — | loaded | 0 |
| `hdr_magic` | header | magic[0] 'F' -> 'X' | **refused** | bad magic (expected FORGENN3) | refused (exit 2) | 0 |
| `hdr_version_4` | header | version 3 -> 4 | **refused** | unsupported version 4 | refused (exit 2) | 0 |
| `hdr_version_0` | header | version 3 -> 0 | **refused** | unsupported version 0 | refused (exit 2) | 0 |
| `hdr_header_bytes_191` | header | header_bytes 192 -> 191 | **refused** | header_bytes must be 192 | refused (exit 2) | 0 |
| `hdr_header_bytes_256` | header | header_bytes 192 -> 256 | **refused** | header_bytes must be 192 | refused (exit 2) | 0 |
| `hdr_inputs_767` | header | inputs 768 -> 767 | **refused** | inputs must be 768 | refused (exit 2) | 0 |
| `hdr_inputs_1536` | header | inputs 768 -> 1536 | **refused** | inputs must be 768 | refused (exit 2) | 0 |
| `hdr_hidden_544` | header | hidden 512 -> 544 (in range, x32, body not resized) | **refused** | file size 6309096 != expected 6703400 | refused (exit 2) | 0 |
| `hdr_hidden_480` | header | hidden 512 -> 480 (in range, x32, body not resized) | **refused** | file size 6309096 != expected 5914792 | refused (exit 2) | 0 |
| `hdr_hidden_1056` | header | hidden 512 -> 1056 (> MaxHidden) | **refused** | hidden must be a multiple of 32 in 32..1024, got 1056 | refused (exit 2) | 0 |
| `hdr_hidden_0` | header | hidden 512 -> 0 (< MinHidden) | **refused** | hidden must be a multiple of 32 in 32..1024, got 0 | refused (exit 2) | 0 |
| `hdr_hidden_500` | header | hidden 512 -> 500 (not a multiple of 32) | **refused** | hidden must be a multiple of 32 in 32..1024, got 500 | refused (exit 2) | 0 |
| `hdr_king_9` | header | king_buckets 8 -> 9 (in range, body not resized) | **refused** | file size 6309096 != expected 7095528 | refused (exit 2) | 0 |
| `hdr_king_1` | header | king_buckets 8 -> 1 (in range, body not resized) | **refused** | file size 6309096 != expected 804072 | refused (exit 2) | 0 |
| `hdr_king_33` | header | king_buckets 8 -> 33 (> MaxKingBuckets) | **refused** | king_buckets must be 1..32, got 33 | refused (exit 2) | 0 |
| `hdr_king_0` | header | king_buckets 8 -> 0 | **refused** | king_buckets must be 1..32, got 0 | refused (exit 2) | 0 |
| `hdr_out_9` | header | output_buckets 8 -> 9 (in range, body not resized) | **refused** | file size 6309096 != expected 6311148 | refused (exit 2) | 0 |
| `hdr_out_17` | header | output_buckets 8 -> 17 (> MaxOutputBuckets) | **refused** | output_buckets must be 1..16, got 17 | refused (exit 2) | 0 |
| `hdr_out_0` | header | output_buckets 8 -> 0 | **refused** | output_buckets must be 1..16, got 0 | refused (exit 2) | 0 |
| `hdr_flags_residual` | header | flags 2 -> 3 (residual + mirror) | loaded | — | refused (exit 2) | 0 |
| `hdr_flags_unknown` | header | flags 2 -> 4 (unknown bit 2) | **refused** | unknown flag bits | refused (exit 2) | 0 |
| `hdr_qa_254` | header | qa 255 -> 254 | **refused** | quantisation must be qa 255 / qb 64 | refused (exit 2) | 0 |
| `hdr_qb_32` | header | qb 64 -> 32 | **refused** | quantisation must be qa 255 / qb 64 | refused (exit 2) | 0 |
| `hdr_scale_0` | header | eval_scale 400 -> 0 | **refused** | eval_scale must be 1..10000 | refused (exit 2) | 0 |
| `hdr_scale_10001` | header | eval_scale 400 -> 10001 (> MaxEvalScale) | **refused** | eval_scale must be 1..10000 | refused (exit 2) | 0 |
| `hdr_reserved_1` | header | reserved[15] 0 -> 1 | **refused** | reserved header bytes must be zero | refused (exit 2) | 0 |
| `hdr_kingmap_oob` | header | king_bucket_map[0] 0 -> 8 (== king_buckets) | **refused** | king_bucket_map entry out of range | refused (exit 2) | 0 |
| `hdr_kingmap_255` | header | king_bucket_map[0] 0 -> 255 | **refused** | king_bucket_map entry out of range | refused (exit 2) | 0 |
| `hdr_outmap_oob` | header | output_bucket_map[0] 0 -> 8 (== output_buckets) | **refused** | output_bucket_map entry out of range | refused (exit 2) | 0 |
| `hdr_outmap_255` | header | output_bucket_map[32] 7 -> 255 | **refused** | output_bucket_map entry out of range | refused (exit 2) | 0 |
| `bomb_max_dims` | bomb | hidden 1024 / king 32 / out 16, body unchanged | **refused** | file size 6309096 != expected 50399496 | refused (exit 2) | 0 |
| `bomb_hidden_max_only` | bomb | hidden 512 -> 1024, king/out unchanged | **refused** | file size 6309096 != expected 12617960 | refused (exit 2) | 0 |
| `bomb_king_max_only` | bomb | king_buckets 8 -> 32, hidden/out unchanged | **refused** | file size 6309096 != expected 25183464 | refused (exit 2) | 0 |
| `bomb_out_max_only` | bomb | output_buckets 8 -> 16, hidden/king unchanged | **refused** | file size 6309096 != expected 6325512 | refused (exit 2) | 0 |
| `ck_flip_w1` | checksum | w1 byte XOR 1 at file/3 | **refused** | checksum mismatch | refused (exit 2) | 0 |
| `ck_flip_b1` | checksum | b1 byte XOR 1 | **refused** | checksum mismatch | refused (exit 2) | 0 |
| `ck_flip_w2` | checksum | w2 byte XOR 1 | **refused** | checksum mismatch | refused (exit 2) | 0 |
| `ck_flip_b2` | checksum | b2 byte XOR 1 | **refused** | checksum mismatch | refused (exit 2) | 0 |
| `ck_flip_scale` | checksum | eval_scale low byte XOR 1 (in range: 400 -> 401) | **refused** | checksum mismatch | refused (exit 2) | 0 |
| `ck_flip_stored` | checksum | stored checksum byte XOR 1 | **refused** | checksum mismatch | refused (exit 2) | 0 |
| `rechecksummed` | adversarial | w1 byte XOR 0xFF at file/3, checksum recomputed | loaded | — | loaded | 0 |
| `tr_zero` | truncation | cut to 0 bytes | **refused** | file too small for a v3 header | refused (exit 2) | 0 |
| `tr_8` | truncation | cut to 8 bytes (magic only) | **refused** | file too small for a v3 header | refused (exit 2) | 0 |
| `tr_191` | truncation | cut to 191 bytes (one short of the header) | **refused** | file too small for a v3 header | refused (exit 2) | 0 |
| `tr_header_192` | truncation | cut at exactly the header length | **refused** | file too small for a v3 header | refused (exit 2) | 0 |
| `tr_200` | truncation | cut at header + 8 bytes | **refused** | file size 200 != expected 6309096 | refused (exit 2) | 0 |
| `tr_w1_start` | truncation | cut at exactly the first weight block (header+w1) | **refused** | file size 6291648 != expected 6309096 | refused (exit 2) | 0 |
| `tr_w1_mid` | truncation | cut mid-w1 (header + w1/2) | **refused** | file size 3145920 != expected 6309096 | refused (exit 2) | 0 |
| `tr_w1_mid_block` | truncation | cut mid-block: b1 cut in half | **refused** | file size 6292160 != expected 6309096 | refused (exit 2) | 0 |
| `tr_w2_mid` | truncation | cut mid-w2 | **refused** | file size 6300864 != expected 6309096 | refused (exit 2) | 0 |
| `tr_b2_mid` | truncation | cut mid-b2 | **refused** | file size 6309064 != expected 6309096 | refused (exit 2) | 0 |
| `tr_drop_checksum` | truncation | cut the last 8 bytes (all weights intact) | **refused** | file size 6309088 != expected 6309096 | refused (exit 2) | 0 |
| `tr_1_short` | truncation | one byte short of complete | **refused** | file size 6309095 != expected 6309096 | refused (exit 2) | 0 |
| `tr_extend_1` | truncation | one byte past complete (appended 0x00) | **refused** | file size 6309097 != expected 6309096 | refused (exit 2) | 0 |
| `tr_extra_block` | truncation | an extra b1 block appended, checksum resealed | **refused** | file size 6310120 != expected 6309096 | refused (exit 2) | 0 |

### Counts by class

| class | mutants | refused | loaded |
|---|---|---|---|
| control | 5 | 0 | 5 |
| header | 30 | 29 | 1 |
| bomb | 4 | 4 | 0 |
| checksum | 6 | 6 | 0 |
| adversarial | 1 | 0 | 1 |
| truncation | 14 | 14 | 0 |
| **total** | **60** | **53** | **7** |

Sanitizer lines across the sanitizer arm on these 60: **0**.

## Class-by-class answer to the four questions

### 1. Header mutants — 29 of 30 refused, the 1 accept is correct

Every header field that must be constant is guarded, and the refusal names it:

| field | mutants | refused | message |
|---|---|---|---|
| magic | 1 | 1 | `bad magic (expected FORGENN3)` |
| version | 2 | 2 | `unsupported version 4` / `unsupported version 0` |
| header_bytes | 2 | 2 | `header_bytes must be 192` |
| inputs | 2 | 2 | `inputs must be 768` |
| hidden | 6 | 6 | `hidden must be a multiple of 32 in 32..1024` / `file size … != expected …` |
| king_buckets | 4 | 4 | `king_buckets must be 1..32` / `file size … != expected …` |
| output_buckets | 3 | 3 | `output_buckets must be 1..16` / `file size … != expected …` |
| flags | 2 | 2 | `unknown flag bits` / (**see below**) |
| qa, qb | 2 | 2 | `quantisation must be qa 255 / qb 64` |
| eval_scale | 2 | 2 | `eval_scale must be 1..10000` |
| reserved | 1 | 1 | `reserved header bytes must be zero` |
| king_bucket_map | 2 | 2 | `king_bucket_map entry out of range` |
| output_bucket_map | 2 | 2 | `output_bucket_map entry out of range` |

**In-range dimension claims are caught by the size check, not by the range check**, and
the message says so: `hdr_hidden_544` (544 is legal, a multiple of 32, in 32..1024) is
refused with `file size 6309096 != expected 6703400`. That is the right way round —
a legal dimension with a body that doesn't match is a size error.

**The one header accept is `hdr_flags_residual` (flags 2 → 3), and it is correct.**
The *loader* accepts a residual net because the format permits the bit; the **UCI layer**
then refuses it and unloads:

```
setoption name NNUEArchFile value …/hdr_flags_residual.fnn3
info string NNUE v3: residual v3 networks are not supported
```

So the refusal is **two-stage and still loud**. My expectation table said "refuse" for
the loader, and that expectation was **wrong** — this is a report of my error, not an
engine defect. The engine-level column is what matters and it says `refused`.

### 2. Truncation at every boundary — 14 of 14 refused

Each cut is at a named structural boundary, not an arbitrary offset:

| cut | bytes | message |
|---|---|---|
| empty | 0 | `file too small for a v3 header` |
| magic only | 8 | `file too small for a v3 header` |
| one short of the header | 191 | `file too small for a v3 header` |
| **exactly the header** | 192 | `file too small for a v3 header` |
| header + 8 | 200 | `file size 200 != expected 6309096` |
| **exactly the first weight block** | 6,291,648 | `file size 6291648 != expected 6309096` |
| **mid-w1** | 3,145,920 | `file size 3145920 != expected 6309096` |
| b1 cut in half | 6,292,160 | `file size 6292160 != expected 6309096` |
| mid-w2 | 6,300,864 | `file size 6300864 != expected 6309096` |
| mid-b2 | 6,309,064 | `file size 6309064 != expected 6309096` |
| **checksum dropped, weights intact** | 6,309,088 | `file size 6309088 != expected 6309096` |
| **one byte short** | 6,309,095 | `file size 6309095 != expected 6309096` |
| one byte long | 6,309,097 | `file size 6309097 != expected 6309096` |
| an extra b1 block, resealed | 6,310,120 | `file size 6310120 != expected 6309096` |

**Nothing reads past the end, and the reason is structural**: the size equality check
runs *before* the weight loops, and it is an `!=`, not a `<`. The loader cannot walk
off the buffer because it has already proved the buffer is exactly the length the
header implies.

Note the last row: a duplicated layer is caught by **size**, not by a layer-count
field. The format has no layer count to lie about — the shape is implied by
`hidden`/`king_buckets`/`output_buckets`, and the length check is what enforces it.

### 3. Oversized dimension claims — 4 of 4 refused, and **no allocation**

This is the decompression-bomb question, and the answer is **the loader validates
against file size before allocating**. Measured with a counting `operator new`, not
inferred:

| mutant | claimed size | file size | allocated by the loader | verdict |
|---|---|---|---|---|
| `bomb_max_dims` (hidden 1024, king 32, out 16) | 50,399,496 | 6,309,096 | **0 for the claim** | `file size 6309096 != expected 50399496` |
| `bomb_hidden_max_only` (hidden 1024) | 12,617,960 | 6,309,096 | **0 for the claim** | `… != expected 12617960` |
| `bomb_king_max_only` (king 32) | — | 6,309,096 | **0 for the claim** | `… != expected …` |
| `bomb_out_max_only` (out 16) | — | 6,309,096 | **0 for the claim** | `… != expected …` |

The proof that the counter is live is the control: the same probe on the pristine net
shows the **6,291,456-byte w1 allocation**, and on a genuinely valid max-dimension net
it shows the **50,331,648-byte** one. So the counter sees the loader's real
allocations, and on the bomb it sees none of the claimed size.

**Amplification is bounded and linear, 2.00×–3.66×** (`evidence/amp.json`):

| file | bytes | accepted | allocated | ratio |
|---|---|---|---|---|
| pristine | 6,309,096 | yes | 23,095,070 | 3.66× |
| valid max dims | 50,399,496 | yes | 184,625,982 | 3.66× |
| any refused file | L | no | ≈2.00 × L | 2.00× |

There is **no claim-driven amplification at all**: memory is a constant multiple of
the *file's* length, never of the header's claim. A bomb of the classic shape cannot
be built from a small file.

**The real resource defect is the slurp, and it is the next section.**

### 4. Sanitizers — 0 lines across every case, with a planted-fault proof

Both sanitizers are **proven live** by deliberate faults compiled and linked exactly
like the loader probe:

```
==3469==ERROR: AddressSanitizer: heap-use-after-free on address 0x502000000010
WRITE of size 1 at 0x502000000010 thread T0
    #0 cmd_plant_asan .../loadprobe.cpp:73
```

```
...loadprobe.cpp:80:18: runtime error: signed integer overflow:
2147483647 + 1 cannot be represented in type 'int'
```

**This cost me two attempts and the reason is worth recording**: my first ASan plant was
a 1-byte heap overrun, and **UBSan's object-size check reported it first**, so the write
never reached ASan's shadow map. An overrun is not a reliable ASan probe in a combined
binary; a use-after-free is, because only ASan's quarantine can see it.

With that proven live: **0 sanitizer lines** on all 60 hand-built mutants (release and
sanitizer arms agree on all 60 verdicts), and **0** on the swept header space, where the
same field/value cases were run through both arms; see the sweep section below.

### 5. The 12th net — it loads, and its checksum is genuinely valid

The one accepted damage case is corruption **plus a recomputed checksum**:

| question | answer |
|---|---|
| does it load? | **yes** — `loaded v3 … max\|w1\| 205 … checksum a1ab778dfa69b9f9` |
| is its checksum state valid? | **yes** — stored `a1ab778dfa69b9f9` == computed `a1ab778dfa69b9f9` |
| what was changed? | w1 byte at offset 2,103,032: `0xCC` → `0x33` (XOR 0xFF) |
| where does that land? | feature **2053** = bucket 2, opponent colour, **bishop**, relative square 5 (f1); lane **284** |
| what does it do to the weights? | `w1[2053][284]` −52 → −205, `max\|w1\|` 64 → 205 |

**FNV-1a detects accident, not intent**, so loading it is correct behaviour, and the
engine accepts it (`info string NNUE v3: loaded v3 …`).

**But "it loads" and "it matters" are different claims**, and I checked the second one
rather than assuming it. The flipped lane **is reachable** by a legal position, and it
**does change an evaluation**:

```
7k/8/3RN3/8/P7/1B6/2Q5/2K2b2 w - - 0 1      (python-chess: valid, 46 legal moves)
  pristine      → 68
  rechecksummed → 94
  restored      → 68     (that one byte put back, checksum resealed)
```

The counterfactual is what makes this a finding rather than a coincidence: restoring
that single byte returns the evaluation to 68 exactly.

**And the first attempt at this measurement was a masked null, which is the trap worth
reporting.** On the small position `7k/8/8/8/8/8/8/2K2b2 w - - 0 1` the lane *is*
reached (accumulator −148 → −301) but **both values are negative and SCReLU clamps
negatives to 0**, so the evaluations agreed at −145. An earlier sweep of 326 positions
found **0** differing evaluations and looked like "the corruption is harmless". It was
not: it was **masked by the clamp**. The fix was to read `w1` and construct a position
whose lane lands positive — which is how `7k/8/3RN3/8/P7/1B6/2Q5/2K2b2` was found.

So: **a checksum-valid corrupted net is silently a different evaluator on real
positions.** Nothing on the wire distinguishes it. That is inherent to FNV-1a and is
not a loader defect — but it is the honest scope of the "corrupt nets are refused"
claim, and it should be stated that way rather than as "nothing loads and produces
garbage".

## What I found that is NOT a corruption bug: the slurp before the check

`load()` reads the **entire file** into a `std::vector` before it looks at the magic:

```287:288:forge-combo29/src/nnue_v3.cpp
    std::vector<std::uint8_t> bytes((std::istreambuf_iterator<char>(in)), std::istreambuf_iterator<char>());
    if (bytes.size() < static_cast<std::size_t>(HeaderBytes) + 8) return fail(error, path + ": file too small for a v3 header");
```

So the cost is bounded by the **file's real length**, which nothing validates, and is
**unbounded** for a source with no length. Measured (`evidence/slurp.json`):

| input | in-process peak RSS (`VmHWM`) | file length | refused |
|---|---|---|---|
| 8 MiB sparse file | 12,316 kB (12.03 MiB, **1.503×** the file) | 8,388,608 bytes | yes |
| 64 MiB sparse file | 69,568 kB (67.94 MiB, **1.062×**) | 67,108,864 bytes | yes |
| 256 MiB sparse file | 266,180 kB (259.94 MiB, **1.015×**) | 268,435,456 bytes | yes |
| 1 GiB sparse file | 1,052,624 kB (1,027.95 MiB, **1.004×**) | 1,073,741,824 bytes | yes |
| 2 GiB sparse file | 2,101,192 kB (2,051.95 MiB, **1.002×**) | 2,147,483,648 bytes | yes |
| 4 GiB sparse file | 4,198,344 kB (4,099.95 MiB, **1.001×**) | 4,294,967,296 bytes | yes |
| **8 GiB sparse file** | **8,390,712 kB (8,194.05 MiB, 1.000×)** | 8,589,934,592 bytes | yes (16 GB box) |
| **`/dev/zero`** (no length) | grew to 1,059,168 kB before the 1 GiB cap killed it | **unbounded** | **no — aborted** |
| `/dev/zero`, ASan arm | grew past 1.1 GB in 20 s, still growing | unbounded | killed at the RSS cap |

Peak RSS tracks the file length at **1.000×–1.004× above 1 GiB**, so the cost is exactly
"the whole file" and nothing less. `peak_rss_kb` is the process's own `VmHWM` read
inside the probe, not an external sample — an earlier 0.25 s sampler reported 0.2 MiB
for the 8 MiB file that the in-process counter saw as 12 MiB, so the sampler is recorded
only as the RSS-cap killer and never as the measurement. My first draft of this table
also converted GiB to "GB" loosely and overstated the 8 GiB case as 8.4 GB; the numbers
above are the evidence file's values with their units.

The refusal is **correct** in every case — the message is right and nothing loads. The
problem is **the order**: it costs L bytes of RAM to refuse an L-byte file, and for a
pipe or `/dev/zero` there is no L to bound it.

**This is a real defect and it is not the one the brief asked about**, so it is
stated separately rather than folded into the matrix. It matters practically because
`NNUEArchFile` is a UCI string a GUI or a config file sets: a wrong path pointing at a
large file — or a FIFO — is enough. **The older loader four files away already caps
this**: `src/nnue.cpp:140-143` refuses any file over 2 MB before reading the body. The
v3 loader has no such cap.

**A fix that is not applied here** (this seat measures, it does not patch): stat the
file, `fail()` on a length outside `[HeaderBytes + 8, file_size_for(MaxHidden, MaxKingBuckets, MaxOutputBuckets)]`,
and only then read. The maximum legal v3 file is 50,399,496 bytes, so the cap is known
at compile time and the check costs one `stat`.

## The swept header space: two runs, and what each covers

Beyond the hand-picked mutants, the header space was swept twice, and the two runs have
**different sizes and different jobs**. Saying "1,819 cases, 0 sanitizer lines" would
merge them and overstate the sanitizer coverage, so they are stated separately:

| run | cases | arms | what it answers |
|---|---|---|---|
| `scripts/header_sweep.py` | **1,819** | release only | does any field value slip past a guard? |
| `scripts/sweep_asan.py` | **1096** | release **and** ASan+UBSan | a superset of fields, a narrower value list, both arms |

Both spread every 4-byte field over 0, 1, boundaries, `INT_MAX`, `UINT_MAX` and negatives,
all re-checksummed, plus the 64 king-map, 33 output-map and 47 reserved bytes.

**Release run (1,819 cases): 0 cases both loaded and evaluated when they should not have.**
**Sanitizer run (1096 cases): 0 sanitizer lines, 0 release/sanitizer verdict disagreements.**
In the sanitizer run (354 of them load, every one legal: 192 king-map and 99 output-map
entries below their bucket count, 47 zero reserved bytes, `flags` 0/1/3, `eval_scale`
1/9999/10000, and the 8 identity values).

Every accept in either space is legal by design and none is a missing guard:

| accepted | count | why it is legal |
|---|---|---|
| identity values | 8 | the pristine value of each field |
| `flags` 0, 1, 3 | 3 | mirror off, residual on, both — all defined bits |
| `eval_scale` 1, 9999, 10000 | 3 | the documented 1..10000 range |
| king-map bytes 0/1/7 | 192 | all `< king_buckets = 8` |
| output-map bytes 0/1/7 | 99 | all `< output_buckets = 8` |
| reserved bytes 0 | 47 | zero, as required |

**No out-of-range bucket entry was accepted** (`8..255` refused for every one of the 97
entries), and **no non-zero reserved byte was accepted** (47 entries × 11 non-zero
values in the release run, all refused).

## What I did not test, and why

- **Threading.** Every load here is single-threaded. `load()` builds a `Net` on the
  stack and publishes it with one `g_net = std::move(net)`, so a concurrent
  `NNUEArchFile` and `go` is a data race on `g_net` — **I did not measure it**, and I
  am not claiming it either way.
- **The residual load path.** `hdr_flags_residual` is unloaded by UCI before any
  evaluation runs, so no residual net ever reached the kernels. Untested.
- **Real corrupt nets from training.** Every mutant is derived from one synthetic test
  net. A net whose *learned* values are out of range in a way my byte-level mutations
  do not produce is not covered.
- **The v2 (`FORGENET`) loader.** Not this seat's subject; it is a separate path with
  its own 2 MB size cap.
- **Allocation failure inside the loader.** I forced it once, via `/dev/zero` and an
  address-space cap, and it aborts with `std::bad_alloc`. I did not test whether a
  `bad_alloc` mid-load leaves a partially-built `Net` published. Reading the code, it
  cannot — `g_net` is only assigned after every field is read — but that is a code
  reading, not a measurement.
