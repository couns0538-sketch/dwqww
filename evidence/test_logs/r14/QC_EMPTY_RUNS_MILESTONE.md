# QC malformed empty-run fix

Recorded: 2026-11-03 13:45:17 Vienna.

Scope: `D:\a14\tools\qc_core.py` and
`D:\a14\tests\test_r14_qc_fixes.py`. The running overlap scan's pinned
r14_overlap.py, r14_scan.py and run_policy.py were not changed.

Confirmed defect: fen_info summed consecutive empty-square digits, accepting
malformed ranks such as `44`, `r12k2r` and `R3K11R`. DuplicateIndex then counted
these rows as valid keys and could report full coverage. An earlier key-spelling
test incorrectly characterized `/44/` as valid FEN; that fixture was corrected
to retain its separate castling-order normalization check with valid ranks.

Fix: a two-line rank check rejects adjacent digits in the range 1 through 8.
The existing DuplicateIndex failure path now records the rejection. Each mixed
valid/malformed fixture reports two attempted rows, one valid key, one missing
key, one parse failure, fill rate 0.5 and UNVERIFIED for every key. Its zero
overlap counts cannot be mistaken for complete coverage.

Validation:

- `qc-empty-runs-red01`: 6 failed, 28 passed, 12 subtests passed, 0.58 seconds.
  All three direct parser fixtures and three DuplicateIndex fixtures failed
  because no ValueError was raised.
- `qc-empty-runs-green01`: 34 passed, 12 subtests passed, 0.58 seconds.
- `qc-empty-runs-green02`: 49 passed, 36 subtests passed, 0.67 seconds. This adds
  the existing core/policy suite to the QC and p5 audit fixtures.
- CPU admission: red used CPU 3 at 0% busy; green01 CPU 1 at 40%; green02 CPU 0
  at 7%. Every test process was Idle and pinned to one CPU. CPU 2 was excluded.
- All fixture files, caches and logs remained below D:\a14. No training or
  inherited datafilter test collection ran. No large data scan was launched.

Self-review checked rejection before decoding, unchanged valid-rank handling,
DuplicateIndex denominators and the corrected prior characterization fixture.
The candidate is frozen for focused independent recheck. Full project regression
remains a later parent task; independent review is not claimed here.

| Full PC path | MD5 |
| --- | --- |
| D:\a14\tools\qc_core.py | 90fbce947d83e8d0801200145813e985 |
| D:\a14\tests\test_r14_qc_fixes.py | 6d15bd5a2411de8b7858a0a10a8d7da5 |
| D:\a14\tools\r14_overlap.py | 812fbbbcccbc05ed20f74456bf1ddc80 |
| D:\a14\tools\r14_scan.py | c5d56b1ee5de5db65f64d1ba14dbd7ca |
| D:\a14\tools\run_policy.py | d124dae9782a7c791164182e7ddb4958 |
| D:\a14\evidence\test_logs\r14\qc-empty-runs-command.ps1 | 309a1b631112bb7385d0e9f9b326e1ee |
| D:\a14\evidence\test_logs\r14\qc-empty-runs-red01\output.log | 9a19159fff0f3d055052efca31fca65b |
| D:\a14\evidence\test_logs\r14\qc-empty-runs-green01\output.log | f95e10bd2c488e0d2d6baadc9cae4928 |
| D:\a14\evidence\test_logs\r14\qc-empty-runs-green02\output.log | 081f765a44521890d23730bf9c485c2d |

Final free-space sample: D: 61,517,717,504 bytes; C: 136,890,040,320 bytes.
No commits were made by this task.
