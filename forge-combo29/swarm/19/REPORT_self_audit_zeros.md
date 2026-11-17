# Self-audit of my own null-shaped claims — the sweep, its results, and the one real gap it found

seat 19 · area 9 · done because I had applied Rule 1 to seat 08's zero and then asked whether my own zeros met it.

## 1. The three lines

**What I did.** Classified every finding I had made into **positive claims** (a number measured as non-zero) and
**null-shaped claims** (asserting absence, sameness, "not faster", "0 of N", "identical", "unchanged"), then asked
of each null: **is there a case where this measure SHOULD have shown a difference?** That is Rule 1 applied to
myself, systematically rather than one finding at a time.

**The result.** **58 F-findings; 15 null-shaped. Four of those 15 needed a plant and did not have one.** Three have
now been planted (§3), and **the fourth — 19-F9's null — was a real gap that I would not have found by fixing them
one at a time.**

**How sure.** Certain of the classification (it is a mechanical pass over my own `FINDINGS.md`); the judgement
calls are §4, stated so a reader can disagree with any of them.

## 2. What the sweep found

| category | count | needs a plant? |
|---|---|---|
| positive claims (a non-zero number was measured) | 43 | no — the number existing is its own evidence |
| null-shaped claims | 15 | **only if they assert an absence** |
| → of those, real absences | **4** | **yes** |
| → of those, counts/refutations mis-flagged by my own filter | 11 | no |

**The four real absences and their state:**

| finding | null claim | plant status |
|---|---|---|
| **19-F54** | "0 of 40" worse-result positions | **planted** (19-C29): same code returns `False` for the mating move and `True` for a legal non-mate |
| **19-C26** | "40 of 40 identical" at Threads 1 | **planted** (19-C30): Threads 4 gives **12 of 12 differing**, so the comparator sees differences |
| **19-F9** | "not measurably faster" | **planted** (19-C31): a `go depth 16` workload gives **Threads 4 = 0.765× Threads 1**, a 23.5 % speedup, detected |
| **19-F19** | "never refreshes a generation" | **withdrawn** with 19-F18 (warm-state artifact) — no plant needed, the finding is gone |

**11 were false alarms of my own filter** — e.g. 19-F17 ("pins are stable across compilers") is a *measurement of
equality* whose contrast is the `stable_sort` finding that moves them; 19-F22/F23 contrast warm vs cold
explicitly. My regex flagged "identical" without checking whether the line also cited a differing case.

## 3. The four plants, and what each cost

| plant | the contrast case | what it bought |
|---|---|---|
| 19-C29 (F54) | one mating move among 18; same code: `False` for the mate, `True` for a non-mate | the 0-of-40 means "not shown to be wrong", not "blind" |
| 19-C30 (C26) | Threads 1 → 0/12 differ; **Threads 4 → 12/12 differ** | the 40-of-40 is a measurement, and independently confirms the Threads rule |
| 19-C31 (F9) | `go depth 16`: Threads 1 154 ms vs Threads 4 117 ms = **0.765** | the null means "below resolution", not "method blind" |
| (none) F19 | withdrawn | — |

## 4. The instructive failure inside the F9 plant

My **first** positive control for F9 used `bench 13` at Threads 1 vs 4: **344 vs 340 ms, ratio 0.988, NOT
detected.** Read naively that says "the timing method cannot detect a 24 % difference" — **which is false.**

The cause is 19-F37's finding applied to the control itself: **`bench` constructs its own `Searcher(16)`, so the
`Threads` option never reaches the bench searcher.** A positive control must use **a workload the setting actually
affects**, which for Threads is a `go` search, not `bench`.

**Had I stopped at the first attempt I would have recorded a false negative about my own instrument.** That is the
same error shape as trap 11 — trusting a measurement whose subject was not actually being measured — and it is
why the failed attempt is kept in `checks/f9_posctrl/RESULT.txt` beside the successful one.

## 5. What the sweep says about the method

**Doing this systematically found a gap that fixing them one at a time did not.** The three I had already planted
were the ones I noticed because they were prominent ("0 of 40", "40 of 40"); F9's null was a *soft* claim —
"not measurably faster" — which reads like a conclusion rather than a zero, and so escaped the Rule 1 question
entirely.

**That is the generalisable bit: soft nulls hide better than hard zeros.** "0 of 40" announces itself as an
absence; "not measurably faster" sounds like a finding. The sweep is what separates them.

### What I did NOT do

- I did not re-examine the 43 positive claims for plants — by definition a measured non-zero number is its own
  evidence that the instrument responds.
- I did not plant the 11 filter false-alarms individually; §2 explains why each already carries its contrast.

## 6. Files

`checks/plant19f54/`, `checks/f24_31_ctrl/`, `checks/f9_posctrl/` (including the failed first attempt), and this
report.
