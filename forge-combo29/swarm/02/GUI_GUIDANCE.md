# GUI guidance for S-F3, S-F4 and S-F5 — what the engine SHOULD do

Requested by the coordinator: one sentence per finding that a GUI author can act on, with my choice and why.
None of this is implemented; it is a recommendation grounded in the measurements in this folder.

---

## S-F3 — `ponderhit` on a search that was NOT started with `go ponder`

**One sentence: the engine is RIGHT to ignore it, and a GUI must send `stop` to end a normal search — never
`ponderhit`.**

Why, and the measurement that settles it (`job2/probe_ponderhit.py`, raw `job2/out_ponderhit/rows.json`):

| search | trigger | did it end by itself? | elapsed |
|---|---|---|---|
| `go ponder wtime 400 btime 400` | `ponderhit` | **YES** | 455 ms (budget ~390 ms) |
| `go ponder wtime 400 btime 400` | `stop` | YES (control) | 402 ms |
| `go infinite` | `ponderhit` | **NO** — needed `stop` | 1601 ms |

So `ponderhit` DOES work in the one case it exists for: after it, the engine switched from pondering to
searching on our clock and stopped itself at the clock budget (455 ms against a ~390 ms budget). That is
correct UCI: `ponderhit` means "the opponent played the move you were pondering, now search on MY time", and
it only has meaning while a ponder search is running. On a normal search there is no ponder state to leave,
so ignoring the command is the correct behaviour and the alternatives are worse:

- *start honouring the real clock* — there is no clock to switch to; a `go depth 20` search has no time
  budget, and inventing one would make the engine stop somewhere the GUI never asked for.
- *treat it as an error* — it would produce an error line for a command that is harmless, and some GUIs send
  `ponderhit` speculatively.

The practical rule for a GUI author: **`stop` cancels any search; `ponderhit` only ever means "ponder over".**
Sending `ponderhit` as a cancel leaves the engine searching and the GUI waiting for a `bestmove` that will
never come. That is a GUI bug, not an engine defect, and I would file S-F3 as a warning of exactly that shape.

---

## S-F4 — `go` with a clock named only for the side that is NOT to move

**One sentence: the engine should keep never reading the opponent's clock, but when NEITHER clock belongs to the
side to move it must not search unbounded — it should emit an `info string` diagnostic and search a bounded
default.**

Why, and the measurement (`finding_clock/partial_clock_options.txt`):

| position | `go` | ended on its own? | info depth lines |
|---|---|---|---|
| White to move | `go wtime 100` | yes, 6.4 ms | 9 |
| White to move | `go btime 100` | **no** (stopped at 2001 ms) | 22 |
| Black to move | `go wtime 100` | **no** (stopped at 2001 ms) | 21 |
| Black to move | `go btime 100` | yes, 8.4 ms | 9 |
| Black to move | `go wtime 100 btime 999999` | **no** — btime is BLACK's clock here, so ~1000 s | 21 |

The last row is the decisive one: the engine is not "ignoring a missing clock". It correctly reads `btime` as
Black's clock when Black is to move, and a huge `btime` therefore produces a huge search. The only defect is
that when the side-to-move's clock is absent, `limits.time_ms` stays unset and the search becomes
**unbounded with no diagnostic at all** — the GUI sees a silent hang, not a mistake.

I reject the other two options on the evidence:

- *use the named clock anyway* — that is the opponent's clock. Spending White's remaining 100 ms as Black's
  budget would be a plausible-looking number with the wrong meaning, and it would hide the GUI's bug instead
  of surfacing it. Worse than the status quo, because it looks like it worked.
- *refuse the search outright* — too harsh. A GUI that sends `go wtime X` during Black's turn still expects a
  move; refusing leaves it with no move at all, which is a worse failure than a bounded one.

My choice — diagnostic plus a bounded default — is the only one that both keeps the clock semantics correct
and guarantees the GUI always gets a `bestmove`. A GUI author reading this should send **both** clocks (which
is what the UCI protocol describes) and should treat a missing `bestmove` after a partial clock as this
condition rather than as an engine hang.

