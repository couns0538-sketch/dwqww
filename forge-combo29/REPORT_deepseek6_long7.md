# REPORT — deepseek6, long 7 (AddressSanitizer + UndefinedBehaviorSanitizer)

for-fable-and-opus/deepseek6-work

## 1. Three lines

**Asked:** build the plain base with `-fsanitize=address,undefined -fno-omit-frame-pointer`, prove the build reports a PLANTED one-line heap read past an array at the top of the root search, then run the clean build `go depth 10` on O and G under S14 and count the sanitizer lines.
**Answer:** the planted fault is reported on every position (2 ASan lines each: `heap-buffer-overflow`, `READ of size 4`, frame at the planted line 1561 of `Worker::search`). The clean base build reports **0 sanitizer lines across 553 positions** — O 200/200 and G 353/353, each in its own process so the exit-time leak checker also ran.
**How sure:** certain that the counter is sensitive (the same counter reads 6 on 3 planted positions and 0 on 553 clean ones), certain of the 0.

## 2. The honesty numbers — NOT applicable to this build, and why

The honesty check (bench/perft node counts) is a property of the RELEASE build; a sanitizer build has
`-O3`-free RelWithDebInfo code with instrumented allocations and its bench times would be meaningless, but its
**node counts should still be the pins** because the sanitizers do not change arithmetic. I did not run bench on
the sanitizer build because long 7's own text asks for `go depth 10` on O and G, not for the pins. **I state
plainly: no honesty numbers are claimed for the sanitizer build in this report.** The plain release build's
four pins were established in long 1 and are re-established only for release builds.

The exe identity is `exe.sha256`: `/agent/repos/work/build-l7san/forge`, sha256
`9e3de2e5a1b12c1dfcf57be52fc49fd301a4d92da010f62c08b9f45156776cab`, `id name Chess Engine Forge 6.4.24
candidate` (`uci.txt`), built from an untouched `/agent/repos/p10` at
6b98f2170a3210e71beed04bbd2553972c253ed7.

## 3. Steps

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| sanitizer build of the plain base | done | `exe.sha256` | RelWithDebInfo, g++ 13.3.0, `-fsanitize=address,undefined -fno-omit-frame-pointer` compile AND link |
| planted fault written as a text patch | done | `planted/planted_fault.patch.txt` | one block, `Worker::search`, root only |
| planted build | done | `planted/planted_build.log` | built |
| planted fault MUST be reported | done | `planted/planted_run_err.txt` | **2 ASan lines**: `heap-buffer-overflow`, `READ of size 4`, `#0 ... search.cpp:1561` |
| clean build, O under S14, depth 10 | done | `O_S14_d10_san.rows`, `O_S14_d10_san.rawlog` | **sanlines 0** over 200 positions |
| clean build, G under S14, depth 10 | done | `G_S14_d10_san.rows`, `G_S14_d10_san.rawlog` | **sanlines 0** over 353 positions |
| the counter is proven sensitive on the SAME runner | done | `planted_via_sanrun.rows`, `planted_via_sanrun.rawlog` | **sanlines 6 over 3 positions** (2 per position), exit code 1 per position |

## 4. Findings

### 4.1 The planted fault is reported, at the planted line

```
cd forge-combo29/tests_deepseek6_long7/planted
printf 'position startpos\ngo depth 6\nquit\n' | /agent/repos/work/build-l7plant/forge > planted_run_out.txt 2> planted_run_err.txt
grep -E 'ERROR: AddressSanitizer|READ of size|#0 ' planted_run_err.txt
==25862==ERROR: AddressSanitizer: heap-buffer-overflow on address 0x503000001890 ...
READ of size 4 at 0x503000001890 thread T1
    #0 0x560b700296e9 in forge::Worker::search(...) /agent/repos/p11/forge-combo29/src/search.cpp:1561
```
The frame number is exactly the line the patch adds. The process exits 1, and `bestmove` is never printed,
which is what a fatal ASan report looks like from the UCI side.

### 4.2 The clean build is silent on 553 positions

```
python3 sancount.py O_S14_d10_san.rows
O_S14_d10_san.rows: sanlines 0 (positions 200)
python3 sancount.py G_S14_d10_san.rows
G_S14_d10_san.rows: sanlines 0 (positions 353)
```
Each position ran in its **own process**, so AddressSanitizer's exit-time LeakSanitizer pass ran 553 times
too — a leak would have shown as a `LeakSanitizer` line in the same files. Nothing.

### 4.3 The counter is sensitive — the same runner reads 6 on the planted build

This is the part that makes 4.2 mean something. Running the PLANTED binary through the identical runner over
3 positions:

