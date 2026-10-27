# S17 Leak-free game-group validation split + dedupe manifest — DONE (v2 for Windows, real split with leak count 0)

`SOL_LEFTOVERS_FOR_CLAUDE.md` §2 item 8. Branch `opus-sol-S17` = `d4f4312` + `0d99f02` cherry-picked (`eeab5c27`) + `43be9428`. The worktree is `F:\opus_scratch\worktrees\opus_sol_s17`, per the new rule. This is a tool job with no engine change. Commits are `[skip ci]`; no CI run.

**Acceptance (QA):** "split on the real games read-only, leak count 0, manifest + sha256".
Sol's pass line: zero cross-split game groups; deterministic.

| item | result | evidence |
|---|---|---|
| Sol's prepared files | 22/22 sha256 OK against his list; 9 copied unchanged to `sol_v1/` | `logs/step0_*` |
| Sol's 14 tests as-is on Windows | Python 3.14: 13/14. The test fixture unlinks a file it made read-only, which Windows forbids; the tool is not at fault. Python 3.10: 7 errors, the same live-SQLite-cursor WinError 32 as S16 plus that fixture. | `logs/step1_*` |
| v2 = Sol's tool + 5 line fixes (cursor `.fetchall()`, three `write_text` with UTF-8 and LF, config read as UTF-8) | PASS 14/14 on Python 3.14 and 3.10. The test file changes only the tool filename and the one Windows fixture line. | `logs/step3_*` |
| split the real games, read-only | PASS. Chronological real window: `forge_selfplay_010` rows 9,800,000-9,999,999, plus all of 011 and all of 012 = 2,930,566 rows. Inputs were copied to scratch; every copy's md5 equals the conversion-time list. Diagnostic mode (inferred groups), real HCE, seed 20261026, 1000 bp. 479 s at Idle. | `logs/step4*`, `logs/step5_real_split.log` |
| result | 33,467 groups; 3,347 validation groups. Train 2,635,839 + validation 294,515 rows; 212 dropped (duplicate_train 185, duplicate_validation 27). | `results/forge_sol_S17_summary_20261026.json` |
| **leak count 0** | PASS. Sol's own audit: cross-split groups 0, positions 0. My independent audit agrees: groups recomputed from the original texts give the same 33,467-group partition as the ledger; 0 groups with kept rows in both parts; 0 exact positions (board32 + STM) in both outputs; 0 duplicates inside each part. Every output POS/HCE/text row equals its source row. | `logs/step6_real_leak_audit.log`, `results/real_leak_audit.json` |
| real multi-file game | PASS. The game crossing 010→011 (the file was cut mid-game) is one group of 54 + 12 rows, all in train. 011→012 starts a new game. Games continue across 18 of the 30 real shard junctions. | `logs/step6b_*`, `logs/step2_real_junctions.log` |
| manifest + sha256 | PASS. `results/real_split_outputs_SHA256SUMS` covers all 11 outputs. Sol's MD5 output manifest is included too. The shard dedupe manifest covers the 3 sealed shards: 2,930,354 unique of 2,930,566, 212 duplicate positions (165 with conflicting labels), 0 whole-file duplicates. | `results/` |
| deterministic | PASS. Real 011 was split twice: 11/11 output files byte-identical. | `logs/step7_*` |
| the audit catches leaks | PASS. A planted group leak and a planted position leak both FAIL; the clean copy passes. | `logs/step8_*` |

## Reproduce
See `README.md`. Sol's tests must run from a scratch copy with `TMP`/`TEMP` pointed at scratch, because they create folders beside themselves. The audit needs numpy (the read-only venv: Python 3.10.22, numpy 1.26.4). Machine exclusive: no.

## Left / UNVERIFIED
- The whole 248M-row dataset was not split: Sol's SQLite design runs at about 6-8k rows/s on the loaded PC, so it would take hours. A streaming version would be needed.
- No global position-level dedupe manifest over all 31 shards was built. S16 provides the whole-file md5 manifest of all 31 (all distinct) and their 013/014 overlap.
- Groups are inferred (no authoritative game IDs on the PC); authentic game isolation is UNVERIFIED and the outputs are `training_approved=false`.
- The 913 MB of split outputs stay in `F:\opus_scratch\sol_s17\real_split1` and are not committed; their sha256 are recorded.
- The 013/014 holdout is outside this window.
- No training or Elo claim.

## Files
- Tools and docs: `README.md`, `IDEA_SOURCE.md`, `sol_v1/` (Sol, unchanged), `gamesplit_v2/` (v2, unchanged pinned dependencies, v2 tests).
- Checks: `audit_split_leak.py`, `audit_planted_leak_check.py`, `real_window_build.py`, `real_junctions_check.py`.
- Evidence: `results/`, `logs/` (no archives).
- Index: `FILES.txt`; checksums in `SHA256SUMS`.
