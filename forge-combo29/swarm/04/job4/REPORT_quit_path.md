# The quit/EOF fabricated bestmove, on the PC build and the PC's real path

## THE HEADLINE: quit at 0 ms fabricates, quit at 1 ms does not

Measured on PC r15 under PC20, Threads 1 — the delay between writing `go depth 20` and writing `quit`:

| quit written after | bestmove | info lines | what happened |
|---|---|---|---|
| **0 ms** | `d5d4` | **0** | **fabricated — the engine never started searching** |
| **1 ms** | `g7g6` | 5 | a real search |
| 5 ms | `g7g6` | 8 | a real search |
| 20 ms | `g7g6` | 12 | a real search |
| 200 ms | `g7g6` | 18 | a real search |

One millisecond is the whole boundary. That reframes the fault: **it is not "the input was batched", it is
"the engine never started"**. A batch containing `go` and `quit` fabricates not because batching is special
but because it gives the search no chance to begin; and two separate writes with no sleep between them
fabricate just as reliably (5/5 each way). Give it one millisecond and it searches properly.

**The consequence for the owner: he is not exposed.** Any match program that sends `go`, lets the engine
work, and then closes or quits — which is every real match program, since it must read the answer — is
outside the window. What breaks is the harness idiom `printf 'go ...\nquit\n' | engine`, where the engine is
handed its own termination before it has read its first line. So this is a **documentation item** ("do not
pipe your whole script into the engine and close it") rather than a defect in the engine's play.

The rest of this report is the evidence behind that headline, on both builds.

Seat 04, area 4. This is a CHECK of seat 19's 19-F12 (they own the finding), extended to the PC build and to
the node budgets the owner's matches actually use.

## What was asked / the answer / how sure

**Asked.** Whether the fabricated-bestmove-on-input-termination fault reproduces on PC r15 under PC20, and
whether it is reachable on the PC's real match path (`go nodes`).

**Answer.** Yes to both. PC r15/PC20 control (read to bestmove, then quit) gives `d2d4` at 21,600 nodes with
12 info lines; `quit` written immediately gives `bestmove a2a3` with **0 info lines**; closing stdin (EOF)
gives the same. On the match path, `go nodes 20000` gives `d2d4` after 11 depth lines when read normally, and
`a2a3` with 0 info lines when `quit` follows immediately. The base build under S14 behaves identically, so
this is **not** an r15 regression and none of the eight FORGE_FIX_* switches covers it.

**How sure.** High on the reproduction: every case is a fresh process, the control arm is verified to have
produced a real search (nonzero node count, nonzero info lines), and the fabrication repeated 5/5 in each of
two different write patterns. On the practical risk: low, because of the one-millisecond boundary in the
headline — a real match program never gets inside it.

## The window, in the original form (kept here as raw evidence)

Measured by delaying the `quit` after `go depth 20` on the ordinary FEN, PC20, Threads 1:

| quit written after | bestmove | info lines | verdict |
|---|---|---|---|
| 0 ms (no delay) | `d5d4` | **0** | FABRICATED |
| 1 ms | `g7g6` | 5 | real search |
| 5 ms | `g7g6` | 8 | real search |
| 10 ms | `g7g6` | 10 | real search |
| 20 ms | `g7g6` | 12 | real search |
| 50 ms | `g7g6` | 13 | real search |
| 200 ms | `g7g6` | 18 | real search |

And the write pattern does not matter: a single write containing `go`+`quit` fabricates 5/5, and two separate
writes with no sleep between them also fabricate 5/5.


## Why it matters anyway

Two reasons, both practical rather than theoretical:

1. **It silently poisons harnesses.** My own first attempt at a quit test, and several other seats' work,
   measured `a2a3`-with-0-nodes as if it were an engine answer. Every result from a pipelined harness is
   invalid, and the failure looks like a plausible move rather than an error.
2. **`bestmove 0000` is not what comes back.** A program that closes the engine's stdin mid-search and
   treats the last `bestmove` line as an answer will read `a2a3` (or `d5d4`, or `a2a3`) — always legal,
   always plausible, never searched. There is no marker distinguishing it from a real answer.

## The two questions seat 19 left open

- **Does a fabricated bestmove ever carry a nonzero node count?** No. Every fabricated case had **0 info
  lines**, in both builds and both settings. So there is no wrong number to be misled by — there is no number.
- **Is a fabricated bestmove ever illegal?** No. `a2a3` on startpos and `d5d4` on the middlegame FEN were
  legal in python-chess in every case. The fabricated move is a plausible move, not an illegal one, which is
  what makes it dangerous.

## Integrity gate

`job4/quit_pc20.py` exits non-zero and prints `INTEGRITY FAILURE` rather than a verdict if the control arm
lacks a bestmove or a nonzero node count. A missing number never becomes a confirmation. The same script's
earlier sibling in `job1/` had a gate that once printed PASSED while every case was missing; that bug is
fixed in `job1/check_quit.py` and is recorded in 04-C1b.

## Times

Every wall time is a `time.monotonic()` difference inside the probe, recorded per case in the raw JSONL. Run
boundaries are `date -u` lines in `job1/hang/stamps.txt` and in this branch's commit times
(`git log --format='%h %ad %s' --date=iso`).

## Commands that show all of this again

```
# the four-case check on either build
python3 forge-combo29/swarm/04/job4/quit_pc20.py /home/ubuntu/builds/pc/forge /tmp/qpc  --settings pc20 --depth 12
python3 forge-combo29/swarm/04/job4/quit_pc20.py /home/ubuntu/builds/rel/forge /tmp/qpc --settings s14  --depth 12

# the delay sweep and the write-pattern comparison are recorded verbatim in STATUS.md at
# 2026-11-16T23:06:34Z and were run as one-off python drivers in the session; the results above are
# their pasted output.
```

Raw: `job4/raw/quit_pc20_pc20.jsonl`, `job4/raw/quit_pc20_s14.jsonl`.
