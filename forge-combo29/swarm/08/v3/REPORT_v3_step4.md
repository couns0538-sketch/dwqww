# Step 4 — the `output_sum` horizontal reduction: bit-identical, faster, and still REJECTED

**Verdict up front: REJECTED. Not because it is wrong — it is bit-identical — but because it is worth +0.05 %,
ten times under the 0.5 % bar I set before measuring. My prediction of +1.2 % was wrong, and I can name why.**

This is the last of the three v3 hot functions. Step 2 (count dispatch, `apply_changes_pair_avx512`, 8.47 % share)
gave +1.2 % and is recommended. This one, on `output_sum_avx512` (7.34 % share) gives a twentieth of that. The
coordinator's hypothesis — "the same removable-test pattern may be here" — is **true in shape and false in size**:
there *was* a removable per-lane tail, and removing it correctly bought almost nothing, because the tail was
32 adds per call on independent lanes, not a branch taken 2.5 M times.

---

## 1. What the patch does

`output_sum_avx512` accumulated two 512-bit vectors of int32 partial sums, then:

```cpp
alignas(64) std::int32_t lanes[32];
_mm512_store_si512(reinterpret_cast<__m512i*>(lanes), sum0);
_mm512_store_si512(reinterpret_cast<__m512i*>(lanes + 16), sum1);
std::int64_t sum = 0;
for (const std::int32_t lane : lanes) sum += lane;
return sum;
```

A 128-byte store followed by a 32-iteration scalar sum, on every evaluate call — **2,556,881 calls** on bench 13.
The patch folds in-register:

```cpp
const __m512i total = _mm512_add_epi32(sum0, sum1);
__m256i v = _mm256_add_epi32(_mm512_castsi512_si256(total), _mm512_extracti64x4_epi64(total, 1));
v = _mm256_add_epi32(v, _mm256_permute2x128_si256(v, v, 0x01));
v = _mm256_add_epi32(v, _mm256_shuffle_epi32(v, _MM_SHUFFLE(1, 0, 3, 2)));
v = _mm256_add_epi32(v, _mm256_shuffle_epi32(v, _MM_SHUFFLE(2, 3, 0, 1)));
return static_cast<std::int64_t>(_mm256_cvtsi256_si32(v));
```

Patch: `v3/step4_output_sum_reduce.patch.txt`, applies with `patch -p1 --fuzz=0` from the repository root.

## 2. Identity — exact, but only after the patch was fixed

My **first** version of this patch folded with `_mm512_shuffle_i32x4` and was **not bit-identical**:

| row | base | first attempt | |
|---|---|---|---|
| bench 11 (PC20+net) | 965,454 | **201,580** | FAILED |
| bench 13 (PC20+net) | 4,151,906 | **1,029,351** | FAILED |

`_mm512_shuffle_i32x4` selects 128-bit quarters by mask, and my masks picked the wrong quarters — so the fold summed
a different multiset of lanes. It compiled cleanly, ran the whole bench, and returned a plausible number. **Only the
identity gate caught it**; a timing run alone would have reported a speedup for a different engine.

Replacing it with the 256-bit fold above restored identity completely:

| identity row | base | patched | |
|---|---|---|---|
| bench 11 no-opt | 312,866 | 312,866 | exact |
| bench 13 no-opt | 862,329 | 862,329 | exact |
| bench 11 net-only | 278,024 | 278,024 | exact |
| bench 13 net-only | 587,276 | 587,276 | exact |
| bench 11 PC20+net | 965,454 | 965,454 | exact |
| bench 13 PC20+net | 4,151,906 | 4,151,906 | exact |
| bench 11 PC20 no-net | 625,258 | 625,258 | exact |
| bench 13 PC20 no-net | 3,652,372 | 3,652,372 | exact |
| evals (3 rows) | 968 / 1176 / 31 | 968 / 1176 / 31 | exact |
| **200-opening node sum** | **27,944,084** | **27,944,084** | **exact** |

## 3. Speed — +0.05 %, interval includes 1.0

Same protocol as Step 3 so the two results are comparable: two builds per side, 20 alternating rounds ordered
B1 P1 B2 P2, PC20-free (Threads 1, Hash 16, test net). The harness requires every build to report exactly
4,151,906 nodes or the run stops.

| build | median ms |
|---|---|
| B1 (unpatched) | 2130 |
| B2 (unpatched, 2nd build) | 2130 |
| P1 (patched) | 2129 |
| P2 (patched, 2nd build) | 2128 |

