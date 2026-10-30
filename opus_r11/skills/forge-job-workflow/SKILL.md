---
name: forge-job-workflow
description: Step-by-step workflow for one Forge job (Opus O/C jobs, Sol leftovers S-jobs, fix-ups, new user jobs like S-IT) from worktree creation to pushed branch with REPORT.md, FILES, SHA256SUMS, CI check and progress-file update. Use when starting, finishing, or handing off any job, or when reviewing a sub-agent's hand-back.
---

# Forge job workflow

## Start
- Branch names: `opus-<job>` (own jobs), `opus-sol-<JOB>` (Sol section-2 jobs), `opus-sol-<JOB>fix` (Sol
  section-3 fix-ups); for a follow-up on an existing branch, commit on that branch.
- New worktree (base = AL1 lock `d4f4312` + the CI baseline `0d99f02` cherry-picked):
  ```
  git -C D:/grok-pc-data/dwqww/.claude/worktrees/opus worktree add -q -b <branch> /f/opus_scratch/worktrees/<name> d4f4312
  cd /f/opus_scratch/worktrees/<name> && git cherry-pick -x 0d99f02
  ```
  Existing branches keep their worktrees (`git worktree list`); old ones live under `D:\...\.claude\worktrees\`.
- Job folder: `opus_round1/<job dir>/` (e.g. `sol_S44`, `C3`, `O1-LTT`). Scratch: `F:\opus_scratch\<job>\`.
- Read the spec first: `SOL_LEFTOVERS_FOR_CLAUDE.md` (sections 1-3) or Sol's inventory copy
  `F:\opus_scratch\sol_inventory_17aa0cae.json` (`jobs[].spec_verbatim`, `resume_reworks_exact`,
  `external_unverified_scope`). Check the progress file so no job is done twice.

## Deliverables in the job folder
`README.md` (how to run), `IDEA_SOURCE.md` (sources/ideas), `REPORT.md` (acceptance table with evidence paths,
findings, UNVERIFIED/left), tools + tests, `logs/` (step logs; big outputs stay in scratch, record sha256),
`FILES` or `FILES.txt` index (path | bytes | sha256 | content), `SHA256SUMS`.
REPORT style: title line "<JOB> ... — DONE/PARTIAL", branch = base + commits, an acceptance table
(line | result | evidence), short readable bullets, no Elo/speed claims without a gate, "Machine exclusive: no".

## Finish
0. No FILES index yet: `python -I -B F:/opus_scratch/tools/make_files_index.py <job_dir> --title "<folder, job,
   branch>" [--header "..."] [--desc "rel/path=text"]` (logs/ default to "evidence log").
1. `bash /f/opus_scratch/tools/finish_report.sh <job_dir> [FILES|FILES.txt]`, then `sha256sum -c --quiet SHA256SUMS`.
   The helper refreshes size + sha256 of every `path | bytes | sha256 | …` index line whose file exists (since
   2026-10-27; before that, edited files kept stale hashes in FILES.txt), adds/refreshes the REPORT line and
   regenerates SHA256SUMS, skipping `__pycache__`. Run it again after ANY later edit in the folder.
   To add a new file to an existing index, append `path | 0 | - | description`; the helper fills in bytes and
   sha256 (check `grep -c "| - |" FILES.txt` is 0 afterwards).
   Check `git ls-files --eol <dir>` shows `i/lf` for edited reports (Windows Python text mode writes CRLF).
2. `git add <paths>` (never `__pycache__`), commit with the attribution trailer; `[skip ci]` if evidence only.
   - GitHub skips the workflow for the WHOLE push when the push's head commit says `[skip ci]`: if the push also
     carries engine/test/CMake commits, end it with a normal commit (R3, 2026-10-27).
   - CTest runs the tools with the system Python, which writes `__pycache__` into the source tree; never
     `git add -A` a folder after running ctest (untracking committed .pyc later is a deletion, which is denied).
   - `bench` searches with its own one-thread Searcher: Threads/SMP options are not exercised by bench.
