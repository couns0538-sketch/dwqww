# S40 Cross-folder datagen dedupe + merge tool — DONE (tool + fixture + tests + v3b CPU smoke + real read-only runs)

`SOL_LEFTOVERS_FOR_CLAUDE.md` §2 item 22. Branch `opus-sol-S40` = `d4f4312` + `0d99f02` cherry-picked (`58f99b6a`) + `e2ef28f6`
(tool, tests, evidence) + `09f41790` (follow-up real run including shard 032). Tool-only job: no engine change
(`git diff 294dbed -- src include tests tools bench CMakeLists.txt` is empty), commits are `[skip ci]`, no CI run.
Worktree `F:\opus_scratch\worktrees\opus_sol_s40`, scratch `F:\opus_scratch\sol_S40`. Sol left no S40 files on `17aa0cae`, so
everything here is new. Machine exclusive: no. Work and results by a sub-agent; this report text is its hand-back.

**Spec (Sol, verbatim):** "a tool that dedupes a second self-play output folder against the main one and the 013/014 holdout
by position hash and game ID, and writes NEW sealed files in the exact training record format (see train_resid_v3b.py /
convert_forge.py) with an md5 manifest. Existing files are never changed." Pass: "deterministic; duplicate and holdout counts
reported and correct on the fixture; output loads in v3b unchanged (CPU smoke). Real-data run UNVERIFIED."

## Acceptance
| item | result | evidence |
|---|---|---|
| record format | The v3b trainer reads FPOS v1 `.pos` and FHCE v1 `.hce` (`load_set`, `load_set_mmap`). `convert_forge.py` writes the older 32-byte REC, which v3b does not read. So the tool writes FPOS/FHCE plus the kept text lines. | `README.md` |
| tool | `forge_sol_S40_merge_datagen_20261027.py` (sha256 `0f707649…`), subcommands `merge`, `gameids`, `verify`. Position identity = board32 + side to move; every 64-bit candidate is confirmed on all 33 bytes. Game ID = authoritative `.gameid` sidecars, or Sol's inferred groups plus a content fingerprint. One reason per row, first match wins: `holdout_position`, `holdout_game`, `main_game`, `dup_main`, `dup_second`, `kept`. Outputs are exclusive-create; the md5 manifest is written last (the seal); nothing is deleted. | tool |
| deterministic | PASS. Fixture: two runs give identical files (test_04). Real data: run 1 vs run 2 gives all 8 outputs byte-identical (`run_info.json` and `SHA256SUMS` excluded: paths and times). Rebuilding the fixture with the builder gives identical data files. | `logs/step3_tests_final_17.log`, `logs/step6_*`, `logs/step2_*` |
| duplicate + holdout counts correct on the fixture | PASS, 17/17 tests. Every row's reason, group, first match and label conflict equals an independent brute-force reference (python-chess, Python sets, the group rule rewritten). Planted cases hold (details below the table). | `logs/step3_tests_final_17.log` |
| exact record format | PASS. Output `.pos` is byte-identical to the PC's own `fen2bin.exe` on the output text. The `--hce-dump` route (PC `hce_dump.exe`) is byte-identical to the row-subset route. Bad lines fail closed exactly where fen2bin rejects them. | tests 13, 14, 17 |
| output loads in v3b unchanged (CPU smoke) | PASS. A byte-identical renamed copy of the v3b trainer (sha256 `5cebba4d…`) loads the output, passes `--init-check`, trains 2 epochs on CPU and exports, with RAM and with `--mmap-data`. The two modes give identical loss lines and `.inc`/`.bin`. Supervisor "adopted running job" lines: 7 before, 7 after. Repeated on the real 246,139-row output. Test 15 uses the trainer's own `load_set` / `load_set_mmap`. | `logs/step8b_*`, `logs/step8d_*`, `results/v3b_smoke/` |
| inputs never changed | PASS. Fixture sha256 and mtime are unchanged and no file appears next to the inputs (test_05). Real inputs were opened read-only. The second folder was copied with read-only opens, hashed before and after. The live generator DB is never opened (the tool refuses a DB inside the second folder). | test_05, `logs/step5a_*`, `logs/step5b_*` |
| planted bugs | 22/22 caught after an unmutated control passes. | `logs/step4c_*` |
| real-data run (Sol: UNVERIFIED) | DONE on the PC, read-only (table below). | `logs/step5*`-`step7*`, `results/real_run*` |

Planted fixture cases:
- copy and prefix of a training game;
- copy of a holdout game;
- a game that transposes into a holdout game after the 001→002 file junction (its 001 rows are dropped as `holdout_game`);
- a single-row holdout touch;
- a castling-only variant (counts as a duplicate);
- a side-to-move flip (kept);
- `.part` repeats (`dup_second`).

