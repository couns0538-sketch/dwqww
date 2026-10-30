# Independent sealed-filter audit

Run **only after the filter process exits successfully**. The auditor requires
`summary.json` with `SEALED`, a complete manifest, no failure record and clean
worker exits. It writes only to a new audit directory outside the source run.
It never starts an engine, edits a dataset or reruns search/filter policies.

From the repository root, the full-run command is:

```bash
nice -n 19 python3 -B validation/astra-a1-data/full10m_audit/run_audit_once.py \
  --run-dir /tmp/astra-a1-filter-full-10m-v2 \
  --receipt-dir validation/astra-a1-data/full10m_audit/post_seal_10000000_20261030 \
  --frozen-dir validation/astra-a1-data/filter_full10m_v2_protocol \
  --expected-rows 10000000 --verify-external-hashes --verify-holdout-source
```

The receipt directory must not exist. Keep it after success or failure; choose
a new name for another attempt. The wrapper preserves exact argv, source hashes,
stdout, stderr, real exit status and actual OS CPU/wall timing. Its 30-minute
timeout applies only to its own read-only audit process.

The bounded-memory audit checks:

- Every sealed manifest entry against its bytes, SHA256 and MD5; output digests,
  final progress/summary agreement and optional original-input/probe hashes.
- Frozen filter/reader/IPC implementation hashes against the run's recorded
  revision. The current edited source is not silently substituted.
- All decision indices, first-drop counts, waterfall denominators and fractions,
  per-shard totals, and original retained file/row/output indices.
- Every retained board/score/meta against original FPOS, full FEN against the
  original sidecar, and HCE/teacher fields against the original native response.
- Ordered merge of every worker's original request/response streams, with
  matching IDs/full FENs, flags, score/node/depth bounds, incomplete-teacher
  handling, process receipts, query CPU sums and speculative-query counts.
- Read-only SQL counts, retained membership for every output identity, digest
  validity, retained/holdout identity overlap zero, and output/index identity
  count plus independent 256-bit sum/XOR checks.
- With `--verify-holdout-source`, every original supplied holdout row is parsed
  by the exact hashed `forge_pos.py` from `--frozen-dir` and looked up in the
  read-only holdout index, comparing the full board+STM key. Original file hashes
  and row counts are checked; duplicated source rows are counted individually.
  This closes source-to-index coverage for the supplied 013 prefix; it does not
  certify missing portions of 013, holdout 014, game IDs or extra index entries.

It **does not** rerun chess legality/search, prove native scores correct, replay
cheap or near-duplicate rules, reconstruct history, or certify unavailable
holdout 014/full 013/game IDs. Query timers remain query timers, not measured
total process CPU. Native legality/evaluation and the game's repetition history
are not inferred from this evidence check.

## Verified small-run result

The real sealed 10k pilot passed: 10,000 decisions, 9,274 retained rows and SQL
memberships, 9,972 original native responses, 9,731 used native results and 241
speculative responses reconcile. All 21 original source files were unchanged.
Its holdout index is empty, so this pilot does not establish production holdout
exclusion.

The audit used 0.685 seconds of CPU, 0.728 seconds wall and 17,004 KiB peak RSS.
At pilot qualification the strict 10M run had not been executed. It subsequently **PASSED**; see `post_seal_10000000_20261030/audit/summary.json` for all 10M decisions, 9,206,371 kept rows, 9,976,584 original native responses and 1.5M original holdout-row coverage. Actual full audit: 605.169 CPU seconds, 617.760 wall seconds, peak RSS 709,948 KiB. A simple extrapolation of the
small-run CPU rate is roughly 10–12 CPU minutes; large SQL/cache/I/O effects may
change that. Do not report a full-run PASS from this pilot.
Original holdout coverage adds a full scalar parse and index lookup for each of
the supplied 1.5M source rows; its complete runtime is not yet measured here.

Six regression tests (eight initial audit executions) pass on retained copies:
missing manifest, wrong retained index, native ID/score/ok corruption, missing
native response and inserted SQL holdout overlap. Each modified artifact's
copied manifest is refreshed so rejection reaches semantic checks. A tightened
missing-last-response case additionally passes with an explicit count mismatch.
Original tests, copies, pre-mutation bytes, logs and source hashes are retained
under `fixtures/`.

The final source-coverage revision passes **10 test methods**: eight CLI audits
plus seven direct helper calls. Tiny legal text and FPOS holdouts (three rows,
two unique identities) pass; a missing key, wrong original row count and wrong
parser hash each fail explicitly. Parser/auditor snapshots and before/after
hashes are preserved in `fixtures/holdout-helper-1793335523272569051-354789/`;
final CLI evidence is in `fixtures/run-1793335523351075214-354789/`.
The tested auditor SHA256 is
`e8f37f824a4fa2458a388bdfd8850b4a3cccfba5e0733ebf26a14fbed0e2d716`.
The initial tested revision remains in Git commit
`2d1076e7fbdb5e11225328eddcc0376f519c7b2e`, with SHA256
`133f97c6c60292454b9e9d9ed14bc09f103f643f293fd5a94895b7224630ab8f`.

IDEA_SOURCE: this project's frozen filter/IPC/FPOS contracts and original
evidence; the user's read-only, exact-revision and preservation requirements.
