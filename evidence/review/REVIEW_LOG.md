# Direct one-hour review

Start: 2026-11-03T18:44:47Z. Earliest completion: 2026-11-03T19:44:47Z.
No subagents or external review service. Source identities captured before review.

Review areas:
1. Windows path aliases, filesystem side effects, subprocess limits and interrupted capture.
2. Numeric/FEN/TSV/FPOS validation, complete alignment and input mutation detection.
3. Independent real-data count and mate-flag readback; normalized distribution reporting.
4. Pack census/checksum changes, report consistency, runtime/source identity and reproducibility.
5. Skill-package scope/link validation, full-suite rerun and allowed-file Git diff.

Confirmed findings, regressions and dispositions are appended below. A passed
fixture or checksum seal does not qualify missing production game provenance.

### R1 — Parser/path/count findings (18:45–18:55 UTC)
- Confirmed RED: Windows reserved device/wildcard paths admitted by lexical validation.
- Confirmed RED: Unicode/multiline FEN normalized rather than rejected; None raised wrong exception.
- Confirmed RED: newline-terminated overlong line bypassed pending-buffer limit.
- Confirmed RED: bool publication counts equaled integer1; old JSON bool score/index/depth/node fields equaled numeric values.
- Fixed with explicit original-text/path/type checks. Core13 and P5 audit9 tests GREEN.
- Independent real-data readback PASS: 999921 + 440000 rows, 3718 exact mate-ledger matches,
  score/White sums, WDL/STM counts, paired deltas and independent SHA256-FEN duplicate sets agree.
- Report improvement: add normalized percentages because cohort sizes differ.
- Flag-ledger improvement: retain full producer label object plus exact input path/line for each mate row.
- Final real QC must be rerun after these changes; qc01 remains preserved evidence of its original source revision.

### R2 — Independent readback and evidence completeness (18:51–19:10 UTC)
- Separate raw CSV/FPOS implementation agrees with all primary cohort and mate-ledger counts.
- Confirmed RED: restoring an input's original mtime after same-size replacement escaped metadata-only final checks.
  Final input receipt publication now rereads and compares complete SHA256/MD5 content. Regression GREEN.
- Extended mate records with exact producer object and input line/path; final independent readback checks these fields.
- Added non-mate descriptive profiles without rewriting/filtering any source or producing training inputs.
- Pack qualification review found success counters alone do not establish per-test coverage; adversarial fixtures authored.
  Their RED/GREEN execution waits for the single-worker property review to finish.
- Windows PowerShell case-insensitive grouping initially suggested duplicate pytest node IDs; case-sensitive check
  confirmed 590 distinct IDs. Validation must preserve parameter-case differences such as KK vs kk.

### R3 — Supervision and pack review (19:10 UTC onward)
- Confirmed by retained property-run observation: Python progress flushes were hidden by the parent FileStream buffer.
  Launcher uses unbuffered write-through capture for new runs.
- Direct control-flow review: supervisor exceptions could bypass owned-child shutdown and omit a failure receipt.
  New catch/finally records the failure and stops only the process tree it created.
- Launcher now rejects reparse ancestors and pins Python/PowerShell source hashes before and after each new run.
- Pack qualification now has adversarial fixtures for skipped, omitted, duplicated and subtest-only evidence.
- Pack verification has a mutation-during-read regression for an added payload or changed manifest.
- Final QC adds a completion manifest over statistics, input receipts and mate ledger; pack requires its successful process receipt.
- Structural skill links now name exact checkout files; global installed skills remain untouched.

### R4 — Executed regression/property results (19:19 UTC onward)
- Twenty-minute seeded property review PASS: 4,098,816 legal-position cases and 41,276 PGN-format pairs;
  exact 1200.0 seconds, four source identities unchanged. Original source-version receipt retained.
- Pack mutation cases reproduced RED (extra payload and changed checksum manifest accepted), then GREEN after final census/manifest checks.
- Pack per-test qualification fixtures RED (missing validation API), then GREEN with exact case-sensitive collection/call matching.
- Old publication totals reproduced RED (done counts exceeding totals; inconsistent row/shard completion), then GREEN.
- Native launcher probe PASS: one CPU affinity, priority64/Idle, temp under owned root, GPU masks -1.
- Native deadline probe PASS: receipt exit70/DEADLINE; PID9860 was absent after shutdown.
- Some launch attempts were refused at >70% sampled CPU load; no forced admission or extra worker was used.
- Full-suite05 exposed a containment regression during collection: subprocess.DEVNULL was mistaken for a filesystem output.
  Narrow fix permits only the exact OS null-sink open without create/truncate/append flags; named device paths stay rejected.
  Full-suite06 is the required rerun; failed full-suite05 remains retained.

### R5 — Final data and publication-boundary checks (19:24–19:37 UTC)
- Final full-suite06: 603 normal tests + 60 subtests passed; zero failures/skips, 134.84 seconds.
  Sixteen warnings are dependency deprecations, hidden-CUDA discovery and the inherited scheduler-only fixture;
  no optimizer/training call was introduced to silence a warning.
- Final QC qc02 PASS: 1,439,921 rows, 3,718 flags, 289.438 seconds; unchanged jobA/jobB final label hashes.
- Independent readback02 PASS, including full producer objects and exact source file/line in every mate flag.
- Non-mate descriptive counts: new997204, old438999. Neither population was edited or exported for training.
- Final scoped pack02 PASS: 17 payloads; sources match full-suite06 and qc02 receipts.
- Real pack CLI negative copies: whitespace-only QC alteration rejected by SHA256; omitted normal test result rejected;
  neither attempt created an output directory. One intervening CPU admission refusal was retried without changing limits.
- Root p5qc seal/independent verify PASS:18 payloads. Root pgnpack seal/verify PASS:41 payloads.
- Source-mutation native fixture: exit70/SOURCE_CHANGED with differing before/after hashes, as required.
- Reparse-entry fixture: refused before worker/run-directory creation; owned alias removed, target preserved.
- Source version note: the 1200-second property run preceded the narrow DEVNULL exception;
  parser/FPOS/game-hash bytes did not change, and the final policy is covered by full-suite06.
Review CLOSED PASS at 2026-11-03T19:45:52.3475514+00:00; elapsed 3665.3475514 seconds. Final tested source hashes, root seals and 13 report MD5 rows agree. No unresolved confirmed implementation defect remains; external game provenance stays UNVERIFIED.
