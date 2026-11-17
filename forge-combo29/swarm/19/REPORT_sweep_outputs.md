# The zero-info-line output sweep: 1983 was my bug, ~1200 survive, and read the file list not the count

seat 19 · area 9 · a static audit across all 49 seat branches.

## 1. The three lines

**What was asked.** Sweep the branches for committed **output** files showing a `bestmove` with no `info depth`
line — the 19-F12 signature — rather than only for input files ending at a `go`. That catches a job that used a
bad driver but committed only outputs.

**The answer.** **My first version of the sweep was wrong and reported 1,983 flags; that number is not usable.**
The bug: I matched `^info depth` without allowing leading whitespace, and most seats' harnesses capture the
engine's output **indented** (e.g. `    info depth 1 ...`). Everything indented looked like "no search". The
corrected run reports **~1,200 flags**, and the large counts are still concentrated in two seats whose output
files are mostly *one aborted search each*, which is the thing being looked for.

**How sure.** The detector is verified in both directions (§3): it does **not** flag my four corrected result
files, and **does** flag files I know are aborted-search artifacts. But **the counts alone are not a finding** —
I am reporting the method, the corrected numbers, and the fact that I checked my own folder's 17 flags by hand
and **all 17 are genuine** (§4).

## 2. My own bug, recorded

| version | regex | flags | verdict |
|---|---|---|---|
| first | `^info depth` | **1,983** | **wrong** — missed indented `info` lines |
| corrected | `^\s*info depth` and line-initial `bestmove` only | **~1,200** | usable, with caveats |

Two compounding errors, both mine:

1. **`^info depth` without `\s*`.** The engine's output is often captured with indentation, so a real search
   looks like no search. This alone inflated the count by hundreds.
2. **Counting `bestmove` anywhere in a file.** A *report* that says "the engine answers `bestmove a2a3`" was
   counted as an output file. Fixed by requiring `bestmove` to start a line.

**The tell I should have caught first: 1,983 of 3,000-odd output files failing is not a plausible measurement
defect — it is a plausible detector defect.** That is the same rule as the ordering bug in 19-C8: a rate too
high to believe is evidence about the instrument.

## 3. The detector verified in both directions

**Does NOT flag** my four corrected result files (`loneking/out3`, `softnodes/out`, `nodes/out2`,
`pcver/threads`) — none of them contains a line-initial `bestmove` at all, because they are tables. Good: no
false positive on clean work.

**Does flag** — from my own folder, 17 files, and every one I inspected is a genuine 19-F12 artifact:

| file | what it is |
|---|---|
| `job1b/quitabort/A_quit_immediately.txt`, `C_eof_immediately.txt`, `D_no_terminator.txt` | **my own 19-F12 demonstration cases** — they exist precisely to show the fabricated `bestmove a2a3` with no `info` lines |
| `job1b/plant/planted.txt` | **the plant control** for 19-F12, expected to show zero nodes |
| `job1b/profR/search.stdout.txt`, `profR12/search.stdout.txt` | the two bad profiling runs I **discarded before using** (this is what led me to write the correct driver) |
| `job1b/go_timing_out.txt` | the pipe-vs-delayed-quit comparison table, which *quotes* the fabricated answers |
| `pcver/f12path/A_only_P1.txt` | the 19-F25 path-identification case |

**So the 17 flags in my own folder are all correct flags of files that are *supposed* to look like this.** That
is the strongest evidence the detector works, and it is also why **a flag is not a defect claim** — several of my
flagged files are the evidence *for* the defect.

## 4. The corrected counts, and how to read them

| seat | files with bestmove | zero info depth |
|---|---|---|
| 10 | 1,117 | **860** |
| 20 | 223 | **222** |
| 07 | 58 | 47 |
| 21 | 446 | 43 |
| 27 | 132 | 28 |
| 17 | 966 | 21 |
| 24 | 52 | 17 |
| 19 (mine) | 32 | 17 |
| 02 | 31 | 8 |
| 30 | 11 | 7 |

**How to read this table, and how NOT to:**

- **A row is not an accusation.** Seat 10's 860 may be one file per aborted probe in a job that was *studying*
  19-F12, exactly as my `quitabort/` folder is. I did not open seat 10's or seat 07's files.
- **The interesting signal is a seat whose flag count is close to its total**, because that means *most* of its
  committed output contains no search. Seat 20 (222 of 223) and seat 07 (47 of 58) fit that shape; seat 10's 860
  of 1,117 is the same pattern at scale.
- **What I verified myself:** seat 20's `job3`, 60 of 60 outputs with zero `info` lines (19-C13), already
  reported and already acted on — its owner has a guard in all 15 harnesses now.
- **What I did NOT do:** open seat 10's or seat 07's files to see whether those are deliberate 19-F12 studies
  (like mine) or unintended. **That is the next step and it is not the same as assuming.**

## 5. Finding

**19-C14 — the corrected zero-info-line output sweep flags ~1,200 committed files across the 49 branches, with
the largest concentrations at seat 10 (860 of 1,117) and seat 20 (222 of 223); seat 19's own 17 flags were each
inspected and are all legitimate 19-F12 evidence files, which verifies the detector in both directions.** An
earlier version of the same sweep reported 1,983 and was **wrong**, because `^info depth` did not permit
indentation and `bestmove` was counted inside prose. **The counts are a triage list, not a finding: a flag marks
a file whose committed output contains no search, and several such files are deliberately so.**

### What I did NOT do

- I did not open seat 10's or seat 07's flagged files, so I cannot say whether their flags are deliberate 19-F12
  studies or accidents. **Given how often this defect has now appeared, they should be checked** — starting with
  whichever of their findings quotes a score from one of those files.
- I did not sweep for the subtler variant: a file with *some* `info depth` lines where one search was aborted.
  My detector only flags files with **zero** `info` lines, so a file with 9 good searches and 1 aborted is
  invisible to it. That is a real limit of this method and probably the more common shape in a long job log.

## 6. Files

`checks/sweep_outputs.py` (corrected), `checks/sweep_out2/RESULT.txt` (corrected run),
`checks/sweep_out/RESULT.txt` (the wrong 1,983 run, kept).
