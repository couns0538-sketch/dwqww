# Settings-list audit (why every grid now asserts its own list)

## The fault, three times
Building a "PC20" option list by hand and getting it wrong, so that a whole grid measured a different
regime while labelling itself PC20. Every instance produced a **plausible wrong number**:

| # | script | what it claimed | what it sent | consequence |
|---|---|---|---|---|
| 1 | job17/timealloc.py | PC20 | 6 options (no S14) | doubled the allocation figure: 457 ms where the truth was 145 ms |
| 2 | job11/depthcap.py | PC20 | 4 options (no S14) | conclusions unchanged when re-run (structural finding), but the label was wrong |
| 3 | job17 (first attempt) | PC20 | same as #1 — the same file, caught by bisecting a 2x | see #1 |

## The fix: one definition, asserted, imported
`lib/settings.py` now holds `BASE`, `S14`, `PC6`, `PC20` and asserts at **import** time:
- `len(S14) == 14`, `len(PC6) == 6`, `len(PC20) == 22`;
- no duplicate option name in PC20;
- **membership**: PC20 must contain all 14 S14 names and all 6 PC6 names plus Threads and Hash — a
  length check alone would pass a list that swapped one entry for something else.

Scripts import it (`from settings import PC20`) instead of retyping the list, and `check(opts,
expect_len, must_include)` is available for a script that builds its own. `describe(opts)` returns a
report-ready one-liner so a report can state exactly what was sent.

## Audit of every script in this folder (2026-11-16)
Checked each file's quoted option names against the canonical 22:

| script | names | claims PC20 | verdict |
|---|---|---|---|
| job4/divide_perft4.py | 22 | yes | complete |
| job5/softnodes.py | 22 | yes | complete |
| job6/divide_perft4.py | 22 | yes | complete |
| job7/pcpath.py | 22 | yes | complete |
| job8/clockpath.py | 22 | yes | complete |
| job9/mates_run.py | 22 | yes | complete |
| job9/negative_mates.py | 22 | yes | complete |
| job10/underreport.py | 22 | yes | complete |
| job12/options_wired.py | 22 | yes | complete |
| job13/book_quality.py | 22 | (no) | complete (uses S14 + PC6) |
| job17/timealloc.py | 22 | yes | complete after fix |
| pcbuild/check_pcbuild.py | 24 | yes | complete (deliberately includes per-regime extras) |
| **job11/depthcap.py** | **4** | **yes** | **WAS SHORT — fixed to import canonical PC20, re-run, conclusions held** |

Scripts with 3–7 options that do **not** claim PC20 (clamp.py, control_*, drawroot.py, pcfixes.py,
loneking.py) are not faults: they deliberately use a minimal regime, and their reports say so.

## The rule
**A settings list is not evidence of what was sent; only its length and membership are.** Assert both
before any grid runs, and prefer importing one definition to retyping it. Two of my three instances would
have been caught by a single `assert len(...) == 22`.
