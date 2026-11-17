# FINDINGS — swarm/71, v3 net-path correctness

Five findings for whoever touches this engine next, ordered by what they should act on. The
detailed evidence for each is in `NET_CORRECTNESS.md`; every claim here has a command there.

---

## 1. The identity baseline 27,944,084 is not reproducible on combo29, and it is not the net

**The fact the next person needs: four of PC20's twenty options do not exist on this branch.**

| option | reply | exists in `src/` or `include/`? |
|---|---|---|
| **`CuckooRep`** | `info string unknown option CuckooRep` | no |
| **`HistRework`** | `info string unknown option HistRework` | no |
| **`TtPruneV2`** | `info string unknown option TtPruneV2` | no |
| **`CorrHistV2`** | `info string unknown option CorrHistV2` | no |

Sixteen of twenty apply. Those four are not merely unadvertised: `grep -rn 'CuckooRep\|HistRework\|TtPruneV2\|CorrHistV2' src include`
returns nothing, so the behaviour is absent from the code, not just hidden from `uci`.

**Consequence.** "PC20's 20 option values" is not an expressible configuration on this branch.
A harness that sends all twenty and does not check the replies is silently running a 16-option
configuration and will report a node count that has no fixed relationship to the published
baseline.

Measured, `go depth 12`, Threads 1, Hash 16, test net loaded, on the committed
`swarm/08/job1/OG200.fens`:

| quantity | measured | documented | match |
|---|---|---|---|
| node sum, 200 openings | **29,791,805** | 27,944,084 | **no, +6.6%** |
| row 1 | 62,951 | 110,540 | no |
| eval startpos | **968** | 968 | **yes** |
| eval Italian game | **1176** | 1176 | **yes** |
| eval rook endgame | **31** | 31 | **yes** |
| bench 11 no net no options | **312,866** | 312,866 | **yes** |
| bench 11 net no options | **965,454** | 965,454 | **yes** |
| bench 11 PC20 no net | 242,804 | 278,024 | no |
| bench 11 S14 no net | **242,796** | 242,796 | **yes** |
| bench 13 S14 no net | **656,517** | 656,517 | **yes** |

Everything that avoids the PC20 set reproduces to the digit — including the three eval values,
which exercise the whole net path. Everything that uses PC20 is off. That is the signature of a
configuration mismatch, not a net regression.

**Action:** restate the baseline against the 16 options combo29 has, or measure it on a branch
where PC20 exists. Until then, any patch gated on "must reproduce 27,944,084 exactly" will fail
for an unrelated reason.

---

## 2. The incremental v3 accumulator is exact, including on the one branch a normal game never reaches

**54,379 distinct positions compared against a fresh refresh: 0 mismatches.** Also 0 eval
disagreements, and 200 positions at depth 12 under the engine's own in-search verifier
(37.5M nodes), 0 mismatches.

The count is not the interesting part. This is: **`replay_ply` has a branch that quiet games
essentially never take.**

When a perspective's king key (bucket, flip) is unchanged, the child accumulator is the parent's
plus the recorded piece changes — the common path. When the king **moves into another rank band
or crosses the mirror line**, the code discards that and rebuilds the piece bitboards for that
ply by *undoing the later plies* from the board at the top of the stack, then refreshing through
the cache. An off-by-one in the undo order would live there and nowhere else.

A 200-sequence, 40-ply fixture of real games triggers it **7 times in 8,200 positions**. So the
audit constructs the worst case: 120 games with only kings on the board, both kings walked
aggressively, giving **5,012 transitions in 7,320 positions** (68% of positions) — and it is
exact on every one.

**Action:** none. This is the strongest correctness result in the run, and its value is the
coverage, not the count. Any future change to `replay_ply` should be re-checked against
`kingwalk.tsv`, which costs under a second.

---

## 3. A damaged net is refused; a deliberately re-checksummed one loads, and must

**11 of 12 damage cases refused, each with a specific reason:** zero-length, header-only,
truncated to half, truncated by one byte, extended by one byte, bad magic, single-bit flip in
`w1`, in `b1`, in `eval_scale`, in the stored checksum, and a header claiming an out-of-range
hidden size.

**The twelfth — a bit flip with a recomputed checksum — loads, and that is correct.** FNV-1a
over the payload detects damaged storage and truncated transfers. It cannot detect a file
rewritten by someone who then recomputes the hash, because they have the same information the
loader has. A loader that rejected a self-consistent file would reject legitimate nets.

**State the guarantee this way:** accidental damage of any kind is refused; deliberate
re-checksummed corruption is outside what this format detects, and no claim is made otherwise.
Structural validation (magic, version, header fields, exact size, bucket-map ranges, `|w2| <=
127`, the accumulator-overflow bound) is separate from the checksum and does real work on a
hand-crafted file.

---

## 4. Fail-loud on a missing net kills the process mid-protocol

`NNUEArch true` with no net, or with a net that failed to load, prints
`info string ERROR NNUE v3: ...` and then **exits with status 2 without answering `isready` and
without emitting `bestmove`.**

A GUI that sets `NNUEArch true` and waits for `readyok` hangs forever. The intent is right — the
engine never falls back silently to the hand-crafted evaluation, and bench proves the net is
genuinely in use (312,866 → 965,454 nodes with the test net) — but the mechanism is wrong. A
`bestmove 0000`, or keeping the process alive in a permanent error state, would be recoverable
where exiting is not.

Related, and correct: a net loaded with `NNUEArchFile` but `NNUEArch` left **false** is
completely inert — identical bench node counts, not merely similar. There is no path where a
loaded file is silently used.

---

## 5. Protocol detail that decides whether a correctness harness is measuring anything

`info string invalid FEN` appears in **two different places** depending on whether `isready`
separates `position` from `go`:

| path | in `position` reply | in `go` output before `info depth` |
|---|---|---|
| `position` → `isready` → `go` | **yes** | no |
| `position` → `go` | no | **yes** |

And it is emitted in both cases. A harness that scans only one stream misses it half the time;
a harness that sends `isready` between `position` and `go` consumes it into a reply it is not
reading and never sees it at all.

This matters directly for finding 2. The engine silently searches the **previous** position when
a FEN is refused, so an incremental-vs-refresh comparison that rebuilt a FEN the engine rejects
would be comparing two different boards, and every mismatch would be a fixture bug. The audit
therefore validates every FEN with python-chess before use **and** scans both streams: 6/6
invalid FENs detected across both paths, 0/12 false positives on valid FENs, 0 refusals across
all fixtures.

---

## Method note that belongs in the record

The first run of the incremental harness reported **960 mismatches over 492 comparisons**. More
failures than comparisons is impossible, and that impossible ratio is what exposed the fault: my
`dirty_of(j)` indexed the ply directly instead of mapping the search's stack index (`ply + 4`) to
frame `j - 4`, so every replay applied a neighbouring ply's changes. Corrected, the same fixture
is clean.

Every check was then shown able to fail before its clean result was believed: injected
accumulator corruption reports 492/492 mismatched; a deliberately patched `replay_ply` makes the
verification build exit `rc=3` with
`incremental 1253 reference 1344 fen rnb1kbnr/ppp1pppp/8/4q3/4N3/8/PPPP1PPP/R1BQKBNR b KQkq - 3 4`.
The source was restored afterwards and `git diff` on those files is empty.

The lesson generalises: a harness whose failure count can exceed its comparison count has no
denominator, so its zero means nothing either.
