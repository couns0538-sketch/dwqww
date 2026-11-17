# CHECK of seat 01's S-F15 — the refusal ORDER is seed-stable; the "within 0.3 points" does NOT reproduce

Their claim:
> S-F15: "The mutation-refusal profile is seed-stable: same order at both seeds (drop 100 > delete > insert > swap
> ~81) and **within 0.3 points per kind**, so it is a property of `set_FEN`, not of the sampled positions."

## Verdict: the ORDER CONFIRMS; the 0.3-POINT STABILITY DOES NOT reproduce on my sample

My own mutation generator, my own positions (R seed 801), 120 mutations per kind per seed, two seeds:

| seed | drop | delete | insert | swap | replace | order |
|---|---|---|---|---|---|---|
| 77 | 100.0 % | 100.0 % | 100.0 % | **60.0 %** | 91.7 % | drop > delete > insert > **replace > swap** |
| 88 | 100.0 % | 100.0 % | 100.0 % | **46.7 %** | 82.5 % | drop > delete > insert > **replace > swap** |

| their statement | my measurement |
|---|---|
| the **order** is the same at both seeds | **CONFIRMED** — identical at both |
| `drop` is 100 % refused | **CONFIRMED** — 100 % at both, and so are `delete` and `insert` |
| "within **0.3 points** per kind" | **NOT CONFIRMED — 13.3 points on `swap`** (60.0 % vs 46.7 %) |
| the profile is a property of `set_FEN`, not of the positions | **the ORDER part is supported**; the per-kind percentages are visibly position-dependent on my sample |

## What this does and does not mean for their finding

**Their core claim survives, and on stronger evidence than the percentage stability:** the *order* of refusal
likelihood is identical at two independent seeds on material they never used, and the three "structural" mutations
(dropping a field, deleting or inserting a character) are **100 % refused at both seeds**. That is a much cleaner
statement of "it is a property of the parser" than a 0.3-point band, because 100 % at two seeds cannot be luck.

**But their specific "within 0.3 points per kind" is a figure I cannot reproduce**, and I think the reason is visible
in the table: **`swap` and `replace` are the two kinds whose refusal depends on WHAT the mutation produces**, not on
the mutation being structurally invalid. Swapping two adjacent characters can yield a *valid* FEN (swap two
identical-rank digits, or two empty-rank digits in a way that still sums to 8) or an invalid one, and which happens
depends on the position's rank structure. So those two kinds must be position-dependent by construction.

That suggests their 0.3-point stability was measured on two samples that happened to have similar rank structures,
and would widen on a different one — which is what mine does.

## My ranking differs from theirs — stated, not glossed
They list `swap` above `replace` ("... insert > swap ~81"); I measure **`replace` clearly above `swap`** at both
seeds (91.7/82.5 vs 60.0/46.7). That is likely the same cause: a one-character **replace** usually breaks the rank
sum to 8 (so ~85-92 % refused), while a **swap** far more often leaves it intact — my generator's `swap` keeps the
character multiset, so the rank sum is preserved and only the *sequence* changes, which `set_FEN` is documented to
tolerate (the adjacent-digit rule). So the two of us ordering these two kinds differently is consistent with the
adjacent-digit behaviour my own 08-C24 area covered.

## What I claim
- **Confirmed:** the refusal order is seed-stable; `drop`/`delete`/`insert` are 100 % at both seeds; the profile is
  a parser property in that structural sense.
- **Not confirmed:** "within 0.3 points per kind". My `swap` moved 13.3 points between seeds.
- **Not claimed:** that their figure is wrong — a different position set with a different rank structure can give a
  tight band, and per-kind stability would then hold *for that set* while not being a general law.

## Show it again

    cd forge-combo29/swarm/08/pc20 && python3 check_s01f15.py /tmp/s01f15.txt