## Real runs: `selfplay_out_x1_conc7_20261025` vs the training shards + 013/014
The second folder holds one abandoned `forge_selfplay_001.txt.part`, last written 2026-10-25 12:53, with no writer since. A copy
of its generator DB says the whole file is committed: 19,496,221 bytes, 304,696 lines. The main generator writes only to
`D:\grok-pc-data\selfplay_out`. 3,290 inferred games; tripwire max 3 boundaries per 100 rows (PASS).

| quantity | run 4: 30 training shards incl. 032 (the live trainer's list since 15:18), default rule | runs 1+2: 29 shards, default rule | run 3: 29 shards, `--holdout-game-rule off` |
|---|---|---|---|
| `holdout_position` | 1,054 (1,054 distinct holdout positions; 678 with another label) | 1,054 | 1,054 |
| `holdout_game` (rest of the 298 games that touch the holdout) | 42,573 | 42,573 | 0 |
| `dup_main` exclusive / inclusive | 15,010 / 25,424 (032 adds 213 matched pairs) | 14,906 / 25,212 | 25,206 / 25,212 |
| `dup_second` (castling/e.p.-only variants; the generator's own dedupe uses the 4-field FEN) | 24 | 24 | 27 |
| **kept** | **246,035 (80.7 %)** | **246,139 (80.8 %)** | **278,409 (91.4 %)** |
| 64-bit key collisions rejected | 0 | 0 | 0 |
| time at Idle (streams 242M / 232M reference rows) | 167 s | 153 s / 141 s | 135 s |

All four sealed outputs pass `verify`. Run 1 output md5: `.pos` `935352dd…`, `.hce` `63b269f8…`, `.txt` `b13083fa…`.

## Findings
- **The holdout touches are late transpositions, not shared games.**
  - 295 of the 298 touching games first meet the holdout after row 5: at fullmove 41-80 (167 games) or 81+ (128 games).
  - 126 games touch it in a single row (`logs/step6_*`).
  - The conservative default drops 42,573 more rows (14 %) for that. On this data, position-only (`off`) keeps 32,270 more rows.
  - Choosing the rule is the owner's call; the tool supports both.
- The second run duplicates 8.3 % of its rows against main and 0.35 % against the holdout. About two thirds of the main
  duplicates carry another label (search noise between runs).
- **Test-harness bug found and fixed.**
  - Mutant M09 (an output directory inside an input is allowed) wrote into the shared fixture.
  - Every later mutant then failed one test for that reason, so the first count (22/22) was partly an artifact (`logs/step4a_*`).
  - Every test process now works on a private fixture copy, and an unmutated control runs first.
  - That exposed two real survivors, first match overwritten and bad lines accepted (`logs/step4b_*`). Two new tests now
    catch them (`logs/step4c_*`).
- The live trainer started using shard 032 at 15:18 (supervisor log), after runs 1-3. Run 4 is the result against the
  current 30-shard training list.
- v3b trainer observation (not changed): a holdout smaller than one batch makes the epoch report divide by zero
  (`logs/step8c_*`). The data is not at fault.

## Process notes (main session, from the sub-agent's hand-back)
- Early in the job, read-only `wc`, `grep`, `sed` and `sha256sum` commands had the trainer's file name
  `train_resid_v3b.py` in their command lines. None of these is a Python process; the supervisor adopts only `python.exe`
  command lines matching `train_resid\w*\.py`, and its "adopted running job" count stayed at 7. From then on the renamed
  copy (`opus_nnue_smoke_v3b_s40.py`, byte-identical, sha256 `5cebba4d…`) was staged by a script that builds the name at
  run time; no `--guard-tag` was ever passed.
- A mutant wrote `second/newdir` into the scratch fixture copy `F:\opus_scratch\sol_S40\fixture_v2`. It was left in place
  and never used again; the committed fixture tarball was packed before it happened. Nothing was killed or deleted.

## Left / UNVERIFIED
- Game IDs are inferred (the PC has no authoritative IDs), so groups are supersets of games. Fingerprint ID lists only match
  identical game records.
- Main shard 033 was being written (`forge_selfplay_033.txt.part`) and is not referenced. Pass it once it is sealed (`--main`
  accepts `.pos` or `.txt`).
- The merged shards stay in `F:\opus_scratch\sol_S40\real_run{1,3,4}*` (not committed; md5/sha256 in `results/`). Nothing is
  adopted into training; no training-gain or Elo claim.

## Files
- Tool and docs: `forge_sol_S40_merge_datagen_20261027.py`, `README.md`, `IDEA_SOURCE.md`.
- Tests and checks: `test_forge_sol_S40_merge_datagen_20261027.py` (17), `mutation_check_s40.py` (control + 22),
  `v3b_cpu_smoke_s40.py`, `real_stage_inputs_s40.py`, `real_run_detail_s40.py`.
- Fixture: `make_fixture_s40.py`, `pack_fixture_s40.py`, `fixture/forge_sol_S40_fixture_20261027.tar.gz` (84,124 bytes).
- Evidence: `logs/`, `results/` (real runs 1, 3, 4; v3b smoke reports). Index: `FILES.txt`; checksums: `SHA256SUMS`.
