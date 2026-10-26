# S06 offline gate miner — 2026-10-26

Keep the four `forge_sol_S06_{gatelog_miner,statistics,pgn,logs}_20261026.py`
files together. Python 3.10+ and its standard library are sufficient. No engine,
compiler, trainer, GPU, network connection or installed Python package is used.

From this flat folder, run all tests:

```sh
python3 -B -m unittest discover -s . -p 'test_forge_sol_S06_*.py' -v
```

Calculate diagnostics from supplied completed-pair counts:

```sh
python3 -B forge_sol_S06_gatelog_miner_20261026.py counts \
  --penta 5 121 458 154 12 --e0 0 --e1 10 --units nelo \
  --out ./forge_sol_S06_G100r_counts_new_20261026
```

Read one declared gate's PGN and/or log, using exact runner player names:

```sh
python3 -B forge_sol_S06_gatelog_miner_20261026.py mine \
  --gate-id GATE_ID --candidate Candidate --baseline Baseline \
  --pgn /path/to/original.pgn --log /path/to/original_console.txt \
  --pairing same-round --e0 0 --e1 10 --units nelo \
  --out ./forge_sol_S06_gate_new_20261026
```

Triage the supplied CSV without treating reported decisions as verified:

```sh
python3 -B forge_sol_S06_gatelog_miner_20261026.py triage \
  --csv /path/to/GATE_RESULTS.csv \
  --out ./forge_sol_S06_triage_new_20261026
```

Every output directory must be NEW and its parent must exist. Existing files and
shards are never edited, moved or overwritten. The exact input bytes, their
SHA256 digests, executed module digests, arguments and structured report are
retained, with a checksum manifest. This is a checksum seal, not filesystem
immutability. Each input is limited to 64 MiB and must be UTF-8 (BOM supported).
Exit 0 means a report was produced without a blocking error, **not acceptance**.
Exit 1 means invalid arguments/input, an existing output, or a blocked report.
Blocked outcome reports retain the input bytes and attempted records.

Pairing is explicit. `same-round` groups identical Round tags, as the supplied
Forge runner does. `adjacent-rounds` means numeric game rounds 1+2, 3+4, etc.
`round-prefix` means N.1+N.2. No convention is inferred from adjacency. A pair
requires two completed trusted results, reversed colors and matching starting
positions. FEN/OpeningFEN spelling and rank widths are checked; first four fields
identify the opening. These are syntax checks, **not board or move legality**.
Missing opening data blocks pairing. All raw game attempts remain visible.

The PGN module records its bounded supported identity tags in each report.
Event, Site, time/resources, explicit Match/Run/Attempt/Seed/Srand/Gate and supported
options metadata partition pools. It never combines their paired bins globally.
Unknown tags remain recorded but are not authenticated settings. Missing binary,
source, options or runner provenance cannot be supplied by the parser. Repeated
openings, incomplete/duplicate pairs and structural errors block the strict
outcome screen. Faulted pairs may retain descriptive counts and are ineligible.
Only recognized normal termination can pass that screen; absent or unfamiliar
termination remains unknown. Fault counts mean observed game/kind occurrences;
attribution and its explicit/result-loser basis are recorded. Comments inside
variations remain observations and cannot count as actual game faults.

Per-opening and per-phase splits contain games, W/D/L, fault counts and paired
bins within each pool. `--phase-tag Phase` uses an explicit categorical PGN tag.
Without it, phase is unknown. A mixed-phase pair is not counted in either phase's
paired sample. No material phase, phase Elo or position-level outcome is invented.

Log support is bounded to the supplied Fastchess Results/Games/Ptnml/LLR,
Finished-game, Player/Timeouts/Crashed and native SPRT completion dialects.
Snapshots are cumulative: decreasing counts (including across empty snapshots),
duplicate count fields, changed resource descriptions, multiple match terminals,
malformed recognized records and conflicting decisions are retained and block.
Final invalid LLR tokens never fall back to an earlier finite value. Original
fault event mentions and reported player totals stay separate; summing them
would double count. Unrecognized logs remain UNVERIFIED, never a clean-match
proof. Original bytes are always available for grammar review.

Statistics use pair scores 0/.25/.5/.75/1 and their population variance. The
supplied QA **Gaussian nElo approximation** is implemented independently; it is
not an exact arbitrary-profile Fastchess likelihood. `--units logistic` explicitly
selects logistic-Elo hypotheses. Displayed Elo uses the logistic transformation.
The fixed 95% normal/delta uncertainty and transformed-score endpoints are
descriptive approximations, especially weak at low counts or boundaries. They
are not sequential coverage guarantees. Zero variance, empty samples, impossible
hypotheses and non-finite derived values stay null/unknown. Five bins do not
identify individual W/D/L. Wald thresholds are diagnostic only.

Reported native LLR/decisions and CSV verdicts are kept separately. Neither a
Gaussian threshold crossing nor an outcome-screen pass authenticates the frozen
source/build, legality, stopping rule, confirm gate, live PC state or lock.
`acceptance_authorized` is always false. No Elo-gain claim is made.

The validation driver can repeat the complete offline evidence run when the
same supplied handoff and historical repository files are present:

```sh
python3 -B forge_sol_S06_validation_20261026.py \
  --handoff-files /path/to/forge_handoff_full_20261025_1435/files \
  --repo /path/to/dwqww --out /path/to/NEW_validation_directory
```

The `.jsonl.gz` evidence file is reversible: each decompressed JSON line contains
`path`, `bytes`, `sha256` and base64 `data_b64`. Its separate index lists the
selected original raw streams, inputs, receipts, and retained earlier source
versions. Decode only after validating relative safe paths; verify the digest
before writing a NEW recovery tree. It includes a superseded 73-test validation
and the final 76-test validation, explicitly separated by directory/version.

Idea sources only: the user's S06 spec; supplied QA count/moment formulas and
`qa_llr_check_nelo_20261025_1215.py`; the supplied `pgn_stats.py` and
`run_hourly_sprt.py` for pairing/integrity concepts; the actual retained historical
Fastchess console/PGN dialect. All new implementation and tests are original.
No other engine code or tuned constants were copied.
