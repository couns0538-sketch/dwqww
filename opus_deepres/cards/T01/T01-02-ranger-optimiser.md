# T01-02: Ranger (RAdam + Lookahead) instead of AdamW in our bullet trainer
Status: COMPLETE

## Source
- Integral PR 266 (merge c06f3e1f, 2026-10-27), test block "Ranger compared to AdamW":
  https://github.com/aronpetko/integral/pull/266
- Viridithas net v108 "outlander" ("Trained with Ranger, instead of Adam"), viri.dev test 676:
  https://github.com/cosmobobak/viridithas-networks/releases/tag/v108
- bullet's optimiser: crates/trainer/src/optimiser/ranger.rs:163-177 and crates/bullet_lib/src/nn.rs:25-46 in the local
  bullet copy our trainer builds against (D:/o30/bullet, recorded as da426a49), https://github.com/jw1912/bullet

## Licence
Integral: no LICENSE file at 29456bb34c (tools/licence_at.py) = ideas only; only the PR text was read, never source.
viridithas-networks: CC0-1.0 at d3da3953e4 (release text read; Viridithas itself is read as ideas only).
bullet: MIT at da426a49 = copy with notice allowed (only its optimiser parameters were looked up).

## Mechanism
Ranger is RAdam (Adam whose adaptive step is switched on only once the variance estimate is reliable, which replaces a
hand-made LR warm-up) wrapped in Lookahead (a second, slow copy of the weights that moves a fraction of the way toward
the fast weights every few steps, damping noise). Integral trained its threat net once with AdamW and once with
Ranger and played the two nets; the Ranger net won at STC. In bullet this is a type swap: the trainer takes a Ranger
optimiser type with its own parameter set (decay, both betas, weight clip, lookahead step count and fraction). Its
defaults have the same weight clip (+-1.98) and decay (0.01) as AdamW's, so a warm start from the lock net must keep
our O30_CLIP / O30_DECAY handling (the lock net reaches |w| 3.47).

## Forge fit
Engine: `bash tools/forge_has.sh 'adamw|ranger'` = 0 hits (training only; the engine just reads the net). Trainer:
D:/o30/wt/opus_30h/a/forge_v2_bullet_o30/src/main.rs:331 sets AdamWParams (clip / decay from O30_CLIP / O30_DECAY);
our npt recipe already trains with a Ranger-type optimiser (the R6 RangerLite port), our bullet recipe does not.
Change: an optimiser switch (env or argv) in that trainer, nothing in the engine.

## Expected gain
Integral PR 266, nets trained with Ranger vs AdamW: STC 10+0.1, 1 thread, 16 MB, +3.22 +- 2.26 (95 %), 25,378 g,
penta 116/2941/6356/3144/132, LLR 2.90 for [0,3]; no LTC, no book named, net = Integral's threat net of that PR.
Viridithas v108 vs the Adam-trained net: LTC 40+0.4, 1 thread, 128 MB, +8.98 +- 3.92, 7,004 g, penta
5/888/1896/709/4, LLR 2.98 for [0,3]; threat + pawn-pair net (v107 arch); no book named. Two engines, same sign.
Forge estimate: 0 to +4 Elo for a net trained long from scratch, 0 to +1 for the warm-start fine-tune at lr 2e-5
(few steps for Lookahead to matter) **UNPROVEN**.

## Effort
Crew ~1-2 h (switch + one smoke). GPU: one extra run per recipe at equal positions and seed (A/B), e.g. the T01-03
R2 run twice. CPU: one SPRT pair only if the offline A/B separates beyond seed noise.

## Test plan
Offline first: two runs, same data, seed and length, only the optimiser differs; paired S31 + jobA holdout vs the lock
net (seed noise of the recipe ~4e-6 on S31). Keep Ranger only if it wins beyond that noise; then gate the better net:
UHO SPRT [0,5] at STC, then LTC, against the identical-evaluation v2 control.

## OFF-by-default design
Trainer-side only: a switch such as O30_OPT=adamw|ranger (default adamw = today's runs bit for bit). Own start values:
lookahead every 6 steps (range 4-10), fraction 0.5 (0.3-0.7), decay 0, clip as O30_CLIP. The engine is unchanged
(EvalFileV2 empty = off = lock pins).
