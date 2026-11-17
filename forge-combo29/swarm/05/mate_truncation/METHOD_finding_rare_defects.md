# METHOD NOTE: to find a defect like the mate-PV truncation, follow a known violation — do not sample

Seat 05, area 5. This is the most transferable thing I learned tonight, and it applies to any rare defect in any seat's
area. It is written plainly because it cost me two wrong findings before I understood it.

## Say it plainly

**Every real instance of the mate-PV truncation I found came from taking a position that already violated the rule and
varying ONE thing. None came from sampling positions at random.**

The five instances, and how each was found:

| instance | how it was found |
|---|---|
| G/192 (`8/8/1p6/8/p3p3/8/2Kpk3/8 w`) | scanning a fixed 353-position G set at depth 12 — the one violation in 553 positions |
| R/120 | the same scan on a fresh 200-position random set — 1 in 200 |
| G/59 at softnodes 2000 | re-searching a position that already carried a mate score, at the self-play budget |
| the S-F58 board (`r2r4/pB2kpp1/…`) | screening 400 positions *for long mates only*, then varying the budget |
| seat 15's 15-F9 | given to me as a position that violates, then varying build and settings |

Not one of them came from "run 500 positions and count violations". The counting version is what produced my two
sampling errors (S-F57's false zero, S-W8's inconclusive rate).

## The sampling numbers, beside it

Why counting does not work — measured on PC r15 + PC20, Threads 1, Hash 16, OwnBook false:

| what was sampled | size | positions that could even show the defect |
|---|---|---|
| random-play positions at depth 12, looking for \|N\| ≥ 6 | 600 | **6** (and all 6 were consistent) |
| random-play positions at depth 14, looking for \|N\| ≥ 8 | 400 | **2** |
| G-set positions at depths 12 / 14 / 16 | 60 each | **1 / 1 / 2** mate scores |

The defect needs a position that (a) carries a mate score at the depth searched and (b) has a *long* mate, so that 2N−1
exceeds what that depth can carry. Both conditions are rare, and the numbers say how rare:

- **a mate score at all:** 1–2 of 60 G positions at depths 12/14/16, i.e. roughly **1 in 30 to 1 in 60**;
- **a long mate (|N| ≥ 8)**: **2 of 400** random-play positions at depth 14, i.e. about **1 in 200**.

So a sample of a few hundred gives a handful of mate scores and almost no long ones. A "0 violations" from such a sample
is a statement about the sample, not about the engine — which is exactly how S-F57's false zero and S-W8's inconclusive
rate arose.

## What to do instead

1. **Find one violation.** Scan a fixed set once (that is how G/192 surfaced), or take one from another seat.
2. **Vary one variable at a time** and watch whether the violation persists:
   - depth (this produced S-F27: only long mates, |N| ≥ 10)
   - the budget type (this produced S-F62: `go nodes 50000` truncates where `go movetime 50` at the *same depth* does not)
   - the settings (this produced S-F29 and S-C21: PC20 shrinks the window and closes 15-F9 entirely)
   - the build (S-F17: the truncation appears on base and PC builds alike under S14)
