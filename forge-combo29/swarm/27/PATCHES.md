# Patches from seat 27 — and how to combine them with seat 12's patch without a silent miss

## READ THIS FIRST: the two patches touch the same block, and the path prefixes differ

Seat 12's `two_doors_mate.patch.txt` and my `job1/drawn_root_reporting.patch.txt` **rewrite the same block**
of `src/search.cpp` (the drawn-root adjudication around lines 2248–2270). They do compose, but only in one
order and only if each is applied from the right directory — **the two patch files use different path roots**:

- seat 12's hunks name `a/forge-combo29/src/search.cpp` → apply with `-p1` **from the directory that contains
  `forge-combo29/`**
- my hunks name `a/src/search.cpp` → apply with `-p1` **from inside `forge-combo29/`**

Get that wrong and `patch` prints `Skipping patch. 1 out of 1 hunk ignored` — it does *not* half-apply, so you
will not get a corrupted tree, but a script that ignores exit codes will think it succeeded. **Check the exit
code of every `patch` call.**

### The exact sequence (verified twice, sha256 reproduces)

From a clean tree at base commit `6b98f217`:

```bash
# 1. seat 12's patch FIRST, from the directory that CONTAINS forge-combo29/
cd <dir-containing-forge-combo29>
patch -p1 < seat12/job1/two_doors_mate.patch.txt          # must exit 0
#    (it also applies as -p2 from inside forge-combo29/, but -p1 from the parent is what I verified)

# 2. seat 27's drawn-root patch SECOND, from INSIDE forge-combo29/
cd forge-combo29
patch -p1 < seat27/job1/drawn_root_reporting.patch.txt    # must exit 0
#    patch reports: "Hunk #1 succeeded at 2275 (offset 19 lines)" — an offset, no fuzz, no failed hunk

# 3. the two other seat 27 patches are independent of that block and can go in any order
patch -p1 < seat27/job2/clear_hash.patch.txt              # must exit 0
patch -p1 < seat27/job3/halfmove_clock.patch.txt          # must exit 0
```

**Reverse order fails**: my patch first, then seat 12's, gives `1 out of 1 hunk ignored` because my change
removes the loop their hunk context expects. So: **seat 12 first, always.**

### Resulting tree, and the sha256 to compare against

Built with `cmake -DCMAKE_BUILD_TYPE=Release -DCMAKE_CXX_COMPILER=g++`, `cmake --build . -j4`:

| tree | forge sha256 |
|---|---|
| seat 12 + seat 27's three patches | `80b5e535fad4ea12305868198c4c4cc4994b9caec75113f617a59c95b5573507` |
| seat 27's three patches alone | `d3f1a40fbae0593e3da3ad56d55b9c5938e33e4876639f7172de1070dd7cb53a` |
| base `6b98f217` | `e06310eca3368556e8e1fc1526a86431272f90e3f5177422e3d47a1d7b316a83` |

A different compiler or flags will give a different sha256 — **the sha256 proves *my* builds were the same as
each other, not that yours is correct. The assertion below is what proves the composition took.**

### The one-position assertion a merger can run

```bash
bash forge-combo29/swarm/27/assert_composition.sh <path-to-your-forge>
```

It searches `6k1/5ppp/8/8/8/8/5PPP/R5K1 w - - 100 60` — a fifty-move-clock root (clock 100) where White has
**Ra8#**. The three states are cleanly separated:

| tree | bestmove | score | info lines | assertion |
|---|---|---|---|---|
| base, no patch | `f2f3` | cp 0 | 8, every pv **empty** | **FAIL** |
| seat 27's drawn-root patch **alone** | `f2f3` | cp 0 | **1** (was 8) | FAIL (correctly: seat 12's is not in) |
| seat 12's patch (with or without mine) | **`a1a8`** | **mate 1** | 8, real pv | **PASS** |

So `PASS` means seat 12's mate scan is in and the search really ran; the `info lines` figure tells you whether
my reporting change is in as well when you run it on a drawn root with no mate available. Exit code is 0 on
PASS and 1 otherwise — wire it into your merge script and ignore the sha256 if you like.

**Why the clock-100 case is the right canary:** on base the engine adjudicates the root as a fifty-move draw and
returns `cp 0` with an empty pv, hiding a mate in one. Seat 12's patch scans the children for a mate before
trusting the claim. If your tree still says `f2f3`, their patch did not land.

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
- The composition result is **seat 12's finding plus my measurement** — they own the mate scan; I only verified
  the two do not collide.
