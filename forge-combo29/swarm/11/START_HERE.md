# SEAT 11 — where to start (area 1, FEN input)

This folder holds one area's worth of work: **15 documents, 116 scripts, 122 raw evidence files, 122
findings.** Everything here is text; no binaries, no engine source. Read in this order.

## If you read only one thing
**`HAZARD_stale_board.md`** — a rejected `position` command leaves the engine on the **previous board**
while still answering `readyok`, so the next search returns a legal, plausible move for the wrong
position. Two routes (malformed FEN; illegal move in a move list), the real-game demonstration, the
one-move blast radius, and the one-sentence defence. This is the only thing I found that can silently
cost the owner a game.

## If you are about to run a match or a training loop
1. **`HAZARD_match_protocol.md`** — fixed `go nodes N` is **not** depth-equal between builds (paired
   depth agreed on 0 of 10 openings at 250k), so compare builds at fixed **depth** or on the clock;
   always send **both** `wtime` and `btime` (136 ms vs 12 s); the engine relies on **your** program to
   end games at the third repetition and the 100th half-move.
2. **`uci_guard.py`** — a small wrapper that enforces all of the above: a refused `position` raises
   `PositionRejected` and resyncs with `ucinewgame` + startpos, a one-sided clock raises rather than
   searching for twelve seconds, and its read deadline means a hung engine cannot hang you.
   Verified on both builds, both routes, against a planted hang (caught at exactly 3.0 s), and across
   40 games with faults injected every fifth game. Costs **1.8 ms** per recovery, **6 ms** worst case.

## If you are writing a probe or a measurement
**`PROBES_THAT_LIED.md`** — nine traps, each with what I saw, what was actually true, the tell I should
have read first, the fix, and which control killed it. Every one of them looked like an engine defect
and was the harness. Two are worth the whole document:
- **Trap 6** — a switch's effect can live in a narrow band; four sampled points (11, 12, 15, 30 ms) all
  missed a 5-in-50 window.
- **Trap 8** — a node count under a clock stop is not deterministic, on either build. Never quote one
  as a result.

Also: **`clock_repeat_check.py`** — run it before quoting any timing figure. It repeats the same binary
against itself, reports whether the move and the metric are stable, and exits non-zero if not.

## Reference
- **`PC_SWITCHES.md`** — the six `FORGE_FIX_*` switches: compiled state in the binary the owner plays,
  measured effect, how measured, and what is still unmeasured. Two are compiled OFF
  (`BARE_KING_ONE_THREAD`, `ABORT_PUBLISH`) so "r15 has all six fixes" is not true.
- **`PCR15_BUILD.md`** — how the PC build was reproduced from `FABLE_TO_swarm_5` (patch sha256 starts
  `d6bd72c531f785f4`) and its three number regimes, all matching the PC: default pins
  312866 / 862329 / 3024920 / 4865609, S14 242796 / 656517, PC20 278024 / 587276.
- **`FINDINGS.md`** — 122 lines, every finding with its evidence path, build and settings. Claims I
  withdrew or corrected stay in it marked as such rather than deleted.
- **`STATUS.md`** — chronological log and the FINAL block.
- **`REVERDICT_file6.md`** — the six findings I withdrew as non-defects under `FABLE_TO_swarm_6`, with
  the inequality test that decided each.

## The job reports
`REPORT_job1.md`, `REPORT_job2.md`, `REPORT_job3.md`, `REPORT_job1r2.md`, `REPORT_job10_2.md` — the
area-1 jobs (20,000 mutated FENs under ASan+UBSan; extreme field values; a 1,000-ply move list; a
second seed; a recount of another helper's report). `RULE1.md` records the planted controls that make
every zero in them a shown zero.

## Raw evidence
`checks/` (122 files) holds every raw output cited above, each reproducible by the script named beside
it. Every script is runnable: `python3 <script>.py <exe> [args]`. The PC build is
`/tmp/pcbuild/forge` (PC20 settings) and the base build `/home/ubuntu/builds/rel/forge` — both are
rebuildable from `PCR15_BUILD.md` if they are gone.

## What is NOT here
Nothing above Threads 1 — every number in this folder is Threads 1, per the swarm rule, and any score
claim above one thread is out of scope by design. Memory growth was measured (flat at 26.4 MB across
120 games). The three remaining `FORGE_FIX_*` switches are resolved rather than deferred: one proven
inert via the preprocessor, two measured.
