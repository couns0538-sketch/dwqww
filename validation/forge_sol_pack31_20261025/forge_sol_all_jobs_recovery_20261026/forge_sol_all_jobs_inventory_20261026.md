# Forge all-jobs inventory — 2026-10-26

Snapshot: `b99a41b18f351a97f19392a06bde1655a23fe0e9`, `forge/sol-pack31-20261025`. Read-only audit; no engines, compilers, network or Git writes.

**54 finite IDs: 9 delivered-scope done, 44 pending (including optional S24 and four Astra jobs), 1 dropped (S23).** Within S01–S50 alone: 9 done, 40 pending, 1 dropped. S48 is an S33 add-on counted once. S00 omits16 IDs: S34–S47/S49/S50. Its repeated S48 order entry is not another job.

Done means bounded delivered scope; it does not turn unrun PC evidence or an engine gain into a verified result. All225 checksum-manifest entries rehashed with no missing/hash failures. Prior publication receipts were inspected and local content matched; no new native or HTTP checks ran.

Nine completed jobs: S01–S06, S25, S27, S28. Scope gaps remain explicit: S03 optional-suite fresh ASan, S28 standalone `--execute` and live AUTOLOCK, G104 actual paired profile, Windows runtime and PC speed/strength. S28 optional4 remains deferred. S28 checklist fixtures do not complete separate S47.

Resource snapshot: about11.35MiB free, about32.5GiB RAM available. pwsh/cmake/fastchess absent from PATH, not assumed absent everywhere. S35/S49 require a presently unavailable PATH runtime. Another23 pending jobs need bounded native/training resource preflight; they are not declared impossible. Fifteen have no proven runtime/disk blocker. Mandatory tests remain mandatory.

Unique remaining Sol order: S33, S48, S07, S26, S08, S09, S10, S11, S12, S13, S14, S29, S15, S16, S17, S18, S19, S20, S21, S30, S31, S32, S22, S34, S35, S37, S38, S39, S40, S41, S42, S43, S44, S45, S46, S47, S49, S50, S36, S24. Then A1, A2, A3, A7, never concurrent with Sol.

