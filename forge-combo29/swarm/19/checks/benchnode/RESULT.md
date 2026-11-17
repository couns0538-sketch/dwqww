# 19-C55 — does the bench-vs-real divergence generalise? YES, and harder than expected: `bench` gets the SIGN wrong

## The question
19-C53 showed `bench 16` understates PC20's per-node cost (1.2 % vs 7 %). **Does that divergence affect other
claims of mine that rest on bench?** The sharpest test: `bench`'s NODE effect, which several findings lean on.

## Measured (`reps.txt`, 3 reps each, both builds, Threads 1, fresh process, deterministic node counts)
Node counts are **identical across all 3 reps** in every cell — so these are pins, not noisy samples.

| bench | S14 nodes | PC20 nodes | **node ratio PC20/S14** |
|---|---|---|---|
| 11 | 242,796 | 278,024 | **1.145** (PC20 uses 14.5 % MORE) |
| 13 | 656,517 | 587,276 | **0.894** (PC20 uses 10.6 % FEWER) |
| 16 | 2,155,620 | 2,343,893 | **1.087** (PC20 uses 8.7 % MORE) |

## The finding
**PC20 reduces nodes on `bench 13` and INCREASES them on `bench 11` and `bench 16`.** The sign flips between
benches.

**On real positions it consistently REDUCES nodes: 0.909 at depth 12 (n=119), and 0.9807 at a fixed 50k node
budget (n=180).**

**So `bench 13` — the single bench I and others have used most for PC20 node claims — is the one bench that
agrees with real positions, and it agrees by coincidence of direction rather than because it represents them.**
Anyone generalising "PC20 saves ~10 % of nodes" from bench 13 to game play would be right about the sign and
badly wrong about the magnitude stability.

## Where this bites specific findings of mine
- **19-F34 ("`corrected_eval` cost is depth-independent: 5.75 % at bench 13, 5.77 % at bench 16 — a flat per-node
  tax")** — measured **only on bench**, and now shown that bench 13 and bench 16 disagree with each other by
  **28 % in node ratio (0.894 vs 1.145 spanning the range; 0.894 vs 1.087 for the two benches 19-F34 used)** while
  the profile share stays flat at 5.75/5.77 %. **A flat profile share across two benches with opposite-sign node
  effects is not evidence of a flat per-node tax in real search.** 19-F34's conclusion is
  **qualified, not withdrawn**: the two shares are genuinely equal, but "flat per-node tax" was a real-position
  claim inferred from bench.
- **19-F32 ("CorrHistV2 saves 4.3 % of nodes, from bench 13")** — the node *measurement* stands for bench 13, but
  the implied real-position saving is unverified, and the sign is the only thing bench 13 can vouch for.
- **19-C35** — already qualified in 19-C53 (that is the finding that started this).

## What I would tell the next seat
**Use bench for: pins, determinism, ablation direction. Do NOT use bench for: magnitudes of node or time effects,
or per-node cost.** Bench 11, 13 and 16 disagree with each other in sign on the PC20 node effect, so there is no
"bench figure" to inherit — there is a bench-13-specific figure that happens to point the same way as reality.

## Provenance
`run.sh` (one pass) and `reps.sh` (3 reps) are in this folder; `reps.txt` is their pasted output; raw per-run
engine output in `raw_<bench>_<regime>.txt`. Builds: base `~/.build_rel` sha256 e06310ec…, PC r15
sha256 068f0927…, both `id name Chess Engine Forge 6.4.24 candidate`.
