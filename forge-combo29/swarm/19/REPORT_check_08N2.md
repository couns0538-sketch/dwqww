# Seat 08's `select()` trap, checked against my own harnesses — and it does not apply, verified

seat 19 · area 9 · a check of another seat's method finding against my own code, prompted by the fact that it is
a trap I could easily have in my own drivers.

## 1. The three lines

**What was asked** — nothing specific; 08-N2 is a method finding worth checking my own code against.

**The claim (08-N2).** `select()` on a Python text-mode buffered pipe **is not a timeout**: because `readline()`
reads ahead, `select` can report "not ready" while complete lines sit in Python's buffer. Seat 08's volatility
harness therefore declared 90 s timeouts on searches that actually answered in **194 ms** — and had it trusted the
result, its report would have said "the sparse class HANGS", which is false and the opposite of its real finding.
Its rule: **a timeout mechanism must be proven against a case known to return quickly, before it is allowed to
declare a hang.**

**The answer.** **The trap does not apply to my harnesses, verified two ways.** (a) No file of mine calls
`select.select` — the three grep hits for "select" are the English word in prose ("boards I select myself",
"partial-selection branch"). (b) My read mechanism is a blocking `readline()` loop that stops at `bestmove`, and
**on two cases known to be fast it returns in 1.5 ms** — so any timeout built on it would be checked against a
fast case, which is exactly seat 08's rule.

**How sure.** Certain of (a) — a grep. High on (b) — measured, and it is the discipline the rule demands rather
than an assertion that the code looks right.

## 2. Why this was worth checking

My drivers (`drive_search.py`, `drive_counters.py`, `drive_hash16.py`, `dtm_oracle.py`, `twin2595.py`,
`threads_check.py`, `noise_floor.py`) all have the same shape: a blocking `readline()` until a token, with
**no independent timeout at all** in most of them. That is a *different* weakness from seat 08's — mine cannot
falsely declare a hang, but mine also **cannot detect a real one**: a driver of mine would block forever if the
engine never answered.

So the honest statement is not "my harness is clean" but: **my harness cannot misfire the way 08-N2 describes, and
it has the opposite gap — no hang detection at all.** I did not add one, because adding a timeout is exactly where
the trap lives and the search durations I run are bounded by node or depth limits.

## 3. The measurement

```
mate-in-1, go depth 1      : bestmove seen=True in 1.5 ms
startpos,  go depth 4      : bestmove seen=True in 1.5 ms
```

Both are cases that must return almost instantly; both did. **That is the proof seat 08 asks for**, and it also
shows the loop is not read-ahead-confused: it saw the token immediately.

## 4. Finding

**19-C20 — seat 08's `select()`-is-not-a-timeout trap (08-N2) does not apply to my harnesses: none calls
`select.select` (the "select" grep hits are prose), and my blocking read-until-`bestmove` loop returns in 1.5 ms
on two cases known to be fast, which is the fast-case proof 08-N2 requires.** The trade-off I do have is the
opposite one — **no hang detection at all**, so a driver of mine would block forever rather than falsely report a
timeout. I have not added one, because the trap lives precisely there and my searches are bounded by depth or
nodes.

### What I did NOT do

- I did not add a timeout to any driver. That is a change with its own failure mode (08-N2) and no current need.
- I did not audit other seats' harnesses for the `select()` pattern. **That would be worth doing** — 08-N2 says it
  produced a false "HANGS" result, and any seat that used `select` on a text pipe has the same exposure.

## 5. Files

The grep and the two timing runs are in this report; no separate artefact file.
