# Exhaustive bounded boundary-window search

Design written 2026-11-03, Vienna. No workload is authorized by this document.
The active source scans retain their computation slots. Implementation belongs in
new tools/tests; the qualified helper, transport, segment driver, parser, and
resource policy remain unchanged. Review the design and candidate before running.

## Exact claim and scope

For each seam, compare every physical endpoint pair from the last 50,000 rows of
012 and first 50,000 rows of 013, then last 50,000 rows of 014 and first 50,000
rows of 015. Short files use every available row. Direction is left to right.
The relation requires equal White result and an exact legal path of 1..8 plies,
including all six FEN fields, raw en passant, castling rights, and clocks.

The finite population is N_left * N_right per seam: at most 2,500,000,000 pairs
per seam and 5,000,000,000 total. Counts require integers wider than 32 bits.
Duplicated endpoint states retain physical-row multiplicity.

Zero resolved links with every pair excluded by a proved necessary condition or
exhaustively searched gives PASS only for **no bounded legal link in these
windows**. A positive legal link makes that narrow claim FAIL; it is not proof
of a shared original game. Any unresolved or unexamined candidate makes it
UNVERIFIED. Original game identity and historical producer binding remain
UNVERIFIED in all cases. Gaps above K and endpoints outside the windows are not
covered. A clean window result cannot authorize export or training.

## Source binding and RAM layout

Load the existing verified source pins. A new bounded window reader consumes
and hashes each complete file, records metadata before/after, physical line
count and exact window bounds, and retains only the requested first/last rows.
Parse and independently validate every retained endpoint. Do not copy source
rows to disk. An input pin mismatch invokes the user's stop rule. Missing,
malformed, or invalid retained states prevent PASS; record their pair population
as unresolved, with syntax-key and legal-state fill rates beside link counts.

Use compact RAM arrays: source line uint32, absolute ply uint32, halfmove uint32,
result and castling flags uint8, per-color piece counts, and twelve piece-type
bitboards uint64. Keep full FEN strings only for retained endpoint queries.
Process one seam at a time. Expected retained data and temporary arrays are below
256 MiB; this is an estimate to be measured, not a resource exemption. No disk
hash sets, caches, source datasets, or training-runtime imports.

## Complete candidate enumeration

Index right endpoints by (White result, absolute ply). For each left endpoint,
visit exactly the eight buckets at left_ply + 1 through left_ply + 8. Absolute
ply is 2*(fullmove-1)+(side is Black), so the selected depth also fixes whose
turn and how many turns each color has. Count result exclusions and ply-gap
exclusions analytically from bucket sizes; do not enumerate their Cartesian
products. Then apply the following necessary conditions, in this fixed order.
Attribute an excluded pair only to its first failing condition.

1. Clock: target_halfmove equals source_halfmove + depth, or is below depth.
   Without a pawn move/capture the clock increases every ply. After the last
   reset its value is the number of subsequent plies, at most depth-1.
2. Rights: target castling rights are a subset of source rights. Rights cannot
   be acquired during standard legal play.
3. Material: each color's total piece count cannot increase. Its loss cannot
   exceed the number of moves made by the opposite color, since each legal move
   captures at most one opposing piece. Promotion preserves the mover's total.
4. Changed piece squares: for color c, let D_c be the sum of popcounts of XORs
   between corresponding source/target piece-type bitboards. Let m_c be that
   color's number of turns and loss_c its total piece-count loss. Require
   D_c <= 2*m_c + loss_c + 2*castle_possible_c, where castle_possible_c is 1 only
   when the source has a castling right for that color and m_c is nonzero.
   A normal move or promotion changes two own piece-square memberships;
   castling changes four and can occur at most once per color; being captured
   removes one. Symmetric-difference distance obeys the triangle inequality.
   En passant changes two memberships for the mover and one for the captured
   color. The allowance is deliberately conservative.

No evaluation, piece-square weights, pawn-distance assumptions, inferred game
IDs, expected game length, or endpoint score is a filter. In particular a
dedup gap is not capped or treated as an authentic new-game marker.

