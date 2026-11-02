# Astra R9 results

Started 2026-11-01 13:57 America/Los_Angeles; six-hour deadline 19:57.
Current status: c1 correctness PASS; advisory speed gate PASS +2.172299% paired
median. Final independent packet/artifact review PASS. Elo: UNPROVEN.
No gate, strength match or merge. QA handover line and packaged exe in FINAL_REPORT.md.

## Frozen identities

- Production source implementation: fb58080, immutable snapshot D:\a9\c1.
- Lock SHA256: FD3A51903E73DC1FA20263F1DCC7A4EEC506592E9F25E50B8F8739CA36873072.
- Kit v2.3 MD5: 729FE7275C3C01D22C751CB751D5C9D2; unchanged, -Expose, znver5, LTO+PGO.
- Candidate b1 = b2 SHA256: 775EDEA1D476A3A18C64AF63F53C55D6E29A4571556AAD2666E87F18A6EF4284.
- Embedded network SHA256 unchanged: A7EBCF3A319675F347E6E8E3F2539901D38D8036CB9B5935F31DD43D084C9638.
- Source manifests: evidence/lock-source.sha256 and evidence/c1-source.json.
- Default-off UCI option: NNUEWideOutput. Only NNUE output packing changes.

## Completed proof

| Check | Result |
|---|---|
| Lock profile before changes | PASS: 24112 samples; output arithmetic 4.380%, quiet SIMD updates 2.999%, refresh 0 samples |
| Separate exact diagnostic harnesses | PASS: 12000 FENs, 684200 evaluations, 324100 moves, 12000 nulls; digest 3bd3b27ac5a60483 |
| Raw float checks and ON execution | PASS: all 16 lanes and pre-conversion output bits; ON counter 684200 |
| Two production kit builds | PASS: identical executable hashes; longest gcda path 83 characters |
| OFF/ON d11/13/16/20/22 pins | PASS: 312866 / 862329 / 3024920 / 12389307 / 34048354 |
| OFF/ON perft 5 startpos/kiwipete | PASS: 4865609 / 193690690 |
| Production lock/OFF/ON corpus parity | PASS: all 12000 score/node/bestmove records identical, every bestmove legal |
| T1/T4 movetime smoke | PASS: 24 legal bestmoves per mode, awaited before quit |
| Native ASan+UBSan self-play | PASS: 8 games and 572 legal plies per mode; zero reports/illegal moves |
| Sanitizer positive controls | PASS: deliberate overflow and out-of-bounds access detected |
| Kit FMA/profile checks | PASS: vfmadd 0, zero missing-profile warnings; one benign serial-LTRANS warning |

Sanitizer executable SHA256: A56762278935AF93344680BA147A9076F63B52504E2495A686D7FE5F28A4A2AA.
Sanitizer compiler archive SHA256: FD5462B7F5D93B2FF981FCD3F9C7E427E47F3203C64EA91C27BCC444EEBD74CD.
Crew corpus: 12000 unique legal FENs, SHA256
c01c0e6a49fb9aaab535058bd7280c33b8735e0f8bd40834f1c029843a75a265.
gcov-dump unavailable; its arcs digest is record-only and optional under the kit.

## Timing and next action

Experiment 1 is INCONCLUSIVE: A/A paired median +1.679% (IQR 3.354 points), candidate
paired median +1.632% (IQR 7.868 points), 21/56 contaminated runs. All measured nodes
exact. These numbers do not establish a gain. Raw logs/table data retained.

Experiment 2 uses preregistered longer warmup and whole-block replacement, as the
approved plan permits. Eligibility uses only fixed CPU-time/sibling telemetry,
never NPS or winner. Four eligible A/A blocks must pass original control criteria,
then ten eligible ABBA blocks are required. A second failed A/A control stops c1.
Completed A/A control PASS: four eligible blocks from 23 attempts, paired median
+0.626352%, IQR 0.943615 points. ABBA completed ten eligible blocks from 48 attempts
(20 pairs), median gain +2.172299%, IQR 1.100699 points, range +0.307487% to
+3.656076%. Quiet arm NPS medians: lock 2219512, candidate 2268064.5.
All-attempt paired gain +1.518022%, IQR 6.998095 points. All rows and rejected
blocks retained. Full table: TIMING_TABLES.md. Prior nine-block checkpoint's manual
16:10 label was approximate and late; commit was at 16:07–16:08. Raw UTC rows prevail.

Next: final push verification; Engine QA owns official timing. Fresh audit04 PASS1226;
packaged executable hash matches b1/b2. FINAL_REPORT.md contains the proof, limitations
and QA line. Official timing remains Engine QA's responsibility.
All-attempt unpaired NPS medians are lock 2188345 versus candidate 2160675 (lower
candidate median). M5 independent timing recomputation PASS; reviewer requested
prominent disclosure of this different statistic, now included in FINAL_REPORT.md.

## Review milestones and retained failures

- M1: independent source review and focused recheck PASS. Fixed raw-float,
  combined-residual-eval and long-sequence test gaps. Reviewed nnue.cpp SHA256
  D11B4EED401A3F6C05EA7A5C8917E1E7F933A9E1BDF3E3992D44C62424F3F635.
- M2: production correctness and validation-harness review PASS. Fixed absolute
  timeout, setup-exception child cleanup and during-run interference telemetry.
  Three regression tests PASS. Production source/executable unchanged.
- M3: first timing rejected; protocol-v2 independent review PASS to run only.
  Reusable skill schema/forward-test PASS, saved under skills/, not globally installed.
- M4: independent packet review and focused recheck PASS. Corrected manual
  592-versus-572 ply-count error; raw tests unaffected and failed audit retained.
  Audit03 PASS 1226 checks, including source-commit blobs and mode attribution.
  Auxiliary build provenance, complete FMA-family scan (zero hits) and current
  status text retained. No outstanding correctness/reporting finding.
- M5: independent timing and final report/artifact review PASS. All 284 runs and
  71 block-table rows checked; fixed selection and stats match raw evidence.
  Requested all-attempt unpaired NPS disclosure added; no unresolved findings.
  Candidate source fb58080 / exe775EDEA1 unchanged. Final safety/artifact audit PASS.
- a1 kit launch failed before compilation: legacy PowerShell could not load
  Get-FileHash. Retained failure; corrected host to pwsh 7.6.8, new tags b1/b2.
- profile01 setup blocked on oversized stdin queue; no profile accepted from it.
  Corrected profile02 completed before engine edits; both attempts retained.

## Safety and experiment decisions

Shallow independent clone avoids copying 7.57 GiB history into the 10 GiB budget.
Original checkout, lock source, datafilter, other branches/jobs/queues untouched.
Writes confined to D:\a9. Initial reserves C 154.82 GiB/D 77.77 GiB; host metadata
records later reserves and verifies CPUs 2/3 share one physical core.
Long jobs Idle, other owned work BelowNormal; approved brief T4 exception confined
to two logical CPUs. Read-only process check found no orphaned owned compute worker;
an unrelated active Python process has all-CPU affinity and was left untouched.

Refresh cache skipped because the profile provided no >=1% opportunity on this
workload. Integer/VNNI deferred because byte inputs and changed rounding lack an
exactness proof. Neither is claimed universally unprofitable. No GPL engine code
or constants copied; external Python chess library used only as a test oracle.
