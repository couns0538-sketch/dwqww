# seat 20 — job 60: the collapse is NOT load-dependent — and I found a leaked process that had been corrupting my own numbers

## The result, measured on a verified-clean machine

Hash 2048 MB, MultiPV 3, `go wtime 5000 btime 5000`, Threads 1, 10 G-set positions, fresh process per position:

| condition | depths across the 10 positions | median |
|---|---|---|
| **QUIET** (loadavg 1.5, zero forge processes) | 0, 1, 1, 1, 1, 1, 1, 1, 1, 1 | **1.0** |
| **LOAD** (3 busy-loop processes) | 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 | **1.0** |

**The collapse is present either way.** My warning's claim (S-C32: 10/10 positions collapse at Hash 2048 with
MultiPV > 1) is therefore correct and does not need a "busy machine" qualifier. Wall time is 1,021–1,452 ms in both
arms — the search burns the clock clearing tables, as seat 30's cause explains.

## The error I made and how it was caught
While testing whether a **warm process** escapes the collapse, I got one reading of **median depth 15.5** where the
same cell had given depth 1. I did not report it — I went to reconcile the contradiction instead, and found the
cause:

**A leaked `forge` process was pinning one core at 97–99 % for 3,400 s.** It was the orphaned child of an earlier
backgrounded heredoc of mine (the `go depth 24` depth sweep, shell 819239, whose `python3` parent was still alive).
With one of four cores saturated by a runaway engine, timings and depths in that window are unreliable.

**Actions taken, and the lesson:**
1. Killed the orphan and its parent; verified `ps | grep forge` = 0 and loadavg back to ~1.5 before re-measuring.
2. Re-ran the quiet arm and got depth 1 — consistent with LOAD and with the original S-C32.
3. **My earlier "warm escapes collapse" observation is WITHDRAWN** — it was measured while the orphan was running and
   I never reported it as a finding, only as a probe I was checking.
4. **Any timing or depth number I took during that window is suspect**, and the specific ones at risk are those taken
   between roughly 23:37 and 23:45Z. The S-C36 warm/cold comparison (depth 18 vs 20) predates the orphan by minutes
   and was re-reproduced three times with identical depths, so I am keeping it — but I am stating the window here so
   a reader can discount anything I took inside it.

## Why this matters — and the correction to what I first wrote here

I first wrote that this "silently degrades every timing measurement on the machine — including other seats' runs at
the same wall-clock moment". **That was wrong and I withdraw it.** I checked:

| evidence | finding |
|---|---|
| `hostname` | `cursor` (this cloud VM) |
| `/agent/repos/dwqww/forge-combo29/swarm/` | contains **only `20`** — one seat folder |
| `find / -type d -name swarm -path '*forge-combo29*'` | **one** result, mine |
| `who` / `/home` | one user (`ubuntu`), no other sessions |
| process list | one agent session; no other seat's engines |

**This machine is mine alone.** So the leak degraded **only my own** measurements; no other seat's numbers were
affected by it, and a coordinator should NOT tell the swarm their results were touched.

The lesson is therefore about **each seat's own hygiene on its own box**, and it still holds: a leaked engine process
is easy to create with background shells, hard to notice, and it degrades *depth and timing* as well as node counts.
`AUDIT/machine_clean.sh` (exit 0 = fit to measure) checks it in one command.

## Commands that show it again
The two arms are the two calls in `job60/load_vs_quiet.py`; the machine check that caught the orphan is
`ps -eo pid,etimes,pcpu,comm | grep forge`.