Implement masks in bounded NumPy integer-array batches with all thread limits
set to one. Check the installed popcount operation against scalar integer
bit_count; do not rely on signed arithmetic or overflowing counters. Array
filters never determine a positive result; they only remove proved negatives.
The first enumeration pass counts all survivors without saving pairs. The
second repeats deterministic enumeration and streams survivors into the qualified
native helper. This avoids an unbounded candidate-pair array and exposes an exact
unqueried count when search reaches its deadline. Check both passes' totals.

## Native resolution and evidence

Reuse the pinned r03 helper and qualified bounded transport. Every query has an
exact ID and endpoints; batches contain at most eight lines and 2,048 bytes.
Reuse the frozen segment driver's reply validation and independent positive
witness replay. An exhaustive negative within a node budget is resolved; budget
exhaustion, transport failure, and timeout remain UNKNOWN. Start with 100,000
nodes and retry UNKNOWN at 1,000,000 only within the admitted time budget. Keep
initial and final outcome counts distinct. No unknown is counted as agreement.

Write compact row-reference query receipts and UCI witnesses, without FEN copies.
Seal fixed-size binary parts below 100 MB with full MD5/SHA256 and record layout.
Record: complete pair population; invalid-endpoint population; every exclusion
count; survivor count; attempted, retried, resolved-negative, positive, unknown,
and unqueried counts; both pass totals; source bounds and fill rates; exact helper,
qualification, runtime, source pins, tool identities; elapsed time and resource
stops. Pair accounting must sum exactly to N_left*N_right. Preserve all positive
row references, including equivalent physical endpoints, rather than only a
sample. Report publication requires fresh resource admission. Hard resource
stops emit stdout only and discard buffered tails.

## Checks and acceptance

Before source execution: tests first, small green checks, focused independent
review, fixes, recheck. Required tests are brute-force small Cartesian products
versus bucket/mask enumeration; exact exclusion accounting with duplicates;
legal paths of depths 1..8 never excluded; both colors; castling at either end
of a longer path; capture/EP/promotion; nonzero clocks and late resets; repeated
piece moves; rights loss; king movement; deliberately invalid endpoints; and
partial readers, missing final newline, long lines, consumed-MD5 mismatch,
truncated query replies, deadline interruption, and insufficient disk budget.
Random legal-path qualification must supplement the rule proofs and include
at least 100,000 generated paths with zero wrongly excluded endpoints. Existing
million native qualification remains authoritative; do not rerun it unchanged.

Use a real-r03 owned-fixture end-to-end run and a synthetic straddle that must
produce a positive cross-window link. The bounded no-link claim must fail for
that fixture. A deliberately tiny node budget and unqueried survivor must remain
UNVERIFIED. The separate authenticated game-ID verdict never derives from this
synthetic truth or the bounded no-link verdict.

## Cost, deadline, and stop rules

Initial engineering/review allocation: 45-75 minutes, useful while existing scans
hold both computation slots. No test process starts without coordinator admission.
Expected necessary-condition bucket population is on the order of 100-400 million
pairs per seam if endpoints span roughly 100-400 plies. This is only a sizing
example; the measured bucket count, not that distribution assumption, controls
execution. Chunked array work may take minutes; no measured rate exists yet.
If every endpoint has the same compatible ply/result, a bucket can hold 50,000
rows, so the design must still handle the full population without allocating it.

Native cost is survivor_count * measured mean query time, plus optional retries.
One million survivors at 1 ms already require about 17 minutes; at 10 ms about
2.8 hours. No completion promise is justified before survivor counts are known.
Recommend a 30-minute initial admitted run and a maximum 90-minute search budget,
adjusted by the parent to preserve the final review hour. If the count indicates
that completion is unlikely, still preserve exact exclusions, all resolved hits,
and the unresolved remainder. Never relax a filter to hide unknowns or call a
partial run exhaustive. Any continuation uses a reviewed receipt/checkpoint design
or a fresh output directory; do not invent resumability during a live run.

One Idle CPU in the admitted spare pool; no GPU; no additional compute worker
while both source scans run. All shared floor/cap/progress rules apply: D: at
least 50 GiB free, C: at least 30 GiB, owned tree below 5e9 bytes, at least 8 GiB
RAM headroom, worker below 2 GiB. Throttle only owned work when shared progress
degrades. Keep native/parser/policy files frozen during existing source scans.