| ID | Job | State |
|---|---|---|
| S01 | DONE (merged 11:10 CET, CR same-diff PASS) | Done, bounded scope |
| S02 | REWORKED: unknown-option warning, review fix-ups | Done, bounded scope |
| S03 | REWORKED: fixed-reference suite, review fix-ups | Done, bounded scope |
| S04 | attacks::init first-Board race fix | Done, bounded scope |
| S05 | FMA checker v2 + ctest wiring | Done, bounded scope |
| S06 | Gate-log miner + gate triage | Done, bounded scope |
| S07 | Depth-sweep + WAC300 screen tool | Pending |
| S08 | Dead-feature audit + FORGE_PROF counters + bench_prof | Pending; resource preflight |
| S09 | 8 piece-count output buckets on the residual net | Pending; resource preflight |
| S10 | Search ideas batch | Pending; resource preflight |
| S11 | Node-exact speed pack | Pending; resource preflight |
| S12 | Lazy accumulator updates + why Job A's refresh path was slow | Pending; resource preflight |
| S13 | TT prefetch + 64-byte bucket static_assert | Pending; resource preflight |
| S14 | Allocation-free MovePicker + mailbox piece_type | Pending; resource preflight |
| S15 | SPSA harness | Pending |
| S16 | Real 013/014 overlap check tool, ready to run | Pending |
| S17 | Leak-free game-ID validation split + dedupe manifest | Pending |
| S18 | Filter threshold sweep + small ablation | Pending; resource preflight |
| S19 | Score-to-WDL scale fit per phase | Pending |
| S20 | Relabel/rescore tool + 1M sample | Pending; resource preflight |
| S21 | int16 range study on all 13 nets + clipped-export tool | Pending |
| S22 | TSan audit at Threads=2/4 + Lazy SMP depth sanity | Pending; resource preflight |
| S23 | DROPPED | Dropped |
| S24 | OPTIONAL: int32 shelf cleanup | Pending; optional/last |
| S25 | Engine output-contract test | Done, bounded scope |
| S26 | Net-pack batch script | Pending; resource preflight |
| S27 | Patch hygiene pre-check | Done, bounded scope |
| S28 | REWORK (fix-ups S28-1..4): QA PASS with notes 12:30 CET | Done, bounded scope |
| S29 | Speed stack | Pending; resource preflight |
| S30 | Epoch and data-size learning-curve study | Pending; resource preflight |
| S31 | Checkpoint-averaging tool | Pending; resource preflight |
| S32 | Self-play datagen v2 | Pending; resource preflight |
| S33 | NEW (crew 6/8): SPRT power and gate planner | Pending |
| S34 | Gate-manifest schema validator | Pending |
| S35 | Locked-log watcher test harness | Pending; pwsh runtime absent from PATH |
| S36 | Same-diff merge verifier | Pending |
| S37 | NNUE inference microbench + per-stage cost table | Pending; resource preflight |
| S38 | Gate speed / TL / time-use audit | Pending; resource preflight |
| S39 | v3b trainer fixed-size epoch option (v3c) | Pending; resource preflight |
| S40 | Cross-folder datagen dedupe + merge tool | Pending |
| S41 | Eval-scale check for a new lock net | Pending; resource preflight |
| S42 | Higher-variance opening book study | Pending; resource preflight |
| S43 | S26 add-on: absolute paths, `--base`, bench-ref file | Pending; resource preflight |
| S44 | Elo-vs-epochs fit with the new gate points | Pending |
| S45 | New-lock rebase readiness for speed and search candidates | Pending; resource preflight |
| S46 | Auto-promote rule replay simulator (Sol, tooling) | Pending |
| S47 | AUTO-LOCK audit verifier and net-only tree check (Sol, lock tooling) | Pending |
| S48 | Gate comparability guard and winner's-curse correction (Sol, add-on to S33) | Pending |
| S49 | PC speed check that works under gate load (Sol, tool only) | Pending; pwsh runtime absent from PATH |
| S50 | Trainer warm-start `--init-weights PATH` (Sol, NNUE trainer, default OFF) | Pending; resource preflight |
| A1 | Correction-history / history rework | Pending after Sol |
| A2 | King-bucket feasibility design doc | Pending after Sol |
| A3 | Full-NNUE design + trainer + converter + smoke net, NO engine integration yet | Pending after Sol |
| A7 | Long-training recipe design for the H256 residual net | Pending after Sol |

The companion JSON retains exact goal/input/deliver/pass text and original line numbers for every finite job, later resume reworks, hash-bound source references, completion evidence, missing inputs and resource constraints. The16 missing checkpoint entries are reconstructed from the actual spec.

Independent bounded offline preparation can cover S34 schema fixtures, S36 approved-diff checks (deliver last), S17 text game-group splits, S40 real-format merge fixtures, S46 rule simulator and S47 new net-only/full-packet checks. Root integrates in the saved order and keeps engine changes sequential. S39/S50 share trainer v3c and need one coordinated owner.

S33+S48 comes next: full630-cell grid (15 Elo values ×7 plans ×6 profiles), >=20k Monte-Carlo trials per cell, six analytic agreement controls, and separate concurrency5/7/8. Actual G104 pair profile and real concurrency8 results remain UNVERIFIED. Then S07, S26 and the saved queue.

S46/S47 use the authoritative user eleven-point AUTOLOCK checklist plus later inflight, CAP-LATE Z-1/Z-2, fallback-note and reviewed-successor additions. Real AUTOLOCK packet/full reviewed script artifact remain missing. A checker never creates CR approval. Original f006 pin proposals stay ATTACHED, not APPLIED.

The four Astra finite jobs remain pending after Sol. Section12 self-directed S51+ work is open-ended followup, outside the finite checklist. The old pool optional labels do not silently remove jobs from the current user request to finish all; S24 remains explicitly optional/last.
