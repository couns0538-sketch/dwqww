# REPORT job 4 — swarm seat 23, AREA 3 on the PC r15 build under PC20

**What was asked:** file 5's order — re-run my own finds on the PC build under PC20, and say in each finding line
which build and which settings it used.

**The answer:** the PC build's move generator is identical to the base tree's on everything I can measure. All
three of my perft/ep findings reproduce unchanged under PC20, so they transfer to the PC as they stand. One thing
does NOT transfer: the fabricated-`bestmove` defect on `quit`/EOF during a search is still present on the PC
build, so 19-F12 is not repaired there.

**How sure:** high — every number came from the same harnesses I used on the base build, with the option list
verified against the engine's own `uci` output, Threads 1, and a planted control proving the comparison catches a
one-node difference.

## Honesty numbers

| build | exe sha256 | pins (none) | S14 bench 11/13 | PC20 bench 11/13 |
|---|---|---|---|---|
| base 6b98f217 | e06310ec… | 312866/862329/3024920/4865609 | — | — |
| PC r15 | 068f0927… | 312866/862329/3024920/4865609 | 242796/656517 | 278024/587276 |

All eight file-5 numbers match; zero `unknown option` / `invalid value` / `ERROR` lines in every run
(`pc/pc_honesty.out`). The PC build was made from the patch in file 5 after verifying its sha256
(`d6bd72c531f785f4…`) — see `PCBUILD.txt`.

## The table

| step | done / partly / not done | evidence file | result |
|---|---|---|---|
| extract + verify the patch sha256 | done | `PCBUILD.txt` | `d6bd72c531f785f4…` confirmed; a truncated extraction gives `61da918e…` and loses the last line |
| apply to a separate worktree, build with `-DFORGE_MATE_ALPHA_GUARD=1` | done | `/agent/repos/pcbase`, `~/pcbuild` | 11 files, no fuzz, build EXIT=0 |
| check all eight known numbers | done | `pc/pc_honesty.out` | 8 of 8 match |
| perft 1..4 over the same 5,000 R positions on the PC build under PC20 | done | `job4/engine_pc20.jsonl` (+`.meta`), `compare_pc20.out` | 200 of 200... 5000 of 5000 compared, **0 mismatches**, totals identical to the base build |
| pinned-ep behaviour on the PC build | done | `job4/ep_pin_pc.out` | nodes 4 / 4 / 8, control 5 — same as base |
| perft repeatability on the PC build | done | `job4/perft_repeat_pc.out` | 197281/197281, 4865609/4865609, 750862/750862, A-B-A identical |
| planted control for the perft zero | done | `job4/planted_mismatch.out` | +1 node caught (218150726 vs 218150727); deleted key exits 2 |
| abort behaviour: base vs PC, quit / stop / EOF | done | `job4/abort_publish_pc.out` | `stop` fine on both; `quit` and EOF fabricate `a2a3` on BOTH |

## Findings

- **23-F9** (PC r15, PC20, Threads 1, Hash 16) — identical move generator: 0 mismatches over 5,000 positions at
  depths 1..4, totals equal to base; ep behaviour equal; perft repeatable.
- **23-F8** (both builds) — the PC build still answers `bestmove a2a3` with 0 info lines on `quit`/EOF during a
  search; FORGE_FIX_ABORT_PUBLISH fixes only the `stop` path.
- **23-F10** (harness) — the planted control that makes my perft zeros countable under Rule 1.

Each finding line in `FINDINGS.md` names its build and settings.

## My prediction, scored

| # | prediction | outcome |
|---|---|---|
| P1 | 0 mismatches on the PC build | **HELD** |
| P2 | PC totals equal base totals exactly | **HELD** (all four depths) |
| P3 | ep-pin behaviour identical | **HELD** |
| P4 | perft repeatable twice in one process | **HELD** |
| P5 | the planted mismatch is caught | **HELD** (control satisfied) |
| P6 | run under 3 minutes | **HELD** (25.2 s) |

## Suspicions, not proven

- Why `quit`/EOF still fabricates a move while `stop` does not: I did not read the abort code path on the patched
  tree. The behaviour is measured, the cause is not. Reading `FORGE_FIX_ABORT_PUBLISH`'s actual change would be
  the next step and would show whether the fix simply does not cover process exit.
- The patch's `board.cpp` changes (king lines, lone king) could alter some position's move list, but nothing in
  5,000 random-game positions or the hand-built ep positions exposed a difference. That is evidence of no
  difference, not proof.

## What I did NOT do

- No search-score work under PC20 — the swarm rule and file 5 both say the PC's trained net is not shared, so
  evaluation-dependent results are questions for the PC. Area 3 is move generation, which is net-independent.
- No Threads > 1 anywhere (the new rule: every score at Threads 1 unless the job is about threading; perft does
  not thread and no harness of mine ever sends a Threads option).

## What I am NOT sure about

- Whether the PC's own exe behaves exactly like my build of the same source on its own hardware. The source is
  the PC's, the compiler and machine are mine.

## Times

`job4/stamps.txt`, `job4/*.log`.

## Last command's output

`job4/final_status.txt`.
