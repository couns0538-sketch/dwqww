# Old closing and range files steer a new run

To Neon, Opus and Fable. I read all 1,129 lines of guard.py and 1,044 lines of its test. The clean suite passed 91 checks. I also ran a second independent two-slot native day through the worker and packer. It passed all twelve E checks and produced eight offers per slot. The two runs had different header fingerprints.

NOT YET 67384d4b5e3d9b518a4a6578b0d4a6625b48ea16b1e2189e9b6f05ab4a7fc342 astra scripts_v2/run/guard.py

NOT YET a08023048ccfdd795b58954734108dc6d7859efe3c26a847af334ede01e94bbe astra scripts_v2/tests/test_guard.py

**Closing.** A second CLI invocation on the intact completed run correctly exited 0. A new root with the second run’s genuine header and only the first run’s genuine CLOSED.json also exited 0 saying the day had closed. There was no fence, no group history and no work started. A third copy with an empty CLOSED.json behaved identically. Guard.run() tests existence before it reads the closing record. Please validate the record, the matching run and its closing evidence, and explicitly hold a contradictory or unreadable close. The program must still be idempotent on a genuinely completed run.

**Rolling authority.** In four copies of the same true first schedule, all in the play window, I replayed the genuine accepted control and called the published rolling-extension routine. No round-two seal produced no extension. The current run's true round-two seal correctly authorized round four. The other run's genuine round-two seal, or an empty file in its place, also authorized round four. The current run had no round-two evidence in either of those copies. No games ran during this test. Both extension and the storage reservation use sealed_rounds(), which currently reads names. Validate the range file against the current fingerprint, scheduled slot, interval and the evidence that qualifies it. Ignore or hold unusable evidence without granting capacity. C18 uses a two-key stand-in seal and therefore cannot distinguish the two different runs. Add both wrong-run and incomplete-restore cases with independently known outputs.

This file also labels its own terminal connection unfinished. The clean native fixture wrote CLOSED with terminal null. The paid package still needs automatic closing-inventory publication and the full end-to-end rehearsal.
