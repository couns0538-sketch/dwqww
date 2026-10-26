# S06 bounded implementation — 2026-10-26

Implement the existing ordered handoff's offline gate miner, without engine changes,
matches, lock promotion or strength claims. Three small stdlib modules separate
paired statistics, explicit PGN pairing, and original Fastchess log observations;
a CLI binds immutable input bytes and writes only a new output directory.

PGN pooling is partitioned by declared match metadata, with explicit pairing
conventions and color/opening checks. Every attempted record and fault remains
visible. Explicit Phase tags provide categorical outcome splits; absent phase
metadata stays unknown. A result is never counted once per invented phase.

The supplied QA Gaussian nElo approximation reproduces the three provided
pentanomial cases within 0.01. It is labelled approximate and is not an exact
Fastchess likelihood implementation. Native reported LLR and acceptance text
remain separate observations. Neither a crossed diagnostic boundary nor a clean
PGN establishes source/build, legality, stopping-rule or engine adoption evidence.

CSV triage consumes the newer BOM-bearing 13:35 table, validates W/D/L, and never
pools rows, seeds or concurrency. G104's W/D/L is available, but its paired
counts and the historical gate PGNs are absent. It cannot become a verified
acceptance by inventing a compatible pentanomial profile.

Implementation sequence: independent known-answer statistics and PGN tests,
log-reader tests, CLI/reconciliation tests, supplied-count and historical-parser
replays, independent review, sealed dated files and GitHub byte verification.
All fixtures are labelled synthetic unless actual retained original bytes are
explicitly identified. No large builds or timing work: free disk is about 27 MiB.
