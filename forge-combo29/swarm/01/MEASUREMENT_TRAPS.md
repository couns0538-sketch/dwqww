# The ten traps that silently change what a harness measures — including three about the harness itself

**Seat 01, 2026-11-17. One page, ready for the brief. Every trap below is confirmed by me on PC r15 + PC20,
Threads 1, Hash 16. Four are settings, one is a timer, one is a command whose safety depends on the position,
one is a measurement whose truth depends on the setting, and one is the act of typing — and all eight share one shape: the default is fine, a plausible
non-default or a careless measurement silently changes the number, and nothing warns you.**

> ## THE RULE
>
> **Assert and record `Threads 1` and `MultiPV 1`; to mean "no limit" OMIT the token — never send 0; time from
> immediately before `go` on a warmed process, verified with a `time 0` search; and put a wall cap and a node cap
> on every fixed-depth command.**

**A note on this page's own shape.** I appended Trap 3 and Trap 5 after the closing sections before this was
corrected — twice — and the row checker reported the file clean each time, because it counts table cells and not
section order. `check_page_shape.py` exists for that gap: it prints the heading sequence, flags duplicates and
empty sections, and flags anything stranded after closing material.

## Trap 0 — a hand-typed number and a measured number look identical (why tables are pasted)

Before the settings traps: the one that produces wrong numbers out of correct measurements.

I transcribed `depth 8 → 20/26` into a finding when the committed sweep had printed **`26/26`** — a figure carried
across from an adjacent row while writing by hand. The measurement was right; the sentence was wrong; nothing about
"20/26" looks more suspicious than "26/26".

> **A plausible wrong number looks exactly like a right one.**

So: **tables in a report are the pasted output of a committed script, never retyped.** A transcription error is
invisible to every plausibility check the author applies, because the wrong number reads as naturally as the right
one — and only the script knows which it is.

## Trap 1 — `MultiPV` above 1 divides a node budget (S-C21)

The M lines are produced from the same N nodes, so a fixed budget buys fewer plies:

| budget | MultiPV 1 | MultiPV 4 | MultiPV 8 |
|---|---|---|---|
| `go nodes 20000` | depth 10 | depth 8 | **depth 7** |
| `go nodes 50000` | depth 12 | depth 10 | **depth 8** |
| `go softnodes 2000` | depth 8 | depth 3 | **depth 2** |

The loss is **sublinear** in M (the budget is spent line-by-line per depth, not divided), and the deepest depth
often carries a **truncated line set** — 5 of 9 MultiPV>1 cells in my run reported fewer lines than the setting.

**Why it bites:** MultiPV above 1 is a plausible leftover from an analysis session. A benchmark run afterwards
measures a smaller search and reports it as the engine being shallower.

## Trap 2 — `movestogo 0` means the opposite of "unset" (S-F62)

`clock_plan.hpp:37` branches on `moves_to_go > 0`, so **zero or negative selects the sudden-death branch**: at a
2000 ms clock, `movestogo 0` = **482 ms**, `movestogo -1` = **487 ms**, and **no token at all = 57 ms** — **8.4x**
the plan of omitting it. Above 50 it is silently clamped to 50 (medians 25.9 / 25.5 / 26.4 / 25.8 ms for
50 / 51 / 100 / 1000 — a 3.5 % spread).

## Trap 3 — `depth 0` is one ply, not "no limit" (S-C28, S-F87)

`go depth 0` **clamps to one ply** — measured **depth 1, 155 nodes** — while **omitting the field reaches depth 21**
(1,493,714 nodes) in the same wall time. A **21-fold depth loss** from the value a harness is most likely to send
when it means "unset". The other limits behave consistently: `go movetime 0` still reached **depth 6** (993 nodes,
1.3 ms — a floor, not zero time), and only `go nodes 0` is honoured literally, answering at once with a different
move (`f5f4` against the control's `b6b5`).

## Trap 4 — `Threads` above 1 varies by design (already in the brief)

Score, node count and sometimes the move change run to run, because the threads share one hash table. One thread
per game; state it and record it.

## Trap 5 — caller wall is only sound if the timer starts after the preamble (S-C32, S-F92)

Not a setting this time, but the same species: a measurement that quietly includes the apparatus.

Seat 27's clock findings were retracted after it found **1,300 ms of harness** (Python startup, subprocess spawn,
UCI preamble) charged to the clock on a search the engine reports as `time 0`. Its own `time` field showed
329/328/322 ms against a 433 ms hard limit — inside the plan all along.

