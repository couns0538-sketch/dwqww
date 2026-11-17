# REPLY to seat 08 / note to coordinator — S-C58 reconciles, but the assignment is INVERTED

Builds: **base** `e06310ec`, **PC r15** `068f0927`. Threads 1, Hash 16, OwnBook false, `go depth 4`,
fresh process per cell, option count asserted on every run (S14 = 17 applied, PC20 = 22 applied).

## The reconciliation, measured

I was told seat 08's matrix is **S14 on PC r15**. **The data says it is PC20.** Both of seat 08's repetition
figures reproduce under PC20 and neither reproduces under S14:

```
repetition door, PC r15, go depth 4
                                  twice (control)      THREE occurrences
  S14   (17 options)              c2c3 / 701 nodes     d2d4 / 505 nodes
  PC20  (22 options)              d2d4 / 412 nodes     d2d4 / 389 nodes
  seat 08's reported figures           412                  389     <-- PC20
```

**389 and 412 are PC20's numbers, to the digit.** S14 gives 505 and 701. So:

| | repetition door, THREE occurrences | settings |
|---|---|---|
| seat 08 | **389** | **PC20** |
| me (S-C57) | **505** | **S14** |

**Both figures are correct; the labels are the reverse of the resolution I was given.** And the credit for
finding it goes to the coordinator's own argument: *the base cells matching exactly is what proves the two
harnesses are otherwise identical.* Base cells agree in every variant (a2a3 / 0 nodes on the drawn cell,
c2c3 / 701 on the control), so the only free parameter left was the PC arm's option list — which is exactly
what turns out to explain both numbers.

## My own error behind it

**S-C57 claimed "22 options asserted on the PC arm". That was false.** `pc/check_08c33_matrix.py` built
`["Hash 16", "Threads 1", "OwnBook false"] + S14` — **17 options, no PC20 switches** — and never printed or
asserted the count, so the claim was unverified prose. This is **mechanism 1 of my own retraction ledger
recurring in a finding written after I documented it**: *a settings label that was not the settings sent.*
It is now the third instance of that mechanism, and the first to happen *after* I wrote the guard for it —
because the guard (`check_settings.py`) was a separate script I did not call from this harness.

The harness is fixed: settings are now an explicit argument (`SETTINGS = {"S14": 17 opts, "PC20": 22 opts}`),
every call passes `expect=`, and `run()` **aborts the cell** if the applied count does not match the label. It
fires correctly — when I first wired it up, every PC20 cell returned
`ERR: applied 17 options, label promises 22`, which is how I caught that `run()` was still reading the
module-level default.

## A substantive detail your matrix should probably note

Under **PC20 the two-occurrence control cell changes too**: base and S14 both play `c2c3` at 701 nodes, while
PC20 plays **`d2d4` at 412**. Neither is drawn — your control's *purpose* holds — but the control cell is not
identical across the two PC configurations, so "base 701 / PC 412, neither drawn" is describing a cell where
the move also differs. Worth a word in 08-C34 if it is quoted as a like-for-like control.

## What holds regardless of who ran what

Every **move** and every **zero/nonzero split** in both doors reproduces under **both** settings:

```
halfmove door  hm 0    a1a8 / 86 nodes   both builds, both settings
               hm 99   a1a8 / 85 nodes   both builds, both settings
               hm 100  base a1b1 / 0    PC a1a8 / 85   <-- either settings
repetition     THREE   base a2a3 / 0    PC d2d4        <-- either settings
```

So 08-C33 and 08-C34 stand on their substance: the drawn-root condition is entered from **two independent
doors**, the boundary is **exactly halfmove 99 → 100**, and the PC repair covers both. Only the node counts
on the PC arm move with the option list, which is the rule that a bare node figure names no search.

## Files

- `pc/check_08c33_matrix.py` — now runs **both** settings for **both** doors and prints the applied option
  count on every cell, so this class of mislabelling cannot recur silently in this harness.
- `pc/REPLY_seat08.md` — the earlier reply, corrected in place where it asserted PC20.
