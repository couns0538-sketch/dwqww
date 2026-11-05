# T05F-01: Node-identical eval memo for the evaluations the TT never keeps (RFP / null-move exits, razor re-entry, re-search revisits)
Status: COMPLETE (no source logs an nps or hit-rate number for an eval memo - missing; step 0 of the test plan is the counter that decides go / no-go)

## Source
- Own lock source (notes/T05F/sources.md L1): exits that return without a TT store - reverse futility `return eval` src/search.cpp:960-963, null-move cutoffs :984-998; razoring re-enters qsearch on the same node (:953-958), whose second probe (:786) misses again and re-runs static_evaluate (:808) and corrected_eval (:809). Stores that keep the raw eval: :817, :868, :1023, :1214; reuse: :807, :935.
- Predecessor row: notes/T05B/TABLE.md row 10 ("separate eval cache keyed by the full key ... no card: counter first") framed the misses as TT replacement only; notes/T04L/TABLE.md row 12 found that the RFP / NMP / razor exits store nothing (the Elo-side fix is the EvalOnlyStore near-miss port).
- Design reference (MIT): Caissa writes an eval-only TT entry right after each evaluation, https://github.com/Witek902/Caissa/blob/57cae7ef71e87c1d02b5a1b1baea98ea79ee5452/src/backend/Search.cpp lines 1680-1686 (search) and 1285-1290 (qsearch), so its razoring qsearch (lines 1765-1771) re-reads the stored eval; qsearch variant https://github.com/Witek902/Caissa/commit/4b2cf654a3 (test https://furybench.com/test/3041/).
- One web search (W4) found no logged nps or hit rate for an eval cache / eval hash in any engine.

## Licence
Own code (lock). Caissa MIT at 57cae7ef71 and 4b2cf654a3 (rows in notes/T05F/licences.md): copy with notice; only grep hits and two short ranges were read, nothing is copied. Arasan (T05B row 10): MIT doc only.

## Mechanism
A per-thread direct-mapped table of (position key, raw eval). In search() it is read only where the lock would call static_evaluate (TT miss, or TT eval = ValueNone), and written after each static_evaluate in search(), i.e. before razoring, RFP and null move can leave the node without a TT store. The stored value is the raw eval (HCE + residual net, before correction); corrected_eval runs on it as today, so correction-history changes between visits are respected. The raw eval is a pure function of the position in the lock: eval.cpp reads no rule-50 or history state, the pawn cache checks the full pawn key (eval.cpp:397), RuntimePsqt is integer, and the net's float accumulators add int16 / 2^12 values (include/forge/nnue.hpp:20, WeightScale = OutputScale = 4096) whose sums stay far below 2^24 units (at most ~33 x 32,767), so every partial sum is exact and the same on every update path. A hit therefore returns exactly what static_evaluate would return, and the TT is never touched - unlike EvalOnlyStore (gates 49 / 50 / 68bnd), which writes eval-only TT entries, changes replacement and is an Elo change. Entry: 8 B = high 48 key bits + int16 eval with a 16-bit index, so all 64 key bits are checked; 2^16 entries = 512 KiB per thread (size checked in step 1 against the 1 MiB L2). A hit at an RFP node saves the whole evaluation (S37: 403.1 ns, HCE ~232 ns); a hit at a node with children saves the HCE + output layer, while the accumulator update moves to the first child's lazy walk (static_evaluate :602-614).

## Forge fit
Has it? NO: forge_has 'eval_?cache|eval_?memo|EvalCache|EvalMemo' = 0 hits. The TT keeps the raw eval only for nodes that reach a store (:817, :868, :1023, :1214). Change: one memo read before static_evaluate at :936 (and at :808 only on the razor re-entry, flagged in the frame, which then hits), one write after it, the table in Worker, cleared at ucinewgame and whenever an eval-changing option is set (values never go stale within one configuration).

## Expected gain
Source number: none for a memo (missing). Related Elo-side numbers (TT writes, NOT node-identical): Caissa 4b2cf65 +1.34 +- 1.08 Elo, 5.0+0.05s Threads=4 Hash=32MB, SPRT [0, 2.5], LLR 2.95, N=105,626; Forge gate49 (EvalOnlyStore, MinDepth 2) +8.57 Elo / +19.19 nElo, 1,500 games, cap, no decision; gate50 (MinDepth 4) -0.93; gate68bnd (bundle incl. EvalOnlyStore) H1 at [0, 10], +14.51 Elo, 1,390 games (notes/TRIED_GATES.md).
Break-even (own arithmetic): a memo read + write costs ~5-15 ns per static_evaluate call (L2-resident) against ~280-400 ns saved per hit and ~450 ns per average node (2.24M nps probe, notes/T05/SPEED_LIST.md row 5), so +1 % nps needs about 6-8 % of static_evaluate calls to hit, +3 % about 12-18 %.
Forge estimate: 0 to +4 % nps **UNPROVEN** (lock, EvalOnlyStore OFF); much less if EvalOnlyStore is adopted (its TT entries then catch the depth >= MinDepth exits) - re-count on that build.

## Effort
Crew hours ~6.5: step-0 counter build 1.5 (exact key set per search; counts static_evaluate calls whose key was evaluated before in the same search, split by first exit: RFP, null-move cut, razor, PVS / LMR re-search revisit, TT replacement) + 1 for its runs; memo + switch 2; verify build + pins + 12k-FEN identity 1.5; ABBA set-up 0.5. CPU ~2-3 h of one Idle core (counter runs on bench 13 / 16 and 200 game positions at gate TC, ABBA). No GPU.

## Test plan
Step 0: counter build (node-identical, not for gating); go only if >= 8 % of static_evaluate calls repeat a position at gate-like movetime. Pre-gate: OFF bench = lock pins; ON bench = lock pins as well (same nodes and moves at d13 / d16; the identity proof), 12k-FEN exe identity, perft unchanged; verify build that runs static_evaluate on every hit and asserts equality over bench + 200 game positions + 10 self-play games; Threads=2 smoke. Gate route: node-identical speed change = nps ABBA only (T12-02 protocol: palindromic, fresh copies per slot, A/A first), on the lock and separately on a bundle-68 build; no SPRT.

## OFF-by-default design
Build switch FORGE_EVAL_MEMO (default 0 = lock source) or UCI option EvalMemo (check, default false; table allocated at the first ON). OFF = no table, no read: the lock path and its bench pins. ON changes no value (pure eval, full key check), so bench pins must match in both states. Sizing option EvalMemoLog2 (14-17, start 16) for the step-1 runs only.
