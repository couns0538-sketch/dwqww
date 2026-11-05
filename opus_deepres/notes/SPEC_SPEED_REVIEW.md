# SPEC_SPEED_REVIEW: adversarial review of SPEC_SPEED (S1-S4) against the lock source

Started 05:23 PC clock (`date`), board slot S2 (S1 was busy), planned stop 05:43. Status: COMPLETE (four specs and the
common part checked; no card and no spec file edited). Reviewer: fable SPECREV2. Read-only lock source FD3A5190 = AL1
s198: `C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/src_al1s198_clean`. Nothing here edits, builds or
runs the engine; every Forge-side number is UNPROVEN. No web read; no source of any other engine opened.

Questions per spec: (a) anchors exist and say what the spec claims; (b) node-identical (move order, generated sets,
keys, TT contents and replacement) and the proof plan catches a break; (c) the timing plan sees 1 % at the PC's 2-5 %
A/A noise (T12-02), A/A first; (d) Windows / MinGW / Zen 5 pitfalls. Verdicts: OK | FIX (exact fix in words) | BLOCKER.
Result: no BLOCKER; 10 FIX items, none of them changes a mechanism.

## Reading record (lock, read-only, 05:24-05:31)
- board.hpp :28-90 (Move :34-47, MoveList :49-73, Undo); board.cpp :420-580 (generate_pseudo_legal :425-540,
  pseudo_legal_moves :542-546, legal_moves, has_legal_move :569 fallback list), :865-880 (perft :874).
- search.cpp :40-55 (MaterialCorrectionWeight 100 at :50), :178-320 (TLS :184, lease :186-209, has_exclusive_access
  :211-216, lock_stripe :218-228, probe :246-281, store :283-302, hashfull :304-312), :319-333 (MovePicker ctor),
  :430-560 (members :438-459, generators :510-555), :580-660 (material_key :588-596, corrected_eval :638-645,
  update_correction :647-656), :820-830, :905-915, :1000-1010, :1030-1048, :1183-1202, :1210-1225, :1274-1282,
  :1308-1340, :1460-1468, :1496-1531 (Searcher::search).
- search.hpp :40-72, :112-182 (TT class), :255-270, :320-330; bitboard.hpp :140-175; bitboard.cpp :18-115; book.hpp
  :34-42; uci.cpp :352-360 (go: TTAccess::Exclusive), :398-408 (bench: Exclusive).
- Own greps of the lock: `thread_local` (2 hits: search.cpp:184 and a cold `static thread_local std::string` in
  eval_params.cpp:23), `material_key` (definition + :642 + :655 only), Magic / attack-table readers (bitboard.* only),
  every bare `Move x;` and `MoveList x;` / `std::array<Move` declaration, TT call sites (`tt.probe` :786 :910;
  `tt.store` :817 :868 :1023 :1214; `tt.prefetch` :847 :1126, no lock).
- Tools: `forge_push/qa_r12fix/pkg/v2t1port/tools/r12_fens12k.py` argument list (no node limit: `--depth`,
  `--deep-n`, `--deep-depth`; it sends `go depth D`). Own arithmetic: `F:/odr/work/SPECREV2/matkey_recheck.py`.
- Notes: SPEC_SPEED.md, cards T12-02 and T12-03, SPEC_REVIEW.md (layout only).

## Common part (identity tooling and the nps ABBA)
- (a) OK: pins, perft values, the ExclusiveLease facts and the kit rules match what the lock and T12-02 / T12-03 say.
- FIX C1 (12k driver): r12_fens12k.py has no node limit (its flags are --out --cpu --net --fens --depth --exe --deep-n
  --deep-depth; it sends `go depth`). The spec's "if not, a small driver (~0.5 h)" is therefore a fixed cost, not a
  maybe: add `--nodes N` to a copy of the tool or write the driver, and count the 0.5 h in step 0.
