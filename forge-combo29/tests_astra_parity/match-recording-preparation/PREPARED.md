# Job B match evidence recorder

Prepared 2026-11-15 around 01:39 UTC. No engine, match, Git, root-state or existing experiment file was changed during preparation. This helper is for the upcoming declared HindsightDepth match, not a declaration or a claim that Job A finished.

After the frozen match controller has finalized and audited a batch, root runs:

```text
node /workspace/work/parity-match-recording-preparation/record.mjs B-0001 --check
node /workspace/work/parity-match-recording-preparation/record.mjs B-0001
```

The first command rechecks without writing files or state; the second publishes text and records the batch. Neither launches an engine or Git. Root can wrap both with the existing `command.mjs` using unique labels. A whole invocation has a 420-second internal publication deadline; each audit is capped at 75 seconds and each package command at 90 seconds or the remaining deadline. Root should retain its existing outer bound below eight minutes.

Checks cover the actual declaration, source and executable hashes, frozen tool hashes, exact plan/argv/seed/opening offset, receipt, every available raw artifact's hash and byte count, and a fresh read-only re-audit of the retained files. Re-audit output must match the controller's stored summary exactly. Mutation-mode re-audit stdout/stderr/command are saved before assertions, including on failure. A failed `--check` prints that inner output to the caller's stderr instead of writing files.

The recorder keeps raw PGN, events, full engine trace, runner stdout/stderr/console, saved config, process outcome, hashes and command. Immutable hard links in a new scratch snapshot avoid a second large VM copy; source artifacts are never modified. The existing packaging helper writes text-only chunks and reconstruction manifests under:

- `tests_astra_parity/matches-hindsight/B-NNNN`
- `tests_astra_parity/matches-hindsight-records/B-NNNN`

New root namespaces are `matchRows` and `matchTotals`. `matchTotals.games`, wins/losses/draws and the five pair bins contain only complete audited batches. An incomplete batch credits zero games/pairs even if some raw games finished; those counts and every process/game fault remain in separate observation fields. A fully completed batch containing scored operational faults retains its W/L/D, while its failed status blocks further work. Disconnect games and process exits/signals are separate counters, not added together as independent crashes.

Existing source, sanitizer, corpus, push and historical-failure state is preserved. If an active state exists, it must name this batch; only that active slot is cleared. Rows append in exact order, and a different duplicate is rejected. A failed/incomplete batch sets the global stop flag; this recorder never clears one. The root-state replacement is atomic and guarded by its original SHA256. A concurrent state write causes refusal after immutable evidence is preserved, allowing root to retry later. Prior receipt/summary/artifact-manifest hashes and stored proof rows are checked; prior large chunks are not reread every batch. Current new packages are fully reconstructed and compared with their sources.

Validation completed against retained historical evidence, with no new games:

| Check | Result |
|---|---|
| Earlier completed 400-game fixture | 400 games, 200 pairs; W-L-D 114-116-170; bins 0,2,198,0,0 |
| Earlier incomplete 314-finished fixture | Zero credit; all 314 raw finished games and two aborts retained |
| Twelve accounting/state checks | Passed, including changed counts, illicit partial credit, wrong order, duplicates, active-work protection and historical-field preservation |
| Three syntax checks | Passed |
| Independent review | No accounting/packaging blocker; six additional fixture/state checks passed |

Peer review identified a failed-re-audit logging gap before use. It was corrected; the pre-review source and pins remain as `*.pre-review.txt`, and all twelve checks and three syntax checks passed again. The actual runtime declaration, native result, publication and state-transaction paths have not yet been exercised for Job B. Root should inspect the first real `--check` and record result.

Launch review is separately retained at `/workspace/work/parity-match-launch-review/REVIEW.md`. The official runner implements `-repeat` by setting `games=2`, so the existing explicit `-games 2` already repeats each opening with colors reversed. Source review also confirmed UCI, nodes-only commands, default disabled adjudication and the explicit per-engine options. Runtime option traces and PGN pairs remain audited requirements.

Final implementation hashes:

- `record.mjs`: `785a1a90039b543cdfb6bc59a61e10c8f6a4d060b3921cd87c19738f4a511e75`
- `accounting.mjs`: `234d6013b14fa9ad5179bb41cd671ab0ecee1adab75d1ad490bca8580ed91040`

Exact validation command records and outputs are adjacent. No Elo, strength or speed estimate is produced.
