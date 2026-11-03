# Closed work queue — UNPROVEN

Completed 2026-11-03 09:25:35 UTC. Improvement work and the full final review
(08:25:06–09:25:35 UTC) are closed. All owned long-running jobs have ended;
confirmed fixes and validation are recorded in RESULTS.md and REVIEW_LOG.md.
Core/packer candidate cb3d24a1, v9 handoff and full 564+11 suite are current.
The former v8/544-case queue below is historical, not an instruction to restart
completed scans or replace current evidence. No training or engine work ran.

## Historical planning notes

# Current bounded work queue — UNPROVEN

Authorized schedule: 2026-11-03 04:23–08:23 UTC improvement; 08:23–09:23 UTC
deep review, fixes and verification. Continue the original task across user
steering/compaction. No engine edits, training, GPU, crew controls or data removal.

08:04 update: CodeRabbit blocked twice by comparison file cap; configuration
restored absent. Current core remains d6e1aae8 and v8/544+11 checks remain valid.
An approved numeric-only census is running at one worker after its466,506-row
pilot/19fixtures passed. It may overlap initial read-only final-hour review;
freeze core and audit_native_counters.py until it closes. Do not package its
active logs. Full scan is not complete evidence yet. Final packaging follows
closed jobs and final review; all original resource limits remain in force.

07:48 update: steps1–6 complete. Current full suite544+11 PASS; all999,953 native
inputs and fresh v8 handoff PASS. CodeRabbit deep committed review started early
on d6e1aae8 implementation to leave repair time before the reserved final hour;
its log is active and must not be inventoried yet. Core/tests stay frozen during
that review. Final packer approved after16 authored fixture checks; actual
packaging stays queued until logs close. Runtime scratch in the ready commands
now lives outside protected handoff directories. Final-hour schedule unchanged.

07:28 update: steps 1–5 below are complete. Admission union: 304,999,573 rows
PASS; corrected lock and intentional JSONL byte equality PASS; Lichess/native
repairs reviewed and tested. Step 6 is active. Full suite v1 passed 542+11;
a subsequent command-path binding fix passed 51 affected tests and awaits
focused recheck/new full run. Fresh proof-driver fixtures: 11 PASS; actual v8
handoff and selected-cohort native admission still pending. Steps 7–8 remain
reserved for the final hour. Older queued wording below is historical.

1. Let the two reviewed single-worker admission scans finish with validator
   files frozen. Both use BelowNormal and occupy the total two-worker budget.
   Active artifacts: `C:/astra8_data/extension5h_20261103/admission_part0` and
   `admission_part1` (currently `.partial`). Do not inventory active logs.
2. When the first slot is free, run the new union/lock harness tests and safe
   RED boundary/race regressions with one computing worker. Do not run the full
   suite alongside the other scan because existing tests can use both slots.
   Do not send unsafe pre-fix whitespace/overflow fixtures to the C ABI.
   Include test_receipt_byte_identity.py and test_manifest_entry_races.py;
   retain the latter's healthy CPU-check/stub-delegation controls. The draft
   BoundInputs exact-byte repair is also pending an actual RED reproduction.
3. Once both scans close, verify command exits, complete disjoint source union,
   counts, source identities/hashes, validator identities and sealed references.
   Record actual source attribution before changing records.py. Preserve all
   failures; a prefix or a still-running job is not full-corpus evidence.
4. Implement the reviewed Lichess selection/castling and native input/identity
   repairs after actual RED reproductions. Keep board_from_fen, record and
   selfplay_record unchanged if possible; record exact changed function hashes.
   Run quick checks, request focused rechecks, and assess every finding.
5. Verify corrected startpos/Kiwipete d5 and five bench pins through the exact
   FD3A5190 UCI executable. Byte-compare and fully hash both cleared JSONL files.
   Preserve the complete protected v7 tree; its manifest must retain the pin.
6. Replay current native-input admission over the complete cleared cohort,
   without native allocation or new full datasets. Run full CPU tests, fresh
   legacy/result/bounded-filter proofs and a new v8 handoff with both CPU
   preflights. No training command may be executed without --check.
7. Use the reserved final hour for the scoped authenticated CodeRabbit review,
   main assessment/fixes, focused reviewer rechecks and necessary validation.
   No paid-credit override. Preserve exact reviewed code/config/log identities.
8. Hash closed extension artifacts, bind historical evidence with original
   source attribution, run the Forge evidence consistency checker, update the
   handoff documents/skills and push the final branch tip. R12 inherits that
   final reviewed tip, not e526fc12. All strength remains UNPROVEN.

Draft tools and tests are locally prepared but have not passed execution yet;
they must not be called accepted. If storage blocks the optional full-corpus
bonus, preserve it and redirect work within the remaining authorized resource
limits. D: must remain >=50 GB; C: >50 GB; aggregate retained artifacts <=15 GB.