- FIX C2 (time budget, question c): "< 30 min of one core per comparison" holds only for bench d16 alone. T12-02's
  own A/A on this PC (-0.02 % [-2.24, +2.25] over 15 runs) means a per-pair sd of roughly 4 % (half-width x sqrt(15) /
  2.14), so n is about 8.6 x 16 = 140 pairs, not 35. With three arms (A, B, A') and the spec's workload list (d16 ~2.5 s,
  d20 ~10 s, plus the 200-position probe) one pair is 40-60 s and 140-215 pairs are 1.5-3.5 h of one core. Fix in words:
  size n from the pilot s at d16, make d16 the decision workload, and run d20 and the game probe only as a
  confirmation on a candidate that already passed at d16 (or budget 2-4 h per comparison and say so in the order).
  A/A first: the spec's 20-pair pilot does not say which arms it uses; make it A vs A' (two fresh copies of the lock
  exe), so s and the per-file bias are measured before the candidate enters, and let B into the blocks only after
  that pilot's interval contains 0.
- FIX C3 (keep rule): the power statement (90 %) belongs to the lower-bound test only. The second condition, point
  estimate >= +1 %, is passed by a true +1 % change only about half of the time at the sized n, and never by a true
  0.75 % change (S3). State that the sized n gives 90 % power to show "faster than the lock", and that a point
  estimate >= 1 % is a stricter extra filter; the open crew decision about sub-1 % members of a stack (S3) stays open.
- FIX C4 (Windows): a fresh exe copy per slot is right (per-file bias), but the first execution of every new file is
  scanned by the real-time antivirus and the loader has a cold image: run each copy once untimed (bench d1 or
  `go depth 1`) before its first timed slot, or exclude the ABBA folder from real-time scanning, and keep the slot
  order palindromic afterwards. Otherwise the first slot of every copy carries extra load (mechanism UNPROVEN, the
  warm-up is free).
- FIX C5 (byte identity at 0): the rule "every restructure inside the #if" must be applied to data members too:
  S4's new Worker member and the Searcher scope guard, S2's new per-square arrays and S1's mode enum / wrapper change
  the class layout or the symbol table when they exist at 0. Write "under the switch" at each of those steps.
- OK: proof steps 1-6 (pc1 = pc2, pins, 12k, T12-03 levels 3 / 5, planted mutant, sanitizer CI) are the right set;
  the mutant step is what makes the proof falsifiable.

## S1 T05C-02 FORGE_NO_ZERO_MOVELISTS
- (a) OK: Move :34-47 with `= 0` at :35-38 and none() at :46; MoveList :49-73 (data_ :71 without `{}`); MovePicker
  members :446-459 (tt_move_, killers_{}, counter_{}, moves_{} 256 x 8 B, bad_captures_{} 64 x 4 B, buffer_,
  check_squares_{}); generate_quiets :523-536 with the filter at :530 (`is_capture() || is_promotion()`);
  init_check_squares :462-472 writes indices 1-6 and direct_check :474-477 reads piece types 1-6; quiets_tried /
  captures_tried :1034-1035, written :1186-1187, read :1198 / :1200 with counts; bare `Move move;` at :827, :1005,
  :1044 (each assigned in its while condition); tt_move_ set in the ctor :324; root list :1278 with front() at
  :1320 (guarded), :1330, :1338, :1465 after the empty return at :1311; book.hpp:38 Candidate::move; has_legal_move
  fallback list :569 (0x408 = 256 x 4 B + size_), perft list :874. All as the spec says.
- Audit completeness (own grep): the bare `Move` declarations in the lock are exactly search.cpp :439 (Scored::move,
  covered by moves_), :446, :827, :1005, :1044 and book.hpp:38; the bare MoveLists are board.cpp :543, :569, :874 and
  search.cpp :456, :1278. Every other Move holder has `{}` (search.hpp :43-44, :69, :263, :266-268, :325) or is
  value-initialised through its container (CounterMoveTable{} :580, SearchStack{} :583, TTCluster{} :241,
  make_unique, std::vector). `(ss + 2)->killers = {}` at :907 stays a zeroing assignment. The list is complete.
- (b) OK: the quiets-only generator yields the identical subsequence. Lock order (:452-539): single pushes, double
  pushes, promotion pushes, pawn captures, en passant, then N, B, R, Q, K each popping (attacks & ~own) in bit order
  with captures and quiets interleaved, then castles under `!captures_only && checkers_ == 0`. The filter at :530
  drops exactly the captures (is_capture covers EnPassant), the promotions and the ep moves; popping (attacks & empty)
  in bit order gives the remaining quiets in the same relative order, and emit's flag is Quiet for every empty target,
  so the Move values are identical too. The assertion build (lock filtered list == new list at every call) and the pins
  catch any break. Evasions untouched: right (a sorted / swapped input must keep its order).
- (c) OK with C2: the zero fill is per picker, qsearch pickers dominate, bench d16 represents it.
- (d) OK: on MinGW `std::uint8_t` is `unsigned char`, so a stray read of an unwritten slot is not undefined behaviour,
  only unspecified - which is why the 0xA5 poison build, not the sanitizer, is the proof that no read exists.
  A kit flag of the `-ftrivial-auto-var-init` family would re-insert the fills: the objdump step covers it (keep it
  before any timing). The dropped `{}` change nothing else: Move stays an aggregate, `Move{}` still value-initialises
  to zero, MoveList becomes trivially default-constructible.
- Verdict: OK (C5 applies to the mode enum / wrapper).

## S2 T05C-03 FORGE_SLIDER_ATTACKS
- (a) OK: Magic :143-152 (mask, magic, table*, shift; index :149-151), RookMagics / BishopMagics :154-155, bishop()
  :162-165, rook() :166-169, queen() :170-171; tables :23-24 (0x19000 = 102,400 and 0x1480 = 5,248 entries, dense),
  sliding_attack :32, init_magics :63-108 (mask :76, shift :77, table :78, seeds :71, rng :88-91, fill :99, offset
  :106), init() :112. Own grep: no reader of the Magic arrays or the tables outside bitboard.hpp / bitboard.cpp.
- (b) OK: only attack values flow out of these functions, so equal values = node-identical. The exhaustive test covers
  the whole domain (every subset of every relevant mask); bits outside the mask are discarded by `occupancy & mask` in
  the lock and by pext in the new code, so the 1M random test is a bonus. The one-bit mutant must fail it: right.
- (c) FIX S2-1 (expectation): per lookup the mode-2 chain is pext (3) -> load -> pdep (3), the lock's is and (1) ->
  imul (3) -> shr (1) -> load: mode 2 is not shorter in latency, mode 1 saves about two cycles. A single-process gain
  can therefore come only from the smaller footprint (210 KiB against 841 KiB; Zen 5 L1D 48 KiB, L2 1 MB per core),
  and the two cited numbers that name a cause point at page sharing between processes (mode 3) or at a software
  fallback as the baseline. Write the single-process mode-2 expectation as 0 to +2 % and keep the perft microbench
  as the gate in front of the ABBA (already there). Latency numbers were not re-checked here (no web read).
- (d) FIX S2-2 (CI): the `#error` without `__BMI2__` fails the sanitizer row on any runner built without `-march`;
  add `-mbmi2` to that row explicitly. PEXT / PDEP are fast on Zen 3 and later and on this Zen 5 PC; on Zen 1 / 2 they
  are microcoded (slow, still correct), so a wrong machine is a speed matter, never a wrong result.
  FIX S2-3 (mode 3): a 102,400-entry constexpr table built with a constexpr pext emulation can hit GCC's constexpr
  operation limit; prefer the generated header (the spec names both: name the header first). Read-only image pages
  are shared between processes on Windows, runtime-filled arrays are private: the mode-3 claim holds.
- Verdict: OK with FIX S2-1, S2-2, S2-3 (C5 for the new per-square arrays).

## S3 T05B-02 FORGE_MATKEY_FAST
- (a) OK: material_key :588-596 (key starts at 0, loop White then Black, Pawn..Queen, `key * P + count + 1` at :592,
  `* G` at :595); corrected_eval :638-645 reads at :642 under `MaterialCorrectionWeight > 0` :641; update_correction
  :647-656 writes at :655 under the same guard; both mask with `CorrectionSize - 1U`; CorrectionSize = 1 << 14 at
  search.hpp:257; the weight's default 100 at search.cpp:50. material_key has no other user in the lock.
- Own re-check (F:/odr/work/SPECREV2/matkey_recheck.py, 300,000 random count vectors 0-10): 0 mismatches between the
  lock's Horner form and K0 + sum c_j K_j, for the 64-bit key and the 14-bit index; constants identical to the spec
  (K0_14 0x1f14; K14 0x238f 0x10b5 0x1ff7 0x1ead 0x2e1f 0x33e5 0x3807 0x3e5d 0x17af 0x3c15; K14[9] = G & 0x3fff; max
  unmasked sum 1,070,556). The identity holds for any count (ring arithmetic), so the 0-10 bound is cosmetic.
- (b) OK: same index at both sites = same correction read and written. The mutant (one K14 term dropped) changes the
  eval and so the pins, because the weight is live at the default. Variant (b) adds the make / unmake check: right.
- (c) OK with C3: the spec itself says S3 alone cannot be timed and that its marginal is below the keep rule.
- (d) OK: the exe's `imul $0x3c15` shows the compiler already narrowed the final multiply to 14 bits but kept the nine
  64-bit chain multiplies; 10 independent popcnt + imul32 pipeline, nothing MinGW- or alignment-specific.
- Verdict: OK.

## S4 T05D-01 FORGE_TT_NOTLS
- (a) OK: TLS definition :184; lease ctor :186-203 (drains the 1024 stripes), dtor :205-209; has_exclusive_access
  :211-216 (walks the thread's lease chain); lock_stripe :218-228 with the deferred, unlocked lock at :220; probe
  :246-281 (lock :249), store :283-302 (handle check :287-288 first, lock :289), hashfull :304-312 (lock :308);
  search.hpp :135 StripeCount, :139-151 ExclusiveLease, :153 `static thread_local`, :154-158. Call sites: probe :786 /
  :910, store :817 / :868 / :1023 / :1214 (six, as the spec says; prefetch :847 / :1126 takes no lock). Searcher::search
  :1498-1531: lease only for Exclusive with one worker (:1513-1515), helper threads only for i >= 1 (:1516-1521), the
  main worker on the calling thread (:1522). uci.cpp :357 (go) and :403 (bench) pass TTAccess::Exclusive.
- (b) OK: under the lease, lock_stripe already returns an unlocked `unique_lock` (:220), so the lock's probe / store
  bodies run unlocked today; the owned bodies are the same text minus the TLS walk. The hit refresh of gen_bound
  (:265-267), the replacement scan (:272-280), the store conditions (:293-301) and the handle check are shared, so the same entries
  are read and written in the same order. The lease and the flag are set in the same branch, the main worker runs on
  the thread that owns the TLS lease, and no helper exists in that case: the flag can never be true on a thread without
  the lease. The counter build (has_exclusive_access calls per TT access OFF vs a handful ON, equal bench nodes) is the
  right dynamic proof; the verify-build assert on every owned call closes the other direction.
- (c) OK with C2 (bench clears the TT per FEN, so TT accesses per node match a game).
- (d) OK: GCC on mingw-w64 lowers every `thread_local` to emutls (an out-of-line __emutls_get_address call), so the
  mechanism is real on this kit; after S4 the only TLS left in the lock is the cold string in eval_params.cpp:23,
  nothing on the search path. FIX S4-1: the Worker member and the Searcher scope guard go under the `#if` (C5),
  else the switch-0 exe differs. FIX S4-2: "Threads 2 / 4 bench" cannot test the multi-thread path because bench
  ignores Threads (forge-ltopgo-pgo pitfall): use `go depth 12` games at Threads 2 / 4 (and the TSan row) for the
  hang / race check. Note (no fix): any counter kind works in the counter build (it is never timed and counts
  has_exclusive_access calls, not TLS reads); a plain static is simplest.
- Verdict: OK with FIX S4-1, S4-2.

## Table
| Spec | (a) anchors | (b) node-identical + proof | (c) timing | (d) pitfalls | Verdict |
|---|---|---|---|---|---|
| Common | OK | OK (mutant step) | FIX C2, C3 | FIX C1, C4, C5 | FIX (5) |
| S1 NO_ZERO_MOVELISTS | OK (audit complete) | OK (subsequence verified) | OK | OK (poison build is the proof) | OK |
| S2 SLIDER_ATTACKS | OK | OK (exhaustive test) | FIX S2-1 | FIX S2-2, S2-3 | FIX (3) |
| S3 MATKEY_FAST | OK (0 / 300k) | OK | OK (C3) | OK | OK |
| S4 TT_NOTLS | OK (6 sites) | OK (:220 unlocked today) | OK | FIX S4-1, S4-2 | FIX (2) |

No BLOCKER. Nothing in the four mechanisms is wrong; the ten fixes are about the budget and order of the ABBA (C2 with
A/A first, C3), tooling that is missing rather than maybe-missing (C1), the byte-identity bookkeeping (C5, S4-1), a
too-hopeful S2 expectation (S2-1) and four small test-plan corrections (C4, S2-2, S2-3, S4-2). Order unchanged: S1, S2
microbench, S4, S3.
