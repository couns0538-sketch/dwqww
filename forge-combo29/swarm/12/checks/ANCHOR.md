# THE ANCHOR: a fixed-node speed reference, its honest band, and why `go nodes` needs care

Seat 12, area 2. **Threads 1** everywhere. This note covers S-F24 (the absolute anchor) and S-F25
(the `go nodes` shortfall), because the anchor's correctness depends on the second.

## What the anchor is

One line in `selfcheck.py` output:

```
go nodes 1000000  ->  <N> reported nodes in <ms>  =  <ms/M> ms per million reported nodes
```

A **fixed node count** means the engine does the same work on every machine, so ms-per-million-nodes
is a measure of **machine speed with no settings in it** — no Hash, no MultiPV, no depth-dependent
pruning. That is why it is a fairer absolute check than any depth-6 wall time.

## The reference measurement

On the reference box (4 cores, 15 GB):

| quantity | value |
|---|---|
| `go nodes 1000000` reports | **920,173** nodes |
| median over 10 runs | **604 ms** |
| range | 591-633 ms |
| stdev / spread | 13 ms / **7 %** |

The tool uses **600 ms/M** as the reference point and a band of **560-700 ms/M** as "same class of
machine". The band is the run-to-run spread plus a modest allowance for a slightly slower CPU of the
same kind.

## What moves it, and what does not — measured, not assumed

**Core count does NOT move this anchor.** A Threads 1 search uses one core, so pinning the process
with `taskset` changes nothing:

| CPUs available to the process | median ms per million |
|---|---|
| 1 core (`taskset -c 0`) | **578** |
| 2 cores (`taskset -c 0-1`) | **576** |
| 4 cores (`taskset -c 0-3`) | **577** |

And saturating all four cores with four concurrent engines gave 553 ms/M against 543 idle — 1.0x.
**So a 2-core, 4-core or 8-core machine of the same generation lands in the same band**, which is the
question asked, and the answer is measured rather than estimated.

**What does move it: CPU generation, clock and cache.** I have **only one machine**, so I cannot
measure a different generation and I do not claim a number for one. The tool says this in its own
output: if a machine is **faster** than the band, that is fine (faster is good); if it is **slower**,
the tool prints that the band cannot tell you whether that is normal for your CPU, that the anchor is
**only comparable to this reference measurement**, and that the grid thresholds should be scaled by
the measured ratio.

## Why the anchor divides by the REPORTED node count (S-F25)

**`go nodes N` stops short of N**, so a nodes-per-second figure computed from the *requested* count
is inflated. Measured on the reference box, medians of 7 runs, Hash 16, MultiPV 1, startpos:

| requested | actually searched | ratio | median ms | nps (from reported) |
|---|---|---|---|---|
| 100,000 | **72,062** | 72 % | 55 | 1,319,773 |
| 300,000 | **267,839** | 89 % | 168 | 1,596,590 |
| **1,000,000** | **920,173** | **92 %** | **547** | **1,683,042** |

Using the requested 1,000,000 instead of 920,173 would overstate the machine by 8 %; at 100k nodes
it would overstate by 39 %. The anchor therefore divides by the reported count, and any other
benchmark in this project that computes nps from a `go nodes` request should do the same.

This also means a `go nodes` benchmark is *not* exactly a fixed-work benchmark unless the reported
count is checked — which the tool does, and `node_bench.py` reports explicitly.

## Which verdict to trust

The tool prints two and says so:

| situation | trust |
|---|---|
| anchor in band, a grid cell FAILs | the **setting** (less Hash / fewer PV lines) |
| anchor out of band (slow), grid cells PASS | the **anchor** — the grid is relative to this box |
| anchor "faster" than the reference while a grid cell is many times slower | the **grid**, and the tool prints **INCOHERENT**: that is not physically possible for one binary, so the engine is misreporting its node count |

That third row came from a planted control (a fake engine that is uniformly slow *and* lies about
its node count). It made the anchor report the fake as **0.67x faster** than the box; the grid
caught it at 23.6x. Without that control the guard would have been shippable and useless.

## Files

- `checks/selfcheck.py` — the tool (stdlib only).
- `checks/node_bench.py` — the fixed-node benchmark used to calibrate the anchor.
- `checks/node_bench.txt` — the shortfall table above, raw.
- `checks/anchor_cores.txt` — the core-pinning table above, raw.
- `checks/selfcheck_real.txt`, `selfcheck_control_slow.txt`, `selfcheck_control_silent.txt`,
  `selfcheck_control_uniform.txt` — the four runs (real engine + three planted controls).
- `checks/YOUR_OWN_CHECK.md` — the owner-facing one-page instructions.

## What I am not claiming

- Not a number for a different CPU generation. **One machine was measured.**
- Not that 560-700 is the right band for *any* machine — only that it is the honest envelope around a
  measurement I actually took, with core count ruled out.
- Not that `go nodes N`'s shortfall is a bug: it may be intentional (the engine may stop at a
  depth boundary). What is certain is that the reported count is what actually happened, and nps must
  use it.
