# The select-plus-readline artefact: how a Python harness invents an unbounded search

Seat 17, area 7. Written 2026-11-16T22:02Z, after this artefact nearly produced a false finding
("`searchmoves` with no legal match hangs a 100 ms clock for 20 s +"). The finding was wrong;
this note is about the artefact, which is reusable knowledge for any harness in this swarm.

## What happened

I wrote a timing harness to answer "does this search ever return bestmove on its own?" It did:

```python
ready, _, _ = select.select([proc.stdout], [], [], 0.05)   # fires when BYTES arrive
if not ready:
    continue
reply = proc.stdout.readline()                             # then BLOCKS for a whole line
```

`subprocess.Popen(..., stdout=PIPE, text=True)` gives a *buffered text stream*. `select()` reports
readable as soon as **any** byte is available, but `readline()` then needs a **newline-terminated
line**, and it blocks inside Python's buffer until one arrives — during which no `select()` runs
again and the wall-clock accumulator keeps counting.

Result: the search finished and printed `bestmove` in 19 ms, but my harness was parked inside a
`readline()` and reported **20.0 s with no bestmove**.

## The failure signature (what to look for)

1. **The controls fail too.** This is the tell. My run said
   `go wtime 1000 btime 1000 searchmoves e2e4` took 20 s, and so did `go wtime 1000 btime 1000`
   with no restriction at all. Neither can be true of a healthy engine on a 1 s clock, so the
   measurement was broken, not the engine. A harness that only measured the suspect command would
   have "confirmed" a hang that does not exist.
2. **Every failing case shows `timed_out: true` and identical wall times.** My bad run reported
   20.002, 20.033, 20.005, 20.011 s across four different commands — that is my own timeout constant,
   not the engine.
3. **The reported `time` field disagrees with the wall time.** The engine's own last `info` line said
   `time 0` / `time 54` ms while the harness claimed 20 s. When the engine and the harness disagree
   about elapsed time by three orders of magnitude, believe neither until a third method agrees.
4. **A raw pipe contradicts the Python harness.** `printf '...go movetime 100\n' | forge` returned
   `bestmove 0000` in 19 ms. The shell has no buffering layer to blame.

Measured proof of the mechanism itself: a diagnostic loop that read `uciok` using
`select()` + `readline()` took **5.03 s and returned exactly 1 line**. The engine had answered
instantly; the harness had not looked.

## The rule

> Read engine stdout either with a **blocking `readline()` per expected answer** (one command at a
> time, wait for `readyok`/`bestmove`, never pipeline `quit` into a live search — see 19-F12), or
> with **`select` plus an unbuffered read** (`os.read`, or a binary pipe with `bufsize=0`) that
> assembles lines yourself.
>
> **Never** call `readline()` after `select()` on a buffered text pipe. And if you must, run a
> **control with the same driver** on a command whose correct timing you already know.

## The two working patterns

Blocking, one command per answer — what `uci_driver.py` in this folder does, and what I now use
for every measurement:

```python
proc.stdin.write(line + "\n"); proc.stdin.flush()
if line.startswith("go"):
    while True:
        reply = proc.stdout.readline()      # blocking, no select
        if reply.startswith("bestmove"):
            break
```

Select with unbuffered bytes, when you need to be genuinely non-blocking:

```python
proc = subprocess.Popen([exe], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        bufsize=0)                      # binary, unbuffered
r, _, _ = select.select([proc.stdout], [], [], 0.05)
chunk = os.read(proc.stdout.fileno(), 65536)            # never readline() here
buffer += chunk
while b"\n" in buffer:
    line, buffer = buffer.split(b"\n", 1)
```

## Evidence in this folder

| file | what it is |
|---|---|
| `job2/unbounded_check.py` | the faulty harness, kept so the error stays visible |
| `job2/unbounded/unbounded.json` | its output: four 20 s "hangs", two of them controls |
| `job2/unbounded/recheck.json` | the same four commands through the blocking driver: 18-91 ms, all with bestmove |
| `job2/unbounded/recheck_*.log` | raw logs for the re-check |
| FINDINGS.md S-F11 | the one-line version of this note |
| FINDINGS.md S-F8 follow-up | the corrected engine statement: misleading report, not a long search |

## Why this is worth more than the finding it nearly produced

A fabricated unbounded search is a fabricated **hang**, and a hang is the most damaging claim a
harness can make in a swarm where other seats act on findings. It would have sent someone hunting a
livelock in the time manager that does not exist. The engine's actual defect in this area is much
smaller and purely cosmetic: 64 `info depth` lines each reporting `nodes 0 time 0`, i.e. a search
report for a search that never ran.
