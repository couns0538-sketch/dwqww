# S09fix [Sol fix-ups S09-1..5] 8 piece-count output buckets — DONE (S09-5 DirectML part UNVERIFIED, CPU proxy done)

`SOL_LEFTOVERS_FOR_CLAUDE.md` section 3, items S09-1..S09-5. Branch `opus-sol-S09fix` = `d4f4312` + CI baseline
`0d99f02` cherry-picked (`a8713ae5`) + `d717c06b` (this job's files) + the REPORT commit. Tool/evidence job: no
engine source change (`[skip ci]`), no net trained, no gate, no Elo or speed claim. Sol's delivered files (commit
`17aa0cae`) were only read; fixes ship as new `_v2` files. Machine exclusive: no (fastchess gates, NNUE training,
self-play and other agents ran throughout).

## Acceptance
| item | command | result |
|---|---|---|
| **S09-1** `--buckets 1` export byte-identical to the current trainer on L/L′/B | `forge_sol_S09_export_identity_v2.py roundtrip` with the current production trainer (v3b `5cebba4d`, renamed copy) and v2 (`fc0821c0`) | **PASS**. L, L′ and B carry the same net (h256_e12, sha256 `74c4009d`, md5 `6d22f612`; B's file taken from the rebuilt base-B tree): current `.inc` = v2 `.inc` = the base's own `nnue_weights.inc` byte for byte, current `.bin` = v2 `.bin` (`b995ae0e…`). Also PASS for the AL1 s198 lock net (`a7ebcf3a`) and f006 ep48 (`0fdf9bdb`). The trained 8-head net b8ep8: v2 re-export has identical int16 arrays (header differs, finding 4). `logs/step3` |
| S09-1, training path | `opus_s09_identity_runs.sh` (CPU, 1 thread, Idle, data32 split 40k/10k) | **PASS**. Same arguments into the current trainer and v2: f006-style tiny run (H256 residual, 2 epochs x 39 steps) 8/8 epoch files (`.pt .inc .bin .json`) byte-identical, also with explicit `--buckets 1`; defaults-only run (H128, 8 epochs x 9 steps) 32/32 identical. The parsed settings differ only by v2's `buckets: 1`. `logs/step4` |
| **S09-2** old trainer defaults restored, new recipe passed as args | `test_forge_sol_S09_v2.py` (parses both trainers' CLIs), negative control run | **PASS**. v2 defaults = v3b: `--shape 128`, no `--residual` (store_true, `--standalone` removed), `--epochs 8`, `--batch-size 4096`, `--lr 1e-3`, `--seed 1`, no `--final-full-val`; all other defaults equal the current trainer's (test). `forge_sol_S09_f006_recipe_args_v2.txt` = the production f006 command's arguments (`--residual --init-check --final-full-val --log-every 60 --shape 256 --epochs 48 --lr 7.07e-4 --blend-end 0.6 --seed 25 --batch-size 8192 --warmup-steps 300 --val-positions 1000000`); parsed by v2 they give exactly that recipe (test). Negative control: Sol's S09 trainer with defaults vs the current one: compare **FAIL** as expected, 7 settings differ (finding 1). `logs/step4`, `logs/step6_7` |
| **S09-3** IDEA_SOURCE for 8 output buckets | — | **DONE**: `IDEA_SOURCE.md` (Stockfish layer stacks: nnue-pytorch docs and `network.cpp` `(pos.count<ALL_PIECES>() - 1) / 4`; CPW NNUE; Forge `bde3dc9d`; Coder's CR-passed step 1/step 2; Sol's trainer patch) |
| **S09-4** one FILES index + per-step archives | `opus_s09_package_sol_packet.py --commit 17aa0cae` | **DONE**. Sol's packet (902 files, 44,777,166 B, indexed by MANIFEST .json/.txt + SHA256SUMS + 3 evidence maps) as 35 per-step archives (2,561,950 B), each member's sha256 re-checked against its git blob; 6 already-compressed files over 1 MiB (36.6 MB) are not re-packed, the index points to them on `17aa0cae`; a second run gave byte-identical archives. This job has ONE index, `FILES.txt` (section 1: this job; sections 2-3: Sol's packet, archives, members, 92 byte-identical groups), one log archive per step, 0 `_before_` copies and 0 duplicate files (S10 hygiene tool). `logs/step8` |
| **S09-5** real 013/014 holdout validation before any 8-head net is trained | `forge_sol_S09_holdout_validate_v2.py` on `holdout_013_014_s16` (1,024,286 rows, md5 `9ebe2f9c`/`c8723ec2`), all rows, float64 sums, the v2 trainer's own forward | **PASS**. Head occupancy 21,386 / 186,859 / 168,605 / 130,461 / 113,027 / 112,727 / 128,329 / 162,892 (pieces 3..32). 1-head vs replicated-8 e12: max \|Δlogit\| 1.9e-6 (limit 1e-5). Head selection on real rows: bias-shift control vs an independent nibble count, **0 mismatches** in 1,024,286 rows. MSE table below; HCE, e12 and f006 equal S31's independent numbers on the same subset to 7 decimals. `logs/step5` |
| S09-5 optimizer check | same tool, 5 in-memory steps from the replicated e12 init on real batches | **PASS on CPU**: the trainer's default optimizer (AdamDML + dev-scalars) vs stock `torch.optim.Adam`: max \|Δparam\| 6.0e-8 after every step; a step with only head-4 rows moves only head 4 (all other heads bit-identical). Nothing saved or exported. **DirectML: UNVERIFIED** (no `torch_directml` in the read-only venv; the GPU runs production training) |
| S09-5 no gate until a trained net passes CR | — | **kept**: no 8-head net trained, nothing queued, no gate |
| tests / planted bugs | `test_forge_sol_S09_v2.py`, `opus_s09_mutants.py` | **11/11 PASS**; **8/8 mutants killed** (default shape, default residual, head off-by-one, export head macro, nibble counter, split offset, patch helper, inc parser). `logs/step6_7` |

## S09-5 holdout table (MSE, lower is better; 1,024,286 rows)
| net | b1.0 (teacher) | b0.6 | b0.8 |
|---|---:|---:|---:|
| HCE alone | 0.0050739 | 0.0170588 | 0.0083605 |
| e12 = L/L′/B net (1 head) | 0.0046797 | 0.0145361 | 0.0069020 |
| e12 replicated into 8 heads | 0.0046797 | 0.0145361 | 0.0069020 |
| e12 x8, head h bias + (h+1)/64 (control) | 0.0048816 | 0.0147926 | 0.0071312 |
| b8ep8 (trained 8-head, md5 `09227945`) | 0.0039304 | 0.0145160 | 0.0065173 |
| AL1 s198 lock | 0.0045724 | 0.0143100 | 0.0067353 |
| f006 ep48 | 0.0045944 | 0.0143462 | 0.0067644 |

Per-head b0.6 values are in `forge_sol_S09_holdout_validation_v2.md`. Holdout MSE is not strength; no Elo claim.

## Findings
1. **Sol's default change was not cosmetic.** With his trainer, a command that relies on defaults trains a different
   net: shape 128→256, standalone→residual, epochs 8→48, batch 4096→8192, lr 1e-3→7.07e-4, seed 1→25,
   final-full-val off→on (negative control). Production commands pass these explicitly, but smoke/CI/queue scripts
   that leave one out would change silently. v2 restores the defaults.
2. **Recipe source.** Sol's f006 JSON lists `val_positions` 4,000,000 as inherited; the production f006 command used
   `--val-positions 1000000`, plus `--init-check` and `--log-every 60`. The v2 recipe file copies the production line.
3. **1-head checkpoints were not byte-identical in Sol's version**: his config always wrote `"output_buckets": 1`
   into every `.pt` and epoch `.json`. v2 writes the key only for 8 heads, so 1-head runs equal the current trainer.
4. **Two 8-head export spellings.** Engine NNUE's b8 exporter writes `#define FORGE_NNUE_OUTPUT_BUCKETS 8`, its own
   first comment line and a one-line `NnueB2[8]`; Sol's writes `FORGE_NNUE_OUTPUT_HEADS 8` and a multi-line
   `NnueB2[8]`. The arrays are identical and the step-1 engine accepts both spellings, but the files differ.
5. **The one trained 8-head net is not ahead on b0.6.** b8ep8 (8-epoch fine-tune of e12, blend-end 0.8) beats its
   e12 parent on teacher and b0.8 and by 2.0e-5 on b0.6, but stays behind AL1 s198 and f006 on b0.6. Any new 8-head
   net needs the full recipe and a CR before a gate.
6. **Head 0 is thin on real data**: 2.1% of rows and no 2-piece positions (heads cover 3-4, 5-8, ... pieces).
7. `qa_adam_dml.py`: Sol's copy (`799faa89`, same as the lock archive's cpu_smoke copy) differs from production's
   (`a0dd4445`) only in the last line ending (production ends with CRLF); the code is identical.

## How it was run
Read-only venv Python 3.10 (torch 2.4.1+cpu), `-I -B`, `nice -n 19`, `OPENBLAS/OMP/MKL_NUM_THREADS=1`,
`TMP/TEMP=F:\opus_scratch\sol_S09fix\tmp`, free RAM ≥ 6 GB checked before each heavy step (11.4-12.4 GB seen).
Trainer copies only as `F:\opus_scratch\sol_S09fix\opus_nnue_smoke_s09_{current,v2,sol}.py` (made by glob, so no
`train_resid*` name was run); run folders `s09_id_*`. Inputs copied into `F:\opus_scratch\sol_S09fix\inputs`: data32
h000 (md5 `b263af99`), the production holdout subset from S31, nets from git (`f4911f27`, `294dbed3`) and the lock
archive; b8ep8 rebuilt from the lock archive's research patch (`a7801690…`; md5 equals the training run's epoch-8
`.inc`, read-only hash). Copying `qa_adam_dml.py` out of `F:\forge_nnue_train` was denied by the permission layer,
so the identical-code lock-archive copy was used. Big outputs (exports, checkpoints, the data split) stay in
`F:\opus_scratch\sol_S09fix`; their sha256 are in the step logs.

**supervisor.log check:** the "adopted running job" count was 7 before and after every trainer/torch step (the last
such line is 2026-10-27T08:55:34, the earlier C4/C5 incident). No new line.

Process notes (recorded by the main session from the sub-agent's hand-back):
- One early read-only `git show` loop that copied Sol's files had his trainer's file name (`…_train_resid_v3b_…`)
  in its command text; nothing was run under that name and supervisor.log showed no new line. All later access used
  globs and renamed copies.
- Two small hash-listing files of the S09 reproducibility check were written to Git Bash `/tmp` (outside
  `F:\opus_scratch`).
- Nothing was deleted: two of the job's own files were moved from the job folder into scratch (a 1 MB step-4 archive
  that contained data, and the separate packet index that was merged into `FILES.txt`). Nothing was killed.

## Left / UNVERIFIED
- DirectML optimizer check on the GPU: UNVERIFIED (CPU proxy above only).
- Full 013/014 holdout (about 4.4M rows): only the 1,024,286-row subset was used.
- No 8-head net trained (rule), no gate, no Elo or speed claim; Sol's native engine delta was not rebuilt here
  (outside S09-1..5).

## Archives (every .tar.gz with its size, 42 files, 2,595,170 B)
`logs/`: step1_make_trainer_v2 1,766; step2_rebuild_b8ep8_inputs 571; step3_export_roundtrip 1,462;
step4_identity_runs 24,018; step5_holdout_validation 4,348; step6_7_tests_and_mutants 580; step8_package_sol_packet 475.
`sol_S09_v2_packet/archives/` (35, 2,561,950 B): S09_00 top_level 191,654; S09_01 ASAN_original_assembly_transport
1,191; S09_02 B_ASAN_FIRST 7,282; S09_03 B_ASAN_FULL 23,276; S09_04 B_ASAN_static 28,170; S09_05 B_FIRST 6,834;
S09_06 B_FULL 313,996; S09_07 B_release 25,867; S09_08 Lprime_ASAN_FIRST 7,177; S09_09 Lprime_ASAN_FULL 22,758;
S09_10 Lprime_ASAN_static 27,349; S09_11 Lprime_FIRST 6,725; S09_12 Lprime_FULL 313,726; S09_13 Lprime_release
25,222; S09_14 arm_bindings 1,059; S09_15 converted8_first10000_parity 1,268,730; S09_16 converted8_helper_build
16,866; S09_17 converted8_original_bit_snapshot 1,923; S09_18 corpus_controller 1,706; S09_19
default_onehead_million_parity 1,744; S09_20 first10000_exact_prefix 90,439; S09_21 full50k_actual_f006_holdout
8,467; S09_22 million_unique_corpus_input 678; S09_23 original_bit_snapshot_pair 1,991; S09_24 primary_lossless_data
2,030; S09_25 prior_overall_failed_torch_probe 2,148; S09_26 reference_FIRST 6,211; S09_27 reference_release 23,365;
S09_28 root_applychecks 5,632; S09_29 root_independent_native_audit 724; S09_30 ASAN_PREP 24,136; S09_31
CONVERT8_NATIVE_PREP 36,750; S09_32 CORPUS_FAST_PREP 27,084; S09_33 FULL_HOLDOUT_PREP 11,054; S09_34 native_controllers 27,986.
