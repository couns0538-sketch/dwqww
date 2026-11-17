# Confirming S-C84: an illegal FEN makes the engine search the previous position (S-C58)

Seat 27's `S-C84` claims three things: an illegal FEN is **diagnosed**, the engine then **searches anyway**, and what it
searches is **whatever was last set successfully** — so a harness with one malformed FEN records a duplicate row that
looks like a genuine measurement. This confirms all three on my own harness, with a discriminator they did not state, and
adds one refinement that makes their consequence worse.

## The discriminator

Their report notes the previous-position behaviour. The experiment that **rules out the alternatives** is to run the
*same* illegal FEN after two *different* valid positions:

| model | predicted invalid-FEN answer |
|---|---|
| a startpos fallback | the same answer both times |
| a refusal | no `bestmove` at all |
| **previous position (their claim)** | **each predecessor's own answer, differing between sessions** |

Invalid FEN: `8/8/8/3kK3/8/8/8/8 w - - 0 1` (adjacent kings). `go depth 8`, Threads 1, Hash 16, OwnBook false.

| preceded by | predecessor's answer | invalid-FEN answer | info string |
|---|---|---|---|
| **A**: `6k1/5ppp/8/8/8/8/5PPP/R5K1 w` | `a1a8`, **mate 1** | **`a1a8`, mate 1** | `invalid FEN: kings may not be adjacent` |
| **B**: `rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b` | `e7e5`, **cp −16** | **`e7e5`, cp −25** | `invalid FEN: kings may not be adjacent` |

**`a1a8` after A and `e7e5` after B.** The answers follow their predecessors and differ from each other, which is
exactly what a startpos fallback could not do. **Reproduced bit-identically three times on PC r15, and identically on
base `release`** — so it predates the PC patch, as they said.

## The refinement that makes it worse than they stated

They say a harness "records a DUPLICATE ROW". **In case A the row is a perfect duplicate; in case B it is not** — the
score differs (`cp −16` → `cp −25`) while the bestmove is identical.

**That asymmetry matters, and it points the wrong way:** a row keyed on `(fen, bestmove)` is a duplicate, but a row keyed
on `(fen, bestmove, score)` **looks like a fresh measurement** — a different score for a different FEN is what a real
measurement looks like. So in the case where the score differs, the fabricated row is *harder* to detect, not easier.

Why the score moves at all: the search re-runs on the restored board with a different transposition/history state, so the
same position searched twice can report a different score. That is normal search behaviour and it is what disguises the
error.

## What this adds to the record

`S-C84` is now **independently confirmed**, on a different harness, a different FEN set, and with a discriminator that
separates "previous position" from "startpos fallback" and from "refusal". The three-part claim holds on both builds:

1. diagnosis emitted — **yes**, one `info string`;
2. search proceeds anyway — **yes**, a normal `bestmove` with a full PV;
3. **the searched position is the predecessor** — **yes**, proven by the A/B contrast.

**And the harness consequence is worse than a duplicate:** a row that differs in the score column cannot be found by
deduplicating on `(fen, bestmove, score)`. **The reliable detector is to check that every FEN you sent was accepted** —
which is the `REFUSED_FEN_TRAP_AND_GUARD.md` rule in this same folder: *`readyok` is not a statement about the position.*

## What I am not claiming

* Not that this is a defect in the *engine's* judgement — it diagnoses correctly. It is a defect in what it does **after**
  diagnosing, and the harness consequence is the reason it matters.
* Not that seat 27 missed the score case; their row says "duplicate row", and my contribution is that the duplicate is
  sometimes *not* exact, which makes it worse rather than contradicting them.