---

## S-F5 — is the button refusal one bug or a class?

**One sentence: it is one bug in one hand-written branch, not a class — this build has exactly one button
option and no generic button code path exists, so the behaviour cannot currently be duplicated elsewhere, but
any FUTURE button would have to re-implement the same `if (value_text.empty())` guard correctly.**

The count and the evidence (`finding_button/button_class.txt`):

```
$ grep -c 'type button' <the engine's own uci answer>
1
$ grep 'type button' <the engine's own uci answer>
option name Clear Hash type button
```

One command per button option found — there is one:

```
$ setoption name Clear Hash value 0     -> info string invalid value for option Clear Hash
$ setoption name Clear Hash             -> (silence, and the hash clears)
```

And the structural answer, which is stronger than the count: the word `button` appears in the whole source
**only** in the line that advertises the option (`src/uci.cpp:247`). There is no option-type dispatch table
anywhere — every option is its own hand-written `else if (name == "...")` branch — so what Clear Hash does is a
property of three lines:

```
} else if (name == "Clear Hash") {
    if (value_text.empty()) searcher.clear_hash();
    else note_invalid();
```

So: a single bug, in a single branch, not a shared type-level defect. The risk it represents is that
`type button` is advertised to GUIs but never actually drives any behaviour, so a second button added later
would start from nothing and could easily get this wrong again.

---

# TODAY vs SHOULD — for a GUI author who cannot change the engine

Everything above says what the engine SHOULD do. This section says what it DOES today, so a GUI can defend
itself. Measured, not remembered: `today_state/today_state.txt`, an interactive driver (a piped one would
report the 19-F12 fabrication instead of the real answers); the S-F5 rows are collected from before the
`setoption` under test, because a first version of that probe collected after it and wrongly showed silence.

| case | WHAT IT DOES TODAY | warning line today? | what the GUI must do instead |
|---|---|---|---|
| S-F3 `ponderhit` on a non-ponder search | **silently ignored; the search runs on and no `bestmove` follows** | **NO — 0 `info string` lines** | send `stop`, never `ponderhit`, to cancel. There is no reply to detect: the only signal is the `bestmove` that never arrives, so a GUI that waits on it hangs. |
| S-F4 `go` with only the opponent's clock | **silently unbounded: searches until something else stops it** | **NO — 0 `info string` lines** | **never send `go` without the side-to-move's clock.** No warning exists, so the only defence is on the GUI side. |
| S-F5 button `Clear Hash` given a value | refuses the value, so the clear may not happen | **YES — `info string invalid value for option Clear Hash`** | send `setoption name Clear Hash` with NO value. This is the one of the three that tells you it went wrong, so check for that line. |

The asymmetry is the point, and it is why the first two are the dangerous ones: for S-F5 the engine tells you it
refused (so a GUI that reads `info string` lines can log or retry), but for S-F3 and S-F4 the engine says
**nothing at all**. Silence there is indistinguishable from a slow search, which is exactly how a GUI ends up
waiting forever with no diagnostic to show a user.

## the two rules a GUI must enforce itself, in one line each
1. **Never send `go` without the clock of the side to move** (`wtime` when White is to move, `btime` when Black
   is): today the search then has no time limit and no warning is printed.
2. **Never use `ponderhit` to cancel**: it only ends a `go ponder` search. For any other search the engine keeps
   searching and prints nothing, so use `stop`.

Both are GUI-side only. Neither is detectable from the engine's output today, which is why the recommendation in
the SHOULD section is for the engine to emit an `info string` — until it does, there is nothing on the engine
side to wait for.

## scope of the "silent" finding — do not build on it
S-F3 and S-F4 print **no warning line in THIS build** (`6b98f217`, `id name Chess Engine Forge 6.4.24 candidate`); that is a description of today's behaviour and not a guarantee, so a GUI must not write code that depends on the silence — check `info string` lines if they appear, and do not treat their absence as proof that the command was understood.
