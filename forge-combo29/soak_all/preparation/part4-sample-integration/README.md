# Part4 sampled KRK integration — scratch proposal only

Prepared in `/workspace/work/part4-sample-integration`. No native build/search, controller invocation, state write, branch/ref change or repository edit was performed. The existing clean and partial smoke evidence was read only and remains preparation, not Part4 sample coverage. All synthetic fixtures are likewise excluded.

Files ready for root review:

- `make-spec.mjs`: pure exported `makeSpec({id,offset})`, plus CLI that writes one fresh spec. Never starts a workload. Phase is **4sample**, separate from the existing Part4 observation/counter summary.
- `4sample-0001.spec.json`: concrete unexecuted example. Target run output and log do not get created by generation.
- `audit-sample.mjs`: read-only original/preserved evidence auditor; writes only an explicitly named fresh report. No controller import, native invocation, fault-file write or state write.
- `control-proposed.mjs` and `control-proposal.diff.txt`: narrow proposal against frozen `control-baseline.mjs` SHA256 `5222d635077c6364ebb52454f3057f7289b478450ba05b1bdafc20cc4cd03595`. Production control.mjs remained equal to that baseline at final source capture. Root must review/adopt only this change; preserve any later controller edits.
- `fixtures.mjs`, `fixture-final-check.txt`: 25 checks passed, native_runs=0, state_writes=0. `syntax-checks.txt` and `syntax-final-auditor.txt` record syntax checks. `source-hashes-final.json.txt` records final helper, driver, engine binary and source hashes.

## Exact proposed workload

For every batch the generator requires a fresh phase/id, output directory and log. It freezes hashes for the audit executable, both release engines, three audit/transport/oracle sources and merged search/uci/header sources. The engine options are set by the existing native driver: Threads1, Hash16, OwnBookfalse, depth13, four variants lock/merged × UseNNUE false/true; all new t22 options remain at defaults; every observation uses a fresh process and cold ucinewgame.

```
/usr/bin/taskset -c 4 /workspace/work/all-run/part4-review/mate_bound_audit \
  --lock /workspace/work/soak-run/build-lock-rel/forge \
  --merged /workspace/work/all-run/builds/release/forge \
  --out /workspace/work/all-run/part4-sample/4sample-0001 \
  --roots 10000 --seed 1296127045 --limit 10000 --offset 0 \
  --seconds 300 --timeout-ms 5000
```

This command is proposed, **not executed**. Controller run-spec already adds its 450s external timeout/5s kill grace. The native budget is 300s, response timeout 5000ms, and shutdown grace 500ms. Native construction/corpus time is inside its budget. No timing/speed claim follows from these limits.

The exact countMap is completed_units -> completed_units, and each of these destinations -> counts.<same name>:
`trials positive_mates_checked mate_bound_check_failures illegal_moves operational_faults faults unexpected_exits sanitizer_reports reproductions reproduction_faults`.
Configuration, elapsed time, corpus size, partial counts and cursor are not aggregated as completed work. Counts.trials/faults and outcome categories are baseline-only. unexpected_exits/sanitizer_reports also include noninterrupted reproduction observations from completed roots; these are observations, not numbers of distinct bugs or warning blocks.

## Controller contract that needs adoption

CountMap alone is insufficient with current control.mjs: mode=mate_bound_audit is unknown, so a native incomplete_units=1 makes the whole batch unrecordable even if earlier roots completed. The proposal recognizes this exact mode, still requires explicit countMap, and independently validates safe-integer counters, next_offset=offset+completed_units, trials=4*completed_units, reproductions=10*faults, partial/interrupted invariants and observed=completed+partial for every counter. It then exposes the explicit completed-unit/exclusion contract. Zero-completed-root batches remain unrecordable. Other unknown schemas retain their existing exclusion behavior. No integer tolerance was added.

Controller support is necessary before root executes the proposed run-spec. The proposal is not installed by any supplied helper.

## Root-operated use, after review

Generate each spec with the audited cursor from the preceding batch. Use a fresh id even when repeating a partial root.

```
node /workspace/work/part4-sample-integration/make-spec.mjs \
  --id 1 --offset 0 --spec /workspace/work/all-run/specs/4sample-0001.json
```

No run-spec is invoked automatically. Root owns all execution/checkpoints/state. **Immediately before launch, root must recompute every spec.expectedHashes SHA256 and refuse launch on any mismatch.** The generator declares pre-run provenance and the auditor compares current hashes afterward; control.mjs does not enforce expectedHashes itself. A preparation-time match is not a substitute for the immediate prelaunch check. The controller's existing evidence collector automatically preserves the log, immutable metadata and every file recursively under --out, with byte/hash manifests and text chunks. That includes config.json, roots.tsv, results.jsonl, summary.json, complete per-observation stdout/input/observed-shutdown transcripts, stderr, and native fault sidecars.

