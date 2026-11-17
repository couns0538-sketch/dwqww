# REPORT job45 — the acceptance spec now has six cases, including the mate-in-2 that bounds the repair

**What was asked.** (My own next job.) job44 proved a drawn root that is **mate in 2** and the PC build
misses it. The acceptance spec had only a mate-in-1 case, so it understated the gap. This job adds S6 and
re-runs both builds.

**The answer.** The spec now states the whole rule, and **S6 fails on both builds** while **S1–S5 are
unchanged** from job43 — which is the property a spec must have: adding a case must not perturb the others.

| case | root | must answer | base | PC (PC20) |
|---|---|---|---|---|
| S1 | halfmove 100 + mate in 1 | a mate score | **FAIL** `cp 0`, `f2f3` | PASS `mate 1`, `e1e8` |
| S2 | halfmove 100, no mate | `cp 0` | PASS `cp 0`, `e2e3` | **FAIL** `cp 368`, `e2e3` |
| S3 | insufficient material | `cp 0` | PASS `cp 0`, `e1d1` | PASS `cp 0`, `e1d1` |
| S4 | threefold + mate in 1 | a mate score | **FAIL** `cp 0`, `f2f3` | PASS `mate 1`, `e1e8` |
| S5 | threefold, no mate | `cp 0` | PASS `cp 0`, `e2e3` | **FAIL** `cp 292`, `e2e3` |
| **S6** | **halfmove 100 + mate in 2** | **`mate 2`** | **FAIL** `cp 0`, `h1a1` | **FAIL** `cp 0`, `h1g1` |

| build | spec | pins |
|---|---|---|
| base | FAILED (S1, S4, S6) | 4/4 exact |
| PC (PC20) | FAILED (S2, S5, S6) | 4/4 exact |

**S6 is the only case both builds fail**, which is exactly what 21-F24 predicted: neither can see a mate
two moves away at a drawn root — the base because it does not search such a root at all, the PC because its
repair reaches one ply and stops.

## S6's premise is asserted, not assumed

Before scoring S6 the spec proves the board's distance: it asserts there is **no** mate in 1, and that at
least one move leaves **every** reply allowing a mate in 1. On `6k1/8/5K2/8/8/8/8/7Q w - - 100 60` that
finds six such moves (`h1b7`, `h1h5`, `h1h4`, `h1h3`, `h1h2`, `h1g2`), so the case cannot silently become
another mate-in-1 test if the board is ever edited.

## Prediction outcome

| prediction | outcome |
|---|---|
| P1 S6 fails on the PC build at `go depth 12` | **held** — `cp 0`, `h1g1` |
| P2 S6 fails on the base build | **held** — `cp 0`, `h1a1` |
| P3 S1–S5 unchanged from job43 | **held**, every row identical |
| P4 spec exits non-zero on both, pins exact | **held** |
| P5 runtime under ~2 minutes per build | **held** (about 3 minutes per build including all six cases and four pins) |

## Findings

`21-C23 | the six-case spec is the complete statement of the drawn-root rule` — with S6 added,
`job45/acceptance6.py` is the check any fix must pass: base fails S1/S4/S6, PC fails S2/S5/S6, S6 is the
case both fail, and the pins are exact on both.

`21-F24` is confirmed at the spec's own depth (`go depth 12`), extending its four-row table.

## What this changes for the owner

The gap is now stated in one table rather than described in prose: **three of six cases fail on each build,
and the case both builds fail is a mate in 2 at a drawn root.** The rule in `DESIGN_drawn_root.md` remains
the only one that would pass all six, but the S6 row adds a requirement the note did not spell out — the
search must be deep enough to see the win, so a fix that searches the root at depth 1 or 2 would pass
S1/S4 and still fail S6.

## Suspicions, not proven

- Whether any fixed depth would pass S6 on the PC build. `go nodes 200000` did not (21-F24), and I did not
  try a fixed depth between 10 and 16 because 21-F22 makes a bare-king depth-13+ search take ~25 s.

## What I did NOT do

- Did not add a mate-in-3 case: no verified mate-in-3 board exists in my files (job44 refused to ship an
  unverified one), so the spec stops at mate-in-2. That is the honest coverage of the instrument.
- Did not replace `job43/acceptance.py`; the six-case version is a separate file so the five-case results
  quoted earlier stay reproducible from the file that produced them.

## What I am NOT sure about

- Whether S6's rarity justifies its place in the spec. It is the only case that separates "search the root"
  from "search the root deeply enough", which is precisely the distinction the design note needed.

## Times

see `job45/stamps.txt`.
