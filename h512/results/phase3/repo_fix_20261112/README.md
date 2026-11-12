# Repository-wide fix of 2026-11-12: one deleting script removed, three download scripts repaired

Owner's instruction (2026-11-12): "no files must exist that if opened can do destructive behavior". This folder
records what was changed on other branches of `couns0538-sketch/dwqww`, how it was tested and how to undo it.

## What was changed

One ordinary commit was added on top of each of **57 branches** (list with old and new head: `branches.tsv`).
No force-push, no history rewrite. `main` and every `lock/*` branch did not contain these files and were not touched.
Each commit message ends its subject with `[skip ci]`, so no workflow run was started (checked: none).

| File | Branch tips | Change |
|---|---|---|
| `opus_round1/C4/instrument_refresh_stats.py` | 53 | **removed**. Run from a repository root it deleted the folders `src` and `include`, then stopped at the placeholder path `'<repo>/'` |
| `opus_round1/C1/ci_fetch_tables.sh` | 49 | repaired (11 lines added) |
| `opus_round1/C1/download_tb.sh` | 49 | repaired (11 lines added) |
| `opus_r13/p6/ci_fetch_tables.sh` | 3 | repaired (11 lines added) |

The repair of the download scripts: every line of the checksum list must be `<32 hex digits>  <table file name>` with
a plain Syzygy table name (letters `KQRBNP`, one `v`, extension `.rtbw` or `.rtbz`). Any other line stops the script
before a single file is fetched. Before, a list line such as `<md5>  ../x.rtbw` made the script write outside its
destination folder. The repaired files are in `scripts/`.

## How it was tested (`test_fix.sh`, local fake mirror, nothing from the network)

22 checks, all passed (`TEST_OUTPUT.txt`):
- clean list: repaired and original scripts produce identical folders;
- tampered list: the original scripts write `x.rtbw` outside their folder (the defect, shown in a sandbox); the
  repaired scripts exit 1, fetch nothing and write nothing outside;
- six other malformed lines (short checksum, absolute path, sub-folder, shell text, `.exe`, `*name`) are refused;
- the real list of the mirror (290 lines, fetched 2026-11-12) passes the filter with 0 refused lines and still yields
  the 70 three- and four-piece tables.
The test needs the scripts as they were before the fix in a folder `orig/` next to `scripts/`; they are not kept
here on purpose. Take them from history, for example
`git show ad612845f99ad9eec67f96bf4e23b0ec518b2744:opus_round1/C1/ci_fetch_tables.sh`.

## After the push (checked on GitHub)

- all 57 branch heads equal the commits in `branches.tsv`; no other branch head changed; `lock/combo29-20261110` is
  still `16833ecc03b425586f91f4c8834dea8807bf4c22`, `main` still `5176ddf79ae15b76c08c4485d90ee5600ba30a1a`;
- a rescan of all 416 branch tips: `instrument_refresh_stats.py` is absent everywhere; the three download scripts
  exist only in their repaired versions.

## What this does not do

- **History.** The old versions are still reachable in earlier commits of those branches and at one tag,
  `astra-a1-data-results-20261030` (the other 2 tags and the 12 pull-request refs do not hold them). Removing them
  there needs a history rewrite with force-pushes, or moving the tag; neither was done.
- **Transport.** The table mirror (`tablebase.sesse.net`) has no valid HTTPS certificate (checked 2026-11-12), so the
  list and the tables still travel over plain HTTP. They are chess data and are never executed.
- **New branches.** A branch cut later from an old commit brings the old files back. `tip_targets.py` finds them.
- **Other scripts that delete folders** were read again and left as they are: each removes only a named scratch
  sub-folder that it creates itself (`<out>\tmp\...`, `<work>/tree`, `<pack>\evidence`, `/tmp/forge-...`) and needs
  its folder arguments to run. One has fixed paths and no arguments:
  `validation/forge_sol_20261025/.../recovered_build_h256_e12.ps1` (4 branches) deletes and re-extracts its own build
  folder `C:\Users\Administrator\grok-pc\forge_push\src_h256_e12` from a zip after checking hashes. It is a stored
  copy of a build script and was not changed.
- **Checkpoint loading in other jobs' trainers** (22 `torch.load` calls in 16 files on 17 branches, for example
  `tools/nnue/fable_nnue_train.py`, `astra_r8/datafilter/train_adapter.py`, `opus_30h/a/o30_fit.py`) was not
  changed: a blind switch can break their resume and cannot be tested without their checkpoints. The risk exists
  only with a checkpoint from someone else. This job's own tools were switched and tested (`../safe_load/`).
  Correction to the safety review of 08:30: its "62 lines" counted every version in the history and included 13
  `yaml.load(..., Loader=yaml.BaseLoader)` lines, which use a safe loader. Unsafe checkpoint loads: 49 lines over
  the whole history.

## How to undo

Each change is one commit. `git revert <new head>` on a branch restores the old files there; `branches.tsv` has the
old head of every branch.

## Tools

`make_fix_commits.py` built the commits in a bare copy of the repository (plan first, then `--build`; it refuses
`main` and `lock/*` and leaves any file alone that is not the exact known version). `tip_targets.py` lists where the
files of interest sit at the branch tips.