After a batch is finished and its manifest exists, audit the preserved evidence, not active state:

```
node /workspace/work/part4-sample-integration/audit-sample.mjs \
  --metadata /workspace/work/all-run/logs/4sample-0001.txt.run-spec.json \
  --manifest /workspace/work/dwqww-all/forge-combo29/soak_all/batches/4sample-0001.evidence/manifest.txt \
  --evidence-root /workspace/work/dwqww-all/forge-combo29/soak_all \
  --report /workspace/work/all-run/4sample-0001-audit.json
```

The metadata argument denotes its original source path; the auditor reconstructs that file from the verified manifest. `--allow-direct` instead permits inspection of original files when a checkpoint is not available; it is mutually exclusive with --manifest and is explicitly labelled as not proving checkpoint preservation. `--preparation` relaxes official workload limits/hash requirements only for old preparation fixtures; never use it to validate official sample coverage. Report paths use exclusive creation and will not overwrite existing files.

Exit0 means accounting/evidence valid and no retained findings; exit1 means accounting/evidence invalid; exit2 means valid accounting with actual findings retained. `accounting_valid` is never a claim of engine correctness. Always inspect `safety_findings` and `fault_candidates`.

For cross-batch reconciliation, exported `auditSequence(reports)` requires matching corpus hash/seed/phase and contiguous completed cursors, sums completed counters only and identifies prior partial roots actually completed in later audited units. It does not mark a retry complete merely because another batch started and never writes state.

## Audit scope and fault handling

The auditor independently reconciles every RESULT/UNIT with results.jsonl and SUMMARY, all four ordered variants per completed root, baseline-conditional repeats1..10, per-unit and aggregate counters, noninterrupted partial counters, and separately excluded interrupted observations. A partial root may contain all four baselines if its final reproduction sequence was interrupted. A budget can also stop between roots with incomplete_units0 and next_offset below10000. Both cases resume at next_offset.

It verifies the full 10000-root permutation geometrically (distinct squares; nonadjacent kings; Black king not in rook check, including White-king blockers), not by engine-score selection. It checks real raw inputs, returned bestmove, final complete score/depth/node line, observed shutdown status, canonical unique per-observation filenames, native fault sidecars, full logs/metadata, all manifest bytes/hashes/chunks, and frozen source/binary hashes. It does not rerun an engine or recompute DTM.

Nonzero exit66, unexpected signals, sanitizer text and shutdown failures cannot be hidden by faults=0. Budget-induced signals are distinguished from unexpected exits. Interrupted-row diagnostics are retained despite exclusion from all counters. Main-log-only sanitizer diagnostics are retained as unattributed findings with ten reproductions pending; mirrored observation lines are not treated as new bugs. Diagnostics outside the native predicate do not acquire an invented frequency.

No actual sample fault has occurred in this preparation, so no numbered-fault materializer is installed or executed. If a future batch has a native faulty baseline, the read-only report supplies a proposal keyed by phase+batch+root+build+NNUE, exact FEN/options via metadata, full actual records/transcripts and actual additional reproduction frequency. Partial sequences explicitly show the remaining repetitions. Root can then review a concrete materialization action. Upperbound criterion failures are labelled as criterion failures, not proof of a false bound. CP-only observations are not mate-score misses in this phase.

Limits: finite White KRK sample, not universal mate correctness. The native oracle shares board/attack primitives and has no repetition/fifty-move model. Audit validates recorded legality/DTM classification and its arithmetic/provenance; it does not independently regenerate those chess results. Source/binary hashes establish the versions captured and observed at audit time, not proof against an intervening substitution. No Elo, speed or strength claim is made.

## Preparation evidence

`fixture-first-failure.txt` preserves a real rerun of an early fixture failure: its synthetic interrupted-startup transcript had two shutdown records, but the fixture changed only the first exit code. The auditor correctly rejected the last raw shutdown/JSON mismatch. The fixture mutation was corrected to update both synthetic records; production/native evidence and auditor accounting were not relaxed. Later fixture transcripts and the final25-pass result are retained.

The independent peer contract/review evidence is under `/workspace/work/part4-sample-contract-peer`. Peer findings led to requiring raw shutdown provenance, canonical unique transcript filenames, refusing mixed original/manifest fallback and retaining unattributed main-log diagnostics. Dedicated final fixtures cover each. Existing smoke/partial evidence was inspected only; no new native run took place.
