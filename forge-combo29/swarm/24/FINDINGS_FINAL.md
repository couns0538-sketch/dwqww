# FINDINGS — seat 24 (area 4, THREADS), final state of every find

Every line names **build** and **settings**. Threads 1 for anything score-shaped; where Threads > 1 was needed
(race tests, the instability study) it is stated and no score is compared.

## The one-line rule a tuner needs

**No result above one thread is reproducible on either build, at 2 or 4 threads — so any A/B comparison must be
single-threaded, or repeated enough to average the spread.**

The matrix behind it (depth 12, Hash 16, OwnBook false, 6 fresh processes per position, the same first 20 positions
of G, moves compared, no score read):

| build | Threads 1 | Threads 2 | Threads 4 |
|---|---|---|---|
| base tree, S14 | **0 of 20** | **8 of 20 (40 %)** | **9 of 20 (45 %)** |
| PC r15, PC20 | **0 of 20** | **10 of 20 (50 %)** | **8 of 20 (40 %)** |

Every Threads-1 node count was identical to the digit; every thread count above 1 varied in every position tested.
An independent position set (R, seed 2411, never used elsewhere in the session) reproduced it at 4 of 20 on the PC
build, so this does not depend on one set of positions.

---

## Findings of mine, with state

### Confirmed by another seat

| id | build / settings | claim | confirmed by |
|---|---|---|---|
| 24-F1 | base, TSan, Threads 1/2/4/8/16 | 300 random `setoption Threads`/`Hash` changes between searches (131 with `ucinewgame`) give 0 TSan reports, 0 crashes, 0 illegal bestmoves | **21-C5** (own harness and own planted race, reported 12/12) |
| 24-C1 | base, S14, all thread counts | `go searchmoves` naming no LEGAL root move answers the quoted info line + `bestmove 0000` on a board with legal moves | **21-C8**, **seat 11's S-C11** |
| 24-C2 | base, defaults | `ucinewgame` resets the board to startpos (perft 1 enumerates 20 startpos moves on a 6-move board) | **seat 11's S-C12** |
| 24-F14 | PC r15 + base, PC20/S14, Threads 1 | at a terminal root every BOUNDED form answers `0000` in 0.00 s and only the unbounded forms hang | **30-C15** (adds the control my row lacked) |
| 24-F16 | PC r15, PC20, Threads 1 | `terminal_root_infinite.patch.txt` applies to the PC tree and removes every MISSING entry | **30-C16** (own build, own matrix, same 154-line offset) |

### Open — no other seat has confirmed these yet

| id | build / settings | claim |
|---|---|---|
| 24-F2 | base, TSan, Threads 2/4/8/16, 398 searched | 0 TSan reports, 0 crashes, 0 illegal bestmoves across the Threads sweep (planted control 102 blocks) |
| 24-F5 | base, TSan, Threads 8, 1000 rounds | `go infinite`+`stop` is race-free (planted control 22 blocks) |
| 24-F7 | PC r15, PC20, Threads 1 AND 4 | **the terminal-root `go infinite` hang is STILL PRESENT on the PC build** (`stop` rescues it in 0.20 s) |
| 24-F9 | PC r15 TSan, PC20, Threads 4, 400 rounds | stop path race-free on the PC build (planted 29 blocks) |
| 24-F11 | PC r15 TSan, PC20, Threads 2/4/8/16, 400 searched | 400/400 clean sweep, 0 TSan, 0 timeouts (planted 29 blocks) |
| 24-F13 | PC r15 TSan, PC20, Threads 1–8, 250 steps | option churn including all four PC switches is race-free (planted 10 blocks) |
| 24-F18 | PC r15 TSan, PC20, Threads 16, 150 rounds | stop path clean at 16 threads on 4 cores |
| 24-F20 | PC r15 TSan, PC20, Threads 8/16/32, 60 steps | clean at 8x oversubscription (Threads 32 on 4 cores) |
| 24-F21 / 21b | PC r15 PC20 / base S14, Threads 4, 6–8 fresh runs per position | **the chosen MOVE differs between runs on ordinary positions** (both builds) |
| 24-F22 | PC r15, PC20, Threads 4, 20 positions | 8 of 20 (40 %) change move |
| 24-F23 | PC r15, PC20, Threads 2, 20 positions | 10 of 20 (50 %) — Threads 2 is **not** a safe middle ground |
| 24-F24 | both builds, Threads 1/2/4, 20 positions each | the full matrix above: architectural, not PC-specific |
| 24-F26 | PC r15, PC20, Threads 4, independent R set | 4 of 20 — the effect is not specific to set G |
| 24-F15 / F17 | base + PC r15, PC20 | one text patch fixing **both** silent GUI hangs (terminal root, and the opponent-only clock), honesty numbers unchanged |
| 24-F25 | both builds, defaults | an ABORTED search publishes the generator-order first move with 0 nodes — but **not** at a terminal root, where it correctly answers `0000` |
| 24-F6 | PC r15, none/S14/PC20, Threads 1 | every published number reproduced (none 312866/862329/3024920/perft5 4865609; S14 242796/656517; PC20 278024/587276) |

