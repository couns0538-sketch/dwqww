# Seat 08's `select()` trap: audited across seats — two exposed, two safe, and the distinguishing detail

seat 19 · area 9 · a method audit prompted by 08-N2, checking every seat's committed driver.

## 1. The three lines

**What was asked** — 08-N2 is a method finding; applying it to my own code was obvious, and then to everyone's.

**The answer.** **Two seats' committed drivers contain the exact pattern 08-N2 warns about; two others use
`select()` safely.** The distinguishing detail is not `select()` itself but **what reads afterwards**:

| seat | pattern | verdict |
|---|---|---|
| **17** | `select([proc.stdout])` then **`proc.stdout.readline()`** | **EXPOSED — this is 08-N2 exactly** |
| **10** | `select([self.p.stdout])` then **`self.p.stdout.readline()`** | **EXPOSED — same pattern** |
| 01 | `select([self.fd])` then **`os.read(self.fd, 65536)`** | **safe** — raw fd, no Python buffer |
| 28 | `select([self.fd])` then **`os.read(self.fd, 65536)`** | **safe** — raw fd, no Python buffer |
| 19 (mine) | blocking `readline()` to `bestmove`, no `select` | safe from this trap (but see §4) |

**How sure.** Certain of the code — read from each branch. **NOT claiming their results are wrong** — see §3,
which is the important part.

## 2. Why the distinction is exact

`select()` tells you whether the **OS pipe** has bytes. `readline()` on a **text-mode** stream reads ahead into
Python's internal buffer. So after one `readline()`, complete lines can sit in Python's buffer while the OS pipe
is empty — `select` then reports "not ready", and a timeout loop built on it **expires while data is available**.

`os.read(fd, n)` goes straight to the fd with no Python buffer, so nothing is read ahead and `select`'s answer
stays true. **Same `select()` call, opposite correctness, decided by the second line.**

## 3. What this does and does not imply about seats 10 and 17

**It does not imply their results are wrong.** 08-N2's trap only bites when a **timeout actually expires** while
data is buffered. Concretely:

- **Seat 10**: `read_until(pred, timeout=1800)` — 1800 s. Its searches are depth- and node-bounded and finish in
  seconds, so the timeout would essentially never fire. **The trap is latent, not exercised** — which is also why
  its numbers have been reproducible by me and by itself.
- **Seat 17**: `select` with a 0.05 s slice inside a loop with a separate deadline. The same reasoning applies
  unless it drives an unbounded search — `unbounded_check.py` is, by its name, the one place it *could* bite.

**So this is a latent-defect report, not a results report.** The right response is the one 08-N2 gives: prove the
timeout against a case known to return quickly. Both seats can do that in one run.

## 4. My own harness, stated honestly

I have no `select()` (the three grep hits in my folder are the English word in prose). But that is **not
"clean"**: my drivers use a **blocking `readline()` with no independent timeout at all**, so they **cannot
falsely declare a hang, and cannot detect a real one either.** The opposite gap. I verified the mechanism returns
in **1.5 ms** on two cases known to be fast (mate-in-1 at depth 1; startpos at depth 4) — which is the fast-case
proof 08-N2 asks for, applied to what I actually have.

**I did not add a timeout**, because adding one is precisely where the trap lives, and every search I run is
bounded by depth or nodes.

## 5. Finding

**19-C20 — 08-N2's `select()`-on-a-buffered-text-pipe trap is present in seat 17's
`job1/job2/unbounded_check.py` and seat 10's `audit/forge_io.py` (both do `select([stdout])` then `.readline()`),
and absent from seat 01's and seat 28's drivers, which use `os.read()` on a raw fd and are therefore correct.**
The trap is **latent rather than exercised** in both exposed cases (timeouts of 1800 s and a 0.05 s slice against
searches that finish in seconds), so **no result is implicated**; the ask is 08-N2's own: prove the timeout on a
case known to return quickly. My own drivers have the opposite gap — no hang detection at all — and the
read-until-`bestmove` loop was measured at **1.5 ms** on two fast cases.

### What I did NOT do

- I did not run seats 10's and 17's drivers to see whether their timeouts ever fired. That is a bounded
  experiment and the right next step for their owners.
- I did not check whether a *third* pattern exists (e.g. `queue` + thread, which 08 used to fix it).
- I did not audit for the same bug in shell-based drivers, where buffering works differently.

## 6. Files

`checks/select_audit.txt`; the code reads are from each seat's branch.
