# T01 recipes: side-by-side table, documented levers, ranked bullet configs (written 23:03, last update 23:09 PC clock)

WDL = weight of the game result in the training target (0 = pure eval score, 1 = pure result); nnue-pytorch's
"lambda" is the opposite (lambda 1.0 = pure eval score). Sigmoid scale = the cp divisor inside the loss sigmoid.
Every Forge-side number below is **UNPROVEN**. Source numbers are quoted with their own test conditions.

## 1. Side-by-side table

| recipe | source / licence | inputs | net | data | batch | length | LR schedule | WDL (schedule) | sigmoid scale | init | result |
|---|---|---|---|---|---|---|---|---|---|---|---|
| OUR npt (R11 "full" = owner's line-104 recipe, r11_config.json) | own, run on nnue-pytorch (GPL-3.0, used as a tool) | HalfKA K32H3^ | L1 1024, npt's layers after L1 | 344.4M-row inventory; 152.5M per epoch | 16,384 | 20 epochs = 3.05G positions | lr 8.75e-4, trainer's default per-epoch decay (not set in the profile) | lambda 1.0 start and end = WDL 0 | trainer default (not set) | from scratch | gates NPT104 / NPTS3 / NPTW4S4: -86 to -116 Elo vs the lock (notes/TRIED_GATES.md) |
| OUR bullet v2 (30-h job, window 2; forge_v2_bullet_o30 main.rs 286-347) | own trainer on bullet da426a49 (MIT) | 768 piece-square x king buckets KB4 / 8 / 16 / 32 (rank maps), OB8; residual on the hand-crafted eval | H256, SCReLU, one output per bucket | 304,999,573 train rows (FPOS / FHCE 001-039 minus holdout 013 / 014) | 16,384 | 200 SB x 1,024 batches = 3.36G positions (also 300 / 400 / 600 SB) | cosine lr0 -> lr0 / 100, lr0 2e-5 (1e-5 .. 3e-5 tried; 3e-5 worse) | 0.4 constant | 400 / 2.25 = 177.8 cp | lock net written exactly into the layout; AdamW clip +-7.99, decay 0 | S31 paired vs the lock: KB4 -1.41e-4 .. KB32 -1.80e-4; play within noise (sanity 200-400 g). Separately (owner's note; its recipe is not restated here): a bullet net "sb08" was about even with npt ep07 offline and its 760-game early stop read -11.9 +- 13.6 |
| bullet examples/advanced at da426a49 | bullet (MIT) | 16 mirrored king buckets x 768 + factoriser; sparse threats 59,808 (cap 128 active); pawn pairs 4,560 (cap 120) | L1 768 pairwise, L2 16 dual (x, x^2), L3 32, 8 material output buckets | not in the file (reads Viridithas-format data) | 131,072 | 3 stages: 100 + 800 + 200 SB x 763 batches (~100M positions / SB) = ~110G positions | all linear: 1: warm-up 1e-4 -> 5e-3, then down to 1e-4; 2: 1e-3 -> 1e-6; 3: 1e-5 -> 1e-7 | 1: 0.2; 2: 0.2 -> 0.5; 3: 1.0 | 400 | from scratch | no Elo in the file |
| Viridithas net v100 "eleison" (from-scratch schedule) | viridithas-networks release text (CC0-1.0) | as v99 (king buckets, mirrored); L1 factorisation removed | as v99 (not restated) | not stated; "5/6 random skipping" of the data | not stated | not stated | cosine 1e-3 -> 1e-3 x 0.3^5 | linear 0.4 -> 1.0 | not stated | from scratch | 25k nodes -3.49 +- 3.18 (19,006 g, failed [0,3]) but STC 8+0.08 +4.84 +- 2.90 (15,854 g, passed [0,3]) |
| Viridithas net v102 "noumena" (fine-tune stage) | viridithas-networks release text (CC0-1.0) | as v101 (L1 2560) | as v101 | not stated | not stated | 400 SB on top of v101 | "very low" cosine 2.5e-5 -> 2.5e-5 x 0.3^5 | 1.0 (pure WDL) | not stated | the finished v101 net | LTC 40+0.4 +2.38 +- 1.74 (36,436 g, [0,3]) |
| Integral (README at 29456bb34c + PRs 243 / 256 / 266) | README / PR text only (no licence) | 768 x 16 factorised mirrored king buckets + 11 halfmove-clock inputs + threats 59,808 + pawn pairs 4,560 (README arch line) | L1 768 (README; PR 266 says 1024), L2 16, L3 32, 8 output buckets | "hundreds of millions" of self-play games, 20k soft nodes per side, 5-man Syzygy in datagen, UHO_Lichess_4852_v1 openings + 3-4 random moves; dataset card on Hugging Face says MIT but holds no files today | not stated | not stated | not stated | not stated | not stated | from scratch (bullet) | Ranger vs AdamW STC +3.22 +- 2.26; new threat net LTC +24.43 +- 7.77 |

## 2. Documented levers with measured Elo (feature sets, bucket layouts, recipe)
Engines: Viridithas (V, PR text + CC0 release text), Integral (I, PR text). "+x" = Elo +- 95 % error.
- Threat inputs: V PR 425 / net v105, threats 60,144 mirrored + 704 x 16 king-bucket piece-square, L1 2560 -> 1024
  in the same change: 25k nodes +27.43 +- 7.91, STC 8+0.08 +2.98 +- 2.09 (30,040 g), LTC 40+0.4 +5.38 +- 2.97
  (12,730 g), ~87 % of the old speed (AVX-512). I PR 243: LTC +24.43 +- 7.77 (1,866 g, [0,4]). -> T01-01.
- Pawn pairs: V PR 445 / net v107 (59,808 threats + 4,560 pawn pairs, the bullet example's counts): 25k nodes
  +3.65 +- 3.00 (19,144 g, unfinished). -> T01-05.
- King buckets: V v84 4 mirrored buckets (1536x2); V v91 16 king buckets + L1 2048 together: 25k +31.64 +- 8.76;
  I PR 256 16 buckets + the 11 halfmove-clock inputs decoupled from the buckets: STC +4.23 +- 2.65, LTC +2.17 +-
  1.64 (39,946 g). -> T01-04.
  V v95.1 merged king planes (768 -> 704 per bucket): neutral (+0.29 +- 1.74 under [-3,0]); no card.
- Output buckets: V v86 eight material output buckets + a larger dataset (confounded): 25k +19.76 +- 6.80,
  STC +23.89 +- 6.91 (2,826 g). Ours: OB8 already in the v2 layout.
- Pairwise product after L1: V v92 2048x2 -(pairwise)-> 16 -> 32 -> 1 (with a new layer stack and a feature
  permutation, confounded): LTC +9.44 +- 4.12 (7,028 g). Out of this track (layers after L1); no card.
- L1 size: I PR 266 L1 1024 with Ranger: 25k nodes +21.35 +- 6.98 but 60+0.6 +0.70 +- 1.64 (38,948 g, unfinished);
  V v101 L1 2048 -> 2560 + more data: LTC +2.90 +- 2.04. Fixed-node gains of a wider L1 shrink at real TC (speed).
- Data: V v105.1 "additional data" STC +5.33 +- 2.95; V v95 +200 SB with ~1.2G injected positions LTC +4.99 +- 2.87;
  V v104.1 more data LTC +1.13 +- 1.23 (unfinished).
- Optimiser: I PR 266 Ranger vs AdamW STC +3.22 +- 2.26 (25,378 g); V v108 Ranger vs Adam LTC +8.98 +- 3.92
  (7,004 g). -> T01-02.
- Recipe stages: V v102 pure-WDL low-LR fine-tune LTC +2.38 +- 1.74 (36,436 g). -> T01-06. V v110 distillation
  from a much larger teacher net LTC +3.69 +- 2.35 (19,226 g): no card (we have no teacher that beats the lock
  offline). V v111 "improved initialisation and weight clipping" LTC +6.52 +- 3.70 under [-3,0]: no details.
- Speed: I PR 266 one merged threat + piece-square accumulator +6 % speed (STC +1.70 +- 1.36); inference = T5.

## 3. Ranked bullet configs (each <= ~1 GPU-day on one RX 7900 XT 20 GB; offline check before any SPRT)
Common base (the 30-h method): warm start = the lock net written exactly into KB8 (rank4x2) + OB8, H256, residual
on the hand-crafted eval, AdamW clip +-7.99 decay 0, batch 16,384, 1,024 batches per SB (16.8M positions), the
305M-row train set (review fix, critic: 304,999,573 J1 self-play rows, card T02-01), mix 8, scale 400 / 2.25. Own start values throughout (R3 starts from bullet's own Ranger
defaults, MIT); none is taken from another engine.
Offline check for every net (fixed before the run): paired S31 + jobA holdout vs the lock net (rule: S31 >= 2e-5
below, jobA z <= +2) AND vs the run's parent / control net beyond the recipe's seed noise (~4e-6 on S31); a net
that fails is not gated. Gate: UHO SPRT [0,5] at STC, then LTC, against the identical-evaluation v2 control.

| rank | config | lever / evidence (licence) | claimed source Elo | Forge estimate | GPU hours | inference cost | code needed |
|---|---|---|---|---|---|---|---|
| R1 | pure-WDL final stage on our best warm-start KB8 single net (run 5 or r12, not a soup): 200 SB at WDL 1.0, cosine 1e-5 -> 1e-7 (own; LR range 5e-6 .. 2e-5), fresh AdamW or the parent run's own optimiser state (cheaper A/B: our soup fine-tune that got worse used fresh state), same clip / decay; also score a 100-SB checkpoint | V v102 (CC0 text) + bullet example stage 3 (MIT) | LTC +2.38 +- 1.74 (V v102) | 0 to +2 Elo over the parent **UNPROVEN** | ~0.25-0.4 h per run at our measured 3-4.4M pos/s (H256 KB8); 2 parents x 2 LRs = ~1.5 h | none (same layout as the parent) | none: trainer argv wdl = 1.0 |
| R2 | KB8 + OB8 warm start + sparse BINARY threats (T01-01 encoding, own index map), threat block zero-initialised (step 0 = the lock function): 400 SB at WDL 0.4, cosine 2e-5 -> 2e-7 (our proven warm-start rate; 3e-5 was worse in the 30-h job; bullet's per-weight optimiser settings cover clip / decay / betas, not LR, so the zero block shares the rate; Adam's per-weight step lets it grow over ~410k steps; try 4e-5 only if its weights stay near zero at the checkpoints); optional R1 stage on top | V PR 425, I PR 243 (ideas only); bullet example (MIT) | LTC +5.38 +- 2.97 (V, with an L1 cut); LTC +24.43 +- 7.77 (I, new arch) | 0 to +5 Elo vs the KB8 control **UNPROVEN** | unmeasured (10-min smoke first); upper bound = 6.7G positions at 3-4.4M pos/s = 25-37 min; fits one GPU-day while threats slow training < ~40x | threat accumulator updates at H256: unmeasured (nps ABBA on a zero-threat identity net; V lost ~13 % with its L1 cut) | Rust sparse input type, exporter, engine feature set, parity + walk (~8-12 crew h) |
| R3 | R2 with Ranger instead of AdamW (start = bullet's RangerParams defaults, lookahead every 6 steps, fraction 0.5, MIT; own ranges 4-10 / 0.3-0.7), same seed / data / length; pawn pairs (zero-init) only as an R2 variant after R2 passes offline | I PR 266, V v108 (ideas only / CC0 text); bullet Ranger type (MIT) | STC +3.22 +- 2.26 (I); LTC +8.98 +- 3.92 (V) | 0 to +1 Elo on a warm start, more only from scratch **UNPROVEN** | as R2 | as R2 | optimiser switch in the trainer (~1-2 crew h) |

Not ranked: a from-scratch L1 768+ threat net like the bullet example (~110G positions seen per run): our data is
305M rows (review fix, critic: 304,999,573 J1 rows, card T02-01) (the example would see each row ~360 times) and our from-scratch nets lost (npt L1 1024 -86 to -116 Elo;
bullet KB4 from scratch worse than the lock at 1.46G positions). Revisit after the 50M relabel / more self-play data.
