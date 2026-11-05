# T01B-01: pairwise clipped product instead of SCReLU on the v2 hidden layer (single-layer net)
Status: COMPLETE

## Source
- Obsidian commit beaa1374 (2024-08-15, "New net"): https://github.com/gab8192/Obsidian/commit/beaa13742e08a40c1e766db74c750e65c4393222
- Context: Stormphrax PR 183 "pairwise mul support" (no test) https://github.com/Ciekce/Stormphrax/pull/183 ; Stormphrax
  PR 237 multilayer net with a pairwise first activation (confounded) https://github.com/Ciekce/Stormphrax/pull/237
- bullet examples/advanced (MIT) trains its L1 768 with a pairwise activation (notes/T01/sources.md row 1).

## Licence
Obsidian GPL-3.0 at beaa13742e, Stormphrax GPL-3.0 at 41f435dd88 (tools/licence_at.py) = ideas only; commit message
and PR text read, never source. bullet MIT at da426a49 (T01 row) = copy with notice; nothing copied here.

## Mechanism
SCReLU squares each clipped hidden value. The pairwise form cuts each perspective's accumulator into two equal halves,
clips both to [0, 1] and multiplies neuron i of the first half with neuron i of the second; the output layer reads
half as many values per perspective. The net learns products of two features instead of squares of one. A product of
two clipped values has the same bound as a square, so the integer path's magnitude bounds carry over.

## Forge fit
`bash tools/forge_has.sh 'pairwise|crelu|screlu'` = 1 hit, include/forge/nnue.hpp:11 (SCReLU, lock net). v2 port: SCReLU
(opus_30h/a/v2port.patch:21); trainer forge_v2_bullet_o30/src/main.rs:316-317, 407-408 calls screlu(). Nothing pairwise.
Blocker: the lock net cannot be written exactly as a pairwise net of width 256, so the warm-start identity every v2
result rests on (lock-as-v2 = lock pins, forge-o30-v2net skill) does not exist at equal width: the start is from scratch
(our from-scratch KB4 at 1.46G positions: S31 +7.7e-4, worse than the lock) or approximate. An exact start needs width
512 with the second half a copy of the first (clip(a) x clip(a) = SCReLU(a)), plus a small own perturbation to break
the symmetry - but that doubles the accumulator work = the bigger-L1 trade already reported on 30-Oct. All pairwise
sources run L1 >= 768, where the halved output layer also saves time; at H256 that saving is small (own reasoning).
Change: activation flag in FORGENN2, output kernel variant (AVX2 / SSE / scalar), trainer switch, exporter.

## Expected gain
Obsidian beaa1374: "now using pairwise CReLU instead of SCReLU", STC 6+0.06 1 thread 16 MB +3.18 +- 2.10 (29,514 g,
penta 138/3441/7356/3657/165, LLR 2.90 for [0,2.5]); the author flags the TC itself ("false tc due to broken nps");
lower 95 % bound ~+1.1; no LTC, no book, no nps number; Obsidian's hidden size at that commit is not stated (1280
at 132e8653; the later 62f32032 arch is not named). Stormphrax PR 237 (pairwise -> CSReLU -> CReLU, new layer stack and L1 1792 in one change): LTC
40+0.4 +22.69 +- 6.51 (2,730 g) - not attributable to pairwise.
Forge estimate: 0 to +2 Elo at equal width over an SCReLU twin of the same recipe; negative while the from-scratch
start stays behind the lock **UNPROVEN**.

## Effort
Crew ~6-8 h (trainer switch, exporter flag, engine kernel x3 ISAs, parity 10k, walk). GPU: two from-scratch runs of one
own recipe (SCReLU twin + pairwise; KB8 + OB8 H256, lr 1e-3 cosine to 1e-5, WDL 0.4, 700 SB = 11.7G positions,
~70 min each at 2.8-3M pos/s if pairwise trains at the same speed; range lr 5e-4 .. 2e-3). CPU: STC + LTC SPRT at
430-502 games/h (~13 h per ~6.6k-game SPRT).

## Test plan
Offline first: pairwise vs its SCReLU twin (same data, seed, length), paired S31 + jobA beyond the ~4e-6 seed noise;
gate only if it also passes the lock rule (S31 >= 2e-5 below the lock, jobA z <= +2). Pre-gate: OFF bench pins
(EvalFileV2 empty), an SCReLU v2 file unchanged, export parity 10000/10000 vs an own float32 reference, incremental ==
refresh walk, SIMD == scalar, output-kernel nps ABBA. Gate: UHO SPRT [0,5] at STC, then LTC, against the identical-eval
v2 control (-20.9 +- 18.5 for the lock net on v2p4, sanity only).

## OFF-by-default design
FORGENN2 flag bit 2 = pairwise (own choice; bit 0 residual, bit 1 mirror exist), read under the existing string option
`EvalFileV2` (empty = off = the lock's compiled net and code path, bench pins unchanged); a file without the bit runs
today's SCReLU kernel; unknown bits are refused. Halves = first / last 128 of each perspective (own choice).
