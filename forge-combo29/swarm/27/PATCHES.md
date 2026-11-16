# Patches from seat 27 — how to combine them with seat 12's patch

**CHECK FIRST: `bash forge-combo29/swarm/27/verify_patch_order.sh 6b98f217 <seat12>/job1/two_doors_mate.patch.txt forge-combo29/swarm/27/job1/drawn_root_reporting.patch.txt` — it runs both orders, prints every exit code, and shows the `-p`-level trap below. Verdict PASS = order does not matter and both patches landed.**

## THE CORRECTION (found by seat 12; my earlier "one order only" was wrong)

**Order does not matter. The `-p` level does.** Seat 12 tested this on a clean `6b98f217` worktree in both
orders and got a **byte-identical** `src/search.cpp`, sha256
`24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671`. I re-ran both orders independently and
reproduce that sha256 exactly (see "What I verified" below).

The two patch files were generated from **different directories**, so each needs a different `-p` level:

| patch file | its hunk header names | correct invocation |
|---|---|---|
| seat 12's `two_doors_mate.patch.txt` | `a/forge-combo29/src/search.cpp` | `-p1` **from the repo root**, or `-p2` **from inside `forge-combo29/`** |
| seat 27's `job1/drawn_root_reporting.patch.txt` | `a/src/search.cpp` | `-p1` **from inside `forge-combo29/`** only |

Using one flag for both is what fails. Naively running `-p1` for both from inside `forge-combo29/` gives
`Skipping patch. 1 out of 1 hunk ignored` for seat 12's — **that** is what produced my "reverse order fails"
reading, not the order. **Check every `patch` exit code**; `patch` prompts/skips rather than half-applying, so a
script that ignores the code will believe it succeeded.

### The sequence (either order; this one is what I verified)

```bash
# working from a clean tree at base commit 6b98f217

# 1. seat 12's patch, from the repository root (its hunks name forge-combo29/src/...)
cd <repo-root>
patch -p1 < seat12/job1/two_doors_mate.patch.txt           # must exit 0

# 2. seat 27's drawn-root patch, from inside forge-combo29/ (its hunks name src/...)
cd forge-combo29
patch -p1 < seat27/job1/drawn_root_reporting.patch.txt     # must exit 0

# 3. the two other seat-27 patches are independent of that block; any order
patch -p1 < seat27/job2/clear_hash.patch.txt               # must exit 0
patch -p1 < seat27/job3/halfmove_clock.patch.txt           # must exit 0
```

**The reverse order works too** — my patch first from inside `forge-combo29/`, then seat 12's from the repo
root — and produces the same file. If you prefer a single working directory, run seat 12's with `-p2` from
inside `forge-combo29/` instead of `-p1` from the root; both are equivalent and both verified.

## What I verified myself (after seat 12's correction)

On a clean `6b98f217` archive, each patch at its own correct level:

| order | seat 12 exit | seat 27 exit | sha256 of `src/search.cpp` |
|---|---|---|---|
| seat 12 first, then mine | 0 | 0 | `24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671` |
| mine first, then seat 12 | 0 | 0 | `24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671` |

Both orders: **byte-identical**, matching seat 12's number. And `patch -p1` for seat 12 *from inside*
`forge-combo29/` fails with `1 out of 1 hunk ignored` — reproducing the trap, and confirming it is the flag and
not the order.

All of this is re-runnable, not prose — it prints every exit code:

```bash
bash forge-combo29/swarm/27/verify_patch_order.sh 6b98f217 \
     <seat12>/job1/two_doors_mate.patch.txt \
     forge-combo29/swarm/27/job1/drawn_root_reporting.patch.txt
```

Its output on my machine: ORDER A sha `24912a43…`, ORDER B sha `24912a43…`, `TRAP seat12 -p1 from INSIDE
forge-combo29 rc=1`, `TRAP seat12 -p2 from INSIDE rc=0`, verdict PASS.

### The tree sha256 and what it does and does not prove

| tree | forge sha256 |
|---|---|
| seat 12 + seat 27's three patches | `80b5e535fad4ea12305868198c4c4cc4994b9caec75113f617a59c95b5573507` |
| seat 27's three patches alone | `d3f1a40fbae0593e3da3ad56d55b9c5938e33e4876639f7172de1070dd7cb53a` |
| base `6b98f217` | `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83` |

A different compiler or flags gives a different exe hash — **the exe sha256 proves my builds matched each other,
not that yours is right. The source-file sha256 above and the assertion below are what prove the composition.**

### The one-position assertion a merger can run

```bash
bash forge-combo29/swarm/27/assert_composition.sh <path-to-your-forge>
```

Searches `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 60` (clock 100, White has **Ra8#**). Exit 0 = PASS:

| tree | bestmove | score | info lines | assertion |
|---|---|---|---|---|
| base, no patch | `f2f3` | cp 0 | 8, every pv **empty** | **FAIL** |
| seat 27's drawn-root patch **alone** | `f2f3` | cp 0 | **1** (was 8) | FAIL (seat 12's is not in — correct) |
| seat 12's patch (with or without mine) | **`a1a8`** | **mate 1** | 8, real pv | **PASS** |

On base the engine adjudicates the root as a fifty-move draw and returns `cp 0` with an empty pv, hiding a mate
in one. If your tree still says `f2f3`, seat 12's patch did not land. All three rows above were measured, not
inferred.

---

## The patches themselves

| # | file | what it changes | finding | applies |
|---|---|---|---|---|
| 1 | `job1/drawn_root_reporting.patch.txt` | a drawn root reports ONE `info depth 1` line instead of one per depth up to the limit | S-F1 | `-p1` from inside `forge-combo29/` |
| 2 | `job2/clear_hash.patch.txt` | `Searcher::clear_hash()` calls `worker->clear()` so `Clear Hash` also drops the move-ordering histories | S-F4 | `-p1` from inside `forge-combo29/` |
| 3 | `job3/halfmove_clock.patch.txt` | refuses a FEN half-move clock above 100 instead of clamping it to 65535 | S-C3 (seat 01's 01-F5/01-F8) | `-p1` from inside `forge-combo29/` |
| — | `job5/searchmoves_iir.PARTIAL.patch.txt` | **PARTIAL ONLY** — stops IIR firing at a `searchmoves`-restricted root; does **not** close S-F8 | S-F8a | `-p1` from inside `forge-combo29/` |

## Honesty numbers for every build named above

| build | bench 11 | bench 13 | bench 16 | perft 5 |
|---|---|---|---|---|
| required | 312866 | 862329 | 3024920 | 4865609 |
| base `e06310ec` | 312866 | 862329 | 3024920 | 4865609 |
| seat 27's three `d3f1a40f` | 312866 | 862329 | 3024920 | 4865609 |
| seat 12 + seat 27 `80b5e535` | 312866 | 862329 | 3024920 | 4865609 |

Raw: `honesty/`, `job6/honesty_all3/`, `job6/honesty_integ/`, `job6/honesty_final/`.

## What none of these patches does

- **No strength change is claimed or measured.** Patches 1 and 3 change reporting/validation; patch 2 changes
  what a GUI command clears. None alters the search's choice on a legal, undrawn position.
- **No speed change is claimed.** Node counts are identical on all four honesty checks.
- Patch 3 is seat 01's finding, not mine (S-C3); my contribution is the independent confirmation on the release
  build plus this patch.
- The composition result is **seat 12's finding plus my measurement** — they own the mate scan, and they found
  and corrected the instruction error described at the top of this file.
