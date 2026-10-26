# S16 overlap runner and Job D filter v2, 2026-10-26

Prepared independently for later ordered root integration. This is not a claim
that S16 has reached its place in the ordered queue. No Git/network operations,
engine/compiler execution, GPU use, training or live PC execution occurred.

The new filter imports the unchanged Job D parser/writer dependency shipped
under its original name, forge_sol_datafilter_20261025.py. Its SHA256 is checked
before import: `6ccf78c864c44155cea22044fe05d0584bec5241acdc5ebb2b71e23886007ab3`.
The old 21-test file is also supplied unchanged and hash-pinned. There is no
second record parser or writer implementation. FPOS is a 16-byte header and
three column blocks: board32*n, int16 STM score*n, meta*n. FHCE has a 16-byte
header followed by int16*n. Full fields are retained exactly. Position identity
is SHA256(board32 || STM); unavailable castling, en-passant and clocks cannot
be included.

To run on owner-provided production inputs, fill the example configuration and
then use one command:

```sh
sh forge_sol_S16_overlap_runner_20261026.sh owner_config.json
```

```powershell
pwsh -NoProfile -File forge_sol_S16_overlap_runner_20261026.ps1 -Config owner_config.json
```

Keep both filter versions beside the runner. Linux uses python3 by default;
FORGE_PYTHON can select another interpreter. The PowerShell runner uses python
and accepts -Python. Python 3.10-compatible standard-library code is used;
the receipt names the actual tested interpreter. PowerShell and exact Python
3.10 execution are unavailable here and remain UNVERIFIED. The production CLI
checks at least 256 MiB of free RAM before reading the configuration. Its Linux
RAM path was exercised; the Windows MemoryStatusEx path is UNVERIFIED.

The configuration explicitly lists Job D output POS files and every directory
containing sealed shards. The runner recursively includes every *.pos file in
those directories, requires their read-only attribute, and refuses an empty
directory. It requires both exact 013/014 filenames. Matching HCE beside each
training POS is preferred, otherwise hce_dir/<stem>.hce is used. A direct import
API additionally supports hce_map. Neither holdout nor its HCE is filtered.
Configuration paths are relative to the configuration file. Each text-map or
ID-map JSON maps a unique source stem to a file path; those paths are relative
to that map JSON file. ordered_stems must enumerate all candidate and holdout
stems in their true chronological source order. Empty example fields cause a
refusal; they are not synthetic defaults.

Production needs an **owner-authoritative, row-aligned game-ID file for every
source**, plus a statement identifying the IDs' origin. Each UTF-8 file contains
one identifier per POS/text row, with 1-128 ASCII letters, digits, underscore,
dot, colon or hyphen, starting with a letter or digit. IDs must be globally
unique between games and contiguous in the declared source order; a game can
continue across shard edges. Reopened A/B/A/B IDs are rejected. Text must match
every binary board/score/meta row exactly. Within a continued ID, fullmove and
piece count cannot move backwards/forwards respectively and the WHITE result
must stay constant. These checks validate the mapping contract; the owner's
authority is a necessary supplied input, not inferred from counters.

Generic ordered FEN text cannot prove game IDs. In particular, synchronized
A1 B1 A2 B2 interleaving can have identical counters and no detectable boundary.
The production CLI refuses this input without authoritative IDs before output
creation. A separate explicit --diagnostic-mode CLI and the documented import
API default production=False preserve the old conservative grouping for
diagnosis. Legacy game_overlap:0 then means zero *observed inferred-group*
overlap only. game_overlap_verified:false, authentic_game_overlap:UNVERIFIED,
production_eligible:false and sealed_for_training:false prohibit a production
interpretation. A diagnostic anomaly tripwire rejects more than 20 old-style
boundaries in any rolling 100 rows across shard edges. Passing it is never a
claim that interleaving is absent. Combining --config with --diagnostic-mode
is rejected rather than silently overriding the prohibition.

