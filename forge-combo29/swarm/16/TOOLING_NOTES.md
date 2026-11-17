# TOOLING NOTES — environment defects and traps, in order of how badly they bite

> **A tooling note that overstates is worse than none, because the next seat trusts it instead of re-checking.**
> Every claim below was verified against the files before it was written. **Three** were corrected — two narrowed,
> and one *withdrawn outright* because I could not reproduce it — and all three are kept visible at the end of this
> file, since a note that quietly improves itself teaches the reader nothing about how much to trust it.

Written by seat 16 for whoever runs this work next. Every entry cost me real time or nearly produced a wrong
result; each says what the trap is, how it presents, and the fix.

---

## 1. A `perf` REPORT FROM EMPTY DATA LOOKS LIKE A REAL PROFILE OF KERNEL TIME

**This goes first because it produces a confidently wrong profile, and it is the trap I actually fell into.**

- **What happened:** my first profile attempt produced `perf.data` of **0 bytes**, because recording was blocked by
  `kernel.perf_event_paranoid = 2` (see entry 2). `perf report` on it does not fail loudly in the way you would
  expect — the report text I captured showed only a handful of **kernel** symbols (`do_user_addr_fault`,
  `clear_page_erms`, `_raw_spin_lock`) and 0.96 % "accounted". Reading that as a profile would say the engine spends
  its time in the kernel. It does not.
- **The tell:** `ls -la perf.data` is 0 bytes, and `perf report` prints
  `zero-sized data (perf.data), nothing to do!` — or, if a stale file exists, `# Samples:` far below
  `rate × seconds`.
- **CORRECTION I OWE, because I first published this as a redirect defect:** I claimed that
  `perf report --stdio` redirected to a file **silently drops user symbols** (4 kernel symbols vs 58 in a terminal)
  and that `--sort symbol` was the fix. **I could not reproduce that.** Tested on a fresh good profile, the plain
  form and the `--sort symbol` form both reported the same 8 symbols including `nnue::`, and redirecting to a file
  changed nothing. What produced the kernel-only report was **empty data**, not redirection. `--sort symbol` is a
  convenient field selection, not a fix for a defect.
- **The rule that survives, and it is the useful one:** **if `nnue::` is absent from a profile of an engine with a
  net loaded, check the DATA first, not the engine.** One command:
  ```
  ls -la perf.data                       # must be non-zero
  perf report -i perf.data --stdio --sort symbol | grep -c 'nnue::'
  ```
  Zero hits plus a small `perf.data` means the recording failed, not that the engine is fast in the kernel.

## 1b. A STALE SUMMARY FILE RECORDED THE NET AT 0.00 % AND WAS THE MOST PERSUASIVE WRONG ANSWER IN MY FOLDER

**This deserves its own entry because it is the failure mode that looks like a clean result.**

- **What it was:** `v3/prof_open/summary.txt` recorded `nnue_pct 0.00` and `accounted_pct 0.96`. Both came from my
  FIRST profile run, whose `perf.data` was **empty** because recording was blocked by `perf_event_paranoid = 2`
  (entry 1/2). The file sat in my folder for hours after I had diagnosed and fixed that cause — in the folder of the
  seat that had *documented* the empty-profile trap.
- **Why it is worse than an error:** a zero that agrees with a comfortable prior needs no defending. "The net path
  costs 0.00 %" would have read as a clean measurement, supported a conclusion already in the air ("the kernel is not
  where the time is"), and nobody would have re-derived it. A number that *contradicted* the prior would have been
  challenged within a minute.
- **How it was caught:** I replaced hand-typed figures with a generator script, and the generator read the *stale*
  file and printed "0.00 %" into a FINAL block next to a 20.85 % from the other arm. The disagreement between two
  numbers from the same folder is what exposed it.
- **The disposition:** renamed to **`summary_BROKEN_emptyperfdata.txt`** rather than deleted, so the failure is
  visible in the filename. Deleting it would have removed the evidence that the trap had fired in my own folder.
