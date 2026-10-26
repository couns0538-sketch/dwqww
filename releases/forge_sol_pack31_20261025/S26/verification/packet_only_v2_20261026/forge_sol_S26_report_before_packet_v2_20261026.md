# Forge Sol S26 net-batch development report — 2026-10-26

Delivered script implementation; **native qualification is not fully passed**.
Accepted h256_e12 stays code1ab50b2dd64d9b2f752f7f1285f6968cad2fd792 plus explicit netMD5 6d22f612c855e17c62d396d32da99ea4 / SHA256 74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b. No accepted engine, evaluation, search, training process or PC gate was changed.

The new batch tool builds private sources, verifies the strict C++20/H256 recipe, runs the first bare d11 before UCI, checks all five documentary benchmark references, qualified NNUE FMA on executable/object, one original WAC300 screen at1000ms, pin observations and full CTest. It uses a shared read-only flock file, nice19/one core,3GiB free-RAM floor and owned cleanup; all outputs stay beneath a NEW batch output. No host limits or unrelated processes are changed.

All genuine native runs executed frozen v3 SHA275b2c9a686f633d2ed9ae04cffbcb6b0c67f144d31adb36c4975adc92aa3fb0. Delivered v4 SHA4dbf73e63032d7512c6beff12fdca03b7d29e1489b6d0ae3cab26b09753ac36f adds complete configured CTest discovery and non-run rejection. Its42 synthetic/parser tests pass; original native15-case metadata/JUnit replay passes. Twenty-nine original top-level definitions are AST-identical; only check_ctest/one_net change and three inventory helpers are added. No native run is retrospectively attributed to v4. The portable setup/launcher has six final relocated synthetic tests, with all four unchanged helper hashes enforced.

## Original native results

All six separate first attempts completed: one B+lock control and five supplied nets. No engine or test expectation was edited. All five benchmark references and NNUE-scoped FMA checks pass. No speed/Elo/adoption claim.

| Net | d11 / d13 / d16 / d20 / d22 | FMA exe/object | WAC/300 | Reference | CTest | Recorded v3 status |
| --- | --- | --- | --- | --- | --- | --- |
| B_lock | 308972 / 745494 / 2460422 / 11901452 / 31111774 | 0/0 | 268 | UNKNOWN | 15/15 | PASS |
| f019 | 436412 / 1053482 / 3392913 / 9497467 / 25814067 | 0/0 | 260 | 286 FAIL | 15/15 | FAIL |
| f020 | 363303 / 799290 / 2818664 / 11474211 / 36089996 | 0/0 | 238 | 279 FAIL | 15/15 | FAIL |
| f021 | 319575 / 794601 / 3861826 / 15637403 / 24860172 | 0/0 | 242 | 287 FAIL | 15/15 | FAIL |
| f022 | 291058 / 884859 / 2658642 / 12506971 / 26484975 | 0/0 | 226 | UNKNOWN | 15/15 | PASS |
| f023 | 357687 / 836742 / 2877734 / 12036229 / 30243429 | 0/0 | 238 | UNKNOWN | 14/15 | FAIL |

f020 reference279 is supplied INFO/unconfirmed; its comparison FAIL is not a confirmed CR strength verdict. f022/f023 have no measured historical WAC reference. f023 preserves one PIN_MISMATCH (documented661 vs actual620), two WAC FAIL diagnostics and two KNOWN promotion diagnostics; its proposal remains UNREVIEWED/unapplied.

All configured builds contain19 translation units. Games0; Elo and NPS difference not measured. Per-net ASan/UBSan was not run. The v4 standalone completeness successor has separate42-test and original-JUnit replay evidence; original native processes executed v3. The old controller zombie false positive and its f023-only successor lineage remain in original/additive records.


## Decisions and limits

f019/f021 fail their historical WAC reproduction tolerance; f020 fails comparison with an explicitly INFO/unconfirmed historical value. f022/f023 WAC reference reproduction remains UNVERIFIED because those historical scores were not measured. f023's original default CTest guard fails on the documented WAC001 score661 versus observed620; original mate/move expectations stay intact. The test-only pin proposal is UNREVIEWED/unapplied. No new net is adopted and no allowlist is silently broadened.

The old outside controller stopped before f023 because its global compiler check mistook five verified state-Z zombies for live work. Original stale RUNNING bytes/exception transport evidence and a separate stop receipt remain; the original OS stderr for that outer exception was not separately captured and is not reconstructed. A separately frozen state-aware controller launched ONLY the previously unstarted f023. All first four native outcomes remained unchanged; no case was rerun. New guard tests preserve active R/S/D/unknown-state rejection. Zombie/PID1 processes were never signalled.

The portable fixture's first3s operational-watchdog attempt failed; its outer CLI log is preserved. The original unittest cleanup removed that temporary synthetic child evidence, so its cause and raw child details are UNVERIFIED. A separately preregistered15s synthetic attempt passed6/6; production/native deadlines and the original42-test fixture were unchanged. This does not rescue the first attempt.

No paired games were run: games0, Elo/uncertainty NOT MEASURED. No controlled NPS comparison, Ryzen9850X3D/Windows runtime, per-net sanitizer run, production datagen or GPU training was performed. These are UNVERIFIED, not passes. No speed or playing-strength claim is made.

## Recovery

Original native commands, streams, WAC per-position observations, CTest XML/logs, pin proposals, effective compile/link/source/input/binary hashes and process/resource observations are retained in a reversible exact-byte JSONL.gz capsule with index and unchanged S27 decoder. Compiled caches, main/test/helper ELFs, full private source copies, ZIPs and unrelated jobs are excluded from this delivery; their originals remain local. Capsule verification must finish before publication is called verified.

Next ordered engine job is S08's already built profiling option: d11 OFF/ON/profile is exact, other reference depths/perft/FMA/full CTest/sanitizers still need qualification. Continue the complete54-ID queue; this single delivered job is not completion of the whole request.
