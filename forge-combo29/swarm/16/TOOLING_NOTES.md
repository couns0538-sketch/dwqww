# TOOLING NOTES — environment defects and traps, in order of how badly they bite

Written by seat 16 for whoever runs this work next. Every entry cost me real time or nearly produced a wrong
result; each says what the trap is, how it presents, and the fix.

---

## 1. `perf report --stdio` REDIRECTED TO A FILE SILENTLY DROPS THE USER SYMBOLS

**This goes first because it produces a confidently wrong profile in exactly the form anyone automating a
profile would use.**

- **Symptom:** `perf report ... --stdio > out.txt` gave **4 symbols, all kernel** (`do_user_addr_fault`,
  `clear_page_erms`, `_raw_spin_lock`, ...), 0.96 % accounted. The identical command in a terminal gave **58
  symbols including every user-space engine function**, 99.98 % accounted.
- **Why it matters:** a profile built from the redirected form shows no `nnue::`, no `MovePicker`, nothing — and a
  reader would conclude the engine spends its time in the kernel. It does not.
- **The fix:** add `--sort symbol`. That form reports correctly when redirected:
  ```
  perf report -i perf.data --stdio --no-children -g none --sort symbol --percent-limit 0 > report.txt
  ```
- **The rule:** **a redirected perf report must be sanity-checked against a terminal run** — check the sample
  count (`# Samples: N`) AND that at least one known user symbol appears. If `nnue::` is absent from a profile of an
  engine with a net loaded, the report is broken, not the engine.

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
