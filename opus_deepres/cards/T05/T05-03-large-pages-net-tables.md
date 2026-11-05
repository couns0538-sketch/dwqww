# T05-03: 2 MB pages for the v2 first-layer tables and refresh caches (KB8-KB32 nets)
Status: COMPLETE

## Source
- Stockfish PR 6359 "Use huge pages for worker data" (PR text): https://github.com/official-stockfish/Stockfish/pull/6359 ,
  STC test https://tests.stockfishchess.org/tests/view/68e9f3c0d323fd15c04e3ba4
- Stockfish PR 7041 "Place continuation history on large pages" (PR text): https://github.com/official-stockfish/Stockfish/pull/7041 ,
  STC test https://tests.stockfishchess.org/tests/view/6a736a122cf557d58a2e1f51
- Zen 5 TLB sizes: AMD's Zen 5 architecture deck as summarised by search results (notes/T05/sources.md no. 7; deck not fetched).
- Own: QA's S1 LargePages candidate and its ABBA CSVs, C:/Users/Administrator/grok-pc/forge_push/qa_s1lp_20261031 .

## Licence
Stockfish ff7cee4244: GPL-3.0 - ideas only; only PR text and test pages were read, never source. S1 is Forge's own code
(written from the Win32 API documentation, per its own README).

## Mechanism
A table spread over 4-KiB pages needs one TLB entry per 4 KiB touched. The v2 first-layer table is float32
[KB][768][256]: KB4 3.1 MB, KB8 6.3 MB, KB16 12.6 MB, KB32 25.2 MB = 768 / 1,536 / 3,072 / 6,144 pages of 4 KiB,
against a Zen 5 core's 96-entry L1 DTLB and 4K-entry L2 DTLB, which also serve the TT, histories, stack and code.
Every accumulator update reads 2-4 columns (1 KB each) per perspective at addresses that jump with the moved piece, so
on the big layouts most column reads miss the L1 DTLB and, for KB16 / KB32, often the L2 DTLB too (a page walk on top
of the L2 / L3 data miss). On 2-MiB pages the KB32 table needs 13 entries (corrected by verify: 25,165,824 B = exactly 12 x 2 MiB, so 12 entries
when the block starts on a 2 MiB boundary, as S1's large-page blocks do; 13 only if it straddles one). Same bytes, same arithmetic, same order.

## Forge fit
Lock: no large-page code (`tools/forge_has.sh 'large_page|MEM_LARGE|madvise|huge'` = 0 hits). S1 (UCI LargePages,
default false, QA 2026-10-31) backs the TT and the COMPILED-IN w1 only. The v2 port allocates its tables with aligned
operator new (64 B; `AlignedFloats` in include/forge/nnue_v2.hpp of v2port.patch) and the refresh caches with
std::vector, so no exe puts a v2 table on large pages. Change: route Net::w1 / w2 / b1 and the RefreshCache entries
through the S1 allocator when LargePages is on (S1 and v2port are both lock-based; they touch different code).

## Expected gain
Sources: Stockfish 6359 ~+1.2 % nps for 14 MB of worker data (20 runs on a large machine), STC SPRT [0, 2] passed,
LLR 2.95, 166,272 games, W 43479 L 42993 D 79800 (about +1.0 Elo computed); Stockfish 7041 +1.04 % nps (200 runs,
paired t 3.415, p 0.0008), STC [0, 2] passed, LLR 3.42, 231,360 games, W 60152 L 59553 (about +0.9 Elo computed) (verify: both fishtest runs 10+0.1, Threads 1,
book UHO_Lichess_4852_v1.epd, bounds [0, 2] in normalized Elo; 7041 D 111655; read from tests.stockfishchess.org/api/get_run).
Own: S1 on the lock (TT + 786 KB w1) ABBA nps x1.011-1.016 at Hash 64 and x1.027-1.032 at Hash 256.
Forge estimate (v2 path, on top of S1's TT part): KB4 +0-1 %, KB8 +0.5-1.5 %, KB16 / KB32 +1-3 % nps **UNPROVEN**.
It also tells how much of the measured layout cost (KB32 0.942 vs KB4) is TLB rather than refresh work.
Why a full card although the Stockfish Elo is ~+1 at STC only: for a node-identical change the source number is nps
(+1.0-1.2 %), judged by the +1 % nps line; our own S1 data on the lock reaches +2.7-3.2 % at Hash 256.

## Effort
Crew ~2-3 h (reuse S1's allocator and its fallback / info line; one more table kind). CPU ~1-2 h of nps ABBA on
CPUs 0-1 at Idle. No GPU. The gate machine needs the "Lock pages in memory" right (QA already set it up for S1).

## Test plan
Pre-gate: LargePages=false: lock pins (bench d11-d22, perft) unchanged; with a v2 net and LargePages=true: the net's
packed ON benches unchanged (n2L 292397 / 836621 / 2200750), info line "LargePages: on (.. MiB v2 w1)", the walk and
parity runs unchanged (same values). Gate route: node-identical speed change = nps ABBA only - one exe, LargePages on
vs off (no per-file effect), depth_probe_ab.py game positions (200 positions, movetime 200, both orders) for KB8 and
KB32 nets, plus an identical-command A/A first.

## OFF-by-default design
UCI `LargePages` (check, default false, S1's option) extended to the v2 tables; false = today's allocation, byte
for byte; nothing in search or eval reads the flag, so OFF is the lock (bench pins equal).
