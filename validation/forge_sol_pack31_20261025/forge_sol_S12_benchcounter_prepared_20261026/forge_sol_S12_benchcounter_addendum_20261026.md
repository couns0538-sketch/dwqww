# S12 counter-helper addendum, 2026-10-26

Reason: the sealed S12 preregistration described a small actual benchmark API
helper for OFF/ON counts but did not include its source. This addendum closes
that source gap. It adds no engine feature or UCI/default change. The original
39-file compact packet remains unchanged and is not superseded.

The final generated helper is
`generated_final/forge_sol_S12_benchcounter_helper_20261026.cpp`.
The pure source producer hashes the actual canonical lock's src/uci.cpp,
board.hpp, and tools/search_benchmark.cpp before extracting its exact eight
ordered FENs, including the actual StandardStartFen declaration. It verifies
the actual UCI bench loop's one Searcher(16), clear-before-every-FEN, fixed depth,
emit_info=false, and TTAccess::Exclusive contract. The four-position support
benchmark is used only to confirm existing constructor initialization, never
as the FEN suite. No engine sources are copied into this addendum.

Both helper modes link the feature-ON core/header ABI and require H256 residual
NNUE. Before the first search, OFF or ON is stored into the existing pending
atomic. Exactly one default-Threads1 Hash16 Searcher searches all eight cases;
the actual returned SearchInfo contains worker counters aggregated after join.
The helper prints eight raw per-FEN rows plus their checked sums: actual nodes,
completed depth, refreshes, physical updates, zero-dirty edges, avoided copies,
alias hits, and NNUE evaluations. There is no elapsed time or NPS output.

The stdout parser retains the distinction between returned API counters and
the real library's ON info-string diagnostics. It requires binding/active/stats/
per-FEN/total order, exact source/suite/header identity, all eight FENs in order,
uint64 counter types, complete depths, fixed node totals, and raw sum equality.
OFF and ON pairs must have identical per-FEN nodes, refreshes, evaluations, and
zero-dirty edge counts; OFF physical updates must equal ON physical updates plus
ON avoided copies. These are future native acceptance checks, not observed
counter results. A printed hash cannot authenticate its linked core: actual
compile, archive, ELF, link-map, and main-first-runtime receipts remain mandatory.

Source tests use explicitly SYNTHETIC parser fixtures. Eleven tests pass,
including wrong Hash/depth/access/info/clear contract, changed actual source pin,
missing/reordered/duplicate FENs, early depth, bad node totals, malformed/missing/
overflowing counters, ON/OFF branch proof, substituted sums and pair accounting.
Their invented numbers are never labeled as native evidence or shipped as a
benchmark result. Original pure-test stdout/stderr are retained. Independent
source review found no must-fix issue. Early generated source revisions remain
in separate directories for provenance; only generated_final is the build input.

| Check | Status |
|---|---|
| Canonical source/FEN/contract binding | PASS, source only |
| Deterministic source output/no overwrite | PASS, pure tests |
| Parser positive/mutant controls | PASS, synthetic only |
| Independent helper/producer/parser review | PASS within source scope |
| Original sealed39 payloads unchanged | Checked again at sealing |
| Compile, link-map and core/ABI binding | UNVERIFIED |
| Main-first bare bench11 before helper | UNVERIFIED |
| Actual OFF/ON counters at d11/13/16/20/22 | UNVERIFIED |
| Actual node refs308972/745494/2460422/11901452/31111774 | UNVERIFIED |
| Sanitizers, Windows, NPS and Elo | UNVERIFIED |

Deferred source reproduction into a NEW directory (never overwrite this packet):

```bash
python -B forge_sol_S12_benchcounter_source_producer_20261026.py \
  --out /tmp/forge_sol_S12_benchcounter_new_source_20261026
```

After the ordered native lease and actual candidate main FIRST bare bench11
gate, compile via the existing bounded owned build protocol, same compiler/core
flags/source/header as the actual featureON build. Example exact compiler argv,
with private paths assigned by that future controller:

```bash
/usr/bin/x86_64-linux-gnu-g++-14 -std=c++20 -O3 -DNDEBUG \
  -march=x86-64-v3 -mtune=znver5 -fno-fast-math -ffp-contract=off \
  -DFORGE_NNUE_HIDDEN=256 -DFORGE_NNUE_LAZY_ACC=1 \
  -I/tmp/forge_sol_S12_native_20261026/LP_candidate_source/include \
  /tmp/forge_sol_S12_benchcounter_prep_20261026/generated_final/forge_sol_S12_benchcounter_helper_20261026.cpp \
  /tmp/forge_sol_S12_native_20261026/LP_buildon_release/build/libforge_core.a \
  -pthread -Wl,-Map,/tmp/forge_sol_S12_native_20261026/LP_benchcounter.map \
  -o /tmp/forge_sol_S12_native_20261026/LP_benchcounter
```

Inspect the actual map and source/ELF hashes before execution. A fresh helper
process takes exactly two arguments, e.g. `11 OFF` or `11 ON`; repeat both modes
at11,13,16,20,22 sequentially. Use the existing owned runner, pinned granted CPU,
nice19, bounded600s work/hard window and owned RSS<=4GiB; capture unfiltered raw
stdout/stderr, exit and process-closure receipts. Never invoke it before the
corresponding new main's bare11 gate or infer a run from generated source.

Then validate the preserved ORIGINAL stdout pair without launching an engine:

```bash
python -B forge_sol_S12_benchcounter_records_20261026.py \
  --binding generated_final/forge_sol_S12_benchcounter_source_binding_20261026.json \
  --off-stdout /tmp/forge_sol_S12_native_20261026/LP_d11_OFF.stdout \
  --on-stdout /tmp/forge_sol_S12_native_20261026/LP_d11_ON.stdout --depth 11
```

No compile or native execution was performed here. The exact next action remains
the previously ordered main engine Release qualification, then this helper under
that source-bound native lease. Counter runs establish work accounting, not speed.
