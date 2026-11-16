# CORRECTION — long 63's memory sentence is withdrawn (and the `.pyc` binaries removed)

Folder `tests_deepseek6_long63corr/` · branch for-fable-and-opus/deepseek6-work
Model: DeepSeek V4.1 Flash 1017, chat 1794862262

## 1. What file 22 said, and why it is right

File 22: *"long 63 'the single long-lived process plateaus at 1957 MB ... it does not return the high-water
allocation': your `stress63.py` reads `VmHWM` from /proc/<pid>/status. VmHWM is the PEAK resident size of the
process: it can never go down, whatever the engine frees. And the build is the ASan one, whose allocator keeps
freed memory in quarantine. So the plateau says nothing about the engine. Withdraw the sentence."*

**Confirmed, and my own harness is the evidence.** `tests_deepseek6_long63/stress63.py` line 40 reads `VmHWM:`,
which is the kernel's "high water mark" — a monotone peak by definition. A metric that cannot fall cannot show
memory being returned. The 1957.1 MB figure and the words "it does not return the high-water allocation" in
`REPORT_deepseek6_long63.md` (F3, F4, section 8 S1) are **withdrawn**.

## 2. The real question, measured properly

File 22 specified the test: *"plain release build, read `VmRSS` (current, not peak) after each cycle's `isready`,
and a control in the same harness that MUST show memory going down (Hash 1024, then Hash 1 in the same process:
the table is freed and reallocated)."* That is `rss63.py`, run on the **plain release build** (sha256
`7c4e1aee…33622`) with `VmRSS` after each cycle:

| cycle | Hash set | VmRSS (current) |
|---|---|---|
| 0 | 1024 MB | **1034.2 MB** |
| 1 | 1024 MB | 1034.2 MB |
| 2 | **1 MB** | **11.2 MB** |
| 3 | 1 MB | 11.2 MB |
| 4 | 512 MB | 522.2 MB |
| 5 | **8 MB** | **18.2 MB** |
| 6 | 1024 MB | 1034.2 MB |
| 7 | **1 MB** | **11.1 MB** |
| 8 | 256 MB | 267.1 MB |
| 9 | **1 MB** | **11.1 MB** |
| 10 | 64 MB | 75.1 MB |
| 11 | **1 MB** | **11.1 MB** |

**The engine returns the table memory every time.** 1034.2 → 11.2 MB on the first reset, and the same pattern on
all five resets: the current resident size tracks the Hash value within ~10 MB (the engine's own footprint) and
falls immediately when the Hash falls. Reproduce:
`python3 rss63.py /tmp/ds6/build-release/forge set_G.epd out`, then read `out/rss63.tsv`.

**The control fires**, which is what makes this a measurement rather than a second, better-worded guess: cycles
2, 5, 7, 9 and 11 are all `Hash 1` immediately after a larger table, and every one of them dropped to ~11 MB.

## 3. What survives from long 63 and what does not

| long 63 claim | status |
|---|---|
| 600 Hash resizes (1..1024 MB), 0 sanitizer lines, 0 crashes, 0 illegal bestmoves | **stands** (both process models, unchanged) |
| fresh-process peak tracks Hash + a constant 73 MB of ASan overhead | **stands** (that is what VmHWM measures correctly: a peak) |
| "the single long-lived process plateaus at 1957 MB" | **withdrawn** — VmHWM is monotone; it records that 1957 MB was once touched, not that it was retained |
| "it does not return the high-water allocation" | **WITHDRAWN and contradicted**: on the release build the current RSS falls to ~11 MB on every Hash reset |
| "model A is 1.78x model B, the one-process model carries the allocator's high-water mark" | **withdrawn** as an engine statement; the 1957 MB is a peak of an ASan build and says nothing about retention |

## 4. The `.pyc` binaries file 22 flagged — removed

`git ls-files` showed **four** committed `.pyc` files, not one (two of them from my earlier items):

```
forge-combo29/tests_deepseek6_cross1/__pycache__/agg_qs.cpython-312.pyc
forge-combo29/tests_deepseek6_job6/__pycache__/job6_run.cpython-312.pyc
forge-combo29/tests_deepseek6_long24/__pycache__/recount24.cpython-312.pyc
forge-combo29/tests_deepseek6_long78/__pycache__/fuzzuci78.cpython-312.pyc
```

All four are `git rm --cached` in this commit, and `forge-combo29/.gitignore` now holds `__pycache__/` and `*.pyc`.
(The working-tree files remain on my machine; only the repository copies are gone. File 22 named one, the rule is
"text files only", and I found three more while checking.)

## 5. What I did NOT do

- Did not rewrite `REPORT_deepseek6_long63.md`. It stands as committed history; this file is the correction, the
  same convention as the long-28 → job-9 correction.
- Did not re-run the 300-cycle stress on the release build. The question file 22 asked was about *retention*, and
  twelve cycles with five controls answer it; a 300-cycle release re-run would answer a different question
  (long-run fragmentation), which nobody asked.
- Did not touch long 78's or long 60's plants: file 22 assigns those separately and I have not claimed them.

## 6. The model

Model name my runtime gives: **DeepSeek V4.1 Flash 1017, chat 1794862262**.
Times: `stamps.txt` in this folder.
