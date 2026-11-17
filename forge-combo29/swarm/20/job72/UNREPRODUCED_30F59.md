# seat 20 — job 72: seat 30's 30-F59 (PC20 pick a 200+ cp worse move until depth 18) — NOT REPRODUCED on my build

I tried to confirm 30-C56 / 30-F59 independently. **I could not reproduce it**, and I am recording that as
*unreproduced*, **not** as a refutation — because their run does not state its exe identity, so a build difference
cannot be excluded.

## What they claim
On position 29 (`rnb3nr/3kb2p/1p2p3/p1p2pP1/1PP1p1P1/P3PQ1R/1B1P1P2/RN2KB2 w Q - 0 18`), PC20 plays `f3g3`, which is
**200+ cp worse** than S14's `f3g2`, from depth 10 through 16, and only switches at depth 18.

## What I measured (PC r15 build, Threads 1)

| depth | S14 move / score | PC20 move / score |
|---|---|---|
| 10 | f3g2 / cp 1744 | **f3g2** / cp 1770 |
| 12 | f3g2 / cp 1838 | **f3g2** / cp 1790 |
| 14 | f3g2 / cp 1905 | **f3g2** / cp 1940 |
| 16 | f3g2 / cp 1985 | **f3g2** / cp 2019 |
| 18 | f3g2 / cp 2053 | f3g2 / cp 2031 |
| 20 | f3g2 / cp 2113 | f3g2 / cp 2187 |

**PC20 plays `f3g2` at every depth on my build**, and the two arms' scores agree to within ~50 cp throughout. Their
reported `f3g3 / cp 1627` at depth 12 does not appear in any configuration I tried.

## What I ruled out before concluding "unreproduced"
- **Option ordering / Hash:** their `settle_pos29.py` S14 list carries no `Hash` or `Threads`, so I tried all four
  combinations (S14 and PC20 each with the default Hash 32, and with Hash 16) at depths 12/14/16 — **`f3g2` in all
  twelve cells**, scores within a few cp of each other.
- **The FEN:** their raw JSON's FEN is valid (37 legal moves). (Their *FINDINGS line* misquotes it as `RN2KB1` with
  unequal rank lengths — I used the raw file's `RN2KB2`, which is the right thing to do and is worth their correcting.)

## Why I stop at "unreproduced"
Their `check17/run.log` and `prediction.txt` **do not record the exe's sha256 or `id name`**, so I cannot show their
build is the same as mine. My PC r15 build is
sha256 `068f0927768d30be60e8…`, `id name Chess Engine Forge 6.4.24 candidate`, and it reproduces all four honesty pins.
Given that, the honest verdict is:

> **NOT REPRODUCED (not refuted).** On my build PC20 and S14 agree at every depth. Their result may depend on a build or
> option detail their files do not record — which is itself the actionable note: **a claimed 200 cp behaviour needs the
> executable identity in the file.**

This is exactly the failure mode my S-F44 regime triple exists to prevent, one level down: not just *which settings*,
but *which binary*.

## What would settle it
1. Their exe's sha256 and `id name`.
2. The exact option list they sent, in order, with Hash and Threads included.
Then a re-run of the same six depths on their build — if it still shows `f3g3`, the difference is in the build, not in
the measurement method.

## Limits
- One position, depths 10–20, my build only, Threads 1, built-in net.
- I did not run their `A_isolated` (per-move `searchmoves`) arm; a difference could in principle appear there, but that
  would not explain the *unrestricted* disagreement, which is the claim.

## WHAT I NEED FROM SEAT 30, stated plainly (please relay)

To settle whether 30-F59 is a real behaviour or a build difference, I need two things that their `check17/` files do
not contain:

1. **The executable's identity**: `sha256sum` of the binary they ran, and its `id name` line.
   For comparison, mine is sha256 `068f0927768d30be60e8cce6c9f29620dec330565397357dccc9e0fe361e32f4`,
   `id name Chess Engine Forge 6.4.24 candidate`, 4/4 honesty pins (312866 / 862329 / 3024920 / 4865609).
2. **The exact ordered option list they sent**, including `Hash` and `Threads` — their `settle_pos29.py` S14 list
   contains **neither**, so the two arms may have differed in table size, which I could not test without knowing.

With those two, re-running the same six depths (10/12/14/16/18/20) on their binary decides it in one command: if it
still shows `f3g3`, the difference is in **the build**, and that is a much more interesting finding than either of our
current positions.

**Meanwhile, the claim should be quoted with its build unstated** — which is why I am not refuting it. And the general
form for every seat: **settings without a binary are half a citation.** I found the same gap in seven of my own job
folders while writing this, and my driver now stamps `{exe, sha256, id_name}` for every future job.

## RESOLVED — seat 30 retracted 30-F59; the cause was the option list, not provenance

Seat 30 has **retracted 30-F59 and the PC20 half of 30-C56**. The bug in its `settle_pos29.py`: it passed
`PC20EXTRA` **alone**, so its "PC20 arm" was the six extra switches on top of **DEFAULT** options — never S14 + six.
It also confirms our binaries were **identical (same sha256)**, so provenance was not the cause, and reports that
`f3g3` reproduces at Hash 16, 32 and 64 on that binary — which is why my Hash retries could not have found it.

**I reproduced all three arms myself** at depth 12 on my build (sha256 `068f0927768d30be60e8…`):

| arm | bestmove | score |
|---|---|---|
| **six extras over DEFAULTS** (their bug) | **f3g3** | **cp 1627** — exactly what they published |
| S14 alone | **f3g2** | cp 1838 |
| **TRUE PC20** (S14 + six + Threads/Hash) | **f3g2** | **cp 1790** — exactly my figure |

So **only the option list explains it**, and my "not reproduced" verdict was correct about the behaviour while
correctly declining to refute. The distinction I drew — unreproduced, not refuted — was the right call: their result
was real *for the options they actually sent*, and the disagreement was in the option construction.

## What stands, unaffected by either side
`f3g2` **outscores `f3g3` by ~200 cp in isolation under S14**, which seat 30 keeps. That part of 30-C56 never depended
on the PC20 arm.

## The provenance instinct, and what it did and did not do
Asking for the exe sha256 before refuting **did not solve this** — the binaries turned out identical. What it bought was
**the elimination of a whole hypothesis class cheaply**: with the hash in hand, "different build" was off the table in
one line, and the remaining explanation had to be the options. It also forced me to notice that their S14 list carried
no `Hash` or `Threads`, which is what pointed at option construction in the first place.

So the honest accounting: **provenance was not the bug, but asking for it is what narrowed the search to the bug.**
That is worth stating as method rather than as vindication.
