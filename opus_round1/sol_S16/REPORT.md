# S16 Real 013/014 overlap check — DONE (Sol filter v3 + read-only scanner, real run on the PC data)

`SOL_LEFTOVERS_FOR_CLAUDE.md` §2 item 7. Branch `opus-sol-S16` = `d4f4312` + `0d99f02` cherry-picked (`65eaa214`) + `6364f36c`. This is a tool job with no engine change. Commits are `[skip ci]`; no CI run.

**Acceptance (QA):** "publish tool + README; real 013/014 run read-only on the PC data (no writes next to it)".

| item | result | evidence |
|---|---|---|
| where the real data is | `D:\grok-pc-data\forge_push\nnue_data\pos` and `...\hce` (FPOS/FHCE v1), plus ordered text in `D:\grok-pc-data\selfplay_out`. It is not under `F:\forge_nnue_train` (logs only). The live trainer holds out exactly 013+014 and trains on 001-012 + 015-031. There is no Job D output on the PC. | `logs/step1_data_inventory.log` |
| publish tool + README | PASS. `sol_v2/`: Sol's 14 delivery-ready files, unchanged, verified by his SHA256SUMS. `filter_v3/`: v3 + runners + tests. The new read-only scanner `forge_sol_S16_overlap_scan.py`. `README.md`. | |
| Sol's 41 tests (21 legacy + 20 S16) as-is on Windows | FAIL. Python 3.14: 40/41, because `write_text` defaults to cp1252 and cannot encode a Unicode stem. Python 3.10: 39/41, because a live SQLite cursor keeps `work.sqlite` open after `close()`, so cleanup fails with WinError 32. | `logs/step2_*` |
| v3 = v2 + 4 line fixes (cursor `.fetchall()`, three `write_text` with UTF-8 and LF) | PASS 41/41 on Python 3.14 and on the venv's 3.10. The pwsh one-command runner passes 1/1 on both. This closes Sol's "PowerShell/Windows" and "Python 3.10" UNVERIFIED items. | `logs/step3_*` |
| real 013/014 run, read-only, no writes next to the data | PASS. Scanner run 3 used the committed tool (sha256 `4bdd2520…`): 448 s at Idle priority, free RAM ≥ 12 GiB. Outputs went only to `F:\opus_scratch\sol_s16\real_run3`; the scanner refuses an output dir inside any input dir and opens inputs read-only. Run 2 gave byte-identical results. | `logs/step6_real_run3_final.log`, `results/` |
| scanner tests / planted bugs | PASS 13/13. 14/14 mutants caught; the first mutation run exposed 4 test gaps, which were fixed. | `logs/step4_*`, `logs/step8_*` |
| cross-validation vs Sol v3 on real records | RECONCILED on a 250k-row fixture copied from 015/013/016 with a real straddling game. Holdout unique positions 99,994 = 99,994; `holdout_position` rows equal row for row (500); `holdout_game_group` rows equal row for row (28). | `logs/step5_*` |

## Real 013/014 result (29 training shards = the trainer's `--train` list)
| quantity | value |
|---|---|
| holdout 013 + 014 | 16,388,575 rows; 16,387,223 unique positions (1,352 duplicate rows, verified exactly) |
| training | 231,913,894 rows |
| training rows whose position (board32 + side to move) is in the holdout | **6,069** (0.0026 %), present in every shard (3 to 339 per shard) |
| distinct holdout positions found / holdout rows affected | 6,009 / 6,010 (0.037 % of the holdout) |
| of the 6,069, label differs (score or result) | 5,042 |
| 64-bit key collisions rejected by the exact 33-byte check | 0 |
| whole-file duplicates | none (31 distinct md5); all 14 md5s recorded at conversion (`F:\forge_nnue_train\data_md5s.txt`) still match |
| inferred holdout game groups | 186,841 (median 83 rows); interleaving tripwire PASS (max 4 boundaries per 100 rows) |
| text vs POS | stm, score and result equal on every holdout row; boards equal on 16,439 sampled rows |
| games straddling a holdout/training junction (012→013, 014→015) | 0; both junctions start a new game |
| holdout groups with ≥1 position in training | 4,084 |
| holdout groups with all positions in training | 105: 98 one-row groups and 7 opening fragments of 3-14 rows, all starting at fullmove 5. No full game is duplicated. |
| overlapped holdout rows by fullmove | 1-10: 3,474; 11-20: 365; 21-40: 5; 41-80: 1,878; 81+: 288 |

Committed outputs (all in `results/`):
- the summary JSON;
- a removal list of 6,069 rows (`stem,row,reason,holdout_stem,holdout_row,label_conflict`);
- a holdout-row bitmap (gzip);
- the run's own SHA256SUMS.

Nothing was removed; removing the listed rows is the owner's decision.

## Notes
- Windows `PROCESS_MODE_BACKGROUND_BEGIN` starved the scan on the loaded PC. It reached 31k rows/s and was stopped by the wall budget at shard 003 (run 1, `logs/step6_real_run1_background_mode.log`). The I/O probe showed I/O was not the bottleneck. The default is therefore the Idle priority class, which is never raised.
- Sol's filter was not run on the full data. Its SQLite design needs about 300 B/row (≈70 GB) and hours. The scanner gives the counts read-only in under 10 minutes and agrees with Sol's v3 row for row on real records.

## Reproduce
See `README.md` (scanner, v3 filter, tests, cross-validation). On the PC, the read-only venv `C:\Users\Administrator\grok-pc\nnue\.venv` provides Python 3.10.22 and numpy 1.26.4; nothing was installed. Machine exclusive: no.

## Left / UNVERIFIED
- Game IDs are inferred with Sol's conservative rule; the PC has no authoritative IDs. Authentic game overlap is UNVERIFIED, and production mode of Sol's filter cannot run on the PC.
- The scanner does not count training-internal duplicates (Sol's filter does, at SQLite cost).
- Sol's 200k t300 reproduction (157,666 kept) was not re-run here.
- Label conflicts are counted against the first holdout row of each position.
- No training-gain or Elo claim.

## Files
- Tools and docs: `README.md`, `IDEA_SOURCE.md`, `sol_v2/` (Sol, unchanged), `filter_v3/` (v3, unchanged dependency copy, tests, runners, pwsh test).
- Scanner: `forge_sol_S16_overlap_scan.py`, `test_forge_sol_S16_overlap_scan.py`, `mutation_check_scan.py`.
- Cross-validation and detail: `xval_build_fixture.py`, `xval_reconcile.py`, `real_run_group_detail.py`.
- Evidence: `results/`, `logs/` (archives `step5_xval_final_outputs.tar.gz` 30,085 B, `step6_real_run1_run2_outputs.tar.gz` 9,218 B).
- Index: `FILES.txt`; checksums in `SHA256SUMS`.
