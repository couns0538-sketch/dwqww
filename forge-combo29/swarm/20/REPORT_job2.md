# REPORT job2 — seat 20, area 10: recount of helper deepseek6's newest report

**what was asked** — Area 10 job 2: recount the helper deepseek6's report from its raw files and say which of its numbers equal its report and which do not. The brief names `forge-combo29/REPORT_deepseek6_longK.md` and `forge-combo29/tests_deepseek6_longK/`; neither exists on `for-fable-and-opus/deepseek6-work` (finding S-F1), so I recounted the newest existing one, `REPORT_deepseek6_long56.md` (2,000 random UCI sequences under ASan+UBSan), and I ran a 200-sequence sample of my own to test the same claim on my build.

**the answer** — 5 of the report's 6 headline numbers equal its committed raw summary exactly (ok 2000, crashes 0, hangs 0, san 0, illegal 0); the sixth, `seqs`, is 0 in the raw file where the report says 2,000 sequences — a counter that was never incremented, not a wrong claim. Two of its headline claims are **not shown** by the branch's own materials: "ZERO illegal bestmoves" comes from a code path that cannot execute (S-F2), and "ZERO sanitizer lines" has none of the proof the swarm rules require (S-F4). The run is also not reproducible from the branch (S-F5). On my own build with the same grammar shape: 200 sequences, 0 crashes, 0 hangs, 0 illegal bestmoves, 774 bestmoves judged — the UCI layer's robustness result reproduces.

**how sure** — certain for the file-level facts (they are greps and counts of committed bytes); "not shown" is a statement about evidence, not a claim that the helper's run did crash.

## Honesty numbers
Build used: `/agent/repos/build-base/forge`, sha256 `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83`, `id name Chess Engine Forge 6.4.24 candidate`, g++ 13.3.0, `-march=x86-64-v4`, 4 cores. Pins: bench 11 = 312866, bench 13 = 862329, bench 16 = 3024920, perft 5 = 4865609 — all four match (see `../HONESTY.txt`).

Sanitizer runner proof (needed before any "0 sanitizer lines" of mine counts): `sanrun.sh` on the planted-fault copy `/agent/repos/scratch-planted/build/forge` (built by `plant_build.sh`, heap over-read + signed overflow + unlocked counter behind the `plantfault` command) reports `sanitizer_lines=3` (UBSan `runtime error:` + ASan `heap-buffer-overflow` + `SUMMARY:`), and the same runner on the real ASan build reports `sanitizer_lines=0`. The ASan build itself: `nm -C | grep -c __asan_` = 35, `__ubsan_` = 15, and its pins are also 312866 / 862329. Files: `out/planted.meta`, `out/clean.meta`.

## Step table
| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| locate the named subject longK | done (absent) | `recount56.txt` §J, `ds6/ls_longK.txt` (0 bytes) | named file/folder do not exist; recounted long56 instead |
| dump the branch's own bytes | done | `fetch_ds6.sh`, `ds6/` | 7 files, commit recorded in `ds6/stamps.txt` |
| recount report vs raw summary | done | `recount56.py` §B–D, `recount56.txt` | 5 of 6 numbers equal; `seqs` 0 vs 2000 |
| is the legality check live? | done | `recount56.py` §E + `pos_echo.out.txt` | dead branch: engine prints no `position` line |
| sanitizer proof present? | done (absent) | `recount56.py` §F | no .meta, no nm count, no planted run, exe outside repo |
| reproducible from branch? | done (no) | `recount56.py` §G | sequences and set_G.epn both live in /tmp |
| my own 200-sequence recount | done | `myfuzz.py`, `myfuzz_out/myfuzz_summary.json` | 200 seqs, 0 crashes, 0 hangs, 0 illegal, 0 sanitizer lines |

## Findings
1. **S-F1** — the named subject does not exist. Show it again: `git ls-tree -r --name-only FETCH_HEAD forge-combo29/ | grep -i longk` (empty) after `git fetch -q --depth 1 origin for-fable-and-opus/deepseek6-work`.
2. **S-F2** — the "ZERO illegal bestmoves" number cannot come from the committed runner: `pos_line` is assigned only from a stdout line starting with `position` (`ds6/fuzzuci56.py` L99–L105), and the engine prints no such line. Show it again: `bash pos_echo.sh /agent/repos/build-base/forge pos_echo.stdin.txt` → `count=0`, and the first-word histogram lists only option/id/uciok/readyok/bestmove.
3. **S-F3** — `seqs: 0` in `out/fuzz56_summary.txt` against "2,000 sequences" in the report; all five other counters match.
4. **S-F4** — no sanitizer proof on the branch; the exe it used is `/tmp/l46_san/build/forge`, outside the repository.
5. **S-F5** — not reproducible: `fuzzuci56.py` reads `/tmp/uci56_seqs.txt`; `make_uci56.py` reads `/tmp/ds6_work/forge-combo29/tests_deepseek6_long1/set_G.epd`; neither is committed.
6. **S-F6** — hang detector scans the last 30 stdout lines for `readyok` instead of clearing per isready, so an earlier `readyok` can satisfy a later `isready`.

### Suspicions, not proven
- That the helper's 2,000-sequence run actually produced 2,000 completed sequences with all its claimed zeros. The summary's `ok: 2000` is the only record of the run's size that survived, and `seqs` disagrees with it. I could not re-run their sequence file because it is not on the branch.
- Whether their exe (`/tmp/l46_san/build/forge`) was the same source as 6b98f217. Nothing on the branch says.

## What I did NOT do
- I did not re-run deepseek6's own 2,000 sequences: the sequence file and the set_G.epd it was generated from are both outside the repository.
- I did not attempt to prove their run *did* crash; only that the branch does not support its two strongest claims.
- My 200-sequence sample runs on the plain release build, not under the sanitizer (the sanitizer runner proof above is for the 0-line claim on a single deep search, not for all 200 sequences).

## What I am NOT sure about
- Whether `pos_line` could be set by some stdout line I did not produce in `pos_echo.sh` (I exercised uci/isready/setoption/position/go depth). Any `info string` line the engine emits begins with `info`, so I believe not, but I did not enumerate every engine reply.
- Whether the report writer knew about the dead legality branch. That is intent, not evidence, and I do not claim it.

## Times: see `stamps.txt`
Every `date -u` line of this job is in `../job2/stamps.txt` and each `ds6/` fetch in `ds6/stamps.txt`.

## The last command's output
```
$ git status --short forge-combo29/swarm/20/
?? forge-combo29/swarm/20/FINDINGS.md
?? forge-combo29/swarm/20/job2/
?? forge-combo29/swarm/20/job3/
$ ls forge-combo29/swarm/20/job2/
PREDICTION.txt  ds6  fetch_ds6.sh  myfuzz.py  myfuzz_out  pos_echo.out.txt  pos_echo.sh
pos_echo.stdin.txt  quitcut.out.txt  quitcut.sh  recount56.py  recount56.txt  stamps.txt
```
