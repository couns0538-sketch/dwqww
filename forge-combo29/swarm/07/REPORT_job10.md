# REPORT — seat 07, job 10: the GUI's normal `go`/`stop` cycle, and a bug in my own test

## What was asked / the answer / how sure

**Asked:** continue the area-7 UCI-loop read, prioritising what shows in normal play.

**Answer:** the shape a real GUI drives — `position`, `go infinite`, `stop`, `bestmove`, next
position — is **safe over 40 plies in one process**, including a `go ponder` + `ponderhit` round and
a `go depth 200` + `stop` round, with `ucinewgame` interleaved every 7 rounds and a plain
`go depth 6` afterwards that still searched properly.

**How sure:** high *after* I fixed my test. My first version of the test was **blind**: it passed a
build with the stop-flag reset deleted. I found that with a planted-fault control, fixed the test,
and the control then failed as it must. Both runs are kept.

## Honesty numbers

Base build: 312866 / 862329 / 3024920 / 4865609 (job0/raw/summary.txt). No engine source changed in
the repo; the fault build is a copy at `/tmp/stalefault`.

## The result

    rounds requested 40, plies played 40
    final search after the cycle: bestmove d2d4 nodes 1155
    RESULT: every go/stop and go/ponderhit cycle returned a legal move with nodes > 0,
            and a plain search still worked afterwards

Per round the test asserts: a `bestmove` arrives within the timeout (a hang is a failure), the move
is **legal in the position that was sent** (python-chess), a `bestmove 0000` only when the position
has no legal move, and a parsed `nodes` figure greater than zero.

Raw: job10/raw/transcript.txt (every line the engine sent, with `>>` for commands sent).

## The bug in my own test, and the control that found it

The engine's stop handling is this chain in `uci.cpp`:

    uci.cpp:169  auto stop_search = [&]() { ... searcher.stop(); ... worker.join();
                                              ponder_search_active = false; };
    uci.cpp:551  searcher.reset_stop();      // before every search
    uci.cpp:637  } else if (command == "stop") { stop_search(); }

**Planted fault:** delete `searcher.reset_stop();` from a copy of the tree, rebuild
(`/tmp/stalefault`, built with the same CMake recipe and flags). A stale stop flag should then make
every search after the first answer instantly.

**My test did not catch it.** The control run printed:

    rounds requested 12, plies played 12
    final search after the cycle: bestmove a2a3 nodes None
    RESULT: every go/stop and go/ponderhit cycle returned a legal move with nodes > 0 ...

The tell was `nodes None` — no `info depth ... nodes` line was parsed at all — and my assertions
treated "no nodes figure" as "not zero", i.e. as a pass. That is exactly the failure mode seat 19
warned about: a missing measurement passing as a good result.

**Fix:** a missing nodes line is now itself a failure. Re-running the control:

    FAIL round 1: no 'info depth ... nodes' line was parsed, so the round measured nothing (bestmove a2a3)
    FAIL final go depth 6 produced no nodes line: the engine never searched
    RESULT: 2 failure(s)

Only then did I re-run the real build, which passed. The committed script is the fixed one; the
control output is kept in job10/raw_control/ so the correction is visible.

## Why this matters for the engine

`stop` / `ponderhit` / `quit` while a search runs is the most frequent UCI interaction a GUI makes.
A stale stop flag there would show as an engine that answers `bestmove` instantly with a first-legal
move — a strength bug that no bench or perft would reveal. Over 40 real cycles, plus the two special
branches, it does not happen.

## Findings

**07-C5** in FINDINGS.md records the clean result **and** the harness bug, because the second half is
what makes the first half trustworthy.

## Suspicions, not proven

- Round 1 of the control returned `a2a3` with no nodes line; the clean build returns a real search
  on round 1 as well, so the difference is confined to the reset path. I did not trace it further
  than the control shows.
- Seat 10's warning (two searches in one process give 56,720 then 4,951 then 4,516 nodes) is a
  *node-count* effect, not a stop-flag effect, and my cycle test does not contradict it: it only
  asserts nodes > 0, not a specific count.

## What I did NOT do

- Did not test `stop` arriving *before* `go` (a malformed GUI) — that is job1 edge-case territory.
- Did not test `quit` during an infinite search beyond the single `ponder_quit` case in job1.

## Times

See job10/stamps.txt.
