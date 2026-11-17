# Why the base cells matching is a stronger argument than it first looked

Seat 27. Builds: **base** `e06310ec`, **PC r15** `068f0927`. `go depth 4`, Threads 1, Hash 16, OwnBook false.

## The argument as it was made

When reconciling the 389/505 node discrepancy with seat 08, the argument that settled it was: *the base cells
agree exactly (a2a3/0 and c2c3/701), so the two harnesses are otherwise identical, and the only free parameter
is the PC arm's option list.* That was right, and it located the answer.

**But the reason it works is stronger and more specific than "base is base", and it is worth stating because it
bounds what such an agreement can prove in general.**

## The actual mechanism

The base build **does not advertise the PC20 options at all**:

```
base build, setoption name CuckooRep value true
  -> "option 'CuckooRep' not advertised"
```

So a PC20 option list cannot be applied to the base build — it is refused outright. Which means:

- **The base cells cannot differ because of the PC20 switches**, by construction, not merely in practice.
- **The base cells matching therefore rules out every difference that is expressible as a PC20 switch.** What
  it does *not* rule out is anything the two harnesses could both do — a different `go` command, a different
  depth, a different Hash, a different board. Those are ruled out by the cells matching only if the harnesses
  agree on them, which is a separate claim.

So the agreement is a **strong** argument about one specific axis (the PC switches) and a **weak** argument
about the rest. Stated precisely:

> **A cell that is invariant across the configurations under test proves those configurations differ nowhere
> that the invariant cell can see.** It is exactly as strong as the cell's sensitivity, and no stronger.

The base cells are insensitive to PC20 *by construction*, so they are a perfect control **for PC20** — and only
for PC20. If the two harnesses had also differed in Hash size, the base cells would have agreed anyway at
`Hash 16` vs `Hash 16`, and would have disagreed at `Hash 16` vs `Hash 1024` only if the position were
hash-sensitive at depth 4. The control would have been silent about a difference in a parameter the cell does
not respond to.

## What this changes in the reconciliation

Nothing about the conclusion — seat 08 is PC20, mine was S14, and the four measured cells settle it. What it
changes is the **confidence statement**: the base-cell agreement is decisive *because and only because* the PC20
switches are the sole remaining free parameter, which I established by measuring them, not by reasoning that
"base is base".

## The general rule for a control cell

A control cell earns its name only when you can say **what it would have looked like had the difference been
present**. Here:

- would the base cell differ under S14 vs PC20? **It cannot — the options do not exist there.** (Strongest
  possible: a structural impossibility, not an empirical observation.)
- would the base cell differ under Hash 16 vs Hash 1024? **Unknown — not measured, and it need not.**

**So when quoting a control cell, say which axis it controls for.** "The base cells agree" is a complete
argument about the PC switches and an incomplete one about the harnesses.

## Files

- `pc/check_08c33_matrix.py` — runs both settings on both doors, asserts the applied option count per cell, and
  will now report the base build's refusal rather than a None count.
- `pc/REPLY_seat08_settings.md` — the reconciliation itself.
