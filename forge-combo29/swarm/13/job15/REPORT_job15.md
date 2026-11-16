# REPORT_job15 — which of the PC patch's seven fixes are actually active, and do they work?

## What was asked
Nothing specific. The PC patch (FABLE file 5) declares seven fixes. I had verified only
`FORGE_FIX_ROOT_DRAWN` (S-F17). An unverified fix is a risk in match play, so I read the patch's own
comments — not a summary of them — to find each switch's default, then tested the ones that are on.

## Finding 1: TWO OF THE SEVEN FIXES ARE COMPILED OUT BY DEFAULT

Reading the `#define` defaults in the patch itself:

| switch | default | patch's own stated reason |
|---|---|---|
| FORGE_FIX_ROOT_DRAWN | **1 (on)** | the drawn-root repair — verified as S-F17 |
| FORGE_FIX_HARD_LIMIT_EMERGENCY | **1 (on)** | hard limit already passed → play hash move or <=2,000 nodes, not an unsearched first move |
| FORGE_FIX_BARE_KING_LMR_CAP | **1 (on)** | the *gentle* lone-king rule; wins MORE of the hard endings (KBB-K 175/300 vs 142) |
| FORGE_FIX_GO_PARSE | **1 (on)** | a `go` keyword never consumed as another keyword's value; r9 let `go wtime btime 50` lose the clock |
| FORGE_FIX_ISREADY_PENDING | **1 (on)** | `isready` must answer while NNUEArch is on and no net file is named |
| **FORGE_FIX_BARE_KING_ONE_THREAD** | **0 (OFF since 16:30)** | "removes the missed mates (82 of 1,680 → 1) but at self-play depth the unpruned search wins the hard endings less often (KBB-K 14/50 vs 21, KBN-K 1/50 vs 4)" — kept as a switch until a gentler rule is found |
| **FORGE_FIX_ABORT_PUBLISH** | **0 (OFF since 16:45)** | "measured, it is **not a repair**": in 73 differing stops the replaced move scores higher 43 times, lower 30, on average 14 cp LOWER |

This matters because a reader could reasonably assume "the PC patch fixes the abort-publish problem"
or "fixes one-thread bare-king mates". **It does neither by default** — and the patch says so, with
measurements, which is the honest way to leave a switch off. My report records it so nobody builds on a
fix that is not compiled in.

The OFF choices are internally consistent: the gentle `LMR_CAP` rule (on) gets most of the missed-mate
benefit without the hard-endings regression, so it *replaces* the blunt `BARE_KING_ONE_THREAD` rule.

## Finding 2: `FORGE_FIX_GO_PARSE` — the clearest before/after in the patch, confirmed

`go wtime btime 50` (no value after `wtime`). The patch says r9 took the clock away here.

| build | info lines | final depth | nodes | bestmove |
|---|---|---|---|---|
| base 6b98f217 | **1** | 1 | **26** | `d2d4` |
| PC r15 | **5** | 5 | **1,001** | `c2c4` |

The base build stops after one depth as if it had no time at all; the PC build searches to depth 5 and
plays a different move. **Control** — `go wtime 50 btime 50` (properly formed) gives *identical* results
on both builds (5 lines, depth 5, 1,001 nodes, `c2c4`), so the fix does not disturb a well-formed clock
command. That control is what makes the comparison mean something: it shows the difference above is
about the malformed line, not about the builds searching differently in general.

## Finding 3: `FORGE_FIX_HARD_LIMIT_EMERGENCY` — the boundary is visible

| command | base | PC |
|---|---|---|
| `go wtime 11 btime 11` | 5 lines, depth 5, 1,001 nodes, `c2c4` | 5 lines, depth 5, 1,001 nodes, `c2c4` |
| `go wtime 10 btime 10` | 1 line, depth 1, **26 nodes**, `d2d4` | 1 line, depth 1, **26 nodes**, `d2d4` |

Both builds behave identically on both. The patch's story is that at 11 ms the search runs normally and
at 10 ms (== default Move Overhead) the hard limit has already passed. What I observe is consistent with
that: 11 ms searches, 10 ms answers after one depth. **I did not separate the emergency path from the
ordinary "no time left" path**, so I am reporting this as consistent-with, not as a confirmation of the
emergency branch specifically. The patch claims the fix prevents `go wtime 11` being answered *worse*
than `go wtime 10`; both my values are the same on both builds, which neither confirms nor refutes it.

