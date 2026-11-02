# NNUEWideOutput evidence handover — UNPROVEN

Review owners: Engine QA and CR. Source R9 f43a26aeed2448379fc2916b25f31ead8707b0ec.
The exact kit v2.3 LTO+PGO -Expose znver5 candidate is
775EDEA1D476A3A18C64AF63F53C55D6E29A4571556AAD2666E87F18A6EF4284.
Both fresh builds pc1-a and pc2-a and the recovered R9 binary have that SHA256.
NNUEWideOutput remains default false; the proposed candidate setting is true.
All strength and speed claims remain UNPROVEN until the required measurements
and crew review pass. The R9 +2.17% estimate is not accepted evidence of a gain.

| Check | Result | Original evidence |
|---|---|---|
| Two kit binaries identical | PASS | build-proof01/REPORT.json and pc1-a/pc2-a artifacts |
| OFF and ON d11/13/16/20/22 | PASS both builds | build-proof01, original ident logs |
| Perft5 start/kiwipete | PASS both builds | build-proof01, original ident logs |
| T1 UCI smoke, OFF/ON | PASS | smoke-01/REPORT.json |
| ASan+UBSan short self-play | PASS rerun of recovered auxiliary build | sanitizer-01/REPORT.json and original build provenance |
| ASan and UBSan positive controls | PASS: deliberately detected | sanitizer-01 original logs |
| Pinned 12k raw-bit evaluation parity | PASS, 0 differing roots | native-parity/evidence and parity/check-launch01/stdout.log |
| One-weight negative control | PASS: 3975 differing roots detected | native-parity/evidence; separate mutated source |
| T4 smoke | UNVERIFIED, host loaded | RESULTS.md |
| A/A noise gate | FAIL, eligible IQR1.098525pp exceeds1pp | timing/run01/summary.json;39complete/10eligible |
| Candidate ABBA comparison | NOT RUN, blocked by calibration failure | all timing records retained |

Pins (T1, isolated bench Hash16): 312866 / 862329 / 3024920 / 12389307 / 34048354.
Perft5: startpos4865609, kiwipete193690690. UCI default Hash32 is unrelated to
the bench's isolated Searcher(16). Smoke, sanitizer and timing set Hash16 explicitly.

The original kit MD5 is729FE7275C3C01D22C751CB751D5C9D2; scheduling-only copies
change BelowNormal to Idle. Generic proof helper Werror-witness requirements do
not describe this exact kit. The pinned kit enforces its fatal profile-warning
scan; the reviewed collector checks the kit's success receipts and authentic
identity/check outputs. No compiler flags or generic helper PASS are
invented. The sanitizer SHA a56762278935af93344680ba147a9076f63b52504e2495a686d7fe5f28a4a2aa
was recovered with its R9 build provenance and rerun, not rebuilt in this run.

Only the production executable with SHA775EDEA1D476A3A18C64AF63F53C55D6E29A4571556AAD2666E87F18A6EF4284
is a candidate. Plain builds, instrumented builds, sanitizer executables and parity
diagnostics are auxiliary evidence and must never be substituted into a gate.
The mutated weight exists only in a separate diagnostic source tree.

Pinned fens12k SHA256:c01c0e6a49fb9aaab535058bd7280c33b8735e0f8bd40834f1c029843a75a265.
Embedded production weights SHA256:a7ebcf3a319675f347e6e8e3f2539901d38d8036cb9b5935f31dd43d084c9638.
All original failed attempts are retained. See RESULTS.md for review findings,
confirmed fixes and the exact scope of each successful check.

## Crew follow-up

This is an evidence handoff. It does not authorize or start a gate. QA should run
official ABBA and, after its own acceptance checks, a short non-regression SPRT
against FD3A51903E73DC1FA20263F1DCC7A4EEC506592E9F25E50B8F8739CA36873072.
Use UHO. Keep 8moves_v3 HELD confirmations separate. Candidate NNUEWideOutput=true;
baseline OFF/default. Crew chooses and records the official time control, limits,
fresh start/srand, and inventory coverage before enqueueing. No trusted fresh seed
inventory was supplied here, so no seed-clearance or gate-readiness claim is made.

Complete T4 smoke when resources permit. Resolve the timing result according to
the preregistered protocol; do not relax eligibility/noise thresholds after seeing
the data. Incomplete or failed calibration is inconclusive, not a measured gain.
Do not merge, enable by default, or label this candidate accepted from this pack.

## Final calibration (same FD3A5190 binary in both labels)

| Retained blocks | Count | Median % | Q1 % | Q3 % | IQR pp | Min % | Max % |
|---|---:|---:|---:|---:|---:|---:|---:|
| Eligible |10|0.361084|-0.473842|0.624683|1.098525|-1.467115|1.411394|
| All complete |39|-1.173411|-4.421909|0.716115|5.138024|-24.280917|8.671963|

Calibration ran2026-11-02 06:21:02Z through07:07:56Z. Median and extreme bounds
passed, dispersion failed. There are zero candidate comparison blocks. The native
runner returned1 for CALIBRATION_FAIL with no capture errors or disk-floor breach.
No post-hoc threshold changes or additional calibration retries were made.
Required progress checkpoint Git I/O at22:37 and22:56 Pacific is disclosed;
eligibility remained telemetry-only and every affected attempt was retained.

Independent final-record review passed2273 consistency checks, including156
transcript hashes and312 warmup/timed node pins. It recomputed eligibility from
recorded derived telemetry: raw CPU counter snapshots were not retained. The
protocol matches the preregistration commit and current remote ancestry; the
session push output establishes publication before start, with no separate
immutable push-time receipt. These limitations remain explicit in
timing/review01/REVIEW.md. Preserve this run unchanged; any future timing adapter
should retain raw counter snapshots and a dedicated publication receipt.
