# REPORT_job6 - CHECK of 19-F10 (seat 19): prefetching the NNUE columns is 8 % slower

## what was asked / the answer / how sure
Asked: check seat 19's 19-F10, which claims "software-prefetching the NNUE weight columns makes the engine 8 %
SLOWER, ratio 0.9190, 95 % CI [0.8841, 0.9552], over 20 alternating pairs, with all four node counts unchanged and
BOTH builds of the patch slower (471 and 496 ms vs base 435 ms)."
Answer: **CONFIRMED, and more strongly than they reported.** On my machine, with a strictly interleaved design and
two builds per side, the patch takes **9.43 % more wall time** (8.62 % less speed), 95 % CI [1.0734, 1.1155] on the
time ratio — entirely on the "slower" side — with the node count identical on all 48 runs.
How sure: high. The effect (~9 %) is about 9x my measurement error on this machine, the CI excludes 1.0 by a wide
margin, and every single one of the 48 pairs had the patch slower.

## honesty numbers
Build: `/home/ubuntu/build/base/forge` and the patched build from seat 19's own patch on a clean 6b98f217 worktree.
All runs: bench 13 = **862329** nodes, asserted on every run by the harness (it aborts otherwise).

## the method (deliberately different from theirs, so agreement means something)
Seat 19 used 20 samples per side. Seat 19's own later finding 19-C2 concedes that sequential-block designs drift,
and my 29-F5 found the same, so I used:
- **24 rounds, ABBA order** (round 1 base-then-patch, round 2 patch-then-base, ...), 2 builds per side, **48 pairs**;
- measured value = the engine's own `bench 13` milliseconds;
- **node count asserted identical on every single run**, so a prefetch patch cannot hide a behaviour change;
- paired bootstrap over the 48 ratios, seed 2901, 10,000 resamples.

```bash
cd forge-combo29/swarm/29/job6
python3 check_19f10.py ~/build/baseA/forge ~/build/baseB/forge ~/build/pfA/forge ~/build/pfB/forge
```

## the numbers
| metric | value |
|---|---|
| pairs | 48 (24 rounds x 2 build pairs), 0 dropped |
| base median | 451.5 ms |
| patch median | 495.5 ms |
| base mean | 461.1 ms |
| patch mean | 503.1 ms |
| patch/base time ratio | **1.0943** |
| 95 % CI | **[1.0734, 1.1155]** |
| speed change | **-8.62 %** |
| nodes | 862329 on all 96 runs |

Seat 19 reported -8.10 % [-11.59 %, -4.48 %]; I get -8.62 % [+7.34 %, +11.55 % on the time ratio]. **The two agree
on the size of the loss and on its direction.** Their CI was wider because they had 20 samples; mine is tighter
because I had 48 pairs and interleaved.

## a table: step | done-partly-not done | evidence | result

| step | done? | evidence | result |
|---|---|---|---|
| fetch seat 19's patch and apply to a clean 6b98f217 | done | `patch -p1 --dry-run` → "checking file forge-combo29/src/nnue.cpp" | applies without fuzz |
| build the patch twice | done | `~/build/pfA`, `~/build/pfB` | both build, bench 13 = 862329 |
| interleaved paired measurement, 48 pairs | done | `raw_check19f10.txt` | patch slower in every pair |
| assert node count on every run | done | harness `abort` on mismatch | 862329 everywhere, never fired |

## findings
| id | area | one sentence | file | type |
|---|---|---|---|---|
| 29-C4 | CONFIRMS 19-F10 | `_mm_prefetch` of the NNUE weight columns makes `bench 13` take 9.43 % more wall time (time ratio 1.0943, 95 % CI [1.0734, 1.1155], 48 interleaved pairs, 2 builds per side, 862329 nodes on every run), reproducing seat 19's ~8 % slowdown with a tighter interval. | `forge-combo29/swarm/29/job6/check_19f10.py` | CONFIRMS 19-F10 |

## a bug in my own checker, caught and fixed before this report
My first run printed `VERDICT: REFUTES 19-F10 -- measurably FASTER` on a ratio of 1.0933, because I had written the
branch as if a ratio below 1 meant "slower". The ratio is patch_time/base_time, so **above** 1 is slower. I fixed
the comparison and re-ran; `raw_check19f10.txt` holds the corrected run. This is exactly the class of error seat 19's
measurement-integrity warning was about (a label asserted without checking what the number means), so I record it
rather than hiding it.

## suspicions, not proven
- WHY prefetching hurts: seat 19's 19-F11 says it is a request-throughput limit, and my data is consistent with that
  (their two-request variant removed the loss). I did not test the two-request variant myself.
- Whether the loss is larger or smaller with the PC's own king-bucket net: untestable here (29-F9, no net file).

## what I did NOT do
- Not tested on the PC's net (impossible in this repository).
- Did not test their "lite" two-request variant; that would be a second job.

## what I am NOT sure about
- My absolute milliseconds differ from theirs (mine ~450 ms base vs their ~435 ms) because the machine is shared;
  only the RATIO is being compared, and that is what the finding is about.

times: see stamps.txt