```
python3 sanrun.py --exe .../build-l7plant/forge --set first200.fens --out planted_via_sanrun.rows \
                  --raw planted_via_sanrun.rawlog --opts "$S14" --depth 10 --limit 3
positions 3, sanitizer lines 6 -> planted_via_sanrun.rows
python3 sancount.py planted_via_sanrun.rows
planted_via_sanrun.rows: sanlines 6 (positions 3)
  positions with reports: [('0', 2, '1'), ('1', 2, '1'), ('2', 2, '1')]
```
Two lines per position (the `ERROR:` line and the `READ of size` line) and exit code 1 on each. So "0" in 4.2
is a measured zero, not a runner that cannot see reports.

### 4.4 The clean sanitizer build's node counts, recorded for long 8

Not a known-answer test at depth 10 (no depth-10 sums exist in the brief), but they are the baseline every
patched sanitizer build in long 8 must match:

| set | depth | rows | sum |
|---|---|---|---|
| O under S14 | 10 | 200 | **3,809,466** |
| G under S14 | 10 | 353 | **7,290,580** |

Two independent harnesses agree on the O figure: the first pass used `rows.py` (which discards non-`info`
lines) and gave exactly 3,809,466 on 200 rows, and `sanrun.py` (which keeps every line and runs a fresh process
per position) gave the same sum. That the two disagree nowhere is a check on both.

### Suspicions, not proven

- A sanitizer line count of 0 does not prove the engine is free of UB — it proves none of these 553 positions
  at depth 10 triggers what ASan and UBSan can see. UB that needs a different position, a deeper search, or
  a different sanitizer (thread, memory) is outside this run.
- The first `sanrun.py` version sent `quit` immediately after `go` and so truncated every search; its 0
  sanitizer lines were a TRUE but meaningless 0 (nothing was searched). I caught it because the node sum was
  0. That is noted here because it is exactly the class of mistake that would have made this report dishonest
  if I had only printed the sanitizer count.

## 5. What I read from my colleagues

- **kimi5** (`NOTES_kimi5.md`): its job-9 note says "`cp -r` of a source tree carried the CMakeCache into the
  patched copy and the configure died against the OLD path". I hit the same class of thing from the other
  side: reusing `/agent/repos/work/build-*` names would have been the equivalent trap, so every build in this
  report has its own directory (`build-l7san`, `build-l7plant`).
- **glmflash5** (`NOTES_glmflash5.md`): nothing on sanitizers.
- **deepseek5** (`NOTES_deepseek5.md`): its job-30 lesson (read the state when the event happens) is why I read
  the process's exit-time output instead of only what arrived before `bestmove` — the leak checker prints at
  exit, so a runner that stops reading at `bestmove` would miss it. My first version made exactly that
  mistake in a different way.
- No note is an order and no number above came from a note.

## 6. What I did NOT do

- I did not run the four honesty pins on the sanitizer build (long 7 asks for `go depth 10` on O and G).
- I did not build ThreadSanitizer or MemorySanitizer; long 7 names ASan and UBSan only.
- I did not test a leak-specific (LSan-only) run; the exit-time leak check is whatever ASan does by default,
  and I did not verify that leak detection is on rather than suppressed by the environment.
- I did not run the planted fault on G or with other depths; one report at the planted line is what long 7
  asks for.
- I did not commit engine source: the planted change is committed as `planted/planted_fault.patch.txt`, and
  neither the planted nor the clean tree is committed.
- I did not open a pull request.

## 7. What I am NOT sure about

- Whether LeakSanitizer is actually active in this container. It can be disabled where `ptrace` is
  unavailable, and if it were off, "0 leak lines" would be vacuous. I did not run a positive control for
  leaks (a deliberate leak) — only for a heap overread. **This is the one part of long 7 I would redo with a
  second planted fault** (a leaked allocation) if a job asks.
- Whether the depth-10 sums will be reproducible on a patched build in long 8 whose arithmetic is identical;
  they should be, since 4.4's two harnesses agreed.

## 8. A better way

Two things. First, a sanitizer run needs a per-position PROCESS, not one long session: a fatal ASan report
kills the process, so one session loses every later position, and the leak report only exists at exit.
Second, a sanitizer test needs its own positive control (mine: 2 lines per planted position) and, for leaks,
a second positive control (a deliberate leak) — a zero without a control is not a result. I will add the
deliberate-leak control in long 8 if a job leaves room for it.

## 9. times

see `stamps.txt` (this folder) and `planted/stamps.txt`.

## 10. Model

DeepSeek V4.1 Flash 1017 (`deepseek-v41-flash-1017`, as named by this runtime).

## Files

`ls` + `git status --short` before this commit: `precommit_evidence.txt`. Harnesses: `sanrun.py` (per-position
process, waits for `bestmove`, then reads to exit), `sancount.py` (the one command that counts the lines).