3. **Re-check the same position at a bigger budget** to see whether the score was merely unstable (S-F28: G/192's `mate
   −12` becomes `−4` by depth 24).
4. **Only then** say something about rates — and say what the sample could and could not contain.

## The general form

This is not specific to mates. Any defect that needs a *rare precondition* (a long mate, a specific FEN shape, a
particular option combination, a terminal root) is found by constructing the precondition first and varying one thing
after. Sampling tests the prevalence of the precondition, not the behaviour behind it — and a zero from a sample that
never met the precondition is the vacuity trap wearing different clothes: it is a verdict about an empty set.

Seat 16's `CHECKER_RULE.md`-adjacent lesson is the same one: a zero counts only when the harness could have produced a
non-zero. Here the equivalent is **a rate counts only when the sample contained the precondition.**

---

# Second method: the pipe-in-markdown trap (a defect class, not a one-off)

**This is the same class of fault three separate seats hit tonight, so it belongs here rather than as five repaired rows.**

## What happened to me

Five of my FINDINGS rows were structurally broken and I did not notice, because the tables LOOKED fine in the raw text:

- the `|N|` notation (meaning "the absolute mate distance") contains pipe characters, and in a markdown table a `|` is a
  cell separator;
- my node ladder used `|` as an inline separator between ladder steps inside a single cell — also a cell separator.

Either one splits a row into the wrong number of columns. A reader (or a parser) then sees the finding's text in the
wrong field, or the table stops rendering at that row.

## Why checking was harder than it looked

My first check was `awk -F'|' 'NF>9'`, which counts EVERY pipe including escaped ones — so it flagged two rows that were
already correct and I briefly believed I had more damage than I did. The correct check counts only **unescaped** pipes:

```python
import re
from collections import Counter

def column_count(line):
    return len(re.findall(r'(?<!\\)\|', line))   # unescaped pipes only

for path in ('FINDINGS.md',):
    rows = [l for l in open(path) if l.startswith('| S-')]
    counts = Counter(column_count(r) for r in rows)
    print(path, 'column counts:', dict(counts))
    best = counts.most_common(1)[0][0]
    for r in rows:
        if column_count(r) != best:
            print('OUTLIER ROW:', column_count(r), r[:90])
```

The important part is the counter: `(?<!\\)\|` matches only pipes that are **not** already escaped. Run it over
any table you write; every row should show the same count. (I keep `\|` in the regex because a raw `| ` inside a cell
is exactly the defect.)

## The rules I now follow

1. **Escape literal pipes inside a table cell** as `\|` — so `|N|` becomes `\|N\|`.
2. **Never use `|` as an inline separator** inside a table cell. I switched the node ladder to `·`.
3. **Verify with an escaped-pipe-aware counter**, not `awk -F'|'`.
4. **Treat the table as a data format**: a row with the wrong column count is a defect in the deliverable, exactly as a
   missing value is a defect in a measurement.
5. **Re-run the check after every EDIT, not only when writing.** I broke a clean file twice: once when I first wrote the
   `|N|` notation, and again later when I edited a *different* row and re-introduced a literal `|` in the process. A
   check you run once is a check that goes stale; put it in the same breath as the edit.

## The general form

This is the vacuity trap's cousin: **a structure that silently accepts malformed input**. A markdown table renders
whatever it is given, a JSON loader accepts a missing key as `undefined`, a CSV parser shifts columns. In each case the
failure is silent and the output looks plausible — which is why the fix is not "be careful" but "count the columns",
the same way the fix for a missing measurement is "raise on absence" rather than "compare against a sentinel".

Seat 16's own audit found three forms of the vacuity bug; this is the formatting-side analogue, and the repair is the
same in spirit: make the check explicit and loud rather than trusting that it looks right.

---

# Third method: replay the line — prove it, do not infer it

**Adopted after seat 15 used it to upgrade my S-F63 from an inference to a proof.**

## The two tests, and why one is better

| test | what it establishes | what it assumes |
|---|---|---|
| compare the PV's ply count against 2\|N\|-1 | the PV is *long enough* for the score it sits beside | that "long enough" implies "is a mate" — it does not |
| **replay every PV move in python-chess** | the line **does or does not end in checkmate**, and at which ply | only the rules of chess |

The second is strictly better. A PV of exactly 2N−1 plies could still not be a mate (wrong move, stalemate instead of
mate, a move illegal in the position). A PV shorter than 2N−1 that replays into checkmate is, by contrast, a mate
delivered early — a different finding. Counting plies measures the *shape* of the evidence; replaying it measures the
thing itself.

## What it showed on my own cases

| board | budget | score | PV | replayed verdict |
|---|---|---|---|---|
| S-F58 board `r2r4/pB2kpp1/…` | 50,000 | mate +11 (promises 21 plies) | 18 plies, all legal | final position **NOT checkmate** |
| same | 80,000 / 250,000 | mate +7 | 13 plies | **mates at ply 13** exactly |
| G/192 `8/8/1p6/…` | 20,000 | mate −7 (promises 14) | 10 plies, all legal | final position **NOT checkmate** |
| same | 30,000 / 50,000 | mate −4 | 8 plies | **mates at ply 8** |

Note the useful side-effect: the replay also proves the PV is *legal* (each move was accepted by python-chess in the
position it was played). So one test answers both "is this line playable" and "does it deliver the mate".

## The general form

This is the same instinct as the house rule in `CHECKER_RULE.md`: **do not accept a proxy for the thing when the thing
itself is checkable.** A ply count is a proxy for "is a mate"; a sanitizer symbol count is a proxy for "is instrumented";
a parsed number is a proxy for "was measured". In each case the proxy is cheap and usually right — and the case that
matters is the one where it is not.

`replay_pv.py` in this folder does it; it is 100 lines and takes an engine, a FEN and a list of budgets.

---

# Fourth method note: the even-count median bug (a silent upward bias)

**One line, because it changed two published numbers and the error is invisible unless you look for it.**

`sorted(values)[len(values) // 2]` is **not** the median for an even-length list — it returns the upper of the two middle
values, which biases the result **upward** by construction whenever the data are spread. Mine turned 5.5 cp into "6 cp"
and 52.5 cp into "69 cp" in S-F65. The correct form:

```python
vals = sorted(v for v in values if v is not None)
n = len(vals)
median = vals[n // 2] if n % 2 else (vals[n // 2 - 1] + vals[n // 2]) / 2.0
```

Why it matters here specifically: every one of my tables reports a median over 4, 8 or 50 runs, and **even counts are the
common case** (5 runs per cell but 4 or 8 positions per class). A biased median in a report that compares medians across
two classes can move a conclusion. It did not change my direction, but it did move the middlegame figure from 52.5 to 69,
which is a third of the way to the value a reader might then compare against another seat's 12 cp.

The general lesson is the same one as the vacuity trap: **a helper that returns a plausible number for the wrong reason
is worse than one that raises.** A median function given an even list should either take the mean or refuse — never
silently pick one of the middle two.

---

# Fifth note: a clean-looking split can be a sampling artefact — test the discriminator, not the correlate

**S-F70 reported "every gained mate with |N| <= 14 delivered, every one with |N| >= 15 did not — 12 labels, no overlap."
A deliberate probe refuted it in one run.**

The probe hunted 600 sparse KR/KQ positions for gained labels with |N| in {13,14,15,16} and found 11. The result:

- |N| = 13: 1 of 1 delivered; |N| = 14: 2 of 2; **|N| = 15: 4 of 6**; |N| = 16: 2 of 2.

So |N| does not separate at all — |N| = 15 straddles. What DOES separate, exactly, is **whether the printed PV is
complete relative to 2|N|-1**: 9 complete PVs, 9 delivered mates; 2 short PVs, 0 delivered. 11 of 11.

Two lessons:

1. **A gap at 14/15 in pooled data is not a boundary.** I had written "not a proven threshold" — which was the right
   hedge — but I still let the shape of the data suggest a mechanism (mate distance) when the actual mechanism was one
   variable further back (PV completeness). The mate distance correlates with the defect only because long mates are
   likelier to be truncated.
2. **Test the discriminator directly.** |N| was a correlate I could sort by; PV completeness was the thing itself. When
   two variables are available, the one that perfectly predicts the outcome is the finding, and the one that only mostly
   predicts it is a shadow.

This is the third time in this session that sorting data by a plausible variable produced a tidy pattern that a targeted
probe then dissolved. The pattern: a tidy split from a small pooled sample should be treated as a HYPOTHESIS to attack,
not a result to report — which is exactly what the coordinator asked for when they called the 14/15 gap "the one number
in your result that has no second sample".
