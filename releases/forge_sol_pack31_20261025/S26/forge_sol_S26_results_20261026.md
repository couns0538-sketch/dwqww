# S26 original native results — 2026-10-26

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
