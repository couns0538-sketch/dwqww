# Independent A2 final review — 2026-10-28 UTC

Verdict: no new blocking defect identified in the scoped A2 change.

Reviewed the production comparator/selector, UCI parsing and shutdown path, option declarations, Syzygy score contract, iterative result handling, and A2 tests/evidence. The existing mate comparison remains first. The opt-in positive-TB-band guard rejects a lower-scoring helper and accepts a higher-scoring helper independent of depth. Equal proven-band scores retain the existing winner. Negative TB scores retain original depth semantics unless a mate is involved; the request concerns winning TB results.

The non-atomic new option is written by UCI only after stop_search joins the search driver. The comparator is called after every helper joins. The source therefore provides quiescent option writes in supported UCI usage; this review is not a full-engine ThreadSanitizer claim.

## New native checks actually run after environment recovery

- Built the same independent comparator probe against the real base and candidate forge_core libraries. 7,200 score/depth/tablebase-state cases per mode, 21,600 total. Base and candidate OFF outputs are byte-identical. ON output differs. No main mate was replaced by a lower helper in any mode; no main positive TB-band result was replaced by a lower helper in ON/tablebases-active cases. The TB invariant is intentionally checked only in that enabled state, not claimed for the base.
- Live UCI lifecycle smoke with 2 and 3 threads and SmpBestThread=true: four changes of SmpProtectProvenScore while an infinite search was active; six legal startpos bestmove replies; readiness replies after shutdown; clean exits. Binary SHA256 stayed 1c3c0d03d43ab09d8abeb66dac576b9093df6f033198fbe0dafb23f02a5b5551. Raw command/output/error streams retained. No actual tablebase files loaded, so this is lifecycle coverage, not end-to-end TB semantics or proof of race freedom.

The first attempt to start the comparator probe failed at process creation during an environment outage. It ran only after recovery; results.json and uci_toggle_results.json describe the successful executions. No engine changes, Git mutations, benchmarks, NPS comparisons or strength matches were performed by this reviewer.

## Limits retained

SearchInfo has no score provenance/bound tag and ordinary evaluation can occupy the TB numerical band while tables are loaded. Therefore this option conservatively protects a score band; it does not authenticate a proof of a tablebase win. Existing same-move early-return behavior and interrupted-search result behavior were preserved. A real-tablebase end-to-end qualification remains pending. The initial full-suite failure evidence must remain visible.

IDEA_SOURCE: Owner A2 and Forge production source only.