### Checks of other seats

| id | verdict | of |
|---|---|---|
| 24-C1 | CONFIRMS | seat 02 S-F2 (searchmoves → `0000`), re-verified under the integrity rule with a negative control |
| 24-C2 | CONFIRMS | seat 12 S-F1 (`ucinewgame` resets the board) |
| 24-C3 | CONFIRMS | seat 05 S-F8 (terminal-root `go infinite` never answers) |
| 24-C6 | CONFIRMS | seat 04 04-F1 (thread-scaled node explosion; 165.5x over 8 fresh processes) |
| 24-C8 | MAIN CLAIM CONFIRMS, **CONTROL REFUTED** | seat 02 S-F4 — an opponent's clock is parsed and **discarded** at `src/uci.cpp:184-191`, so no opponent clock can bound a search |
| 24-C9 | CONFIRMS | seat 19 19-F25 (aborted search publishes the generator-order first move) |

### My own corrections, recorded so they are not lost

| id | what I got wrong |
|---|---|
| 24-C5 | I explained the pos-90 slowdown as "warm state"; at Threads 1 **neither** build shows it, so warm state alone is not sufficient |
| 24-C7 | I then narrowed it to "Threads > 1 **and** warm state"; my own 8 fresh-process runs show the explosion needs **Threads > 1 only** — the sweep rows that looked warm-state-dependent were unlucky draws from the threaded distribution. **F3's measurements stand; its mechanism is withdrawn.** Seat 11's S-C10 additionally shows the effect does not appear at all on their uninstrumented build, which I accept as a scope on F3 (their machine, their history). |
| 24-C4 | my first planted control for the PC TSan zero was invalid (the base planted binary refused PC20 and I got a false 0); fixed by planting into a copy of the PC source |
| — | my first PC honesty script omitted the `value` keyword, so every `setoption` was refused and all three regimes printed the default numbers — caught by reading the raw file, not the table |

---

## Deliverables for the owner

- `patches/two_gui_hang_fixes.patch.txt` — one text patch against the PC r15 source, fixing both silent GUI hangs.
- `patches/APPLY_SHEET.md` — one page: apply, both faults, before/after, honesty table, regressions (ponder and
  abort paths unchanged), and **"NOT MEASURED — no match was run, the strength effect is unmeasured."**
- `REPORT_threads.md` — the instability study and the matrix.
- `REPORT_job1.md`, `REPORT_job2.md`, `REPORT_job3.md`, `REPORT_pc.md` — the area-4 jobs and their PC-build re-runs.

## Limits I want on the record

- The mechanism behind the threaded move instability is **not identified**. Two candidate families remain (shared
  TT entries written at different times, and helper-cutoff ordering), untested.
- Whether the differing moves are equally good is **not measured**; the honest claim is "not reproducible", not
  "worse".
- The 40 %/50 % rates are for samples of 20 positions each, not global probabilities.
- My job-1 family ran without `OwnBook false` and at Threads > 1; no book move appeared and every bestmove was
  checked legal, but those scores are **provisional** and are labelled so.
