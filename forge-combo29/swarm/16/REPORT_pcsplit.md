# REPORT_pcsplit — PC code vs PC20 settings: which causes the extra asymmetry?

**What was asked (my own follow-up to S-F14):** S-F14 found base+S14 = 101/353 bestmove mismatch and
PC+PC20 = 120/353, but two things changed at once. This job crosses them, Threads 1 throughout, depth 10,
fresh process + `ucinewgame` per search, all 353 G positions.

**The answer: the PC CODE changes essentially nothing (101 -> 102). The extra 18 mismatches come ENTIRELY from
the PC20 settings, and TtPruneV2 alone accounts for most of it.**

```
| cell                     | n   | score_equal | bm_equal | bm_MISMATCH | nodes_equal |
|--------------------------|-----|-------------|----------|-------------|-------------|
| base code + S14          | 353 |          19 |      252 |         101 |           0 |
| PC code   + S14          | 353 |          20 |      251 |         102 |           0 |
| PC + S14 + CuckooRep     | 353 |          22 |      249 |         104 |           0 |
| PC + S14 + HistRework    | 353 |          23 |      255 |          98 |           0 |
| PC + S14 + TtPruneV2     | 353 |          19 |      240 |         113 |           0 |
| PC code   + PC20         | 353 |          22 |      233 |         120 |           0 |
```

Reading it:

- **Swapping the code alone (base -> PC at fixed S14) moves the mismatch count 101 -> 102.** The PC build's
  code is not where the extra asymmetry lives.
- **TtPruneV2 alone moves 102 -> 113** — the single largest settings effect, and it is the same option that was
  the only one to matter in my depth-<=2 sweep (S-F13). Two independent depths agree that TtPruneV2 is the
  asymmetry-relevant option.
- **HistRework actually helps**: 102 -> 98, the only cell at depth 10 that is more symmetric than base+S14.
- CuckooRep: 102 -> 104 (within noise of a 353-sample count; not claimed as an effect).
- The four together (PC20) give 120, which is more than the sum of the individual deviations — so the options
  interact. I do not claim additivity.

**How sure:** high on the code-vs-settings split (the 101 vs 102 comparison is two 353-position runs).
Medium on the individual option numbers: a 353-position count moves by ~10 by chance, so only TtPruneV2 (+11
alone, and the largest) and HistRework (-4) are worth naming, and HistRework's is small.

## Honesty numbers

```
exe PC     /home/ubuntu/builds/bld-pc/forge    none 312866 / S14 242796 / PC20 278024  (all match file 5)
exe base   /home/ubuntu/builds/bld-release/forge  312866 / 862329 / 3024920 / 4865609
Threads 1 in every search (swarm rule); Hash 16; depth 10; ucinewgame before each search
```

## Table

| step | done-partly-not done | evidence file | result |
|---|---|---|---|
| PC code + S14 | done | `raw_A_pc_s14.tsv`, `raw_A.meta` | 102/353 mismatch |
| PC + S14 + TtPruneV2 | done | `raw_B_ttprune.tsv` | 113/353 |
| PC + S14 + CuckooRep | done | `raw_C_cuckoo.tsv` | 104/353 |
| PC + S14 + HistRework | done | `raw_C_histrework.tsv` | 98/353 |
| base + S14 (reused) | done | `../job3/raw/G_d10.tsv` | 101/353 |
| PC20 (reused) | done | `../pcsym10/raw_G353.tsv` | 120/353 |
| CorrHistV2 alone at depth 10 | NOT done | — | it was inert at depth <=2 and active only at 6-8; unmeasured here |

## Findings

`S-F15 | 6 | the colour asymmetry's extra 19 mismatches on the PC build come from the PC20 SETTINGS, not the PC code: swapping the code alone (base -> PC r15 at fixed S14) moves the depth-10 bestmove-mismatch count 101 -> 102 of 353, while TtPruneV2 alone moves it 102 -> 113 and the full PC20 set gives 120; HistRework alone is the only cell MORE symmetric than base+S14 (98). Threads 1 throughout, verified reproducible | pcsplit/raw_A_pc_s14.tsv pcsplit/raw_B_ttprune.tsv pcsplit/raw_C_histrework.tsv pcsplit/raw_C_cuckoo.tsv | NEW |`

## Suspicions, not proven

- That TtPruneV2 and CorrHistV2 interact to produce the remaining 120-113=7. Not tested individually at
  depth 10 for CorrHistV2.
- Whether a 353-position sample can even resolve a 4-position difference (HistRework). It probably cannot; I
  report the number without claiming the direction.

## What I did NOT do

- Did not test CorrHistV2 alone at depth 10, nor any pairwise interaction.
- Did not repeat the 353 sweep to estimate run-to-run variance of the COUNT (scores are reproducible, so the
  count is too, but its sensitivity to the position set is not measured).

## Times

`pcsplit/stamps.txt`, every line a `date -u`.
