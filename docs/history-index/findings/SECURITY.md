# Security notes from the repository

These are locations and what the files say. The scripts were not opened and not run. No intent is inferred beyond the behaviour the repair note records.

## Deleting script, removed at tips, still in history

`h512/results/phase3/repo_fix_20261112/README.md` (blob `f1981569133942aa98783f2e82985738f4705557`) on `fable/standalone-h512-20261111` @ `efb2ff960037`:

- `opus_round1/C4/instrument_refresh_stats.py` was on 53 of the 57 tips that received a fix commit on 2026-11-12. The note says that, run from a repository root, it deleted the folders `src` and `include`, then stopped at the placeholder path `'<repo>/'`.
- The file is absent at all 416 tips after that push, according to the note's own rescan. It remains in earlier commits of those branches and at tag `astra-a1-data-results-20261030`.
- The 57 old and new tips are listed in `h512/results/phase3/repo_fix_20261112/branches.tsv` (blob `9432638271fb82661a48021b9c22e311b33491d4`). Example: `astra-notes` moved from `605e5a1c23e00a1fb787090bf8929b8b7b7a1fbe` to `3e50336ac0249cfcc87d23f8154e1e842d2f7c79`. This index checked that the new SHA matches `git ls-remote` for the rows read. It did not re-verify all 57 against the network beyond the full-tip snapshot, which does contain those new SHAs.
- `main` (`5176ddf79ae1`) and `lock/combo29-20261110` (`16833ecc03b4`) did not contain the file and were not moved.
- A branch cut from a parent of those fix commits brings the script back. The note names `tip_targets.py` as the finder. Do not run the old script to confirm it.

## Tablebase download path check

Same note. Before the repair, a checksum-list line such as a name beginning with `../` could make `opus_round1/C1/ci_fetch_tables.sh`, `opus_round1/C1/download_tb.sh`, or `opus_r13/p6/ci_fetch_tables.sh` write outside the destination folder. At the fixed tips every list line must be 32 hex digits, two spaces, and a plain Syzygy name (`KQRBNP`, one `v`, extension `.rtbw` or `.rtbz`). The note says 22 local checks passed, including a tampered list that writes outside with the old script and exits 1 with the new one. The mirror still uses plain HTTP because the certificate check failed on 2026-11-12. Tables are data, not executables. The old scripts are not stored in the fix folder on purpose; the note points at `ad612845f99ad9eec67f96bf4e23b0ec518b2744:opus_round1/C1/ci_fetch_tables.sh` for the previous text.

## Other destructive or code-loading behaviour left in place

The same note, not independently audited here:

- `validation/forge_sol_20261025/.../recovered_build_h256_e12.ps1` on 4 branches deletes and re-extracts `C:\Users\Administrator\grok-pc\forge_push\src_h256_e12` after a hash check. It was left as a stored build script.
- Other scripts that delete a scratch directory they themselves create were read by that job and left unchanged. This index has not re-read them.
- Unsafe checkpoint loads: the note's correction is 49 `torch.load`-style lines over history, and 22 calls in 16 files at tips outside the H512 branch. Examples named: `tools/nnue/fable_nnue_train.py`, `astra_r8/datafilter/train_adapter.py`, `opus_30h/a/o30_fit.py`. Risk is a checkpoint from someone else. This index did not open those files.
- On the H512 branch, `h512/train/ckpt_io.py` is the restricted loader. A crafted checkpoint that carries a command is refused. 44 checkpoints this job reads match the old loader's content. Tests are described in `h512/results/phase3/safe_load/`. Those test logs were not read in this pass. The note also says 13 `yaml.load` lines use `BaseLoader` and were wrongly counted as unsafe in an 08:30 review.

## What this index did not scan

The H512 status says 519 files over 2 MB in the repository were not inspected by that safety review. This index listed large blobs and did not open them. No credential files were sought inside blob contents. Filenames were not grepped for key material in this checkpoint. A later pass should list paths matching private-key or dotenv names and record the path only.
