# S17 game-group split and shard manifest — 2026-10-26

This offline tool writes a new validation split plus a read-only dedupe manifest. It never edits, moves or overwrites an input. It does not change an engine, network or trainer.

Keep the unchanged dependencies `forge_sol_datafilter_v2_20261026.py` and `forge_sol_datafilter_20261025.py` beside the new tool. SHA256 checks run before their code is imported. Existing FPOS/FHCE readers, writers, position identity and game-provenance checks are reused; no record codec is duplicated.

Fill `forge_sol_S17_owner_config_example_20261026.json` with chronological text/POS sources and run:

```sh
python3 -B forge_sol_S17_gamesplit_20261026.py --config owner_config.json
```

Production is the default. It requires read-only POS and supplied read-only HCE, owner-authoritative row-aligned game-ID files for every ordered source, and a provenance statement. Reopened/interleaved IDs, mismatching text/POS and incomplete maps are rejected. A game may continue across files; shard boundaries do not reset grouping. IDs must satisfy the existing S16 contract. An owner's authority is an input contract, not inferred from chess counters.

For diagnostic input without authentic IDs, explicitly add `--diagnostic-mode`. S16's conservative grouping starts a new defined group when fullmove decreases, piece count increases or WHITE result changes. Missed boundaries merge games; interleaving can invalidate the assumptions. The anomaly tripwire is not a proof of authentic IDs. Diagnostic ledger groups are labelled `inferred:...`; authentic game isolation remains UNVERIFIED. The real916 sample was tested only in this mode.

`sources` is the complete ordered dataset to split. Extra files found recursively under each declared `sealed_pos_dirs` root are audited in the dedupe manifest; they are not silently added to the split without matching ordered text. Empty declared directories are refused. Source names must be unique portable identifiers. Paths resolve relative to the configuration file. The output must be NEW; its parent and the scratch directory must already exist. Neither output nor scratch may lie inside sealed input roots or protected lock/baseline/dist-v directories.

Groups are ranked by an independently implemented SHA256 of a domain tag, seed and group ID. The validation count is the ceiling of the requested basis-point fraction, bounded to one through n−1 groups. There must be at least two groups. Position dedupe gives validation priority, then retains the first record within each part. This may remove rows but never reassigns a group's rows to the other part.

Outputs include exact text records, a row-selection ledger, per-shard hashes/counts, a duplicate-row ledger, a summary and an MD5 manifest. Original LF/CRLF is preserved; an EOF-unterminated row receives LF when exported so merged records stay separate. If every retained row has provided HCE, selected POS/HCE pairs are written through the unchanged writer. Missing HCE is never filled with a placeholder: text and selections are written, binary export is UNVERIFIED. Every generated file is made read-only only after audits and input rehashes. Failures leave an explicit UNSEALED marker and retain their own scratch.

Dedupe identity is the existing SHA256(board32 || side-to-move). Castling, en-passant and clocks are absent from FPOS and are not guessed. The manifest reports whole-POS MD5 duplicates, position duplicates and conflicting known labels. It records missing HCE as unknown rather than comparing it to an invented value. SQLite and streaming verification avoid loading all dataset text/keys into Python memory.

Outputs are never automatically training-approved. Real013/014 exclusion is a separate S16 prerequisite; this job does not manufacture that certificate. Python3.12/Linux is tested; exact Python3.10 and Windows execution remain UNVERIFIED.

Run the small tests from this directory:

```sh
PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest -v test_forge_sol_S17_gamesplit_20261026.py
```
