# Job A closeout: shutdown finding0020

This supplements the frozen closeout without changing its evidence or counts.
Recorded 2026-11-15T04:20:50.463Z. Source d9a8587df8ad4d0ff1231632cb1ac72b590c04bf.
Finding resolved: false. Effective engine-work stop: true. No resume authority is granted by closing Job A.

The ASan Threads1 batch with seed202611171101 completed56 games and8291 checked searches, then failed shutdown. It receives zero clean credit. The driver assigned250ms total, escalated to SIGTERM then SIGKILL, and reaped signal9 at235.556687ms after quit. No sanitizer report appeared. Cause remains unverified; no targeted repeat had run when the finding was recorded.

Job B retains deadline 2026-11-15T05:06:50.313Z; the closeout does not reset its clock or override any stop. Current credited match games: 500.

[Full trigger, command and output](faults/asan-shutdown-0020.txt)
[Independent review](asan-shutdown-review-0020/REVIEW.md)
[Frozen Job A closeout](job-a-closeout-0420/REPORT.md)

Fault SHA256 f205dfeaa23737f6ba4d36a1f5354639d24e5400d36429084b427bdde2eb882b.
