# Coverage ledger

Checkpoint 1. Figures below are counts from this session, not estimates of "the important parts."

## Snapshot

| Item | Value |
|---|---|
| Remote queried | `git ls-remote --heads origin` at 2026-11-13T11:46:13Z |
| Remote branch tips | 416 |
| Local remote-tracking tips before and after `git fetch` | 416 branch tips, 0 differences. `refs/remotes/origin/HEAD` is a symbolic ref to `5176ddf79ae1` and is not a branch |
| Unique tip commits | 327 |
| Unique tip trees | 327 |
| Tip commits that share a tree with a different tip commit | 0 |
| Branches whose tip commit is shared with another branch | 105 branches in 16 groups (`branches/SHARED_HEADS.tsv`) |
| `git ls-tree -r` entries across the 327 trees | 831,064 |
| Unique blobs at those tips | 35,982 |
| Of which text-like extensions were listed | 32,877 |
| Markdown blobs | 2,666 (17.8 MB total) |
| Archive, binary, or >=20 MB blobs listed and not opened | 1,710 (`inventory/LARGE_AND_ARCHIVE_BLOBS.tsv`) |
| Gitlinks (submodules) | 0 |
| Pack | one pack, about 7.67 GiB, repository is not shallow |

`git fetch` of `refs/heads/*` returned immediately with no ref updates. `ls-remote` then matched every local tip. Heads were not moving during this snapshot. A later run must repeat `ls-remote` and diff it against `branches/HEADS.tsv` before assuming the tips are still these commits.

## What each depth means

| Depth | Meaning in this ledger |
|---|---|
| Inventoried | Path, blob id, and size recorded from `git ls-tree`. Bytes not opened |
| Screened | A census or a keyword/layout pass. Not a reading of the file |
| Full read | The whole file was read in this session. The blob id is listed below |

## Full reads (11 files, plus one 57-row table)

All of these blobs are on `fable/standalone-h512-20261111` at `efb2ff960037087299332bc6a44baea69441a17a` unless noted. Reading the blob covers every other branch that has the same blob at any path.

| Blob | Path read | Lines |
|---|---|---|
| `d4f489b98264bc905d5f020ad1417a219c841513` | `three_model_prompt.txt` | 30 |
| `d8f761ef914247f6fcf589293be6a1afc1cd114e` | `h512/STATUS.md` | 220 |
| `4088ead03bdd3f719eaeece58fdf18d0846567f2` | `h512/REPORT.md` | 467 |
| `74bf5339667eac7d8545163f8ccb12493a8e9612` | `h512/REPORT_PHASE2.md` | 601 |
| `33ca539a571fe83afee9e7fa2fd8d094cfc75b1b` | `fair_eval/STATUS.md` | 45 |
| `e1f86ff992a71788b80bbcc584fb58eb182941e0` | `fair_eval/REPORT.md` | 305 |
| `4ae6a095ee3bbd2383c7c1c6049a2edde41ef58e` | `forge-combo29/LOCK.md` | 48 |
| `3922b537a9dd25841d3fc7a07922adfe2dcf41da` | `forge-combo29/README.md` | 16 |
| `5b32b256fbe59d26c6ea13bfb325ad6d4c887d8c` | `forge-combo29/docs/context/HANDOFF.md` | 15 |
| `4613567c0062e0742301684a1bb6b2cf54c2191b` | `forge-combo29/docs/overnight/RANKED.md` | 36 |
| `f1981569133942aa98783f2e82985738f4705557` | `h512/results/phase3/repo_fix_20261112/README.md` | 75 |
| `9432638271fb82661a48021b9c22e311b33491d4` | `h512/results/phase3/repo_fix_20261112/branches.tsv` | 57 data rows |

That is about 1,900 lines of prose plus the 57-row fix table. It is the newest H512 / fair-eval / combo29 lock line. It is not a reading of the October engine history.

## Screened, not read

- All 416 tip subjects and commit dates (`branches/HEADS.tsv`).
- Family counts (`branches/FAMILIES.tsv`).
- Top-level layout, file counts, extension counts, and files over 5 MB for 15 trees: `main`, `cursor/chess-engine-elo-bba2`, `cursor/engine-strength-overhaul-66cc`, `cursor/speed-and-search-patches-c7cb`, `forge/6.4-hourly-20261019`, `forge/nnue-capture-fusion-20261019`, `opus-summary`, `opus-sol-S50`, `fable-nnue-arch`, `fable-review-summary`, `fable-fb2-j1`, `fable52-search-gap-20261109`, `fable52-movegen-proof-20261110`, `fable/fair-eval-builds-20261111`, `fable/standalone-h512-20261111`. `astra-notes` was included in the same pass.
- Markdown size buckets: 691 blobs under 2 KB, 1,815 from 2–20 KB, 151 from 20–80 KB, 9 from 80–200 KB. No markdown blob is 200 KB or larger.
- Basename census of report-like markdown (316 `README.md`, 199 `REPORT.md`, 74 `STATUS.md`, 40 `REVIEW.md`, 20 `FINAL_REPORT.md`, and smaller counts).
- Unique blob counts for selected source names (`inventory/KEY_SOURCE_BLOBS.tsv`): 95 `search.cpp`, 71 `search.hpp`, 50 `nnue.cpp`, 114 `uci.cpp`, 26 `board.cpp`. These counts are unique blobs that use that basename, not a diff.

