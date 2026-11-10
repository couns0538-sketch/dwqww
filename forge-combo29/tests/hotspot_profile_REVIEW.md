# Locked-source hotspot audit

**Exploratory profiling only. No production changes, optimization acceptance, speed gain or Elo claim.**

## Method and integrity

`perf` was not installed. The available GNU gprof tool and GCC 14 were used without installation, escalation or security changes. The profiling build uses immutable lock `16833ec`, the same strict-FP/O3/x86-64-v4 settings as the validated lock, plus `-pg -g -fno-omit-frame-pointer`. All 20 source/include blobs were verified against that immutable commit; hashes are in `hotspot_profile_results.json`.

The bounded workload is the built-in eight-position bench at depths 16 and 18, in both NNUE modes. Each instrumented run was checked against the byte-verified uninstrumented lock (`1371770e...`). Nodes matched exactly:

| Mode | Depth 16 | Depth 18 |
|---|---:|---:|
| NNUE on | 3,024,920 | 6,066,072 |
| NNUE off | 2,448,617 | 6,134,776 |

Only the single-threaded built-in bench was profiled. This was not a controlled timing window; load samples are preserved. Instrumentation and shared-host contention mean these results should guide investigation, not quantify native speed.

## Attribution correction

The stock gprof text mislabeled some move-sort activity as `std::vector<tune::Parameter>::~vector()`. Direct symbol-range/disassembly inspection shows that callee PC `0x2e796` belongs to the introsort clone starting at `0x2e780`, beyond the actual destructor's range `0x2e730..0x2e75a`. The caller is MovePicker or recursive introsort, not parameter-vector destruction.

`hotspot_profile_decode.py` independently decodes the captured x86-64 little-endian gmon histogram/arcs and maps PCs against explicit `nm -S` function ranges. It preserves every nonzero histogram bin and call arc. The corrected rankings below use this mapping. The mislabeled destructor is **not** ranked as a hotspot. At depth 18 NNUE-on, introsort has 1,106,003 instrumented entries, including 560,758 recursive entries, and four histogram ticks (about 1.09%). Raw gprof text is retained unaltered for comparison.

Flat gprof call counts for recursive functions omit recursive entries. The corrected counts below include them: for example, main search has 4,923,596 instrumented entries at depth 18 NNUE-on, not the flat report's 253 nonrecursive entries.

## Ranked observed hotspots

Percentages are self samples divided by **all recorded histogram ticks**, not parent-inclusive time. Depth 18 contains only 368 ticks with NNUE on and 265 with it off, at 100 Hz. Seven and six ticks, respectively, fall outside named function ranges and remain unassigned. Small percentage differences are not precise measurements.

### Depth 18, NNUE on

| Rank | Function | Self samples | Instrumented entries including recursion | Immutable source location |
|---|---|---:|---:|---|
| 1 | HCE evaluate_position | 18.75% | 3,633,938 | src/eval.cpp:375 |
| 2 | nnue::update | 11.68% | 4,409,146 | src/nnue.cpp:110 |
| 3 | Worker::search, main recursion | 11.14% | 4,923,596 | src/search.cpp:1115 |
| 4 | MovePicker::next | 10.87% | 13,100,224 | src/search.cpp:447 |
| 5 | TT probe_body<false> | 5.71% | 6,058,697 | src/search.cpp:270 |
| 6 | Worker::qsearch | 4.89% | 2,380,945 | src/search.cpp:989 |
| 7 | nnue::evaluate | 4.62% | 3,633,938 | src/nnue.cpp:170 |
| 8 | generate_pseudo_legal | 4.08% | 3,315,770 | src/board.cpp:441 |

### Depth 18, NNUE off

| Rank | Function | Self samples | Instrumented entries including recursion | Immutable source location |
|---|---|---:|---:|---|
| 1 | HCE evaluate_position | 23.40% | 3,564,133 | src/eval.cpp:375 |
| 2 | Worker::search, main recursion | 15.85% | 4,996,558 | src/search.cpp:1115 |
| 3 | MovePicker::next | 11.32% | 12,787,658 | src/search.cpp:447 |
| 4 | TT probe_body<false> | 8.30% | 6,121,437 | src/search.cpp:270 |
| 5 | corrected_eval | 5.66% | 4,720,644 | src/search.cpp:852 |
| 6 | Worker::qsearch | 4.91% | 2,492,517 | src/search.cpp:989 |
| 7 | generate_pseudo_legal | 4.53% | 3,343,437 | src/board.cpp:441 |
| 8 | Board::make_move | 3.40% | 5,891,604 | src/board.cpp:998 |

