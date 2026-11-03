# R15 Job 0 - the four R14-B Code Review fixes (verified, not redone)

The four fixes were already written, tested and pushed earlier today (PC clock 10:05-10:31, before R15 started):

| CR item | fix commit (full) | branch | test that covers it |
|---|---|---|---|
| 1 install_fast_loader: is_live refuses symlinked / hard-linked copies of the live files | f124ed3f (opus-r14b-fast-loader) | head 34ea50ee28716821758034ca627689777327c9cd | test_installer.sh: linked_hard_refused, linked_sym_refused, linked_check_refused, linked_hard_refused_by_link_count, linked_sym_refused_by_link_type, linked_live_unchanged |
| 2 fl_abba refuses warmup >= batches (fl_equal too) | e29bf186 (opus-r14b-fast-loader) | same | test_cli.py: abba_warmup_equals_batches, abba_warmup_above_batches, abba_negative_warmup, abba_zero_batches, equal_dump_warmup_not_below_batches, equal_dump_negative_warmup |
| 3 pc_gate.ps1 fails when Get-Counter fails | d3ad6881 (opus-r14b-status) | head be7fdbfce042b4f45fe2237ef47025161f57401c | test_tools.sh: pc-gate-counter-throws-fails, -nothing-fails, -error-fails, -nototal-fails, -nullvalue-fails, -counter-good |
| 4 fl_fuzz: bit identity vs the old loader, "ok" with 0 batches rejected, disk floor, --flips cap | 1656e093 (opus-r14b-fast-loader) | head 34ea50ee | test_cli.py: fuzz_without_old_dll, fuzz_old_dll_missing, fuzz_flips_over_cap, fuzz_negative_flips, fuzz_disk_floor, fuzz_rules (outcome / identity / disk-floor rules) |

## Re-verification in R15 (2026-11-03 11:34:20-11:34:55 PC clock)
Fresh `git clone --shared` of both heads into `D:\o15\job0\clone_fast-loader` (34ea50ee28716821758034ca627689777327c9cd)
and `D:\o15\job0\clone_status` (be7fdbfce042b4f45fe2237ef47025161f57401c); TMP/TEMP = D:\o15\tmp; script
`D:\o15\job0\run_job0.sh`, logs `D:\o15\job0\*.log`.

| suite | result |
|---|---|
| item1/tools/test_installer.sh | 38 PASS / 0 FAIL, exit 0 |
| item1/tools/test_scope.py | 20 PASS / 0 FAIL, exit 0 |
| item1/tools/test_cli.py | 51 PASS / 0 FAIL, exit 0 |
| opus_r14b/tools/test_tools.sh | 43 PASS / 0 FAIL, exit 0 |

The R14-B CI runs on these heads were green (ffl-sanitize 41611666712 on 34ea50ee). Nothing to re-fix. Owner item kept
from R14-B: the R13 copy of pc_gate.ps1 (branch opus-r13-p1-nearmiss-ports) still has the 0 % bug; R15 uses the
fixed copy (opus_r15/tools/pc_gate.ps1 = opus_r14b/tools/pc_gate.ps1, sha256
bb33d5e7a58aa6627043a61a35a4100a5a22f67c59dd7b6ca4daf687f27910b2).
