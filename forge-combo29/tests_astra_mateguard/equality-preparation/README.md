# Prepared successor equality stage

Preparation only. No equality searches were launched. Native comparator compilation succeeded at 2026-11-14T20:46:46.187Z; stdout and stderr were empty, exit0. Exact argv and input/object hashes are in `compile.json.txt` and `input-hashes.json.txt`. Syntax checks, byte comparisons and a first-config dry run all exited0; the expected wrapper `diff -u` exited1 because its two path declarations changed. Full actual outputs are in `readiness-commands.json.txt`.

The frozen C++ comparator and POSIX transport are byte-identical to the proven original drivers. Only the JS wrapper's output root and binary defaults changed. Native comparison fields, counts, eligibility, ten repetitions, partial-record recovery, and timeouts remain unchanged.

Binary identities:

- Candidate: `/workspace/work/r4-run/builds/guard-enabled/forge`, SHA256 `710cfcf73fcc3b9897281113759ed18565feb167eb0effe7023cbbe1706037dc`.
- Reference: `/workspace/work/all-run/builds/release/forge`, SHA256 `e2788a101d11acfca637b14471e2b067ae11e551500cfb0656019a193ec2cb3e`, frozen f27 source / e04556dd documentation point.
- The legacy `--lock` argument and JSON key name now denote that reference. They do **not** denote `/workspace/work/soak-run/build-lock-rel/forge` or branch lock/combo29-20261110.

Every comparison starts a fresh engine process and `ucinewgame`. Threads1, Hash16 and OwnBookfalse are set explicitly; all other options retain that binary's defaults, including MateAlphaGuardfalse and HindsightDepthfalse. The legacy CONFIG options object enumerates only the original options; it was preserved unchanged. Full UCI startup transcripts accompany differences and contain the candidate's advertised defaults.

## First bounded batch, when the root authorizes equality to start

```text
timeout -k 2 475 node /workspace/work/r4-run/command.mjs successor-equality-0001 node /workspace/work/r4-run/equality-tools/compare4.mjs run /workspace/work/r4-run/equality-configs/E-0001.json.txt
```

This launches four workers for at most330seconds each plus bounded shutdown. Their per-worker timeout is345seconds with5seconds kill allowance. The outer command runner retains exact argv and output and remains under8minutes. Output is fresh `/workspace/work/r4-run/equality-batches/E-0001/`; the wrapper refuses to overwrite it. No global state, refs, commits or pushes are managed by these tools.

## Cursor continuation

After reading the real batch summary, create the next explicit config:

```text
node /workspace/work/r4-run/equality-tools/successor.mjs /workspace/work/r4-run/equality-configs/E-0001.json.txt /workspace/work/r4-run/equality-batches/E-0001/summary.txt /workspace/work/r4-run/equality-configs/E-0002.json.txt /workspace/work/r4-run/equality-batches/E-0002 1449420002
```

The seed is metadata only; it never shuffles the corpus. Increment the batch identity and seed for each successor. The utility verifies binary pins and config/summary cursor continuity, uses only accepted committed records, and leaves rejected workers at the old cursor. An incomplete position, including incomplete ten-repeat evidence, is excluded and retried at SUMMARY.next_offset. Inspect any validation/transport/process failure before launching; do not silently relabel it. Do not derive offsets from eligible counts alone because excluded records advance the input cursor. Once every remainingEligible is zero, the utility refuses another batch.

## Every difference requires attribution

The inherited driver records and repeats **both** low-clock and high-clock differences. Its `fault_positions`, `hasCompletedFaults`, `required_equality` labels, and process exit verdict implement the old halfmove<80 gate. Therefore exit0 or zero legacy fault_positions does not establish the new all-position equality requirement.

Use the read-only aggregate on every completed summary in chronological order:

```text
node /workspace/work/r4-run/equality-tools/audit-all-differences.mjs /workspace/work/r4-run/equality-batches/E-0001/summary.txt /workspace/work/r4-run/equality-batches/E-0002/summary.txt
```

Retain its full stdout in a fresh text file. It verifies summary/JSONL artifact hashes and cursor/count continuity, combines both clock groups, indexes each difference by original global record index and exact FEN, retains reproduction frequencies and evidence paths, and separately includes any reproduction-only difference. Every indexed entry starts `requiresAttribution:true`. It exits1 for an incomplete corpus or any unexplained difference; operational/validation failures exit3. It never assigns a difference to r3-21/r3-24/r4-09 merely because those fixes exist. Root analysis must supply the actual attribution; all high-clock cases remain in scope.

## Same original100k selection

The immutable source corpus SHA256 is `571fd73cf5ec3ddad78d6afc1dd65c57d7f4c3f8eaa424cbfbabe94a4a8b06c1`; it has199020 records. The frozen manifest selects the first25000 **eligible** comparisons of each of four round-robin shards. This is the same previous100k set, not necessarily the first100k eligible records in global source order. Duplicates remain separate records; there is no engine-result filtering.

`original-selection.json.txt` was derived read-only from the seven accepted old batches. Per-worker final cursors are25000,25363,25000,25352; exclusions are0,363,0,352. It hashes each selected `(local index, exact FEN)` sequence. At completion the aggregate requires all four new selection hashes and cursors to match, in addition to100000 eligible comparisons. Global input record index is `4 * local_index + worker`.

Preparation changed no engine source, old artifact, reference or state. Only C++/HPP/MD/TXT evidence should be published. Live `.mjs` tools and the native comparator executable remain in the VM; inert `.mjs.txt` copies are retained here. Existing native logs report actual values only; no speed or strength conclusion is made.

## Budget and storage planning from the retained old run

`historical-planning.json.txt` records the seven actual old batches:100000 eligible comparisons,2057.091seconds of active batch wall time (34.285minutes),181082620bytes of artifacts (about173MiB). Of those bytes,172643869 are JSONL result records,6247195 are full difference/partial traces,1223741 are pending-fault text, and967815 are metadata/console text. This is historical protocol evidence, not a measurement of the new tree.

Keep four workers with330second budgets, one wrapper batch at a time, after sanitizer play finishes. Each worker runs one Threads1 engine at a time, so four workers fit the VM's four-CPU quota. Initially reserve45–60minutes of the remaining task budget and reassess after the first real batch; additional differing positions require ten repetition pairs and can change the needed time substantially. Native test builds or other CPU-heavy work should not overlap if they threaten the bounded equality budget.

At the old volume, raw evidence plus one publication copy would use about346MiB. Provision at least0.5GiB initially, check actual disk growth after each batch, and keep headroom for existing-suite binaries. At preparation time the filesystem had4784152576bytes free. Reuse the original corpus/shards read-only, do not copy the old174MiB result tree, and publish each new completed batch once with its hashes instead of making repeated full trace snapshots. Preserve all new failures and partial records; do not discard them to meet a storage estimate.
