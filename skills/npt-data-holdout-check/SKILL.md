---
name: npt-data-holdout-check
description: Use when qualifying Forge or nnue-pytorch training exports against holdout shards 013 and 014, checking game-level separation, or verifying that full-FEN castling and en-passant state survived conversion.
---

# NPT Data Holdout Check

Independently audit frozen exports; never modify the running NPT trainer, its inputs or a gate. Reuse `validate-chess-engine` for wider qualification and `grok-pc-safe-run` before any authorized PC workload.

## Establish the evidence boundary

Inspect the actual trainer reader, source format, converter and provenance. A `.pos` board record cannot recover missing castling, en passant, clocks or authentic game IDs. Use the original row-aligned FEN sidecar and trustworthy original game identifiers. If IDs are absent or guessed, **game split is UNVERIFIED**; the earlier whole-shard policy does not satisfy this newly requested game-ID proof.

Freeze the complete real 013/014 shard hashes and row counts from a trusted crew manifest, not from an arbitrary supplied prefix. Freeze train/source identities, decoder versions and commands. Missing complete holdouts blocks real clearance. A synthetic fixture can test the checker only.

## Independent checks

1. Decode with the authoritative current record reader into a documented normalized audit export; verify counts and round-trip full state. Do not invent NPT/binpack layouts or copy GPL decoding code into Forge. Keep licensing and external adapters explicit.
2. Independently scan training keys against **both complete holdouts**, using a separate audit implementation/index. Report overlap rows and key semantics. Conservative board+side-to-move matching also excludes collisions with different rights/clocks.
3. Independently compare authentic game IDs across train and holdout. Any overlap fails even when positions differ. Never derive IDs from row order or silently prefix identical real IDs by shard to hide leakage.
4. Match each retained row to its original source provenance and compare all six FEN fields, including castling and en-passant. Preserve legal-but-noncapturable EP exactly when the authoritative representation carries it; engine normalization is not proof of source identity.
5. Publish a new audit report with original input/reader hashes, row counts, overlap counts, FEN mismatches, missing-ID count, command and status per check. Keep audit indexes/evidence; no pruning step is authorized.

The bundled `python scripts/audit_exports.py --help` audits **normalized exports only**. Read [the export contract and PowerShell recipe](references.md). Its PASS does not certify an untested native-format adapter or the identity of a real private shard. It requires trusted export hashes/counts, exact source provenance and real IDs; missing IDs yield UNVERIFIED. Files/commands must go through the PC safety workflow.

For frozen Forge `FEN | score | result` shards and the result-aware JSONL cohort,
use `scripts/audit_selfplay.py` with a reviewed pinned manifest; see the native
adapter contract in [references.md](references.md). It joins both cohort and
retained rows directly to original raw physical source rows, streams complete
013/014 without duplicate JSONL exports, and retains a SQLite index. It reuses the
same independent FEN and identity helpers. Missing authentic game IDs still make
clearance UNVERIFIED. Fixture results are explicitly synthetic and cannot certify
real inputs or NPT decoding.

## Decision

Any position/game overlap or changed full-FEN provenance is FAIL. Missing formats, identities, complete holdouts, authentic IDs or native reader evidence remain UNVERIFIED/BLOCKED. Training readiness requires every applicable check, not just a zero position-overlap number. Do not claim training gain or Elo.

Test a known overlap, different-position same-game leak, stripped castling/EP and missing IDs before trusting a new adapter. Preserve failed examples. Update this skill rather than create another overlapping holdout workflow.

## R11 authentic-game evidence boundary

The R11 working implementation is `astra_r11/gameprov/` in this branch. It
accepts complete frozen R10 raw source/cohort/filtered/013/014 inputs and a
separately reviewed historical-origin registry. Its normalized archived-game
adapter is not a PGN/binpack decoder and does not authenticate arbitrary files
merely because their hashes are known. Production registry entries require
independent review of original source/exporter history. Never populate the
registry from a request's own assertion.

Authenticate the row-to-game mapping separately from the source game archive.
Identical FEN/ply positions can occur in multiple real games; a legal match is
not proof that a particular row came from one of them. The R11 binding registry
pins the reviewed historical mapping digest together with exact population-input
digests, and starts empty. A request cannot authorize its own mapping, and fixture
trust cannot override the production archive or binding registries.

Do not infer original games from decreasing fullmove counts, piece counts,
results or maximal FEN chains. Sampling, deduplication and file rollover can
remove or split the evidence needed to establish a game. Use FEN chains only
to validate an independently authenticated match. Canonical source/game
identity must survive relocation and shard rollover; a repacked export needs
reviewed original-origin mapping, not a new namespace hiding overlap.

Account for every original filtered and holdout row exactly once. UNTRACEABLE
rows have null IDs and explicit exclusion reasons. R11's approved policy
requires COMPLETE original 013/014 provenance: missing holdout identities mean
BLOCKED, with game_overlap null, even if retained subsets happen to be disjoint.
Reject empty-population success. The pack checker independently recomputes
source hashes, state correspondence, canonical IDs, population counts and game
sets from bundled files; it does not trust producer counts. Synthetic controls
are FIXTURE_PASS only and grant no production qualification or training access.

Use `gameprov/REQUEST.md` and `README.md` for the precise adapter and narrow
input-boundary resume contract. Current initial R11 fixtures were authored but
native execution was deferred because the permitted shared CPU lane was busy;
do not cite them as passing until a reviewed admitted run supplies receipts.
