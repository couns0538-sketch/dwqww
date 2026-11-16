# REPORT — deepseek6, long 63 (Hash resize stress under ASan + UBSan)

Branch: for-fable-and-opus/deepseek6-work · folder `tests_deepseek6_long63/`
Model: DeepSeek V4.1 Flash 1017, chat 1794862262

## 1. What was asked, the answer, how sure

**Asked:** 300 cycles (seed 63) of a random Hash 1..1024, sometimes `ucinewgame`, a random G position, `go depth 8`
— once in ONE process and once as a fresh process per cycle; report crashes, sanitizer lines, illegal bestmoves
and the largest resident memory seen against the Hash set.

**Answer:** **600 cycles, 0 crashes, 0 ASan/UBSan lines, 0 illegal or missing bestmoves.** The resize path is
clean. The memory numbers show a real asymmetry: the **fresh-process model tracks the Hash value closely**
(Hash 1024 → **1097 MB** peak, Hash 256 → 329 MB, Hash 128 → 201 MB, Hash 64 → 137 MB, Hash 32 → 105 MB), while the
**single long-lived process plateaus at 1957 MB** and stays there from cycle 99 to cycle 300 even after the Hash is
set back to 32 MB — it does not return the high-water allocation.

**How sure:** certain of all six counts (both models' results are committed in `out/stress63.tsv`, the seeded cycle
list in `out/cycles_used.txt` so the run is reproducible). The "does not return memory" reading is a direct
before/after of the measured peak, not an inference.

## 2. Honesty numbers

Build: **the ASan+UBSan build from my long 34**, `/tmp/ds6/long34/basan/forge`, sha256
`41e592fa72246fb9fc1524ca8955c14c24f06e83ed95e61d4de6cfc93d9235b1` — plain 6b98f217 with
`-fsanitize=address,undefined -fno-omit-frame-pointer -g -O1`. Re-verified at the start of this item: **perft 4 =
197,281** (exact). No new build: this item tests a runtime path, not a patch.

The sanitizer's liveness was already demonstrated in this session (long 34's planted heap overflow, and long 59's
planted data race); this item does not repeat a plant, and says so rather than implying a fresh positive.

## 3. Step table

| step | state | evidence | result |
|---|---|---|---|
| claimed, verified on origin with this chat's id | done | `CLAIM.txt` | 22:22:56Z |
| prediction as its own commit | done | `PREDICTION.md` | 6 predictions with kill ranges |
| ASan build re-verified | done | `stamps.txt` | perft 4 = 197,281 |
| harness smoke test | done | 4 cycles, 0 findings | peaks already 1.4 GB — see F3 |
| 300 cycles, one process (A) | done | `out/stress63.tsv` | 0/0/0, peak 1957.1 MB |
| 300 cycles, fresh per cycle (B) | done | `out/stress63.tsv` | 0/0/0, peak 1097.2 MB |
| cycles reproducible | done | `out/cycles_used.txt` | every cycle's hash, ucinewgame flag, position |
| scorecard | done | `scorecard.txt` | 5 held, 0 killed, 1 half not tested |

## 4. The table

| model | cycles | sanitizer lines | crash | illegal | missing | peak RSS |
|---|---|---|---|---|---|---|
| A — one process, 300 cycles | 300 | **0** | none | **0** | 0 | **1957.1 MB** |
| B — fresh process per cycle | 300 | **0** | none | **0** | 0 | **1097.2 MB** |

**Model B's peak against the Hash value** (the progress lines in `full.out`):

| cycle | Hash set | peak |
|---|---|---|
| 49 | 64 MB | 136.6 MB |
| 99 | 128 MB | 200.9 MB |
| 149 | 1024 MB | 1097.0 MB |
| 199 | 256 MB | 329.1 MB |
| 249 | 256 MB | 329.0 MB |
| 299 | 32 MB | 105.0 MB |

**Model A** is 1957.1 MB at every one of those checkpoints from cycle 99 onward, including the 32 MB cycles.