## Finding 4: lone-king smoke test (not the full BARE_KING_LMR_CAP test)

`6k1/8/5K2/8/8/8/8/7R w - - 0 1`, `go depth 14`:

| build | bestmove | score | nodes |
|---|---|---|---|
| base | `h1h4` | **mate 2** | 532 |
| PC | `h1h4` | **mate 2** | 573 |

Both find the mate. The node counts differ (573 vs 532), which is expected from the changed reduction
rule, and neither loses the mate. **This is a smoke test only.** The patch's actual claim is about 13
missed mates in 400 depth-14 searches of hard lone-king endings with warm history; reproducing that needs
a lone-king position set, warm tables and a 400-position sweep, which I have not run. I state it as
untested rather than implying the cap works.

## Two things I could NOT test, and say so
- **`FORGE_FIX_ISREADY_PENDING`** needs `NNUEArch`, which this build does not advertise, so the state the
  fix guards cannot be entered here.
- **`FORGE_FIX_BARE_KING_LMR_CAP`** in full — see finding 4.

## My own test bug, recorded because it looked like an engine fault
My first K+R vs K position was `7k/8/6K1/8/8/8/8/7R w - - 0 1`. python-chess reports
`STATUS_OPPOSITE_CHECK` — black is in check with **white** to move — so the FEN is illegal. The engine
**refused it and kept the previous position (startpos)**, then answered `e2e4` from startpos. That looked
exactly like "the engine played an illegal move in a K+R vs K ending", and it was entirely my FEN's fault.

This is a **sixth** member of the absence-of-output family, and a nasty one: the engine's refusal message
was there in the output, but the *board it searched* silently stayed the old one — the same
"refused FEN keeps the previous position" behaviour the swarm has documented since file 1. Anyone
comparing two builds must assert that the position was actually accepted before comparing their answers,
or they will compare two searches of startpos. A guard for this is now in the script: the replacement FEN
is verified with python-chess (`is_valid()` and no `STATUS_OPPOSITE_CHECK`) before use.

## Builds and settings
Base `forge-combo29` 6b98f217 release g++ 13.3.0 x86-64-v4; PC = that tree + `pc_r15.patch`
(sha256 prefix `d6bd72c531f785f4`, already verified against file 5), built with
`-DFORGE_MATE_ALPHA_GUARD=1`. Threads 1, Hash 16, OwnBook false, fresh process per case, every option
name checked against the exe's `uci` list.

## Findings
- S-F18: **two of the PC patch's seven fixes are compiled out by default** (`FORGE_FIX_BARE_KING_ONE_THREAD`
  and `FORGE_FIX_ABORT_PUBLISH`, both `#define ... 0`), each with the patch's own measured reason; the
  gentle `FORGE_FIX_BARE_KING_LMR_CAP` replaces the former. Verified `FORGE_FIX_GO_PARSE` works:
  `go wtime btime 50` gives base 1 info line / 26 nodes / depth 1 versus PC 5 lines / 1,001 nodes /
  depth 5, while the well-formed `go wtime 50 btime 50` is identical on both builds.
  `FORGE_FIX_HARD_LIMIT_EMERGENCY` observed consistent-but-not-isolated; `ISREADY_PENDING` and the full
  `BARE_KING_LMR_CAP` claim are untested here and stated as such.
  Reproduce: `cd forge-combo29/swarm/13/job15 && python3 pcfixes.py ~/b/rel/forge ~/b/pc/forge /tmp/pf`.

## Suspicions, not proven
- The three-node-count difference in the lone-king smoke test (573 vs 532) is consistent with a changed
  reduction rule but I have not traced it; it could equally be a hash-state difference.

## What I did NOT do
- Did not test the two OFF switches by rebuilding with them ON (that would answer "does the patch's
  code work", not "does the PC build have it", and the PC build does not have them).
- Did not run the 400-position missed-mate sweep for `BARE_KING_LMR_CAP`.
- Did not test `ISREADY_PENDING` (needs NNUEArch).

## Files
`pcfixes.py`, `out2/pcfixes.json` (all rows plus an explicit `untestable` map), `stamps.txt`. `out/` holds
the run with my invalid KRK FEN, kept because the `e2e4` it produced is a good example of the
refused-FEN trap.

## Last command output

```
$ ls
out
out2
pcfixes.py
REPORT_job15.md
stamps.txt
```