- **The rule:** when a metric file is produced by a run you later diagnose as broken, do not leave it at its original
  path. Rename it so the breakage is in the name, and make ONE script the only producer of that metric
  (`v3/perf_shares.py`) so a second format or a stale read cannot creep back.

## 1c. PERF'S DEMANGLED NAMES WRAP ONTO FOLLOWING LINES — ONE PARSER OR NONE

The same `perf report` output gave me three different totals from three parses:

```
naive "percent then a complete symbol on one line"   0.96 %   (most symbols skipped: names wrap)
a slightly better regex                             2.06 %
the parser that matches the name PREFIX only        20.85 %   correct, 100.05 % accounted
```

A demangled C++ name is long enough that perf wraps it; the share belongs to the line carrying the percentage and the
name may continue below. So there is no "roughly right" parse — either the accounted total is ~100 % or the parse is
wrong. **Check `accounted_pct ≈ 100` before believing any share**, and keep one parser as the only source.

## 2. `perf` ON THESE MACHINES: ABSENT, THEN REFUSED BY TWO DIFFERENT LAYERS

- `perf` is **not installed** (`which perf` empty; `apt-get install linux-tools-generic linux-tools-common` works).
- After installing, `/usr/bin/perf` is a **version wrapper** that refuses on kernel **6.12.113+**:
  `WARNING: perf not found for kernel 6.12.113+`. The 6.8 **binary** works fine:
  ```
  /usr/lib/linux-tools/6.8.0-149-generic/perf
  ```
- Recording then fails with a **zero-sized data file** until `kernel.perf_event_paranoid` is lowered. It was **2**;
  `sudo sysctl -w kernel.perf_event_paranoid=-1` fixed it. The error text is a paragraph about `perf_event_paranoid`
  rather than a clean failure, and `perf report` then says `zero-sized data (perf.data), nothing to do!`.
- **Check before trusting any profile:** `ls -la perf.data` must be non-zero, and `perf report` must print
  `# Samples: N` with N > 0.

## 3. A FULLY PIPELINED `go` SCRIPT MAKES THE ENGINE ANSWER A FABRICATED `bestmove a2a3`

- **Symptom:** writing all commands at once (many `position` / `go` pairs, then `quit`) makes the engine answer
  **`bestmove a2a3`** with **zero `info depth` lines** — the first legal move, unsearched.
- **How many:** the count depends on how many searches are queued and how much of the script the reader drains.
  Measured on my own script `v3/prof_open/openings.uci` (a 60-position pipeline): **8 `a2a3` answers** on the first
  run and **3** on each of three later runs — reproducible per script, varying with what gets read. Either way the
  node rows are 0, which is what matters.
- **How it presents in data:** node rows come back **0 of N**, or a depth-N line is missing. That is the tell.
- **The fix:** drive every search to its `bestmove` before writing the next command, and send `quit` only at the end.
  A long-lived process is fine; pipelining is not.
- **Related and separate:** `bench` and `eval` answer with an `info string ...` line and **no bestmove**, so send
  `isready` after them and wait for `readyok` — waiting for bestmove hangs at 0 % CPU forever.

## 4. `ucinewgame` AFTER `position` RESETS THE BOARD TO STARTPOS

