# T01-03: three ranked bullet configs, each at most ~1 GPU-day on one RX 7900 XT (warm start + one lever each)
Status: COMPLETE

## Source
- Table, levers and full configs: notes/T01/recipes.md (OUR npt, OUR bullet, documented open recipes).
- Open recipes: bullet examples/advanced at da426a49 https://github.com/jw1912/bullet/tree/da426a49b2/examples/advanced;
  Viridithas net releases v100 / v102 https://github.com/cosmobobak/viridithas-networks/releases
- Evidence per lever: T01-06 (pure-WDL stage), T01-01 (threats), T01-02 (Ranger), T01-05 (pawn pairs). Ours:
  D:/o30/FINAL_REPORT.md 82-99 + 370-389, forge_v2_bullet_o30/src/main.rs 286-347, r11_config.json "full".

## Licence
bullet MIT at da426a49 = copy with notice; viridithas-networks CC0-1.0 (release text); Viridithas AGPL-3.0 and
Integral (no licence) = ideas only, PR text only. All start values below are our own, none from another engine.

## Mechanism
All three keep the 30-h method (the lock net written exactly into KB8 + OB8, H256, AdamW clip +-7.99, decay 0,
batch 16,384, 1,024 batches per SB) and add ONE lever, so a paired offline diff isolates it:
- R1 (no code): a final stage on the game result only (WDL 1.0) on our best warm-start KB8 single net (not a soup):
  200 SB, cosine 1e-5 -> 1e-7 (range 5e-6 .. 2e-5), fresh AdamW or the parent run's own optimiser state; also score
  the 100-SB checkpoint.
- R2: + sparse BINARY threats (T01-01), threat block initialised to zero so step 0 is the lock function; 400 SB at
  WDL 0.4, cosine 2e-5 -> 2e-7 (our proven warm-start rate: 3e-5 was worse; Adam's per-weight step still lets the
  zero block grow over ~410k steps; try 4e-5 only if its weights stay near zero at the checkpoints).
- R3: R2 with Ranger instead of AdamW, same seed / data / length; zero-init pawn pairs only as an R2 variant once R2
  passes offline.
Not ranked: a from-scratch L1 768+ threat net like the bullet example (~110G positions seen); our data is 305M rows
and our from-scratch nets lost (npt L1 1024: -86 to -116 Elo; bullet KB4 from scratch worse than the lock at 1.46G).

## Forge fit
Trainer forge_v2_bullet_o30 (ROCm, bullet da426a49) already has KB8, OB8, warm start, clip / decay and a wdl argument
(R1 runs today); it lacks a sparse threat / pair input type (our O6 / O7 are dense, count-valued) and an optimiser
switch. Engine: v2 path (EvalFileV2) has buckets, no threats; `forge_has.sh 'threat'` = hand-crafted eval only.

## Expected gain
Sources: pure-WDL fine-tune Viridithas v102 LTC +2.38 +- 1.74 (36,436 g, [0,3]); threats Viridithas STC +2.98 +-
2.09 / LTC +5.38 +- 2.97 ([0,3], with an L1 cut), Integral LTC +24.43 +- 7.77 ([0,4], new arch); Ranger Integral STC
+3.22 +- 2.26, Viridithas LTC +8.98 +- 3.92. Forge estimate: R1 0 to +2, R2 0 to +5, R3 0 to +1 Elo over the
respective parent / control net **UNPROVEN**; vs the lock exe each also carries the v2 path's own cost
(identical-eval control -32.2 +- 18.5) until that is closed.

## Effort
R1: ~1.5 GPU h (2 parents x 2 LRs at our measured 3-4.4M pos/s), no crew code. R2: ~8-12 crew h (input type,
exporter, engine features, parity, walk); GPU unmeasured (10-min smoke first; 6.7G positions = 25-37 min at the
threat-free speed, so a run fits one GPU-day while threats slow training < ~40x). R3: ~1-2 crew h + one R2-sized
run. CPU: STC + LTC SPRT per surviving net.

## Test plan
Offline first: paired S31 + jobA vs the lock net (rule: S31 >= 2e-5 below, jobA z <= +2) AND vs the parent / control
net beyond the ~4e-6 seed noise; for R1 also a result-only holdout loss. Then UHO SPRT [0,5] at STC, then LTC,
against the identical-evaluation v2 control; the threat update cost by nps ABBA on a zero-threat identity net.

## OFF-by-default design
R1 / R3 change only the net file. R2: new FORGENN2 feature-set ids under the existing `EvalFileV2` string option
(empty = off = the lock's compiled net and code path, bench pins unchanged); unknown ids are refused cleanly.
