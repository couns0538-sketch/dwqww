# Astra A1 — correction-history / history rework: UCI `HistRework` (design note, 2026-10-27)

Branch `opus-sol-A1` (base AL1 s198 lock `d4f4312` + CI baseline `0d99f02`). One new UCI option:

```
option name HistRework type spin default 0 min 0 max 3
```

`HistRework=0` (default) is the AL1 s198 lock search: every new statement sits behind
`if (search_options::hist_rework != 0)`, no new table is read or written, and bench/perft equal the lock pins
(`logs/uci_check_full_off.log`: `ALL OK`). Values 1..3 are the tune steps. No Elo claim: UNPROVEN until gated.

## 1. Idea

The lock's quiet history and its static-eval correction both learn from search results, but neither knows
about **tactical context** or about **which pieces go with a pawn structure**:

- **History, read and write (threat-keyed butterfly twin).** The lock's butterfly table `main[stm][from][to]`
  scores a quiet move the same whether the moving piece is hanging or the destination is covered by a cheaper
  enemy piece. A1 adds a twin table `T[stm][from_bit][to_bit][from][to]`. Its two extra index bits say whether
  the from square and the to square are **attacked by a lesser enemy piece** of the mover:
  - pawn, knight, bishop: attacked by an enemy pawn;
  - rook: by an enemy pawn, knight or bishop;
  - queen: by an enemy pawn, minor or rook;
  - king: never (a king cannot step onto an attacked square; evasions are a separate stage).

  Example: a knight on e4 hit by a pawn on d5 that retreats to c3 lands in slot `[1][0]` ("escape to a safe
  square"); Ne4-g5 into an h6 pawn lands in `[1][1]`. The twin learns the same bonuses and maluses as the lock
  table, with the lock's gravity rule (`apply_history`). `quiet_history` reads a blend of the two butterfly
  terms. Both are kept at the same ±16384 scale, so LMR, history pruning and move ordering see the same value
  range as in the lock.
- **Correction, blend and learning (pawn structure x non-pawn material).** The lock corrects the static eval
  with two tables: one keyed by the pawn structure, one by the piece counts. A1 adds a third table keyed by
  **one joint key**, the Zobrist pawn key mixed with the non-pawn material signature (counts of N, B, R, Q
  per colour). It learns "this pawn structure, with these pieces" — for example a weak square that matters
  with knights on the board but not in a rook ending. Neither existing table can express this: the pawn table
  averages over all material, and the material table averages over all pawn structures.
  - Because the joint key has more distinct values than either single key, its 16384-slot table aliases
    more. It therefore learns with a **gravity-style update**:
    `entry += step − entry·|step|/8192`. Stale or aliased values decay as new results arrive, and the entry
    approaches ±32 cp only asymptotically.
  - It uses the same residual step as the lock tables (`diff·min(depth+1,16)/256`) and the same update
    condition (the caller in `search()` is unchanged).

| level | butterfly term read by quiet_history | joint correction weight |
|---|---|---|
| 0 (default) | `main` (lock) | not read, not written |
| 1 | `(main·2 + T·2)/4` (50 % threat-keyed) | 50 (x0.01) |
| 2 | `(main·1 + T·3)/4` (75 %) | 75 |
| 3 | `T` (100 %, the twin replaces the lock term in the read) | 100 |

The continuation terms, the capture history, the lock correction tables and every update rule of the lock
tables are unchanged at every level.

## 2. IDEA_SOURCE (summary; full list in `IDEA_SOURCE.md`)
- **History heuristic, butterfly boards, history gravity.** Public techniques (Schaeffer; Hartmann;
  chessprogramming wiki). Gravity `h += b − h·|b|/D` is the lock's own `apply_history` (D = 16384).
- **Threat-keyed butterfly history.**
  - Public technique: several modern open-source engines index quiet history by threats on the from and
    to squares. Idea only.
  - Lesser-attacker split: the threatened-by-pawn / by-minor / by-rook square sets in Stockfish's move picker
    (PR #3970, cited on Forge's idea board P14). We use only that square-set structure, as an index, not as a
    static bonus.
  - No constants are taken from any engine.
- **Correction history and gravity on correction tables.** Public techniques (several open engines use a
  gravity formula for correction-history updates, e.g. Alexandria's release notes). The joint pawn x
  non-pawn-material key is our own construction.
- **SplitMix64 finaliser** (public domain), so every signature bit reaches the 14 index bits.
- No code, tables or tuned constants were copied. 16384 / 8192 / 256 are the lock's own limits and grain;
  50/75/100 % are round steps.

## 3. Why this is not a resubmission

| earlier item | what it did | gate / status | how A1 differs |
|---|---|---|---|
| contcorr (ContCorrectionWeight) | correction keyed by the previous move (piece, to) | G11 −1.4 (epa), G87 +5.1 ± 8.6 (h256_e12), capped | A1 adds no move-keyed correction. Continuation correction is skipped (also C2 bit 1) |
| C2 `CorrHistPlus` (opus-C2) | correction keyed by the last two moves; minor-piece placement; non-pawn placement per colour | branch done, not gated | A1's key is pawn placement x non-pawn **counts**. C2 keys non-pawn **placement** and ignores pawns |
| NonPawnCorr (Pack A, P1) | correction keyed by the non-pawn board key (placement) | G14 +5.2, G34 +11.1 ± 7.9 (LLR 2.48), G38 +6.5, all capped | different key, as for C2. NonPawnCorr sees where the pieces stand, not which pawn structure they go with |
| PawnHist (P3) | quiet history keyed by the pawn structure | G37 +4.6 ± 8.4, capped | A1 keys quiet history by tactical threat bits, not by pawn structure |
| LmrCorrThreshold (P7) | LMR from the correction magnitude | G16 −0.7 | A1 does not use the correction size in any search decision (O5 and O8 do that) |
| CorrGravity = omni-s S1 (`CorrUpdateMode`, `CorrDiffClampCp`, `CorrLimitCp`) | gravity / retuned clamps on the lock's pawn and material tables | queued G63/G68, never run | A1 leaves the lock tables' add-and-clamp rule untouched. Gravity is used only for the **new** joint table, whose sparse key is the reason to forget |
| omni-s S3 (`ThreatHist`, `ThreatHistDiv`) | butterfly twin keyed by "attacked by **any** enemy piece" | queued G64, never run | A1 keys by "attacked by a **lesser** enemy piece", per moving piece type (see below) |
| P14 `ThreatOrderPct` (Pack E) | **static** ordering bonus/malus for threatened from/to squares | parked: tactics loss, d22 +91 % nodes | A1 adds no static term. The twin **learns** from cutoffs, so a working sacrifice into a pawn-covered square is rewarded in its own slot |
| O5 `CorrMargins`, O8 `CorrExt` | correction magnitude widens pruning margins / triggers extensions | branches done | consumers of the correction, not its learning or blend. Not part of A1 |
| MinorCorrWeight (G79) | minor-piece correction weight | queued | different key |

**Why the lesser-attacker key and not "attacked by anything".**
- In middlegames most squares near the centre are attacked by some enemy piece. The any-attacker bit
  therefore splits the statistics on a mostly uninformative property: a knight move to a square covered by a
  distant enemy queen and defended by us is fine.
- The lesser-attacker bit marks exactly the squares where the piece is **en prise whatever the defence**:
  - to-bit = moving into a losing exchange unless there is a tactic;
  - from-bit = the piece is hanging now, so moves of it are escapes.

  That is the context in which the plain butterfly entry of the same (from, to) is least representative.

**Spec parts covered elsewhere and skipped.**
- "Continuation correction (previous move piece+to)": contcorr + C2 bit 1.
- A blend keyed on non-pawn **placement**: NonPawnCorr + C2 bit 4.
- Correction-magnitude consumers: O5, O8.

A1 covers the remaining parts:
- "gravity-style update", on the new table only;
- "a correction blend keyed on pawn structure and on non-pawn material", as one joint key;
- "threat-keyed quiet history".

## 4. Overflow proof

**Int widths.**
- `int` is 32-bit on both targets (MinGW-w64 x86-64 LLP64, Linux x86-64 LP64).
- History tables are `std::int16_t`, correction tables `std::int32_t`; bitboards and keys are `std::uint64_t`.
- C++ integer division truncates toward zero.
- Lock tunables are bounded by their UCI ranges (`tune::parameters()`; setoption clamps):
  - `HistoryBonusMax` <= 10000, `HistoryBonusQuadratic` <= 100, `HistoryBonusLinear` <= 500;
  - `MaterialCorrectionWeight` <= 300, `LmrHistoryDivisor` >= 1000, `HistoryPruneMultiplier` <= 20000.
- `HistRework` is clamped to 0..3. The level helpers clamp again, so read quarters are in {2,3,4} and the
  joint weight is in {50,75,100}.

**Lemma G (gravity).** Let D > 0 and |e| <= D, |s| <= D, with n = e + s − trunc(e·|s|/D). Then |n| <= D.

*Proof.* Write a = |s|. Since trunc is odd, n(−e, −s) = −n(e, s), so it suffices to take s = a >= 0.
- e >= 0. Here trunc = floor, and floor(x) > x − 1, so n < e + a − e·a/D + 1 = D − (D−e)(D−a)/D + 1 <= D + 1.
  n is an integer, so n <= D. Also n >= e + a − e·a/D = e(1 − a/D) + a >= 0.
- e < 0. Here trunc(e·a/D) = −floor(|e|·a/D), so n = −|e| + a + floor(|e|·a/D).
  - Upper: n <= a − |e|(1 − a/D) <= a <= D.
  - Lower: n >= −|e| >= −D.

∎ The unit test checks the lemma by brute force:
- all (e, s) with |e| <= 8192 and |s| <= 128 (the reachable domain, 4.2 M pairs);
- |e| <= 8192 against a grid of |s| <= 8192;
- the exact fixed points: constant maximal steps reach exactly ±8192, and ±16384 with bonus 10000.

**Tables (invariants).**

| table | type | invariant | kept by |
|---|---|---|---|
| `main_history_` (lock) | int16 [2][64][64] | \|h\| <= 16384 | `apply_history` = Lemma G, D = 16384 (unchanged) |
| `continuation_history_` (lock) | int16 [13][64][13][64] | \|c\| <= 16384 | same (unchanged) |
| `threat_history_` (A1) | int16 [2][2][2][64][64] = 64 KiB | \|t\| <= 16384 | the same `apply_history` |
| `correction_history_`, `material_correction_` (lock) | int32 [2][16384] | \|p\|, \|m\| <= 8192 | lock clamp (unchanged) |
| `joint_correction_` (A1) | int32 [2][16384] = 128 KiB | \|j\| <= 8192 | `hist_rework::gravity` = Lemma G, D = 8192, plus a guard clamp that never fires (test) |
| `threat_maps_` (A1) | uint64 x 7 x 136 plies = 7.4 KiB | — | bit operations only |

**Update side.**

1. **History bonus.** `history_bonus(d) = min(HistoryBonusMax, Q·d² + L·d − 32)`.
   - Node depth is at most 64 (the `go`/bench depth clamp) plus one per double extension along a path of
     fewer than 128 plies, plus 1 (the `best > beta + 100` bump), so d < 200.
   - So Q·d² + L·d <= 100·40000 + 500·200 = 4.1·10^6 < 2^31.
   - The bonus is at most 10000; the maluses are −bonus, the PV-node bonus is bonus/4. All reach
     `apply_history` with |b| <= 10000 <= 16384.
2. **`apply_history(t, b)` on T**, exactly as on the lock table:
   - `clamped = clamp(b, ±16384)`;
   - |t·|clamped|| <= 16384² = 2^28 < 2^31;
   - |t + clamped| <= 32768;
   - by Lemma G, |result| <= 16384, so the int16 store is exact.

   Test: two T slots driven from 0 to exactly +16384 and −16384 in 11 updates of ±10000. Every step equals the
   lock formula re-derived in int64.
3. **`update_correction` step.** The caller excludes mate scores and in-check nodes, so:
   - |best| <= MateInMaxPly − 1 = 31871 and |static_eval| <= 31871 (corrected_eval clamps);
   - (best − se)·256 <= 63742·256 = 16,317,952 < 2^31, and that value is clamped to ±2048;
   - depth >= 0 at the call (IIR lowers it at most once from >= 1), so weight = min(depth+1, 16) is in 1..16;
   - |diff·weight| <= 32768, so |step| = |diff·weight/256| <= 128.

   Test: the update with best = +31871 against eval = −31871, the worst product.
4. **Joint gravity.**
   - |j·|step|| <= 8192·128 = 2^20. Over the general domain |step| <= 8192 it is <= 2^26.
   - |j + step| <= 8320.
   - By Lemma G, |result| <= 8192.

   Test: a same-sign maximal step at ±8192 stays exactly ±8192, and maximal steps from 0 reach exactly +8192
   (346 updates).
5. **Lock correction tables.** Unchanged: entry + step is at most 8320 before the lock's clamp.
6. **Index arithmetic.**
   - T index: [side in 0..1][bit][bit][from < 64][to < 64]. Bits come from `(set >> sq) & 1`, and
     sq = Move::from/to < 64, so no shift by 64 or more.
   - Joint index: `key & 16383`.
   - `threat_maps_[ply]`: written and read only for 0 <= ply < MaxPly (`search`/`qsearch` return earlier at
     ply >= MaxPly), and the array has MaxPly + 8 entries.
   - `pop_lsb` runs only on non-zero bitboards (the loop guards).
7. **Keys.**
   - `non_pawn_material`: eight 4-bit counts in a uint32. The first count ends shifted by 28 bits, so all
     shifts are unsigned and stay below 32. Counts are saturated at 15; at most 10 occur in legal chess.
   - `mix64` and `joint_key`: uint64 multiply/xor/shift, whose wrap-around is defined.

**Read side.**

1. **`quiet_history`.**
   - blend(h, t, q) with |h|, |t| <= 16384 and q in 0..4: |h·(4−q) + t·q| <= 4·16384 = 65536, so the result is
     at most 16384.
   - Adding the two continuation terms: |sum| <= 3·16384 = 49152. That is the **same bound as the lock**,
     whose sum is main + c1 + c2.

   Test: the worst case is read as exactly −49152 at every level; the mixed-sign read equals the int64
   reference.
2. **Consumers of `quiet_history`** are unchanged and keep the lock's bound:
   - picker score <= 49152 + 12000 = 61152;
   - LMR `history / LmrHistoryDivisor` (divisor >= 1000), clamped to ±2;
   - history pruning: 20000·d < 4·10^6.
3. **`corrected_eval`.** correction = p + m·MW/100 + j·w/100:
   - |m·MW| <= 8192·300 = 2,457,600 and |j·w| <= 8192·100 = 819,200;
   - |correction| <= 8192 + 24576 + 8192 = 40960, i.e. at most 160 cp after /256. The lock's maximum is 128 cp.
   - raw_eval comes from the evaluator or from the int16 TT field, so it is within ±32767; this is the lock's
     own assumption.
   - So |raw + correction/256| <= 32927, then the lock's mate-range clamp applies.

   Test: all three tables filled with ±8192 and MW = 300 give exactly raw ± 144 / 152 / 160 for levels
   1 / 2 / 3, and the mate-range clamp holds.
4. **Search-level stress.** Searches run at level 3 with HistoryBonusMax / Quadratic / Linear =
   10000 / 100 / 500 and MaterialCorrectionWeight = 300 (all at their UCI maxima). Afterwards every entry of
   every touched table is checked against its bound.
   - On CI the same test runs under ASan + UBSan (`-fno-sanitize-recover=all`).
   - On the PC it runs in a `-fsanitize=undefined -fsanitize-undefined-trap-on-error` build, together with an
     engine bench at `HistRework=3` with those tunables at their maxima (`logs/ubsan/`). MinGW has no
     libubsan, so trap mode is the only option. A positive control shows the trap build dies on a signed
     overflow that the plain build silently wraps (`logs/ubsan_positive_control.log`).

## 5. Tuning ranges

| knob | shipped steps | safe range (proof holds) | note |
|---|---|---|---|
| `HistRework` (UCI) | 1, 2, 3 | 0..3 | the only new option |
| threat quarters q (per level) | 2, 3, 4 | 0..4 | q = 0 equals the lock read with the twin still learning |
| joint weight w (x0.01, per level) | 50, 75, 100 | 0..300 | at 300, \|correction\| <= 57344 (224 cp); proof unchanged |
| joint gravity limit | 8192 (= lock limit) | 1..32767 with \|step\| <= limit | Lemma G |
| lesser-attacker definition | fixed | — | change only with a new test fixture |

If a level reaches H1, the natural follow-up is to tune q and w separately. Each knob would get its own
temporary tunable, kept out of the default build's option list.

## 6. Nodes (bench, Threads 1, Hash 16, OwnBook false; PC box-recipe exe; `logs/bench_sweep_full.log`)

Exe `forge_a1_a8b63aa.exe` (engine commit `a8b63aae`). The first build of the same sources (`logs/sweep_v1_full.log`)
gave identical counts.

| HistRework | d11 | d13 | d16 | d20 | d22 |
|---|---|---|---|---|---|
| 0 (= lock pins) | 312866 | 862329 | 3024920 | 12389307 | 34048354 |
| 1 | 373261 (+19.3 %) | 1043893 (+21.1 %) | 3399770 (+12.4 %) | 13180132 (+6.4 %) | 35699757 (+4.9 %) |
| 2 | 320427 (+2.4 %) | 881902 (+2.3 %) | 3041041 (+0.5 %) | 12218938 (−1.4 %) | 28571078 (−16.1 %) |
| 3 | 336192 (+7.5 %) | 869621 (+0.8 %) | 3052885 (+0.9 %) | 15664938 (+26.4 %) | 35705218 (+4.9 %) |

- **A1 blowup flag (>1.5x vs OFF):** none. The largest ratio is 1.264 (level 3, d20).
- **Every ON value changes nodes at d11 and d13.**
- **Crew node rule** (<= +10 % at d13/d16; d20/d22 growth = longer-TC flag), quoted for the gate plan:
  - level 2 passes d13/d16;
  - level 3 passes d13/d16 but has a d20 flag;
  - level 1 fails at d13 (+21.1 %) and d16 (+12.4 %).
- The nps printed by the sweep are single runs on the loaded PC over different trees. They are not a speed
  measurement.

## 7. Risks and limits
- **Two parts in one option.** A gate verdict cannot attribute Elo to either part. The SPRT plan orders the
  levels to limit this; a split follow-up is listed there.
- **Learning speed.** The threat twin starts at zero in each `ucinewgame`. Rare contexts (bits 1/x) get few
  updates at 10+0.1, and level 3 relies fully on them in the read. That is why level 3 is not the first gate.
- **NPS.** A1 adds per-node cost when ON:
  - the threat maps, once per main-search node (pawn shifts plus knight/bishop/rook lookups);
  - one extra table load per scored quiet;
  - the joint key, 8 popcounts plus SplitMix64, per corrected eval, including qsearch.

  No speed claim (loaded PC).
- **Memory.** About +200 KiB per search thread (allocated in every build, cleared with the other tables).
