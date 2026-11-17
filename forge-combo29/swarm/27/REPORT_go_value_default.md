# A FIFTH SHAPE: an unparseable `go` VALUE is replaced by a default, silently

Build: **PC r15** `068f0927`, Threads 1, Hash 16, OwnBook false, startpos, **fresh process per cell**.
Cap 6 s, with `RETURNED` (the engine answered on its own) distinguished from `CAPPED` (my timeout).

## The finding

Every `go` command whose **value** cannot be parsed lands on **the same result**, with no message:

```
command              verdict   depth  nodes   secs   diagnostic
go depth 8           RETURNED  8      4099    0.0    NONE      <- well-formed reference
go depth abc         RETURNED  5      1001    0.0    NONE
go depth             RETURNED  5      1001    0.0    NONE
go nodes abc         RETURNED  5      1001    0.0    NONE
go nodes             RETURNED  5      1001    0.0    NONE
go movetime abc      RETURNED  5      1001    0.0    NONE
go movetime 0        RETURNED  5      1001    0.0    NONE
go wtime abc         RETURNED  5      1001    0.0    NONE
```

**Six different malformed requests produce one identical, plausible search: depth 5, 1,001 nodes, 0.0 s, a legal
bestmove, and nothing on the wire.** A harness reading these rows cannot tell `depth abc` from `movetime 0` from
`wtime abc`, and none of them did what was asked.

## Three distinct behaviours, only one of which speaks

| input class | what happens | says anything? |
|---|---|---|
| **unparseable value** (`depth abc`, `movetime 0`, `wtime abc`) | value becomes a default; a short default search runs | **no** |
| **unknown token** (`go depth 8 zzzz 3`) | token discarded; the well-formed parts proceed normally (`4099` nodes, identical to `go depth 8`) | **no** |
| **`depth 0`** | `std::clamp(0, 1, 64)` = **1**; a legal one-ply search | no |
| **`searchmoves` with only illegal moves** | `info string searchmoves restriction…` | **yes** — the only one |

**`searchmoves` is the exception that proves the rule is not universal:** the parser *can* report a problem, and
does, in exactly one place. So the silence elsewhere is a choice of the code, not an absence of capability.

## Mechanism, from source

`src/uci.cpp:parse_limits` matches each token with `if / else if` and **has no else branch** — an unrecognised
token falls through and is discarded. Values are read by `read_int()`, which returns **0** when `from_chars`
fails, and `depth` is then `std::clamp(0, 1, 64)`. For `nodes`/`softnodes`, `nodes_specified` is only set when
the parse **succeeded**, so a malformed count leaves **no limit at all** rather than a zero one — which is why
`go nodes abc` runs a bounded default search instead of the unbounded one that reading "0 nodes" would predict.

## This is the fifth shape, and it is different from the other four

| shape | what the protocol says | what the output looks like |
|---|---|---|
| `bestmove 0000` | nothing | a move that is not a move |
| empty `info depth` | nothing | a search that searched nothing |
| refused FEN → previous position | one `info string`, then a full search | a normal result for the wrong board |
| ignored `go` token | nothing | a normal result for a different limit |
| **unparseable `go` value** | **nothing** | **a normal result for a DEFAULT limit** |

**The new one is the only shape where the engine substitutes a *value* rather than a *position* or a *token*.** All
four previous shapes replace something the caller named; this one replaces the number the caller named with a
number of its own, and the two are indistinguishable in the output. `depth abc` and `depth 5` produce identical
`info depth` lines — so a harness cannot recover the difference even in principle.

**And the practical harm is the same class as S-C107:** two experiment arms silently becoming one. A harness that
built `go depth %d` from a variable that sometimes held `""` would run depth-5 searches in one arm and real
depths in the other, with no error and no way to detect it after the fact.

## Correction to my own first attempt, kept because it is the same error as the rest of tonight

My first matrix reported **`go depth 123` → depth 26** and **`btime 1000` → depth 26**. Those were **my 8-second
cap**, not engine behaviour: with a longer cap the same command reaches depth 29 in 49 s and is still searching.
**A depth column measured under a timeout is a column of my patience.** The table now reports `RETURNED` versus
`CAPPED` separately, which is why no row above says 26 for a legitimate command.

## Limits

- **One build** (PC r15) and **startpos only**. The values are parser-level, so the behaviour should be
  identical on base and on any position; I did not verify either.
- `go depth 123` was not run to completion (it would take minutes). Its behaviour is "runs as asked", supported
  by reaching depth 29/32 without complaint; it is the one malformed-*looking* command here that is actually
  well-formed.
- `movestogo`, `mate`, `ponder` and the `*inc` tokens were not tested individually. They share the same parser
  path, so the expectation is that they behave like `wtime`, but that is inference, not measurement.

## Files

- `pc/go_grammar_matrix.py` — the matrix, with a `RETURNED`/`CAPPED` distinction and two controls (a
  well-formed reference must reach its depth; an unknown token must not change it).
- `out19c46/go_grammar_matrix.txt` — the transcript.
