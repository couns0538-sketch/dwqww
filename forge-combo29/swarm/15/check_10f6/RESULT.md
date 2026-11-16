# CHECK of seat 10's 10-F6 — the honesty pins hold only in the DEFAULT option regime

**Verdict: CONFIRMS 10-F6, exactly, to the node.**

Harness: `check_10f6.py`, written from the finding's claim alone. Two regimes, each measured in
its own fresh process; the node total is parsed only if a `nodes <n>` line is actually found, and a
missing number is reported as `PARSE_FAIL` rather than 0.
Raw output: `check_10f6_release.txt`. Engine: `e06310ec…16a83` (my release build, pins exact).

## Results

```
bench  regime   nodes          brief says     verdict
11     plain    312866         312866         MATCH
13     plain    862329         862329         MATCH
16     plain    3024920        3024920        MATCH
11     S14      242796         312866         DIFFERS
13     S14      656517         862329         DIFFERS
16     S14      2155620        3024920        DIFFERS

=== perft 5 in both regimes ===
perft5 plain    4865609        4865609        MATCH
perft5 S14      4865609        4865609        MATCH
```

Every one of seat 10's six numbers is reproduced digit for digit: 242,796 / 656,517 / 2,155,620
under S14, against the brief's 312,866 / 862,329 / 3,024,920, with perft 5 unmoved at 4,865,609 in
both regimes.

## Why this matters for the whole swarm (beyond the finding)

The brief orders every seat to run the four honesty numbers and says a build that misses one is not
used. It does not say *in which option regime*. This check shows the pins are only stable with the
engine's default options: apply the brief's own S14 setoptions first and three of the four pins
move. A seat that sets S14 and then measures honesty gets a false mismatch and might discard a
perfectly good build — or worse, "tune" something to make the false mismatch go away.

My own honesty check (`HONESTY.txt`) sent no `setoption` lines at all, which is why it matched; that
was luck of ordering rather than a rule I followed deliberately. It is worth stating plainly that
the correct reading is: **pins are a property of the default option regime**, and S14 must not be
applied before checking them.

## Scope

I checked the claim on one build (mine). I did not test whether other single options move the pins,
nor whether the S14 numbers are themselves stable across rebuilds.
