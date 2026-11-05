# SPEC_EVAL: implementation specs for T04-02 (own constants, packb ReSearchAdjust) and the eval option cards T06-05, T06-04

Started 00:55 PC clock (`date`), planned stop 01:40, written by 01:12. Status: COMPLETE (no section PENDING).
Lock FD3A5190 = AL1 s198 source, read-only:
`C:/Users/Administrator/grok-pc/forge_push/qa_ltopgo_al1_stage/src_al1s198_clean` (below: `search.cpp` = `src/search.cpp`,
`search.hpp` = `include/forge/search.hpp`). Own prior code read: packb `C:/Users/Administrator/grok-pc/forge_push/src_packb_h256`.
Nothing here edits the engine; every Forge-side number is UNPROVEN.

## Common parts
- Lock pins (bench d11 / d13 / d16 / d20 / d22, base FD3A5190): 312866 / 862329 / 3024920 / 12389307 / 34048354
  (F:/forge_push/uhoE3c_evalrule50damp30_vs_AL1lp/PREBENCH.txt, "base ... MATCH"). Every OFF identity proof below =
  these five numbers from the candidate exe at its defaults, plus perft unchanged (the R15 kit's pin_check OFF/ON).
- Option mechanism (lock): plain `tune::` ints plus one row each in `tune::parameters()` (`search.cpp:13-103`, table function `parameters()` from `:66`,
  `{name, &var, min, max}`). `uci.cpp:174-180` ADVERTISES them only when built with `FORGE_EXPOSE_TUNABLES` (kit
  `-Expose`); `uci.cpp:204-215` ACCEPTS them in every build and silently clamps to [min, max] (`:213`). Two consequences:
  (a) the crew's option check wants "options advertised" (UE3C ENGINE_OPTIONS_CHECK.txt), so the gate exe must be an
  `-Expose` kit build; (b) a value outside the row's range is clamped without a message (matters for T06-05 step 2).
  A table min below 0 is allowed (the struct holds plain ints).
- Values are read live from `tune::` in search (E3 copies its four option values into Worker members once per search, its `search.cpp:1420-1423`).
- Gate form = the crew's queue argv (UE3C RUN_INFO.json "argv"): `-engine name=<cand> cmd=<cand.exe> option.Threads=2
  option.Hash=16 option.OwnBook=false <option.X=v> -engine name=base_AL1_s198_ltopgo_x_FD3A5190
  cmd=C:/Users/Administrator/grok-pc/forge_push/bin/forge_ltopgo_x_al1s198_v23.exe option.Threads=2 option.Hash=16
  option.OwnBook=false -each tc=10+0.1 timemargin=1000 proto=uci -openings
  file=C:/Users/Administrator/grok-pc/coder-fuzz/UHO_Lichess_4852_v1.epd format=epd order=random -games 2 -repeat
  -concurrency 4 -sprt elo0=0 elo1=10 alpha=0.05 beta=0.05 model=normalized -recover` (runner picks srand, start, cap).
  The cards' route says "[0,5]"; the crew queue runs [0,10] normalized (nElo). On this gate the nElo / Elo ratio is
  about 1.9 (UE3C: +1.51 Elo = +2.86 nElo, FORGE_RESULTS.csv row UE3C), so [0,10] nElo is close to [0,5] Elo - own
  arithmetic from one row, not a conversion rule. STC cost: cap 12k, mean ~6.6k games ~13 h at 430-502 games/h
  (WORKER_RULES round 2). LTC (only after an STC that is not H0): 30+0.3, [0,15] nElo, cap 6,000, Hash 32-64, mean
  ~2.95k games ~18 h, cap ~36 h (notes/T12/PROTOCOLS.md:84-88). FORGE_RESULTS.csv has no LTC row yet (0 hits).
- Every gate is one option alone vs the lock (never with another candidate). Forge-side Elo: none claimed; card
  estimates stay UNPROVEN.

## T04-02 ReSearchAdjust (lock port of own packb code, own constants, PV adjust, ply guard)
Card `cards/T04/T04-02-lmr-deeper-shallower.md`; second vote `notes/TOP_SECOND_VOTE.md:8-10, :18-19, :49-50`.

### Lock function and lines (`Worker::search`, `search.cpp:875`)
- `:1116-1117` `new_depth = depth - 1 + extension`, declared `const` (stays const: the port adds a separate local).
- `:1136` full_depth_needed init; `:1137` LMR entry (depth >= 2, move_count > 1 + root, quiet or not ttPv or
  move_count > 4); `:1138-1146` r; `:1147` reduced_depth = clamp(new_depth - r, 1, new_depth); `:1148` reduced
  null-window search (child cut flag true); `:1149` re-search wanted iff score > alpha AND reduced_depth < new_depth;
  `:1150-1153` the re-search at new_depth, child cut flag `!cut_node`; `:1154-1157` continuation bonus;
  `:1159-1161` full-depth null-window search of non-reduced moves; `:1162-1163` PV full-window search at new_depth.
- `best_score`: `:1038` starts at -Infinite; the first legal move is never pruned (`:1061` needs best_score >
  -MateInMaxPly), so at the LMR step (move_count >= 2) best_score is a real score and best_score <= alpha.
- Ply-guard inputs: `ply` (`:878`), `root_depth_` (`search.hpp:341`, set each iteration at `search.cpp:1380`; per
  worker, so helper threads use their own depth), MaxPly 128 (`search.hpp:55`), stack MaxPly + 8 (`search.hpp:324`).
- Own prior code (read): packb `src_packb_h256/src/search.cpp:1168-1182` (block), options `:65-68`, `:106-107`,
  `include/forge/search.hpp:247-250`. packb: deeper if score > best + Base + PerDepth x new_depth (60 / 2), shallower
  if score < best + Margin x new_depth (1) to max(new_depth - 1, reduced_depth), no root, PV search `:1192` NOT adjusted.

### What is new vs packb (second vote `:18`)
1. Own defaults (packb's 60 + 2 x depth is Patricia PR 137's tuned rule and 1 x depth Caissa 434bbda's: not reused).
2. The PV full-window search of an adjusted move uses the adjusted depth (the card's mechanism), switchable.
3. Ply guard on the deeper step.
4. The r = 1 case decided (packb then re-searched AT the reduced depth with only the child cut flag flipped: a
   repeated search).
5. Gated alone on the lock (packb gates 12 / 35 / 40 / 41 all ran with FiftyDamp=1 on older bases).

### OFF-by-default options (rows in `tune::parameters()`; names continue packb's so the records line up)
| option | default | range | meaning |
|---|---|---|---|
| ReSearchAdjust | 0 | 0-1 | master switch; 0 = the lock code path, nothing below is read |
| ReSearchDeeperBase | 70 | 0-300 cp | one ply deeper when score - best_score > Base + PerDepth x new_depth |
| ReSearchDeeperPerDepth | 0 | 0-20 cp/ply | depth part (0 = constant margin; an SPSA knob) |
| ReSearchShallowerBase | 10 | 0-100 cp | one ply shallower when score - best_score < Base + PerDepth x new_depth; Base 0 with PerDepth 0 = never (score > alpha >= best_score) |
| ReSearchShallowerPerDepth | 0 | 0-10 cp/ply | depth part |
| ReSearchMaxPlyPct | 250 | 100-400 % | no deeper step once ply x 100 >= Pct x root_depth_ |
| ReSearchPv | 1 | 0-1 | 1 = PV full-window search of an adjusted move at the adjusted depth; 0 = at new_depth (packb) |

Own starts (card T04-02): 70 cp constant (Caissa: constant 80; Patricia: 60 + 2 x depth - neither), 10 cp constant
(Caissa: depth-proportional; Patricia: no shallower step), 250 % (Caissa's own path guard is 2 x root depth - not
taken). The card's LmrDeeperMargin / LmrShallowerMargin / LmrDeeperMaxPlyPct become ReSearchDeeperBase /
ReSearchShallowerBase / ReSearchMaxPlyPct with the same values under one switch, so the gate sets ONE option.
packb's `ReSearchShallowerMargin` (a per-depth factor) is not carried: its meaning differs from the new Base.

### Pseudocode (own words)
    research_depth = new_depth                         -- new local, before the LMR block
    LMR block: reduced search as in the lock
      if score > alpha and reduced_depth < new_depth:  -- the lock's re-search condition, unchanged
          if ReSearchAdjust on, not root, not aborted:
              gain = score - best_score                -- > 0 here
              if gain > DeeperBase + DeeperPerDepth * new_depth and ply * 100 < MaxPlyPct * root_depth_:
                  research_depth = new_depth + 1
              else if gain < ShallowerBase + ShallowerPerDepth * new_depth and new_depth - 1 > reduced_depth:
                  research_depth = new_depth - 1
          null-window re-search at research_depth, child cut flag = not cut_node (as the lock)
      continuation bonus as the lock
    non-reduced full-depth search: unchanged (new_depth)
    PV full-window search: depth = research_depth if (switch on and ReSearchPv = 1) else new_depth

r = 1 rule (decided here): when new_depth - 1 would equal the reduced depth there is NO shallower step and the
re-search runs at new_depth like the lock. So every reduced fail-high is still checked by a deeper search, and every
re-search keeps reduced_depth < research_depth <= new_depth + 1. The other reading (skip the re-search and keep the
reduced score, `TOP_SECOND_VOTE.md:19`) accepts a marginal fail-high from a reduced search; it is a possible second
form for later, not in this gate. Deeper is tested first; both steps compare with best_score (not alpha), so after
earlier moves failed low by a lot the gain is large - the intended "far above everything so far" reading.
Extensions are untouched; with a double extension new_depth can be depth + 1 and a deeper step depth + 2, which is
what the ply guard bounds.

### Identity proof (OFF)
At ReSearchAdjust = 0 the block never runs and research_depth == new_depth at both uses, so every child search has
the lock's depth, window and cut flag: same tree, the five lock pins, perft unchanged. Run the OFF pins a second time
with the six other knobs at extreme values (DeeperBase 0, DeeperPerDepth 20, ShallowerBase 100, ShallowerPerDepth
10, MaxPlyPct 100, Pv 0) and the switch at 0: still the lock pins (proves they are read only under the switch). No struct or stack change (one local).

### ON-live check
ReSearchAdjust = 1: all five bench depths differ from the lock pins and repeat exactly on a second run (bench is one
thread); store them as the runner's "cand ON" pins (as UE3C PREBENCH does). Per-knob live check with the switch on
(pin_on_live, BUG_CHECKLIST row 18): DeeperBase 70 -> 300, ShallowerBase 10 -> 0, MaxPlyPct 250 -> 100, Pv 1 -> 0,
DeeperPerDepth 0 -> 5, ShallowerPerDepth 0 -> 5: each must change at least one bench depth.

### Box tests
1. Debug-build asserts at the re-search: reduced_depth < research_depth <= new_depth + 1; research_depth == new_depth
   at the root; new_depth + 1 only when ply x 100 < Pct x root_depth_ (BUG_CHECKLIST row 20).
2. Counters in a verify build (`info string` after bench): reduced fail-highs, deeper steps, shallower steps,
   shallower steps stopped by the r = 1 rule, deeper steps stopped by the ply guard, root adjustments (must be 0).
   Sanity: deeper + shallower <= reduced fail-highs; at DeeperBase 300 deeper is about 0.
3. Explosion / ply guard (second vote `:9`; BUG_CHECKLIST rows 13 and 21): per bench position and iteration, max
   seldepth and nodes ON vs OFF; flag any iteration with > 20x the previous iteration's nodes and any seldepth >= 120
   (MaxPly 128); then time-to-depth under a node cap on a stress set (long forced mates, perpetual-check and
   many-check endgames, the BUG_CHECKLIST row 13 repro FEN).
4. Mate probe OFF / ON: every mate found, at the same or a lower depth.
5. Threads = 2 smoke (the gate setting): the R15 kit's 2-minute movetime smoke, engine-side legality, no time loss.

### Gate line
Candidate: fresh LF lock copy + this patch (skill forge-lock-port), kit v2.3 `-Expose` build with pc1 = pc2 (skill
forge-r15-candidates, `cand_pack.ps1`). Crew form (Common) with `option.ReSearchAdjust=1` only, STC [0,10] nElo cap
12k; if not H0, LTC 30+0.3 [0,15] cap 6k. packb gates 12 / 35 / 40 / 41 are not results for this line (bundle, old
bases, copied constants). The option NAME is packb's, so tag the candidate distinctly (exe name and INDEX entry e.g.
`rsa2_own`, gate tag `uhoRSA2_researchadjust_own_vs_AL1lp`) so that a later `tried_gates.py --grep ReSearch` does not fold
the new result into gates 12 / 35 / 40 / 41.

### Crew hours
Port ~1 h (about 12 lines in the block, 7 table rows, 7 declarations in `search.hpp`); proofs ~2 h (OFF pins twice,
ON pins twice, 6 knob checks, asserts + counters build, seldepth / nodes table, mate probe, smoke); kit build +
cand_pack + index_check ~0.5 h: about 3.5 crew h. CPU: STC mean ~13 h (cap 12k = 24-28 h), LTC mean ~18 h (cap
~36 h). No GPU. Forge estimate stays the card's +2 to +6 Elo **UNPROVEN**.

## T06-05 EvalRule50Damp at the fitted strength (E3 exe first; packb FiftyDamp not ported)
Card `cards/T06/T06-05-rule50-damp-fitted.md`; second vote `notes/TOP_SECOND_VOTE.md:20-21, :49-50`.

### Lock function and lines (no rule50 eval damping in the lock)
- Eval sites: qsearch `search.cpp:807-809`, search `:935-937`: raw_eval = TT eval or `static_evaluate`, then
  `static_eval = corrected_eval(board, raw_eval)`; `corrected_eval` `:638-645` (pawn + material correction, clamp).
- TT stores the RAW eval: `:817`, `:868`, `:1023`, `:1214`. MaxPly leaves return the raw `static_evaluate` (`:781`,
  `:894`). Correction update from `ss->static_eval` at `:1218-1222`.
- rule50 today: draw at 100 (`is_draw` `:694-697`), TT score guard (`search.hpp:83-86`), TT-cutoff clock < 90
  (`search.cpp:922`). Nothing scales the eval by the clock.

### Existing own code
- E3 (exe `C:/Users/Administrator/grok-pc/forge_push/bin/forge_ltopgo_x_e3evalpost_al1_22fd274d.exe`, sha256
  22FD274D...; source `C:/Users/Administrator/grok-pc/forge_push/stage_e3_evalpost/e3_evalpost_al1_src.zip`, its
  `src/search.cpp`): option `:67`, table row `:105` (`EvalRule50Damp` 0..60), `e3_post_eval` `:643-668` (returns its
  input when all three E3 values are 0, `:648`; rule50 part `:663-667`), applied at `:857` (qsearch) and `:985`
  (search) as `corrected_eval(board, e3_post_eval(board, raw_eval))`; read once per search `:1420-1423`; TT stores stay
  raw (`:865`, `:916`, `:1071`, `:1262`); its proof record is `README_E3_CANDIDATE.md` in the same zip ("README"
  below). Form: v minus v x D x min(clock, 100) / 10000 in 64-bit, truncation toward
  zero, so it is odd-symmetric; clock 0 leaves v unchanged; D = 60 keeps 40 % at clock 100, D = 81 keeps 19 %,
  D = 100 zeroes it.
- packb FiftyDamp (`src_packb_h256/src/search.cpp:656-662`, used at `:826` and `:955`): damps the CORRECTED
  `ss->static_eval` by (200 - clock') / 200 (= about E3 D = 50 at start 0; Patricia PR 153's exact form). Not ported:
  the fit below was made on the RAW static eval (opus-r13-p7-e3fit `opus_r13/p7/RESULTS.md:8, :10`: "all on the raw
  static eval", raw lock evals via raw_eval.cpp), so its D does not transfer to a post-correction damping; and packb's
  four gates (12 / 35 / 40 / 41) were bundles with ReSearchAdjust on older bases.

### The fitted strength (own data, calibration only)
RESULTS.md (branch opus-r13-p7-e3fit @ 360e49df): `:77` D = 81 held-out log-loss 0.566624, -0.002456 vs OFF
[-0.003777, -0.001333], not on a bound; `:84` 81 vs 60 -0.000318 [-0.000632, -0.000039] ("barely separated");
`:87` 81 vs the hand value 30 -0.001191 [-0.001996, -0.000498]. Game bootstrap 2000, 80/20 split by game. A static
calibration, not strength: only the gate decides. UE3C (D = 30): +1.51 Elo, 3,000 games, LLR -0.53, cap.

### Option design (no new option; one range change in step 2)
- Step 1 (no rebuild): the E3 exe as built, `EvalRule50Damp` default 0, range 0-60, gate value 60 (the range max,
  RESULTS.md:93 candidate line 1).
- Step 2 (only if step 1 is not H0): E3 source with ONE change, table row `:105` max 60 -> 100 (own range 0-100: 100
  zeroes the eval at clock 100, a natural end), default stays 0; gate value 81 (the own held-out optimum).
- Not added: a start clock / knee (no fit yet - FIT_RECIPE step 6 is unrun; packb's starts 10 / 20 / 40 were bundle
  gates), damping of the correction term, packb's form.
- If a step passes: adopting means the E3 exe at that value (OFF = lock elsewhere); a minimal lock port with only
  the rule50 piece is an owner choice, not needed for the gates.

### Pseudocode (own words, = E3 as built)
    raw = TT eval or static_evaluate            -- TT keeps raw (unchanged)
    v = raw
    if D > 0: v = v - v * D * min(clock, 100) / 10000   (64-bit, toward zero)
    v = clamp(v, +-(MateInMaxPly - 1))
    static_eval = corrected_eval(board, v)       -- correction added undamped (E3 order, README r2 note :99)

### Identity proof
- Step 1: already executed for this exe - UE3C `PREBENCH.txt`: cand OFF d11-d22 = the five lock pins (MATCH), perft5
  4865609 and kiwipete5 193690690 OFF (README_E3_CANDIDATE.md:98). Nothing new is built.
- Step 2: the range change moves only the clamp, so for every value <= 60 the new exe must give the OLD exe's nodes:
  OFF = lock pins; D = 30 = 302045 / 692834 / 2650909 / 11384271 / 40565493 (UE3C cand ON pins); D = 60 = step 1's ON
  pins. Bit-equal benches at 0 / 30 / 60 are the proof that nothing else changed.

### ON-live check
- Step 1: bench at D = 60 twice: differs from the lock pins and from the D = 30 pins, repeats exactly; becomes the
  runner's "cand ON" want list (the runner checks it, as for UE3C).
- Step 2 trap: the OLD exe clamps `setoption name EvalRule50Damp value 81` to 60 without a message (`uci.cpp:213` in both the lock and E3),
  and the runner's option check (ENGINE_OPTIONS_CHECK.txt) only proves the option was SENT. So the step-2 live proof is
  bench(81) != bench(60) on the NEW exe AND bench(81) == bench(60) on the old exe (shows the clamp); the runner's
  PREBENCH "cand ON" want list must hold the NEW exe's D = 81 pins - that list is what stops a queue entry that
  points at the old exe.

### Box tests
1. Unit grid (v in +-3000, clock 0-120, D in 0 / 30 / 60 / 81 / 100): clock 0 unchanged; |result| never grows with the
   clock; result(-v) == -result(v); clock > 100 acts as 100; D = 100 at clock 100 gives 0; result within the clamp.
2. TT stays raw: verify-build assert at the four store sites that the stored eval equals the node's raw eval (the
   damping is clock-dependent; a damped TT eval would leak across clocks - the reason E3 keeps raw).
3. tests/rule50_tests.cpp (lock test, carried unchanged in E3) runs with the tune defaults, i.e. OFF only. Add a run
   of the same fixtures with EvalRule50Damp at 60 and 81: mate on the hundredth half-move still wins, the resetting
   capture / pawn move children are still evaluated, the clock-99 one-ply draw stays exactly 0.
4. Mate probe at 60 and 81 (E3 README :102-103 did 30 and 60): mate scores identical to OFF, no cp beyond +-30000.
5. Tactics sanity only: E3's Arasan screen flagged D = 30 at arasan2026 40 vs 46 (README :114-122, "soft flag");
   repeat at 60 / 81 and report beside the gate - no Elo reading.
6. Optional counter: mean |correction| at nodes with clock >= 60, ON vs OFF over the bench (the correction is added
   undamped after the damping, so at D = 81 it is a larger share of the eval at high clocks).

### Gate lines
- Step 1: crew form (Common) with `-engine name=cand_e3evalpost_22fd274d_r50d60
  cmd=C:/Users/Administrator/grok-pc/forge_push/bin/forge_ltopgo_x_e3evalpost_al1_22fd274d.exe option.Threads=2
  option.Hash=16 option.OwnBook=false option.EvalRule50Damp=60` vs the lock, STC [0,10] nElo cap 12k (UE3C used a
  3,000 cap: no decision).
- Step 2 (not H0 at step 1): the new exe with `option.EvalRule50Damp=81`, same form. Either step: LTC 30+0.3 [0,15]
  cap 6k only after an STC that is not H0.

### Crew hours
Step 1: ~0.5 h (two ON benches, want list, queue line, option check) - matches the card. Step 2: ~2 h (one-token
change, kit `-Expose` build pc1 = pc2, benches at 0 / 30 / 60 / 81 on both exes, rule50 fixtures ON, mate probe,
smoke, cand_pack / index_check). CPU: STC mean ~13 h per step (cap 24-28 h), LTC mean ~18 h. No GPU. Forge estimate
stays the card's 0 to +3 Elo **UNPROVEN**.

## T06-04 EvalGrain (new option on the lock; own grain values from the fitted slope)
Card `cards/T06/T06-04-eval-grain-jitter.md`; source = Stockfish d212e66 / PR 5449 (GPL-3.0, ideas only: commit text
and fishtest logs): STC +0.91 (220,960 games, <0,2>, LLR 2.95), LTC +2.42 (48,966 games, <0.5,2.5>, LLR 2.94).

### Lock function and lines
- No eval grain in the lock (`CorrectionGrain` 256 at `search.hpp:258` is the correction-history fixed point,
  `search.cpp:644`, not an eval grain).
- Hook = the argument of `corrected_eval` at the two eval sites: qsearch `search.cpp:809`, search `:937` (on an E3
  build: after `e3_post_eval`, E3 `search.cpp:857`, `:985`). New function beside `corrected_eval` (`:638`).
- TT stores stay raw (`:817`, `:868`, `:1023`, `:1214`), MaxPly leaves stay raw (`:781`, `:894`), like E3's rule.
- Values that see the grain: `ss->static_eval` and `eval` (stand pat, RFP / NMP / futility / probcut margins, the
  improving test `:947-948`, the correction update `:1218-1222`). Ties in `improving` (strict >) get more frequent.

### OFF-by-default options (rows in `tune::parameters()`)
| option | default | range | meaning |
|---|---|---|---|
| EvalGrain | 1 | 1-32 eval units | 1 = identity (no rounding, no jitter); G >= 2 rounds the static eval to a multiple of G |
| EvalGrainJitter | 1 | 0-2 | read only when G >= 2: 0 = none, 1 = +-1 from one fixed bit of the position key, 2 = +-1 from the node counter (the card's wording) |

Own grain values: G = 4, 8, 12 from the fitted win-probability slope (`notes/T06/FIT_RECIPE.md:49-51`, own
derivation: OFF slope a = 1.85, dp/dv = a / 1600 at p = 1/2, so 4 / 8 / 12 units are about 0.5 / 0.9 / 1.4 % steps);
gate value 8. No source constant is used. Jitter default = key (1), not the card's node count: a key bit makes the
grained eval a pure function of the position, so a TT re-visit, the second thread and an offline fit tool (FIT_RECIPE
step 7 can recompute it from the FEN) all see the same value; the node-count form (2) stays selectable without a
rebuild. Both are deterministic in the one-thread bench.

### Pseudocode (own words)
    eval_grain(board, v):
        if G <= 1: return v                        -- before BOTH the rounding and the jitter (identity)
        q = sign(v) * ((|v| + G / 2) / G) * G      -- round half away from zero: q(-v) = -q(v), no side bias
        if Jitter = 1: q = q + (fixed key bit set ? +1 : -1)
        if Jitter = 2: q = q + (node-counter bit set ? +1 : -1)
        return clamp(q, +-(MateInMaxPly - 1))
    site: static_eval = corrected_eval(board, eval_grain(board, raw_eval))
A floor-based rounding is not used: it moves every eval toward minus infinity for the side to move, a colour bias.
Mate / TB bypass is by placement: static evals are bounded (residual path clamped at `:620`, TT eval field int16)
and the lock has no TB probe (grep syzygy / tablebase / probe_wdl over src + include: 0 hits), so no mate or TB score reaches the function; the final clamp is still needed because rounding plus
jitter can push an edge value up to G / 2 + 1 past the clamp.

### Identity proof (OFF)
EvalGrain = 1 returns its input unchanged before any rounding or jitter, at both sites; TT and leaf paths are
untouched: same tree, the five lock pins, perft unchanged. Second OFF run with EvalGrainJitter at 0 and at 2 (G = 1):
still the lock pins (the jitter knob is read only for G >= 2).

### ON-live check
EvalGrain = 8: all five bench depths differ from the lock pins and repeat on a second run. Knob checks: G 8 -> 4 and
8 -> 12, Jitter 1 -> 0 and 1 -> 2: each changes at least one bench depth (pin_on_live, BUG_CHECKLIST row 18).

### Box tests
1. Unit grid over v in +-(MateInMaxPly - 1), G in 2-32: G = 1 returns v for every v; with jitter 0, q(-v) == -q(v),
   q is a multiple of G and |q - v| <= G / 2; with jitter, |q - v| <= G / 2 + 1; the result never leaves the clamp.
2. Pure-function test (jitter 1): the same FEN reached by two move orders, and again after a warm-TT search, gives the
   same grained static eval (a verify build prints it). Jitter 2 is expected to fail this - the test documents why
   key is the default.
3. Mechanism counter (verify build, bench): distinct static-eval values, TT cutoffs and total nodes at OFF and
   G = 4 / 8 / 12. The grain is meant to cut distinct values; if TT cutoffs and nodes do not move at all, expect
   nothing in games.
4. Offline calibration guard (FIT_RECIPE step 7 on the R13 fit set): held-out log-loss with the grained eval must not
   be worse than OFF beyond the bootstrap CI (a grain is a calibration-neutral change by design).
5. Mate probe OFF / ON (no mate delayed) and a WAC300 sanity at G = 8, as E3 did; Threads = 2 smoke.

### Gate line and sweep
Candidate: fresh LF lock copy + this patch (forge-lock-port), kit v2.3 `-Expose` pc1 = pc2 (forge-r15-candidates).
Crew form (Common) with `option.EvalGrain=8` only, STC [0,10] nElo cap 12k; then LTC 30+0.3 [0,15] cap 6k whenever
STC is not H0 (the source's gain was larger at LTC: +2.42 vs +0.91). The card's "sweep 3 grains" as fixed-games
runs (3 x 3,000 games vs the lock, no SPRT, ~18-21 h) resolves only about +-6.6 Elo (95 %) per grain (UE3A rerun:
+-4.64 at 6,000 games, scaled by sqrt 2), more than the card's whole estimate, so it can only drop a clearly broken
grain; recommendation: skip it, use box tests 3-4 to drop a grain, and gate G = 8 directly; G = 4 or 12 only after
a G = 8 result that is not H0.

### Crew hours
Code ~0.5 h (one function, two call sites, two table rows, two declarations); proofs ~1.5 h (unit grid, pure-function
test, counters, OFF pins twice, ON pins, 4 knob checks, calibration guard, mate / WAC, smoke); kit build + cand_pack
+ index_check ~0.5 h: about 2.5 crew h (card: 2). CPU: STC mean ~13 h, LTC mean ~18 h (the optional sweep would add
18-21 h). No GPU. Forge estimate stays the card's +0.5 to +2 Elo **UNPROVEN**.

## Sources read for this spec (all own files or this job's notes; no external page, no new licence row)
- Lock source: `src/search.cpp`, `include/forge/search.hpp`, `src/uci.cpp` (read-only).
- packb `src_packb_h256/src/search.cpp` + `include/forge/search.hpp` (ReSearchAdjust, FiftyDamp).
- E3 zip `stage_e3_evalpost/e3_evalpost_al1_src.zip`: `src/search.cpp`, `include/forge/search.hpp`, `src/uci.cpp`,
  `README_E3_CANDIDATE.md`, `tests/rule50_tests.cpp` (copies in F:/odr/work/SPEC-EVAL/e3/).
- Gate folder `F:/forge_push/uhoE3c_evalrule50damp30_vs_AL1lp` (RUN_INFO.json, PREBENCH.txt,
  ENGINE_OPTIONS_CHECK.txt); FORGE_RESULTS.csv through `tools/tried_gates.py`.
- Branch opus-r13-p7-e3fit `opus_r13/p7/RESULTS.md` (git show, @ 360e49df).
- Job notes: cards T04-02 / T06-05 / T06-04, `notes/TOP_SECOND_VOTE.md`, `notes/T06/FORMS.md`,
  `notes/T06/FIT_RECIPE.md`, `notes/T04/BUG_CHECKLIST.md`, `notes/T12/PROTOCOLS.md`.
- External source numbers (Caissa / Patricia MIT, Stockfish GPL ideas only) are quoted from the cards, not re-read.
