# REPORT — seat 12, area 2, job 3/4: every option at its extremes, and `setoption` during a search

(Numbered `job4` in my folder because `job3` holds the PC r15 build record. This is the brief's
area 2 job 3.)

## What was asked

Every option the engine lists in its `uci` answer, set to its min, max, min-1, max+1, a word, and
nothing, both **between searches** and **during a search**. Table per option: the answer line, a
crash, and whether the next search is legal.

## The answer

**No crash, no sanitizer line, no illegal bestmove, no lost `readyok` in 3,111 cases** across three
build/regime combinations, and **every out-of-range or non-numeric value is refused with a line**
— nothing is accepted silently. The substantive find is behavioural, not a fault: **`setoption`
sent while a search is running silently stops that search** (4/4 option types), exactly as `stop`
does, on both builds; `isready` correctly does not.

## How sure

High on the counts and on the `setoption` behaviour: the controls behave as required (`isready`
does not stop a search, `stop` does), and a three-part planted check proves the harness detects an
unknown option, an invalid value, and an illegal bestmove. Moderate only in this sense: the
Threads column of the brief (1,000 repeats) is not what I ran — see "what I did NOT do".

## Honesty numbers

All builds below are the ones already pinned in this folder:

| build | pins | note |
|---|---|---|
| base release (6b98f217) | 312866 / 862329 / 3024920 / 4865609 | `job0/HONESTY.txt` |
| PC r15 release | none 312866/862329/3024920/4865609; S14 242796/656517; PC20 278024/587276 | `job3/PC_BUILD.md`, all 8 matched |

**Threads 1 in every case below**, with one stated exception: `Threads` is itself exercised as an
option (that is the job), and the harness sets it back to 1 afterwards.

## Table — the three runs

| build | settings | options listed | cases | legal bestmoves | cases that fired anything |
|---|---|---|---|---|---|
| base release | none | 82 | 957 | 975/975 bestmoves legal | **0** |
| PC r15 | none | 92 | 1,077 | 1,077/1,077 | **0** |
| PC r15 | PC20 | 92 | 1,077 | 1,077/1,077 | **0** |

Raw: `job4/runs/base.jsonl`, `job4/runs/pc.jsonl`, `job4/runs/pc20.jsonl`, with a `.meta` beside
each (exe, sha256, settings, case count) and a `.summary.json`.

## The refusal behaviour, which is the real content of this job

Of 957 base cases, **628 produced a refusal line from the engine**; of 1,077 PC cases, **708**.
Every one was the engine's own `info string invalid value for option X` or
`info string unknown option X`. **No spin option accepted the word `word`,** no spin accepted
`min-1` or `max+1`, no check option accepted `maybe`, and no option accepted a missing value —
each case answered with a line and left the engine usable (the very next `go depth 6` returned a
legal bestmove).

Worked example, `Hash` and `Threads` on PC r15 (pasted from the raw):

```
Hash     value=1     bm=e2a6 legal=True ready=True  (accepted)
Hash     value=2048  bm=e2a6 legal=True ready=True  (accepted)
Hash     value=0     bm=e2a6 legal=True ready=True  info string invalid value for option Hash
Hash     value=2049  bm=e2a6 legal=True ready=True  info string invalid value for option Hash
Hash     value=word  bm=e2a6 legal=True ready=True  info string invalid value for option Hash
Hash     value=None  bm=e2a6 legal=True ready=True  info string invalid value for option Hash
Threads  value=1     accepted     Threads value=0/257/word/None  refused, same shape
```

The refusal line is identical whether the option was set between searches or during one, and the
engine stays usable in both cases.

## The control that makes the zero mean something

`option_control.py`, on both builds, three plants, **3/3 detected on each**:

| plant | what it proves | base | PC r15 |
|---|---|---|---|
| `setoption name NoSuchOptionHere value 1` | the harness's "unknown option" regex matches what the engine really prints | 1 line: `info string unknown option NoSuchOptionHere` | same |
| `setoption name Hash value 0` | the "invalid value" regex matches | 1 line: `info string invalid value for option Hash` | same |
| a fake engine that answers `bestmove e2e5` to every `go` | the legality check catches a genuinely illegal move | `e2e5` → illegal in position: True | same |

So "0 cases fired" is a measured zero: the same checking code catches a bad option, a bad value,
and a bad move.

## Finding: `setoption` during a search stops the search

Measured with a control pair (`isready` must not stop; `stop` must), 1.5 s observation window,
nothing sent while watching, 50 ms into a `go infinite`:

| command sent mid-search | base | PC r15 | verdict |
|---|---|---|---|
| `isready` | no bestmove | no bestmove | **correct**: does not stop |
| `stop` | `bestmove e2a6` in 0.001 s | same | **correct**: does stop |
| `setoption name Hash value 64` | `bestmove e2a6` | same | **stops the search** |
| `setoption name MultiPV value 3` | `bestmove e2a6` | same | **stops the search** |
| `setoption name LmrQuietBase value 100` | `bestmove e2a6` | same | **stops the search** |
| `setoption name OwnBook value false` | `bestmove e2a6` | same | **stops the search** |
| `ucinewgame` | bestmove | bestmove | stops (expected) |
| `position …` | bestmove | bestmove | stops (expected) |
| second `go depth 4` | 2 bestmoves | 2 bestmoves | the new search answers; the old one was ended |

Source confirmation: the `setoption` branch of `src/uci.cpp` begins with `stop_search()`
(base tree line 259; the PC build keeps it). The behaviour is deliberate in the code, and both
builds share it.

**Why it matters:** UCI lets a GUI change an option while a search runs, and a GUI that sends
`setoption` mid-search will get a `bestmove` it did not ask for and will believe its search is
still going. The engine's answer is legal and prompt, so nothing breaks in the obvious way — but
the GUI's model and the engine's state diverge. For the owner's matches this is harmless (the PC
sets options once, before games). For a tuning harness that pokes knobs during a search, it means
every poke ends the search.

## Suspicions, not proven

- Whether the `stop_search()` in the `setoption` branch is required for safety (resizing the hash
  during a search would be unsafe; a plain `LmrQuietBase` change is not). It may be deliberate
  over-caution rather than an oversight. I did not read the whole branch to decide.
- The second `go` while a search is running produced **two** bestmoves; I did not verify which one
  a GUI should associate with which `go` (this is the same attributution question I hit in job 1).

## What I did NOT do

- The brief says 1,000 repeats for the race job; for THIS job it asks for every option at six
  values in two phases, which I ran exhaustively: 957 / 1,077 / 1,077 cases = every option ×
  every value × both phases, not a sample.
- No `Threads > 1` searching: only the `Threads` *option* was exercised, then reset to 1.
- No TSan run (this is the release build and an ASan build elsewhere; a data race is not what
  either detects).

## What I am NOT sure about

- Whether every one of the 92 PC options is *used* by the search; I tested that each one is
  accepted and refused correctly, not that each one changes behaviour.

## Times

`job4/stamps.txt` (`date -u` lines) and the commit times.

## Last command output

`job4/final_state.txt`: `git status --short` and `ls job4/`.