Depth 16 provides a second workload size rather than a statistical replicate: HCE is again the largest sampled function (15.70% on, 30.83% off); MovePicker, search and NNUE update remain material contributors. Full ranked lists for all four profiles are preserved.

**Residual HCE matters with NNUE enabled.** The shipped network is residual: static evaluation still performs the handcrafted evaluation and adds the network result. HCE's 18.75% share above is observed with NNUE **on**, not an estimate imported from NNUE-off behavior. The NNUE modes also visit different node sets, so their percentage differences are not a controlled speed comparison.

High call count alone does not imply high cost. At depth 18 NNUE-on, `has_legal_move` has 5,651,933 entries but only two sampled ticks. Conversely, the HCE umbrella includes substantial inlined work whose individual functions cannot be ranked separately from these aggregate samples.

## Two small source-grounded hypotheses, not implementations

1. **Reuse the current TT replacement score during the replacement scan** (`search.cpp:296–305`). The scan repeatedly evaluates the current replacement entry's depth/age expression. A local best-score value updated only when the same strict-`<` replacement condition succeeds could preserve the selected entry and tie behavior. TT probe is measured at roughly 5.7–8.3% of depth-18 self samples, with about six million entries. However, these profiles do not distinguish hit/miss branches, and the compiler may already remove some repeated arithmetic. Inspect generated code and count replacement-path visits before writing a patch. No benefit is established.
2. **Avoid a self-swap after the first-four selection scan** (`search.cpp:642–656`, specifically line 649). Guarding `std::swap(moves_[index_], moves_[best])` when `best == index_` would preserve move data and ordering while potentially avoiding writes. MovePicker is measured at roughly 10.9–11.3% of depth-18 self samples and about thirteen million entries. The frequency of `best == index_` is not measured, and an extra branch may cost more than the stores. Measure that frequency/code generation first. Do not change sort tie order or selection policy.

These are bounded, bit-exact design possibilities in observed hot regions, not measured optimization opportunities. HCE and NNUE update warrant deeper instruction/source attribution, but no speculative patch is proposed solely from their umbrella shares. In particular, the NNUE updater already contains generated AVX-512 arithmetic; this profile does not justify claiming it needs basic vectorization.

## Limitations

- `-pg` changes prologues, call overhead, layout and potentially optimizer decisions. Preserved node counts validate the searched work, not production cost equivalence.
- Instrumented entry counts exclude inlined instances. Recursive counts require the raw-arc decoding described above.
- Histogram bins are mapped by midpoint to explicit symbol ranges. Boundary bins, compiler clones and line tables can be ambiguous; unmatched ticks remain unassigned rather than forced into a function.
- The 100 Hz sample count is small. No confidence intervals or line-level cost claims are warranted. The two depths are different workloads, not repeated trials.
- Profiles include process initialization and bench setup; they are not pure search-region measurements.
- No CPU reservation or host-frequency/thermal control was used. No candidate-to-baseline timing comparison was performed.

## Reproduction and evidence

The current recipe snapshots only the explicit source allowlist `forge-combo29/src` and `forge-combo29/include`, verifies every blob, and compiles only those source files. It never needs a Windows executable or bundled archives.

```sh
python3 forge-combo29/tests/hotspot_profile_run.py \
  --output /workspace/shared/forge-build/hotspot-profile-reproduction \
  --baseline /workspace/shared/forge-build/final-lock-identity-fixed/lock
```

The baseline hash is mandatory. If reconstructing it, use the source-only immutable-lock build recipe and verify the hash before profiling.

- `hotspot_profile_results.json`: source verification, compiler command, binary/gmon hashes and matching node receipts.
- `hotspot_profile_raw_reports.json`: exact original flat/callgraph reports and stdout/stderr, compact UTF-8 JSON (about 284 KB).
- `hotspot_profile_decoded.json`: complete address-based rankings, every nonzero histogram bin and every call arc (about 231 KB).
- `hotspot_profile_attribution.txt`: focused symbol/disassembly proof for the introsort labeling correction.
- `hotspot_profile_run.py` and `hotspot_profile_decode.py`: bounded reproduction and independently inspectable decoding.

Binary gmon files remain local under the profiling output directory; neither those binaries nor the source snapshot is distributed in this commit. The decoded records and gmon hashes preserve inspectable provenance without publishing binary profiler inputs.