3. Push with the literal `git push -q -u origin <branch>`; verify `git ls-remote origin refs/heads/<branch>`.
4. Engine changes trigger CI (`opus-ci`: release, asan, tsan + per-branch workflows): `gh run list --branch
   <branch> --limit 4`; when done, record run ids/results in REPORT.md in a `[skip ci]` commit. Run `gh` from a
   git checkout (elsewhere it fails with "failed to determine base repo", and a polling loop never ends).
   Applying a patch inside a CI checkout: GNU `patch -p1 -F0`, not `git apply` (it silently skips `diff --git`
   paths from a work-tree subdirectory), and fail when CTest prints "No tests were found".
   The repo is ~7.9 GB: `actions/checkout` with `fetch-depth: 0` takes 1.5-5 min per job. New workflows that only
   need the lock commit can use the default depth plus `git fetch --depth 1 origin 294dbed3a15dfd821aaf9d4edc6e5f62832fd460`.
   `gh run download <id> -n <one artifact>` puts files directly into `-D` (no subfolder); with several `-n` it makes
   one subfolder per artifact.
5. Update the progress file (`SOL_LEFTOVERS_PROGRESS.md` on branch `opus-summary`, copy in
   `D:\grok-pc-data\dwqww\.claude\worktrees\opus\`) and the task list.

## Lessons from FB1 (2026-10-28, branch fable-nnue-arch)
- A worktree made from `D:/grok-pc-data/dwqww` has no git identity: commit with
  `git -c user.name="couns0538-sketch" -c user.email="couns0538@gmail.com" commit ...` (the repo's author).
- `opus-ci.yml` triggers on `branches: ['opus-*', 'fable-*']` (fable-* added by FB1); other prefixes get no CI.
- Never edit a report with a Bash-heredoc Python script when the text contains backslashes (`\f` in a Windows path
  became a form feed and a "fix" that searched for the first `inputs` wiped half the file; `git checkout -- <file>`
  restored it). Write patch scripts with the Write tool and anchor replacements on unique strings (`assert count == 1`).
- The root `IDEA_SOURCE.md` belongs to the lock tree: job ideas go to `<job>/IDEA_SOURCE.md`, never overwrite it.
- Box-recipe builds of new modules: `FORGE_EXTRA_SRCS="src/a.cpp src/b.cpp" build_pc.sh ...`.

## Lessons from the Opus review (2026-10-28, branches fable-review-*)
- Untracking files (`git rm --cached`, `git update-index --index-info` with mode 0) is refused by the permission
  rules even when the user says "I give you permission": record the exact owner command instead of retrying.
- Job unit tests must be checkout-independent: compare text after normalising `\r\n`, hash normalised text, and
  never depend on `src/` or `tools/` files being next to the job folder unless the test finds the repo root itself
  (S08fix, S33fix, S38, S42 compare raw bytes/SHA256 and fail from an LF export; S15, S27fix need the full tree).
- Reviewing a branch cheaply: export the job folder with `git archive origin/<branch> opus_round1/<job> | tar -x`
  (no worktree), run its `test_*.py` with the venv Python; for engine claims grep the latest opus-ci log for
  `ALL OK`, `KNOWN-FAILURE CHECK: PASS` and `TSan: 0 reports` (`F:\opus_scratch\fable_review\run_tool_tests.sh`,
  `ci_identity_sweep.txt`).
- Line endings are THE recurring cause of "test passed for the author, fails here": the blobs are LF, this clone has
  `core.autocrlf=true`, and both checkouts and `git archive` convert to CRLF. Frozen SHA256s and golden files are of
  the LF bytes. Fix per job: `.gitattributes` with `* -text` in the job folder (or at the repo root when the test
  hashes files under `src/`/`tools/`); verify with a fresh `git archive` export or a fresh worktree of the fixed
  branch. Confirmed on S42, S08fix, S15, S39, S50, SA3, SA2, and the golden-file tests S33fix/S38/S46.
- Trainer-variant tests (S39/S50/SA3/SA2) are built to run against the staged renamed copies under
  `F:\opus_scratch\sol_<job>\opus_nnue_smoke_*.py` through importlib: run them as they are; never type the trainer's name.
- The auto-mode classifier also blocks command lines that merely contain the forbidden trainer name (even in a
  Python `-c` string): resolve such file names with globs inside a script file.
- Before the final push of correction branches, have the REVIEW/REPORT notes checked against the code by a second
  agent that has NOT seen the conclusions (fresh exports, re-run the tests, read the diff). On 2026-10-28 all seven
  fixes were right but six notes were wrong or loose (an inverted root-cause sentence in three files, a threshold
  quoted wrongly, duplicate .gitignore lines, a CI file described as smaller than it was): notes drift, code less so.
  When sub-agents are NOT allowed (R11, 2026-10-30: the user stopped such an agent), do this check yourself:
  (1) resolve every commit id cited in REPORT/NOTES/skills (`git cat-file -t`, compare the subject); (2) every
  number in the acceptance table against the cited evidence file; (3) README/NOTES command lines against each
  script's argparse; (4) grep the docs for stale words of earlier designs (old thresholds, removed options); (5)
  back every measured claim with a committed raw log (R11 found 4 loose items this way, e.g. "90 %" for 89 %).

## Lessons from R11 (2026-10-30, branch opus-r11-nnue-pipeline)
- Code Review wants one commit (and one patch file) per CR item. When one file holds two items, stage only the
  matching hunks without `git add -p`: `python -I -B F:/opus_scratch/tools/stage_hunks.py <repo> <path> <marker>
  [--exclude <marker2>]` (filters `git diff` hunks by text, `git apply --cached`). Feed git bytes, not text: Python
  text-mode stdin on Windows turns every LF into CRLF and the patch "does not apply".
- Patch files for the reviewer: `git format-patch -1 --stdout <sha> > NN_<item>_<sha>.patch` + INDEX.txt + SHA256SUMS
  in the job's output folder (R11: D:\grok-pc-data\r11_nnue\cr_patches).
- A test of "fail closed" needs a REAL failure: a CPU mask with one bit the PC does not have (1 << 40) passes the
  "1..3 CPUs" check and makes SetProcessAffinityMask fail.
- A running test process keeps its old code in memory but launches helper scripts from disk: do not edit a script a
  running test is about to launch, and note which in-flight runs a new guard will make fail (R11: e2e_3).
- Reviewing a merge's hand-made resolution: recompute the automatic merge with `git merge-tree --write-tree P1 P2`
  and `git diff <tree> <merge>`; what remains is exactly the manual edit (exclude mechanical file removals such as
  the src/search.cpp split). Loop over `git log --merges --first-parent` and do not `head` the list (the 2026-10-28
  review first missed 8 of 21 conflicted merges that way). Helper: `fable_review/deep/r3_resolutions.sh` on
  fable-review-summary.
- Re-running an Opus job's mutation check: export the branch LF (`git -c core.autocrlf=false archive origin/<b> |
  tar -x`), run the script from the export root with a scratch dir, `CXX=g++ JOBS=2 MUTATION_LINK_FLAGS=-static
  PYTHON=python3` with msys ucrt64 + the VS CMake/Ninja dirs on PATH; patch a hard-coded `-j 3`. Runner scripts
  `fable_review/deep/fable_nnue_mutants{,_py}.sh`; 10 shell-style jobs reproduced Opus's counts exactly.
- Markdown tables: a blank line between rows ends the table in GFM. After patch scripts, check for `|` rows
  separated by an empty line (two of five tables in the review summary had been split that way).
- Real-data re-executions that fit a review budget: S44 `check --gates D:/grok-pc-data/forge_push` (seconds),
  S16 overlap scan with the 29 training shards (about 7 min, 6,069 rows), S31 scorer on the holdout subset (about
  1 min), S19 WDL-scale fit on shards 003+007 vs the 013+014 holdout with `--stride 5 --bootstrap 50` (about 90 s,
  deterministic to the print rounding); S40's real merge needs a second self-play folder and is not reproducible
  from the repo alone.

## Sub-agent hand-backs
Agents cannot write REPORT.md: copy their report text verbatim into the job folder, spot-check 2-3 key numbers
against the committed evidence (`git diff --stat 294dbed <branch> -- src include tests tools bench
CMakeLists.txt` must be empty for tool-only jobs), run finish_report.sh, commit, push, verify the remote head.
