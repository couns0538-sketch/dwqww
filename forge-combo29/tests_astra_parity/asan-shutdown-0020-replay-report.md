# Shutdown finding0020: one full retained-input replay

The authorized replay completed on 2026-11-15 at04:42:51 UTC. All24,994 recorded commands and8,291 searches were replayed in one process, preserving56 game resets and28 pairs. Every completed search matched the retained stable tuple; independent trace verification repeated legality, score and label checks. There were zero tuple differences.

The unchanged ASan/UBSan engine exited naturally with code0, signal0, no driver signal and no sanitizer diagnostic. Complete engine stderr contained0 bytes (SHA256 e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855). Quit-to-observed-reap was38.103431ms. The declared natural grace was5000ms; no TERM/KILL was sent.

The original shutdown failure did not recur in this single replay. This observation does not support the proposed explanation that exit work exceeded250ms. Original command timing, scheduler/allocator state and concurrent sibling load were not recreated. The original cause and recurrence frequency remain unresolved; this is one diagnostic, not ten repetitions.

The original batch remains a failed shutdown with zero clean credit. This diagnostic also receives zero soak credit. Job A remains closed at846 accepted games and120,313 searches. Release Job B continues under the explicit prior Fable0020 decision; this report does not reinterpret the original audit or grant any new test authority.

[Actual audit and full shutdown fields](logs/asan-shutdown-0020-audit-full-001.stdout.txt)
[Complete raw replay, process metadata and hashes](asan-shutdown-diagnostic-0020-full-001)
[Frozen implementation](asan-shutdown-implementation-0020/PREPARED.md)
[Independent implementation review](asan-shutdown-implementation-review-0020/native-review.md)
[Original full fault](faults/asan-shutdown-0020.txt)
[Fable0020 decision](inputs/FABLE_ANSWER_0020.md.txt)

Audit SHA256 c43b65fe6a60c8984cb061fcc198b8714ec5cca7da6d7f5e849a8a109c4379df.
Raw replay stdout SHA256 5fe8b02e5cdd9ee2718b78b37bee3f058dfcf990895de35c579fcd05b415c1c8.
Source d9a8587df8ad4d0ff1231632cb1ac72b590c04bf; ASan binary SHA256 4c34f8384318b1f23a4ce9ffac3cbfb81169cbf5b2ce120f8021237eb2200090.