- On this tree `ucinewgame` calls `board.set_fen(StandardStartFen)` (seat 12's S-F1). If you send
  `position fen X` then `ucinewgame`, the search runs on **startpos**.
- **How it presents:** every `eval` returns the startpos value. In my first Step 0 run the second and third
  positions both returned `nnue 968` (the startpos value) instead of 1176 and 31, which is what exposed it — the
  raw output is in `v3/run2.log`.
- **The order:** `ucinewgame` / `isready` / `position fen ...` / `isready` / `go`.

## 5. NEVER RETYPE A NUMBER FROM ANOTHER DOCUMENT INTO AN EXPECTATION

- I retyped file 7's `4151906` as `4191906` into my own Step 0 expectation table, then reported a 40,000-node
  "hardware discrepancy" and offered to hand the job over. Three other seats on identical hardware had already
  reported the pair as matching.
- **The rule is the brief's own "never typed by hand", extended to expected values:** paste, or read the value
  programmatically (`od -c`, `awk -F'|'`), and byte-check the source row.
- **Corollary:** when several independent measurements disagree with your one reading, the count of measurements
  against you is evidence about where to look first — and the first place is your own reading.

## 6. `git add <dir>` STAGES A STRAY FILE WRITTEN ONE DIRECTORY SHORT

- A relative append (`cat >> ../../FINDINGS.md` from a job subdirectory) silently creates the file one level short
  of intent. No step errors. It cost me twenty findings rows across four files, and later three recurrences.
- **Two checks, because "outside your folder" has two states:** `git log --diff-filter=A` sees a file that was
  **committed then deleted**; `git status --porcelain --untracked-files=all` sees one that **exists now and was never
  committed** (the likelier state when you run the check). Run both. `check_folder.py` in this folder does.
- **The stronger fix:** an appender that resolves the path absolutely and refuses anything that is not a findings
  row (`addf.sh` in this folder). A refusal is always better than a stray.

## 7. `--march`/CPU AFFECTS BENCH NODE COUNTS ONLY THROUGH THE ISA-BOUND PATHS — NOT AT ALL HERE

- File 7's numbers reproduce exactly with **g++ 13.3.0, `-march=x86-64-v4`, Intel Xeon**, despite the PC using
  clang and `znver5`. So for the v3 workload the compiler/CPU difference the numbers are sensitive to is nil — worth
  recording, because the opposite assumption cost me a wrong hypothesis first.

## 8. `script -q -c` HANGS ON A PAGER

- Tried to capture a perf report through a pty with `script -q -c "perf report ..."`; it hung until killed. The
  `--sort symbol` form makes the pty unnecessary.

---

## THREE CLAIMS I CORRECTED, kept visible — including one I had to WITHDRAW

Two were overstated and narrowed after checking the files; the third was **simply wrong** and is withdrawn. They are
here because the *kind* of error is instructive, and the third is the most instructive of all.

**0. WITHDRAWN: "`perf report --stdio` redirected to a file silently drops all user symbols."** I wrote this after
seeing a kernel-only report and assumed the redirect caused it. **I could not reproduce it.** On a fresh good profile
the plain form and the `--sort symbol` form both report the same symbols, and redirecting changes nothing. The
kernel-only report came from **empty `perf.data`** (recording blocked by `perf_event_paranoid = 2`). This is the
worst kind of note error — a plausible mechanism attached to a real symptom — and it would have sent the next seat
chasing a non-existent bug in `perf` instead of checking whether its recording worked. The `nnue::` check survives
and is *better* for the correction: it points at the data, which is where the fault actually was.

**1. "I got `bestmove a2a3` eight times out of forty searches."** Too fixed. On my 60-position script the count is
**8 on the first run and 3 on each of three later runs** — it varies with how much of the pipelined script the
process drains before it is killed. The useful fact is not the number: it is that **the failure is state-dependent
rather than constant**, which is why a node-row count of 0, not a fixed symptom count, is the thing to check.

**2. "Every `eval` returned the startpos value — I got `nnue 968` for three different positions."** Too broad.
Precisely: the first position IS startpos, so 968 was correct there; the **second and third** returned 968 where
their own values are 1176 and 31. So the claim is "two of three were replaced by the startpos value", not "three
positions all gave the same number". Raw output: `v3/run2.log`.

**The `nnue::` sanity rule, which is the single most useful check in this file (and its CORRECTED form — the
original version of this note blamed file redirection, which I could not reproduce; empty data was the cause):**

> If `nnue::` is absent from a profile of an engine with a net loaded, **the report is broken, not the engine.** One
> command settles it: `perf report -i perf.data --stdio --sort symbol | grep nnue`.

**And the closed explanation that should not be re-opened:** `-march` and CPU do **not** affect these node counts.
The PC's clang/`znver5` and my g++/`x86-64-v4` on an Intel Xeon both reproduce file 7 exactly. I built a
hardware explanation on a disagreement that did not exist; nothing here is hardware-dependent, so no future seat
needs to reach for that hypothesis.