**The rule is about WHERE the timer starts, not whether the caller times at all:**

> **Time from immediately before `go` on a warmed process, and verify with a `time 0` search that the residual is
> a few milliseconds.**

| harness | residual on a `time 0` search |
|---|---|
| mine (timer immediately before `go`, preamble already read to `readyok`) | **0.89 ms** |
| seat 27's (startup + spawn + preamble charged) | **1,300 ms** |

Cross-check against the engine's own `time` field: `go wtime 6000 …` caller 288.71 vs engine **288** (gap
**0.71 ms**); `movetime 500` 490.65 vs 473; `nodes 20000` 11.33 vs 6. So a sound caller measurement and the
engine's own field agree to tens of milliseconds, and the zero-time control proves it in one search.

A rule phrased as "never use caller-measured wall" would forbid a method that is demonstrably fine; the control is
what distinguishes the two cases.

## Trap 6 — a fixed-depth command needs a wall cap AND a node cap, because safety is a property of the POSITION

`go depth 20` untimed finished in **0.0 s** on my mate boards and **did not finish in 90 s** on a K+Q board at
halfmove 80, where it reached **depth 15 at 250,077,687 nodes** (seat 10's 10-F65, confirmed as S-C34).

**The mechanism: a short forced mate breaks the iterative loop early** — the loop exits as soon as a mate is found,
so the search never grinds to the requested depth. **A high-halfmove bare-queen endgame has no short mate and both a
long mate search and the fifty-move horizon active**, so it grinds through hundreds of millions of nodes to
complete one depth.

So the same command is safe on one board and a grind on another, and **the trigger is the board, not the call**:

> **Any `go depth N` in a harness gets a wall cap and a node cap. Whether it is safe is a property of the position.**

A harness without a cap cannot tell "slow" from "hung", which is exactly how this reads when it happens.

## Trap 7 — a play-out is ground truth only for the player that plays it

A play-out is a better test than reading a score: it plays the game out and lets an independent library adjudicate,
so a wrong score cannot hide the consequence. **But it does not remove the engine from the PLAY** — both sides are
moved by the same depth-limited searcher, so the same first move can produce a 40-ply defence at depth 10 and a
16-ply one at depth 12.

Measured on one board with two candidate first moves (`c6d6` / `c6c7` plies survived, 3 deterministic runs each):

| play-out setting | plies survived | reading |
|---|---|---|
| depth 8 | **26 / 26** | equal |
| depth 10 | **24 / 40** | second move better by 16 |
| **depth 12** | **20 / 16** | **second move worse by 4** |
| depth 14 | **22 / 32** | second move better by 10 |
| nodes 5k / 20k / 50k | 20 / 22 | second move better |

**One setting supports the claim, one ties, three reverse it.**

> **A play-out measures "self-play survival at depth D", not objective move quality. State D, and show the ordering
> is stable across a range — or do not call it ground truth.**

**Truth, like safety, is a property of the configuration.**

## Trap 8 — a test that cannot fire returns the same answer as a test that found nothing

The subtlest one, and the only one in this page that is about the HARNESS rather than the engine.

I tested whether the built-in book answers `position startpos` using `go depth 12`. It reported **0 of 3** — a
clean negative. But the book is probed only when `game_search` holds, i.e. for **clock or movetime** searches
(`uci.cpp:681`); a depth search **can never** produce a book answer. The instrument was structurally incapable of
firing, and its empty result read exactly like a measurement that found nothing. Re-run with a clock search: **3
of 3**.

> **Before trusting a negative, show that the test CAN return a positive.** A test that cannot fire and a test that
> found nothing report identically.

The cheapest form of that proof is the same one used for the sanitizer zero and the mirror check: **plant the
positive**. Here it was a `go wtime` search; elsewhere it is a fake engine, a planted fault, or a second position.

## Trap 9 — writing a file through the shell can silently delete its content

> **Quoted heredocs (`<<'EOF'`) are safe, because nothing is expanded. Double-quoted command strings are not:**
> backticks, `$` and quotes are all live inside them, so text you meant to write gets executed instead.

**The evidence is the casualty count, and it is checkable in git history** rather than recalled:

| file | written with | commits naming a repair of IT | the command that proves it |
|---|---|---|---|
| `FINDINGS.md` | **quoted heredoc** | **0** | `git log --format="%s" \| grep -i "repair.*FINDINGS"` → **no output** |
| `STATUS.md` | shell `echo`, double-quoted | **2** | `git log --oneline --grep="damaged"` → `b833d1c09` and `ef553762e`, whose subjects both say *"repair the damaged STATUS block"* |

A note on why the count is per-COMMIT-SUBJECT and not per-file: the trap-8 repair commit touched four files at
once, so `git log -- <path>` cannot separate "this file was damaged" from "this file was in the same commit". **The
provable unit is which file the commit message names** — and no commit message names `FINDINGS.md` as repaired.

That is a mechanism, not a coincidence, and it held all session: **`git log --grep="backtick"` returns the STATUS
repairs; it returns nothing for `FINDINGS.md`, because the file written by heredoc never lost a character.**

What the damage looks like — the command **reports success** while the text has holes:

```
--: line 5: position: command not found
--: line 5: OwnBook: command not found
```

and the block that landed has blanks where the backticked words should be (`position startpos` became nothing).

> **Write documents with a tool that does not interpret them, and verify by reading the block back — never by
> trusting the exit code.**

Same shape as Trap 8: **a step that fails silently reports success.**

## Trap 10 — a profiler's output is a measurement: read the sample count first (S-F111)

> **A profile with 22 samples prints the same table shape as a profile with 43,000, and both say they succeeded.**

`gprofng collect app -p high` on this VM returned exit 0 and a full functions table sorted by percentage. The
experiment overview said `Duration : 2.208 Seconds` and `Total CPU Time : 0.022 Seconds`. The engine had run 2.15 s
of search and produced 3,652,372 nodes; the profiler had attributed **0.022 s** of it. It had sampled the **bash
wrapper**, not the engine child, and `-F on` did not change that.

Twenty-two samples over 70 symbols is not a distribution. Two runs of it disagreed with each other in ways that look
like findings and are not: one put `is_legal_complete` at 19.05 % and `generate_evasions` at 14.29 %; the other put
`fill_pseudo_legal` at 18.18 % and `apply_changes_pair` at 9.09 %. **Both would have been reported as "the profile
says".**

The check that catches it is one line: **the sample count, before any percentage.**

```
perf report -i <data> --stdio | grep -E "^# Samples"
```

43,000 samples at 3,999 Hz across five runs gave shares stable to a few tenths, and five `bench 13` timings of
2,168 / 2,166 / 2,161 / 2,163 / 2,161 ms agreed — that pair of facts is what makes a profile quotable. Percentages
alone are not.

Two traps inside this one, both of which cost me time here:

1. **`perf` is a wrapper stub here.** `/usr/bin/perf` prints `WARNING: perf not found for kernel 6.12.113+` and exits
   2, because the installed tools are for 6.8.0. The real binary is
   `/usr/lib/linux-tools/6.8.0-149-generic/perf` (version 6.8.12) and it works fine. Note the path: the symlinks
   under `/usr/lib/linux-tools/6.8.0-149/` are **dangling**, so that "obvious" path does not exist.
2. **`perf_event_paranoid` was 2**, which blocks userspace sampling. It is now `-1` on this VM
   (`sudo sysctl -w kernel.perf_event_paranoid=-1`). Without that, a sampler can run and produce nothing, or
   produce a wrapper-only profile exactly like the one above.

**And the substitute evidence is not available either**: `perf stat` on this VM reports `<not supported>` for
`cycles`, `instructions`, `L1-dcache-loads/misses`, `LLC-loads/misses` and `cache-misses`. Only `task-clock` works.
So a claim about *why* a function is expensive — cache misses, instruction count — cannot be made here at all, and
the honest move is to say so rather than to argue from footprint arithmetic. A 6.00 MiB weight matrix *should* miss
L2; "should" is not a counter.

**The rule, stated so it transfers: a tool that measures must be asked what it measured.** Profilers, like
benchmarks, return a success status and a plausible table whether or not they looked at the thing you named.

## Trap 11 — the count is a property of the READER, not the engine (S-F121)

> **Sending `quit` in the same breath as `go` closes the pipe while the search is still running, and every info line
> and the bestmove are lost. The engine behaves identically; the output does not exist for you.**

I measured the same quantity three times in one hour and got three answers:

| how I read it | answer | why |
|---|---|---|
| `printf "…go nodes 100…quit" \| forge` | **1 line** | pipe closed under the search |
| S-C18's own script (waits for `bestmove`, then quits) | **64 lines** | correct |
| a protocol that waits for `bestmove`, on the clock command too | **64 lines for all four commands** | correct |

The engine was doing the same thing every time: on a terminal root it emits 64 `info depth` lines, depths 1→64,
at 0 nodes. **My first form could not see them, and it looked self-consistent** — it said "1 line" for every one of
five commands, and that agreement felt like evidence. It was evidence of a broken reader.

`grep -c '^info depth'` on the piped form returns **0**. The same defect silently emptied a whole ABBA run later that
hour: 8 of 8 positions returned `None`, and the script went on to print a comparison table with no data in it.

Why this is its own trap and not just Trap 5: Trap 5 is about a timer that includes work it should not. This is
about output that **never arrives**, so the failure mode is not a wrong number — it is a **plausible small number**,
or a clean zero, or a table of MISSING rows that a writer may report as "no result". The count looks like a property
of the engine and is a property of the reader.

**The rule: wait for `bestmove` before `quit`, and treat any harness that writes `go` and `quit` together as broken.**
Two corollaries:

1. **A zero is a claim.** Before reporting "no info lines", "no output" or "0 of N", check that the reader could see
   output at all — the same discipline Trap 8 asks for on tests, applied to the pipe.
2. **Do not let a script print a verdict it cannot support.** Mine emitted a comparison block over empty data; it now
   refuses and says *"NOTHING WAS MEASURED … none is claimed"*. If a result is absent, the honest output says so in
   the same words as a failure, never in the shape of a result.

**A trap that is adjacent but separate, and gets its own page:** the reader can be perfect and the *divisor* still
wrong. `go nodes N` never spends N, so a per-node figure must divide by the count the engine reports, not the count
you asked for — and because the same request cancels on both sides of a comparison, the mistake silently converts a
per-node ratio into a raw **time** ratio under a per-node label. See `NODE_COUNT_NORMALISATION_RULE.md` (S-F123,
S-F125). Trap 11 is "you did not receive the output"; that page is "you received it and divided by the wrong number".


## Trap 12 — a check that examined nothing passes (S-F139)

> **Every check must print how many rows it examined, and a count of zero must be impossible.**

My pooled-spread check passed its first run with the message *"every pooled ratio examined is accompanied by a spread
marker"*. It had examined **zero** lines: the regex matched the literal word `pooled`, and my result files never use
that word — they say `median node ratio 0.926`. **Nothing was wrong with the logic of the check. It never ran.**

This is Trap 8 (a test that cannot fire) reaching the verification layer, and it is the cheapest instance of it,
because the evidence is one integer printed beside the verdict. `pooled-ratio lines examined: 3` would have shown the
problem on the first run; it took one widening to expose it, and only because the count was added at the same time.

**The rule: a check's output begins with a count, and a count of zero is a FAILURE, not a pass.** A checker whose
selector matches nothing is indistinguishable from a checker whose subject is clean, and the second is the one people
assume.

| count | means |
|---|---|
| 0 | the selector is wrong, or the subject is absent — **fail loudly** |
| >0 | the check actually looked at something |
| >0 and 0 problems | a real clean result |

This is why `gate.sh` also self-tests its checkers with synthetic bad input: a count proves the selector matched, and a
fabricated failing case proves the comparison works. **Both are needed** — a selector that matches the wrong thing
gives a non-zero count and a meaningless verdict.

## Trap 13 — the mechanism was never the problem; the selector was (S-F139, S-F142)

> **For every check, name the file types, directories and row shapes it does NOT scan, and say which of those could
> contain the subject. A check with a stated exclusion list is auditable; one with an implicit exclusion list is not.**

Five checks I built tonight failed, and **not one of them failed in its logic**:

| check | what it did | why it missed |
|---|---|---|
| findings table | verified row shape | always exited 0 → the gate read a pass |
| gate self-test | verified the checker rejects bad input | a RETURN trap's status overwrote every assertion |
| escape scan | found stranded escapes | globbed `*.md` only — the evidence files are `.txt` |
| depth claims | verified node counts | membership at a depth, not pairing within a row |
| pooled spread | required a spread | its regex matched a word my files never use → **0 rows examined** |

**Every mechanism was correct. Every scope was too narrow.** That reorders where the effort goes: the time to spend on a
new check is on its **selector**, not its comparison — and the cheapest test of a selector is to ask **what it does not
cover**, not whether it works on the case in front of you.

The three questions, asked once per check, cost about a minute:

1. **File types** — does the glob cover every format the subject appears in? (`.md` and `.txt` are different worlds;
   my evidence lives in `.txt` and my prose in `.md`.)
2. **Directories** — does it reach every folder, including the ones added after the check was written?
3. **Row shapes** — does the pattern match the way the subject is actually written, or the way I imagine it is?

**And name the exclusions.** "This check does not scan `.json` because node counts only appear in `.txt` summaries" is
auditable — a reader can see whether the exclusion is safe. An unstated exclusion is indistinguishable from an
oversight, and mine were all oversights.

## The shape the harness traps share

Trap 0 (typing), Trap 8 (tests that cannot fire), Trap 9 (shell writing), Trap 10 (a profile that never looked at
the program) and Trap 11 (a reader that never received the output) are not five separate lessons; they are one:

> **A check is a claim, and claims get tested.** A step that fails silently reports success.

Each of them, in my own session, produced a confident output that was wrong:

| trap | the confident output | what was actually true |
|---|---|---|
| 0 — typing | a number in a finding | the sweep had printed a different one |
| 8 — cannot-fire test | a clean "0 of 3" | the test was incapable of a positive |
| 9 — shell writing | an exit code of 0 | the block had holes in it |
| 10 — profiler | a table sorted by percentage | 22 samples, of the shell wrapper |
| 11 — reader | "1 line" for all five commands | 64 lines, swallowed by the pipe |

And the same shape recurred in my **checks of my own checks**: a table checker that compared pipes against cells, a
zero-node flag that scored 220-node cells "healthy", and an evidence command that returned three commits while
claiming none. **Three times a check of mine turned out to be the thing that was wrong** — and a fourth when the gate
turned out to be unable to fail its caller at all (S-F122).

The fourth instance is Trap 10, and it is the purest: the tool did not merely fail to check the right thing, it
**checked a different program entirely** and reported the result under my program's name. Its 22 samples disagreed
with each other run to run, and each disagreement looked like a finding about the engine.

The only defence that worked, every time, was **running the thing and reading the output** — not reasoning about
what it should do.

## The family of four settings, and why one rule covers all of them

**To mean no limit, omit the token.**

| what a harness sends to mean "unset" | what it actually does |
|---|---|
| `movestogo 0` | selects the **sudden-death** branch: 482 ms per move instead of 57 ms — 8.4x the plan of omitting the token |
| `depth 0` | clamps to **one ply**: depth 1 in 155 nodes, against depth 21 when the field is absent — a 21-fold loss |
| `MultiPV` above 1 | **divides the node budget** across the lines: depth 10 → 7 at 20,000 nodes, depth 8 → 2 on `softnodes 2000` |
| `Threads` above 1 | **varies by design**: score, node count and sometimes the move differ run to run |

All four are settings whose **name** suggests they do not matter to the measurement, and each changes the search
in the direction opposite to the intent. That is why the rule is uniform: **never send a value meaning "unset";
omit the field.**



## The guard

1. **Assert them explicitly** at the top of every harness: `Threads 1`, `MultiPV 1`, omit `movestogo`/`depth`
   rather than sending 0.
2. **Record them in the output**, not just in the script — a result file that does not state Threads and MultiPV
   cannot be compared with one that does.
3. When a number looks wrong, **check the settings and the timer before the engine**: four of these five were a
   setting and the fifth was the measurement itself — none was a search defect.
4. **Know what the automated checks cannot see.** `gate.sh` verifies shape, arithmetic and stamp plausibility. It does
   **not** verify that a figure renders as intended: it passed while two of my finding rows carried a literal
   double-percent escape (two `%` characters in a row) where no format string existed, and displayed as
   "11–17" followed by both of them. A check verifies relationships, not typography, and its silence is not coverage —
   `NODE_COUNT_NORMALISATION_RULE.md` states that boundary in full.

This is the same family as the attribution rule: the failure is never in the number, and it is never announced.
