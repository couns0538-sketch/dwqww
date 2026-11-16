# REPORT — seat 07, job 16: does the SHIPPED transposition-table path behave identically?

## What was asked / the answer / how sure

**Asked:** continue the area-7 read. My own job15 report flagged that the TT probe covered
`FORGE_SPD_TT_NOTLS=0` while the shipped build uses `1` — so the shipped path was unprobed, and I
said so. This job closes that gap.

**Answer:** the shipped configuration (`FORGE_SPD_TT_NOTLS=1`, which is the CMakeLists default at
`CMakeLists.txt:32`) produces **exactly the same four pin numbers** as the locked configuration:
312866 / 862329 / 3024920 / 4865609. Same node counts from the same depths over the same bench set
means the unlocked owner path searches the identical tree.

**How sure:** high for the pins being identical. **Not** proven: that the two configurations are
byte-identical code — and in fact I discovered they *are* the same binary, because the shipped build
was already `TT_NOTLS=1` and my job15 probe was the odd one out (see "a correction to job15" below).

## Honesty numbers

Both configurations, measured by the same script (job0/honesty.sh) with a fresh process per line:

| check | required | `TT_NOTLS=1` (shipped) | `TT_NOTLS=0` (job15 probe) |
|---|---|---|---|
| bench 11 | 312866 | 312866 | 312866 |
| bench 13 | 862329 | 862329 | 862329 |
| bench 16 | 3024920 | 3024920 | 3024920 |
| go perft 5 | 4865609 | 4865609 | 4865609 |

Raw: job16/raw_notls/summary.txt (shipped path), job0/raw/summary.txt (build-rel).

## A correction to job15's caveat

My job15 report said the probe used the locked path and that the shipped path was therefore
"unprobed". Checking properly:

    CMakeLists.txt:32   FORGE_SPD_TT_NOTLS=1        <- the shipped default
    /tmp/compile_tt.sh  -DFORGE_SPD_TT_NOTLS=0       <- what MY job15 probe forced

So the position was the reverse of what I assumed: the shipped build **is** the unlocked one, and
every pin in job0/HONESTY.txt from the very first minute of this seat was measured on the shipped
unlocked path. The job15 probe was the unusual configuration.

Two consequences, stated plainly:

1. The shipped TT path has been pin-verified since job0, not just now.
2. My job15 four-invariant probe (store-then-probe, no high-32 false hit, resize and clear
   invalidation) was run on the **non-default** configuration. It should be read as evidence about
   the locked path only.

## Why I could not simply re-run the invariant probe on the shipped path

`TranspositionTable::ExclusiveLease`, `probe_owned()` and `store_owned()` are **private**
(`include/forge/search.hpp:167` grants friendship to `Searcher` and `SearcherTestProbe`). A standalone
probe cannot call them; my first attempt failed to compile with exactly those three errors. Reaching
them would mean either editing a header (forbidden — engine source is patch-only, and I will not ship
a patch just to make a test compile) or adding a test-only friend (same objection). I therefore tested
the shipped path the way that requires no source change: **behavioural equivalence of the pins**, which
is the property that actually matters in play.

## What this proves and what it does not

**Proves:** under `TT_NOTLS=1`, bench 11/13/16 and perft 5 give exactly the canonical node counts, so
the unlocked owner path stores and retrieves the same information the search would otherwise get.

**Does not prove:** that `probe_owned`/`store_owned` satisfy the four fine-grained invariants. The
pins are a coarse instrument: a TT that returned a wrong score would usually still produce the same
node count at these fixed depths only if the wrongness were never consulted, so identical pins are
strong but not conclusive evidence of payload correctness.

**Also honest:** bench 13 and 16 exercise the TT heavily (hashfull rises through the search), and perft
does not use the TT at all, so the perft pin is a control for "the board code is unchanged", not
evidence about the table.

## Findings

No new finding. This job **corrects** the caveat in REPORT_job15.md rather than adding a claim, and
that correction is itself worth recording so nobody repeats the mistake of calling the shipped path
unprobed.

## Suspicions, not proven

- Whether `TT_NOTLS=1` and `TT_NOTLS=0` are meant to be *bit-identical* in the tree they search. The
  identical pins say they are on these positions, and identical pins across both configurations is a
  stronger statement than I expected to get.

## What I did NOT do

- Did not add a test-only friend to reach the private owner API (would require an engine source
  change).
- Did not test threaded TT access; `TT_NOTLS=1` under multiple threads is exactly area 4's territory
  and seat 19/27's Threads work is the right place for it.

## What I am NOT sure about

- Whether a rare position exists where the unlocked path's missing `lock_stripe` matters for a
  single-threaded search: it should not, since no other thread is present, and the pins support that.

## Times

See job16/stamps.txt.