| quantity | value |
|---|---|
| ratio patch/base (40 runs per side) | **0.9995** |
| speed change | **+0.05 %** |
| bootstrap 95 % interval | **0.9984 .. 1.0005** |
| build-to-build spread | 0.00 % / 0.02 % |
| clears the pre-registered 0.5 % bar? | **NO** |

The interval **includes 1.0**. Even the sign is not established on this machine. A 0.05 % effect is under the
build-to-build noise for any shorter run and would not be worth the maintenance cost of a hand-written reduction.

## 4. Why my +1.2 % prediction was wrong

I predicted ~1.2 % by costing 32 adds × 2.56 M calls = 82 M adds at **0.3 ns each ≈ 24.6 ms of 2130 ms**.

That rate is the error. 0.3 ns per add is 3.3 adds per nanosecond — it already assumes *several* adds per cycle,
so it is not a latency figure either; it is a number that does not correspond to any machine limit. The correct
bound, given the 32 lanes are **independent**:

| clock | 82.0 M adds / 4 ALU ports | as time | as share of 2130 ms |
|---|---|---|---|
| 2.4 GHz | 20.5 M cycles | 8.56 ms | 0.40 % |
| 3.0 GHz | 20.5 M cycles | 6.85 ms | 0.32 % |
| 3.7 GHz | 20.5 M cycles | 5.55 ms | 0.26 % |

So even the *upper* bound was 0.26–0.40 %, and measured came in **below** it at 0.05 %, because the tail overlaps
with the surrounding loop work rather than sitting on the critical path. Two compounding errors: I used a
per-operation figure where a port-throughput figure applies, and I treated the result as achievable when it is only
a ceiling.

### And the kill condition I wrote was itself wrong

`ANALYSIS_other_hot_functions.md` said: *"if the bench moves by less than 0.5 %, the compiler was already
vectorising that sum loop."* **It was not.** Disassembly of the unpatched build's sum loop:

| check | count |
|---|---|
| `vpaddd` in the sum tail | **0** |
| scalar `add` in the same region | 53 |

The compiler does not vectorise it; the tail is simply too small to matter. The **bar was right and the stated
reason was wrong**, so I am correcting the reason rather than letting a right verdict inherit a wrong explanation.

## 5. The other function in the question: `refresh_from_pieces` (6.78 %)

**No removable per-lane test, and I did not patch it.** Its loop bounds are `removed`/`added` bit counts, which are
data-dependent — the number of changed pieces varies per call, so there is no small fixed set to specialise on. That
is precisely what made the count-dispatch patch work in Step 2 (a count in 1..4) and precisely what is absent here.

A real inefficiency does exist: for *k* changed pieces the code makes *k* separate load-and-store passes over
`entry.values` (1 KB each). Batching them into one pass would cut the loads. **Recorded as an opportunity, not
attempted** — it is a rewrite rather than a hoist, and on the evidence of this step a rewrite that moves one node
costs more than the tail it removes.

## 6. What this says about the Step 2 recommendation

**It strengthens it rather than weakening it.** Both functions had "a removable per-lane thing"; only one was worth
removing. The difference is *what is being removed*:

| | Step 2 (`apply_changes_pair_avx512`) | Step 4 (`output_sum_avx512`) |
|---|---|---|
| what was removed | a per-lane **test/branch**, 32× per call, on a value in 1..4 | a per-lane **add**, 32× per call, on independent lanes |
| cost model | branch misprediction + dispatch overhead | ALU port throughput |
| removed per call | a control-flow decision | a few cycles of a 4-wide port |
| measured | **+1.2 %** (n=120 paired, p=1.5e-19) | **+0.05 %** (interval includes 1.0) |
| verdict | recommended, worth PC timing | rejected |

A branch is worth orders of magnitude more than an add on a wide machine. **"Removable per-lane work" is not one
category**; the Step 2 result does not license the assumption that the next lane-wise rewrite pays too.

## 7. Files

| file | contents |
|---|---|
| `v3/step4_output_sum_reduce.patch.txt` | the patch, verified `patch -p1 --fuzz=0` on a clean file-5 tree |
| `v3/step4_timing.py` | timing harness (two builds per side, ABBA, bootstrap, pinned-node guard) |
| `v3/step4_timing.txt` | 20-round raw table + verdict + the correction appended after the format bug |
| `FINDINGS.md` | 08-F46 (result), 08-N11 (cost model), 08-N12 (intrinsic bit-identity) |

**Not carried forward.** The patch stays in the folder as evidence, with its numbers, as a rejection.
