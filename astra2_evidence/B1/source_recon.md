# Astra round 2 exact-source reconnaissance — 2026-10-29

Read-only investigation; no source edits, build, acceptance, or Elo result.

## Requested bundle baseline

`origin/forge-bundle-int` = `b7c177222038e9332965a95ec53ea3b94e90dbc9`.
`BUNDLES.md:5–6` explicitly excludes SingularV2, TimeManV2, SmpV2, and NNUE v3. Thus these names must not be silently mapped to different bundle features.

## B1 SmpV2

Authoritative located source: `origin/fable-fb2-j5` = `bf6839e9e65108db76f028532dc15f9587a41fe7`.
`src/search.cpp` SHA256 `b75ae5407e001b5ec10a5a7e783d2e1da397c27104ee910770c51e61eec55cbd`.

- `include/forge/search.hpp:253–262` declares default-off SmpV2 and helpers.
- `src/search.cpp:671` selector accepts each completed helper with a nonempty move/PV if depth exceeds current best; it does not check scores. It preserves main nodes/elapsed.
- Iterative driver: odd helper ids search one extra ply, even helpers widen aspiration windows. Main unchanged.
- `Searcher::search` captures helper SearchInfo and selects after joins.
- `tests/fb2_j5_tests.cpp` contains existing coverage but lacks a main-mate/deeper-ordinary-helper regression.
- Minimal bundle port must retain the default-off option, worker configuration snapshot, helper result collection, depth reporting, and coherent final UCI info; adding only a renamed comparator would not repair this absent SmpV2 path.
- Existing score types have no proof provenance tag. Mate/TB-band protection is a conservative score-band policy and must exclude sentinels. Actual tablebase proof requires real TB probes/files.

## B2 J4

Authoritative source: `origin/fable-fb2-j4` = `eb09fc825ea1ed1e28c46369abd1b9b05d0a006f`.
`include/forge/timeman.hpp:24–43` allocation sets soft=min(soft,available), hard=min(hard,available), independently; increment>>remaining can therefore make soft>hard. This same formula exists in the bundle's `src/search/timeman.hpp`.

J4 also scales its nominal soft budget in decide_v1/decide_v2 and uses an in-search overshoot allowance; these can exceed hard even after allocation alone is clamped. J4 itself is absent from bundle. A bundle-only shared allocation repair must be labelled accurately; it is not a J4 integration.

## B3 NNUE architecture loader

Authoritative source: `origin/fable-nnue-arch` = `08b589e197202d00bb2a840c80c2233262cd9918`.
`src/nnue_v3.cpp` SHA256 `6cf6fac3f97934d98bd16bc72d9a9c91c50f44586614ea5fe22018534c7f30e2`.

- `load` begins at279; line284 constructs an entire-file byte vector before checking minimum size, header, dimensions, exact size and checksum.
- Format: 192-byte header, bounded hidden32..1024 multiples32, king buckets1..32, output buckets1..16. Exact file_size_for includes int16 weights/biases, int32 output bias and8-byte checksum.
- Header maps need validating before payload allocation too; currently map checks occur after vector/read and Net allocation.
- Loader is absent from bundle. Bundle NNUE v2 loader already preflights size/header; passing those tests does not fix this v3 bug.
- Full v3 architecture is ~605cpp+260hpp plus search_v3, evaluation hooks, worker state, UCI parser and CMake changes. Porting it merely to fix file reading is unnecessary scope/risk. Preferred: explicit branch-base exception for exact-source repair, or a narrow pinned-source patch plus native regression harness clearly marked not integrated into bundle.

## B5 SingularV2

Actual located source: `origin/fable-fb2-j3` = `1efc0b2c9e09d38642eabd1d6282acceeb38c0b8`.
`src/search.cpp` SHA256 `0ad09d74ef35f6d27cd74d6f56bbe5c2e8d31b70e3b4eb8f10eb8f2b9613cb99`.

No `SingularV2` match was found in inspected Opus refs `opus-C3`, `opus-O8`, `opus-r3-port-b`, `opus-r3-port-c`, `opus-summary`; this is not an exhaustive proof across all opus branches. Bundle's own documentation attributes SingularV2 to FB2-J3.

Source semantics at `src/search.cpp:1200–1235`:
- Existing singular test stays, then non-PV triple extension when singular_score<singular_beta-80, inherited count<=4, !tt_capture.
- PV double extension when score<beta-60 and count<=3.
- Excluded search multicut if singular_score>=beta and not mate.
- Deeper negative extensions: -3 on non-PV TT fail-high, -2 on cut-node.
- Source counts extensions>=2 once; bundle ordinary path currently counts only extension==2. Triple accounting requires explicit adaptation/documentation.

Bundle interaction: `src/search/alphabeta.inc:398–459` has CorrExt alternate extension selection and counts extra plies rather than number of multi-extensions in that instance. A SingularV2 port must establish precedence/exclusivity rather than accidentally stacking two extension policies. CorrHistPlus itself modifies static evaluation via corrected_eval/update_correction; SingularV2 reads TT/search scores influenced by it but does not directly access its tables. CorrHistPlus=4 is one table bit, distinct from CorrExt; N1 needs exact option configuration and independent tests.

IDEA_SOURCE: User's round-two repair contract and this repository's exact FB2/bundle source; no code from another engine.
