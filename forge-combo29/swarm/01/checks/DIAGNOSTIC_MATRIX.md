# The four-case matrix, measured — and the absolute it refutes (S-C60)

A claim reached me for the record: *"a fresh session gives no diagnostic"*, with a request to retract it. **I measured the
matrix instead of filing either version, and the claim is not mine and not true.**

## The matrix

Two things could plausibly move the invalid-FEN diagnostic: whether `isready` is sent between `position` and `go`, and
whether a predecessor position was set. Four cells, plus a **legal control in each** — because without the control, "no
diagnostic in case 1" would be indistinguishable from "the diagnostic never fires in this shape".

`go depth 6`, Threads 1, Hash 16. Invalid FEN `8/8/8/3kK3/8/8/8/8 w` (adjacent kings); control `6k1/5ppp/8/8/8/8/5PPP/R5K1 w`.

| case | isready? | predecessor? | **invalid: diagnostic?** | invalid: bestmove | control: diagnostic? | control: bestmove |
|---|---|---|---|---|---|---|
| 1 | no | no | **YES** | `d2d4` | no | `a1a8` |
| 2 | no | yes | **YES** | `a1a8` | no | `a1a8` |
| 3 | yes | no | **YES** | `d2d4` | no | `a1a8` |
| 4 | yes | yes | **YES** | `a1a8` | no | `a1a8` |

**The diagnostic appears in all four cases and never for the legal control.** Neither the handshake nor a predecessor
changes it — so *"a fresh session gives no diagnostic"* is **untenable**: a fresh session with no `isready` **is** case 1,
and it diagnoses.

## What the bestmove column adds

The diagnostic is constant; **the searched board is not**:

| condition | answer | what was searched |
|---|---|---|
| no predecessor (cases 1, 3) | `d2d4` | **startpos** |
| predecessor set (cases 2, 4) | `a1a8` | **the predecessor** |

So there are **two fallbacks, not one**: startpos when nothing was ever set, and the previous position when something
was. That is a refinement of `S-C84`, which described only the predecessor case because that is what it tested.

**A harness artifact I caught while pinning this down.** My first attempt to identify the startpos answer gave `a2a3`,
which did not match case 1's `d2d4`, and I nearly wrote it up as *a third fallback behaviour*. Re-running with the same
preamble the matrix uses (`setoption`, `ucinewgame`) gave `d2d4`. **The difference was my harness, not the engine** — the
`a2a3` run omitted `ucinewgame`, which is a different state. Third time tonight that a discrepancy I was about to report
turned out to be my own instrument.

## The record correction, stated precisely

The request was to record four cases **and** retract an absolute. I have recorded the four cases, measured on this
build. **There is no absolute to retract on my branch**: searching it for a claim that a fresh session gives no
diagnostic finds none, and every diagnostic statement I have made says the opposite — that an invalid FEN **is**
diagnosed, which is `S-C84`'s part 1 and my `S-F1`/`S-C59` observations.

**The finding ID quoted to me (`S-C93`) is not mine**; my highest is `S-C59`. So the absolute belongs to whoever wrote
`S-C93`, and the retraction belongs there too. **What my branch contributes is the measurement** — all four cells, with
a control, which is what makes either version testable.

## What I am not claiming

* Not that `S-C93`'s author was wrong about what they measured. Their matrix may differ on their build or their
  preamble; what I can say is that **on my build, with this preamble, the diagnostic is unconditional**, and I measured
  the four cells rather than assuming.
* Not that the diagnostic's presence means the answer is usable — `S-C84` shows it is not. The diagnostic is constant and
  the board is wrong, which is precisely why it is unsafe: **a reader who treats a diagnostic as "refused" is wrong, and
  so is one who treats silence as "fine".** (`S-C59`'s inversion.)
