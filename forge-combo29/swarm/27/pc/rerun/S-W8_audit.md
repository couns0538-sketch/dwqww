## S-W8: after fixing the settings bug, every harness sends exactly 22 PC20 options — and what that re-check found

### The audit

After S-W7 I checked whether my other harnesses really applied PC20, by importing each and counting the option list
it builds. **Two defects, both now fixed:**

| defect | harnesses | effect |
|---|---|---|
| `OwnBook false` sent **twice** (once in the base list, once in `PC20X`) | 8 | 23 options sent, not 22 — harmless in effect (same value, idempotent) but it means the count assertion in my own guard would have failed on the correct runs |
| `OwnBook false` **missing** from `PC20X` | 6 | 21 options — the run was **not PC20** despite the label |

**All 13 harnesses that claim PC20 now build exactly 22 options** (Hash, Threads, 14 S14, 5 PC20 switches, OwnBook),
verified by importing each and counting. `check_settings.py` also had the duplication, now corrected.

### What the re-check changed in my findings

**S-C14 (pos-90 warm repeats) re-run with PC20 genuinely applied, using the engine's own `time` field:**

| run in one process | engine time | nodes |
|---|---|---|
| 1 | 24 ms | 75,311 |
| 2 | 3 ms | 9,701 |
| 3 | 6 ms | 21,526 |
| 4 | 0 ms | 1,597 |
| 5 | 2 ms | 6,088 |
| 6 | 2 ms | 6,512 |

**The conclusion holds** — warm repeats get faster (24 ms → 0–6 ms) and the node counts collapse — but **the specific
node figures differ from the no-PC20 run** (which gave 79,980 → 1,324). So S-C14's direction is confirmed under the
correct settings and its exact numbers are superseded by this table.

**S-C18/S-C18a/S-C18b stay withdrawn** (S-W7). Nothing in this audit rescues them.

### The honest state of my settings discipline

- **The count assertion is now the first thing to run**: `check_settings.py` PASSes at 22, FAILs at 25 (exit 1,
  verified without a pipeline).
- **Thirteen harnesses audited by import, not by reading.** Reading would not have found the 21-option cases,
  because the missing entry was in a list literal appended later.
- **What is still not proven:** that the option *values* I send are the ones a finding claims (the S14 values are
  copied by hand in each harness). A duplicate-value check would catch a transcription error; I have not built one.