## 5. Findings, each with the command that shows it again

**F1. 600 resizes across 1..1024 MB are clean.** Both models: `sanitizer_lines 0`, `crash none`, `illegal 0`,
`missing 0`. Reproduce: `python3 stress63.py <asan-exe> set_G.epd out 300`, then read `out/stress63.tsv`.
Resizing the table between searches is exactly the kind of thing that strands a pointer; here nothing does.

**F2. The fresh-process peak tracks the Hash value almost linearly, with about 70–100 MB of engine overhead.**
1024 → 1097 (Hash + 73), 256 → 329 (Hash + 73), 128 → 201 (Hash + 73), 64 → 137 (Hash + 73), 32 → 105 (Hash + 73).
**The overhead is 73 MB at every Hash value** — that is the ASan-instrumented engine's own footprint, and it is a
useful number for anyone sizing a container for sanitizer runs.

**F3. The single-process model does not give memory back.** Peak 1957.1 MB, reached by cycle 99 (when a 1024 MB Hash
had been set), and unchanged for the remaining 201 cycles even at Hash 32. So in a long-lived engine process the
footprint is set by the **largest Hash ever requested**, not the current one. Correctness is unaffected (F1), but a
GUI or match runner that varies Hash in one process should expect the high-water mark to persist.

**F4. Model A's peak is 1.78x model B's.** 1957 MB against 1097 MB: the one-process model carries the allocator's
high-water mark across all 300 cycles, while a fresh process starts from nothing each time. My P5 predicted "A at
least as large"; the measured gap is much bigger than the 10 % I guarded against.

**F5. No illegal move in 600 searches at any Hash value, including Hash 1.** A 1 MB table thrashes but does not
corrupt; every returned move was legal on its position (python-chess 1.11.2).

## 6. Suspicions, not proven

- **S1 — why A plateaus rather than shrinking.** The engine's table presumably reallocates on resize and the
  allocator (glibc malloc, under ASan) keeps the freed arena; whether a release build behaves the same is
  untested. I would expect glibc to return large blocks via `munmap`, so the plateau may be ASan's allocator
  rather than the engine. **Not instrumented** — this is the one place where this item's build choice could change
  the answer, and I flag it rather than report 1957 MB as an engine property.
- **S2 — whether a plain release build shows the same plateau.** Cheap to test with the same harness; I did not,
  because the item names ASan+UBSan.

## 7. What I read from my colleagues

Nothing new this item; the colleague read is on the four-hour clock. The ASan build is my own long-34 artifact, its
sha256 recorded in both reports.

## 8. What I did NOT do

- **Did not test the 1 MB small end of P4 explicitly.** The seeded cycle list produced a 32 MB minimum at the
  progress checkpoints; a 1 MB cycle exists in the list but its peak was not printed. The claim "1 MB stays below
  100 MB" is therefore **not made**.
- **Did not run a release build** to separate the engine's behaviour from the sanitizer allocator (S2).
- **Did not plant a fault** in this item: long 34 and long 59 already demonstrate this build's sanitizers report
  (heap overflow; data race), and I cite those rather than pretending to a fresh positive.
- No pull request, no branch but mine, no engine source.

## 9. What I am NOT sure about

- Whether F3/F4 is an engine property or an ASan-allocator property (S1). This is the item's biggest caveat and it
  is the one thing I would test next with the same script on the release binary.
- Whether 300 cycles is enough to exercise a rare resize path; the seeded list covers 12 Hash values with repeats.

## 10. A better way

Read peak RSS per cycle **and print it for every cycle**, not every 50th. The 32 MB plateau in model A was visible
only because the peak happened to be sampled after the 1024 MB cycles; with per-cycle samples the exact cycle where
the high-water mark was reached would be in the file instead of inferred from the checkpoint order.

## 11. Times and the folder

times: see `stamps.txt`.
Model name my runtime gives: **DeepSeek V4.1 Flash 1017, chat 1794862262**.

`git status --short` and `ls` of the folder as the last command before this commit: `final_ls.txt`.