The real 916-line text has no authoritative IDs, so its actual game isolation
remains UNVERIFIED. Real 013/014 and the sealed production shards are absent.
Their overlap counts, full-scale scratch needs and training acceptance remain
UNVERIFIED. Exact filenames alone do not authenticate a supplied holdout; the
summary retains this distinction. No training gain or playing-strength claim
is made.

The new filter adds the requested QA fixes:

- SQLite scratch lives in a fresh child of --work-dir, uses WAL/synchronous OFF,
  and is removed only after successful independent audits. Failed runs retain
  their own scratch and a FAILED_UNSEALED marker; no failure is train-approved.
- Free-disk preflight starts from about 300 B/source row, then separately
  reserves repeated stem/index bytes, authentic ID/segment/index bytes,
  per-retained-row IDs, bounded-batch WAL, output pairs, temporary column blocks
  and the removal ledger. Shared-volume requirements are combined. Estimates
  are conservative planning values, not a measured guarantee for PC scale.
- conflicting_label_duplicates counts duplicate training positions whose
  score/meta/HCE differs from the already-retained canonical row. Holdout
  exclusions remain separate; threshold-rejected rows are not canonical.
- Whole-POS MD5 copies of a holdout are marked duplicate_holdout_shard; aliases
  retain holdout_shard accounting. Every removed source row has a deterministic
  JSONL entry with zero-based row, position SHA256, group/ID, reason and conflict
  flag. Summary input-position/game-overlap counts are separate from output
  zero-overlap audits.
- Existing outputs are refused. Protected output/work paths and resolved
  symlink paths into lock/baseline/dist-v* are refused. Input hashes are checked
  again before sealing. Output is reread independently to verify fields,
  count, duplicate positions, holdout position overlap and supplied group
  exclusion. Each new payload, summary and MD5 manifest is sealed read-only.

Run the full standalone regression suite from this folder:

```sh
FILTER_TEST_TOOL_PATH="$PWD/forge_sol_datafilter_v2_20261026.py" python3 -B -m unittest discover -s . -p '*tests*.py' -v
```

The unchanged old 21 tests pass against both their original implementation and
v2. Twenty new tests cover the QA fixes, exact field round trips, deterministic
sealed output, Linux production runner enumeration, missing/authentic IDs,
interleaved and synchronized streams, protected symlinks, low RAM/disk, alias
counts, long IDs and Unicode ledger budgets. TDD RED and GREEN logs retain
actual failures and repairs. Independent review found the config/diagnostic
dispatch issue, hardlink preflight regression and ID/Unicode reserve defects;
all were reproduced and fixed without editing old expectations.

The supplied synthetic 200k sample is recoverable. A read-only selection
reproduction using the pinned parser and selection helpers observed OFF
200000 kept and t300 **157666 kept / 42334 dropped**, with no input changes.
The t300 drops were draw 21122, STM-loss 10756 and STM-win 10456. This was a
count reproduction, not a full 200k v2 SQLite/output run. That larger pipeline
is deferred to root orchestration after its native lease and resource review.
No sample files were copied into this delivery. Synthetic sample game overlap
remains UNVERIFIED because it has no ordered authentic game IDs.

A bounded real916 diagnostic audit reconstructed only temporary test records
with **QA-placeholder HCE0**, not engine-generated HCE. It reproduced the QA
counts: position OFF742/t300735, conservative groups OFF589/t300582. Reversed
training enumeration gave identical MD5s for every output. All runs explicitly
remain diagnostic and authentic-game proof remains UNVERIFIED. The audit helper
deleted only its own generated temporary inputs/outputs after hashing them;
the original supplied text was preserved. Raw reports and repeat MD5s are in
forge_sol_S16_real916_result_20261026.json.

The receipt records commands, statuses, input hashes, interpreter and remaining
UNVERIFIED checks. SHA256SUMS covers this delivery and is checked from inside
the folder. During the root CPU4 native lease, verification and read-only work
used CPU1 with nice19; no full sample SQLite/output or native work was started.
