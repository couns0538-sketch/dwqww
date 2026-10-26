# S18 t500 diagnostic source readiness — 2026-10-26

This is one NEW source-only diagnostic runner, not a repair or acceptance of the old failed repeat. Runtime is NOT RUN. The original 168-file checkpoint and all original failures remain unchanged.

The 21 pure tests pass in Python 3.12. No filter, Torch, real `/proc` sampler, fixture child, SQL connection or partial-row investigation was run. The retained first RED log is a missing-implementation import failure, not a claim of an engine regression test. Later GREEN logs preserve the test progression.

The runner pins the unchanged S16 v2 tool and original codec, ten original input sizes/hashes, the original interpreter, the old failed receipt and the existing S08 owned-group cleanup helper. It requires a coordinator reference and a brand-new nonsymlink `/tmp` output outside protected data/history/source paths. Existing outputs cannot be resumed or overwritten.

One supervised 120-second interval reserves its final second for cleanup, so work stops at 119 seconds. That is a stricter NEW diagnostic, not identical original 120-second child timing. Read-only preflight hashing and final receipt checks sit outside that interval. Budget overshoot and final overhead are reported explicitly; OS scheduling cannot be given a hard wall-time guarantee.

Own-child sampling records CPU ticks, scheduler counters, wait channel, I/O, status and monotonic timestamps. Shared cgroup pressure is context, not cause attribution. Missing, denied and truncated observations remain unavailable, never zero. Output observations use bounded lstat metadata on NEW outputs only. No SQLite database, WAL, ledger or output body is opened by the observer. Both child streams and the observer traceback are bounded, and truncation stops the child. Python-level observer exception capture excludes preflight, launch and transport; it does not recreate the original outer traceback.

The original child limit stays at 1 GiB virtual address space. Supervisor soft AS is 256 MiB and a sampled 512 MiB child RSS watchdog stops abnormal growth. This does not constitute a strict aggregate 1 GiB cgroup RAM cap. No cgroup configuration is modified.

The pinned cleanup helper uses a temporary subreaper and signals/reaps only the NEW Popen group. No saved original PID is used for control. Normal child exit still yields `acceptance=false` and is not data validation. A separate later comparison can validate completed outputs against t500_first; the old repeat stays FAIL even if the new case completes.

See the JSON preregistration for the exact future command. It has NOT been executed. Parent review and an explicit fresh resource window remain required. Full-data histograms, real013/014/game provenance, training, postscore and Elo are UNVERIFIED/NOT RUN.
