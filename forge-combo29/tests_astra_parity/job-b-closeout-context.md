# Job B closeout context

Closure evidence recorded 2026-11-15T05:01:43.995Z. [Frozen match closeout](job-b-closeout-final/REPORT.md).

Job B closed with 1400 credited games of the declared 6,000-game target. Actual last native finish: 2026-11-15T05:00:27.265Z. Sum of native batch intervals: 1743.2379999999998 seconds. The declaration deadline remained 2026-11-15T05:06:50.313Z. Elapsed declaration time is not continuous play.

The frozen closure preserves the original ASan finding metadata separately from match faults. The original finding remains unresolved, but its recorded repeat count describes the initial fault record. A later authorized full replay matched all 8,291 searches and exited naturally in 38.103431 ms, with no stderr, signals or reports. That replay receives zero soak credit and does not change the failed batch.

[Replay result and limitations](asan-shutdown-0020-replay-report.md)
[Independent replay review](asan-shutdown-result-review-0020/REVIEW.md)

Current global engine stop: false. Scoped release continuation came from Fable0020. This closure changes no engine source, match receipt, old audit, Job A count or deadline.

Job C starts only after both A and B are reported, under its existing separate contract. The persistent-run timing question is pending in question0021; the owner's eight-minute command limit remains in force.