## Inventoried only

Every other file at the 416 tips. In particular:

- 1,710 archive or large blobs, including `chess-engine-forge-6.4.0.zip` (77.5 MB), `validation/release-6.0.0/all-match-pgns.zip` (67.2 MB), many `*.zip.part0001` shards near 67 MB, `validation/clock-safety-9850x3d/matches/original-quality-sprt/fastchess.log` (65.4 MB), and `astra_r10/job1/pack/artifacts/inputs/libLLVM-23.dll` (77.7 MB). Not extracted.
- 12,530 unique JSON blobs, 5,140 log blobs, 2,805 Python blobs, 549 C++ blobs. Listed, not read.
- `fair_eval/EVIDENCE_MATRIX.md`, `h512/train/TRAINER_NOTE.md`, and `forge-combo29/docs/QA_LOCK_PUBLISH_COMBO29_20261108.md` are present and were not read.
- Match PGNs and nets cited under `D:\forge_jobs_20261111\...\_work\` are outside the repository.

## Branches with no new tip content

Six `research/grokchess-*` branches dated in the name 2026-10-20 or 2026-10-21 point at `main` (`5176ddf79ae15b76c08c4485d90ee5600ba30a1a`, "Add files via upload"). Their trees are the ten-file upload (two zips, a JS source dump, prompts, logs). The experiments named in the branch are not in that commit. See `branches/NAME_NEWER_THAN_COMMIT.tsv` for 21 branches whose name date is at least one day after the tip commit date. Several October 21 investigator and forge test branches point at the October 20 OwnBook commit `5101c2529d38` and do not contain a newer commit of their own.

Hourly `forge/` and `investigator/` names often share one commit. The branch name is a checkpoint label. The commit subject is the last real change, which may be older and about a different topic.

## Checkpoint 2 full reads

These blobs were read in full after checkpoint 1. They are not on the H512 tip. The branch tip that holds each path is named with the blob.

| Blob | Branch @ tip | Path | Lines |
|---|---|---|---|
| `a0065a88cb1697ea46ba4880425707839dea71f1` | `fable52-search-gap-20261109` @ `56a76b153bb88026f2d83d65df6e422b0f3298f9` | `fable_search_gap/NO_QUALIFIED_GAP.md` | 185 |
| `96681cdea9a21e0a36cd865ab9ef5c452b2653b4` | same tip | `fable_search_gap/STATUS.md` | 125 |
| `683754c8c5283cfde01c616517c10582754e0fbf` | same tip | `fable_search_gap/FALSIFICATION.md` | 151 |
| `23b1387b4a5a4ba84581d9dbda8af31002ca1557` | same tip | `fable_search_gap/data/QUALIFICATION_RULE.md` | 17 |
| `81bdc8ad6cef019eadf80a411be5ec4bbf44ed4f` | same tip | `fable_search_gap/data/gate_table_summary.md` | 117 |
| `2d0cddc5ded464075f5b1128f5c36be4b933c629` | `fable52-speed-lane-20261109` @ `08897a88e11c707c0ac4e39c19e44c06e1360bdd` | `fable_speed_lane/STATUS.md` | 202 |
| `8242abdb64cb28fd4b0a7ae59734fe13b64d4e29` | same tip | `fable_speed_lane/README.md` | 85 |
| `365aff87344299c5cfddc198b6f97b6fe16d581a` | `fable52-movegen-proof-20261110` @ `2ff77f98927cf19d55d6cac5cf182a81eb0d71e6` | `fable_movegen_proof/STATUS.md` | 178 |
| `7e2021ba68c48223514584f44157e5a9f6f4efe8` | `fable52-cpu-20261110` @ `ea3759a9ec3b17c58e3daeab8ff31af53e7ae6ab` | `fable_cpu_speed/STATUS.md` | 67 |
| `a2e1d04d8273cfed34a1b271a074753df6eb0204` | same tip | `fable_cpu_speed/README.md` | 118 |

About 1,245 more lines. Still unread on those same branches: `fable_search_gap/EVIDENCE.md`, `DEDUPE.md`, `REVIEW_LOG.md`, `COVERAGE.md`; `fable_speed_lane/BENCH.md`, `DUPCHECK.md`, `PROFILE.md`, `QA_ABBA_PROTOCOL.md`; `fable_movegen_proof/PROOF.md`, `DONE.md`, `evidence/TABLES.md`; `fable_cpu_speed/DONE.md`, `PREREG.md`, `PROFILE.md`. The speed-lane protocol file was copied out and not read.

## Not claimed

This ledger does not say that every branch was reviewed, that every report was read, or that any Elo or speed number was confirmed by a new match or bench.
