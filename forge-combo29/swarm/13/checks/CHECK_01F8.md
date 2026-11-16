# CHECK of seat 01's finding 01-F8 — seat 13, own build, own harness

## Verdict
**CONFIRMS 01-F8**, and the base-vs-PC comparison shows its stated consequence is exactly right.

Seat 01 claimed: `halfmove` / `fullmove` values above 65535 are **ACCEPTED** (not refused) and silently
clamped to 65535 by a `uint16_t` store, so the engine's counter is not what the FEN said; and the only
search consequence is the `>= 100` drawn-root branch.

## What I measured

All fresh processes, Threads 1, Hash 16, `go depth 8`, on a mate-in-1 board so the drawn-root branch is
observable through UCI alone.

### Base build 6b98f217

| FEN field | nodes | mate | bestmove | refused? |
|---|---|---|---|---|
| halfmove 0 (control) | 144 | **mate 1** | `a1a8` | no |
| halfmove 99 (below threshold) | 144 | **mate 1** | `a1a8` | no |
| halfmove 100 (threshold) | 0 | — | `a1b1` | no |
| halfmove 65535 | 0 | — | `a1b1` | no |
| **halfmove 65536** | 0 | — | `a1b1` | **no** |
| **halfmove 70000** | 0 | — | `a1b1` | **no** |
| **halfmove 300000** | 0 | — | `a1b1` | **no** |
| fullmove 1,000,000,000 (halfmove 0) | 144 | mate 1 | `a1a8` | no |
| halfmove 70000 + fullmove 70000 | 0 | — | `a1b1` | no |

### PC r15 build (the drawn-root repair, S-F17)

| FEN field | nodes | mate | bestmove | refused? |
|---|---|---|---|---|
| halfmove 100 | 144 | mate 1 | `a1a8` | no |
| halfmove 65535 / 65536 / 70000 / 300000 | 144 | **mate 1** in every case | `a1a8` | no |
| fullmove 1,000,000,000 | 144 | mate 1 | `a1a8` | no |

## What each part establishes
1. **No over-65535 value is ever refused** — every one is accepted on both builds, with no `invalid FEN`
   line, on ten FENs across both fields. That is the "ACCEPTED" half of seat 01's claim.
2. **The `>= 100` drawn-root branch is the only behavioural consequence** — the base build treats
   halfmove 100, 65535, 65536, 70000 and 300000 identically (0 nodes, mate missed), i.e. once the counter
   is at or above 100 the exact stored value makes no further difference. That is precisely seat 01's
   "the only search consequence is the `>= 100` branch".
3. **On the PC build the whole class is harmless** — every over-65535 value finds the mate, because the
   drawn-root repair (S-F17) removes the shortcut entirely. So the clamping is a *storage* curiosity, and
   with the repair in place it has no behavioural effect at all.

## Acceptance verified separately (guarding against my own trap)
A perft-1 probe with startpos set FIRST (so a refusal would leave startpos's 20 moves in place): every
over-65535 FEN gives **perft 1 = 17**, which is the mate board's own legal-move count (verified with
python-chess), not 20. So the position really was accepted and replaced the old board. This matters
because "refused FEN keeps the previous position" is the trap that produced a false engine-defect report
earlier in this run (case 5 of my traps note).

**A figure I got wrong and corrected:** my first version of the script printed "the mate board gives 38"
as the expected perft-1. The true value is **17**. The comment was wrong, not the measurement — the
printed value of 17 was always the accepted-board result. Fixed in the script rather than left in a
reported table.

## The one thing I cannot see
**The stored value itself is not observable from UCI.** I can show that over-65535 values are accepted and
that behaviour crosses the ≥100 threshold correctly, but I cannot distinguish "stored as 65535" from
"stored exactly" at the protocol level, because both are ≥ 100 and every consumer of the counter compares
against 100. Seat 01 read the `uint16_t` store in the source, which is the direct evidence; my check
confirms the consequence they state, not the storage width. I say so rather than implying I verified the
clamp mechanism.

## Beyond the finding
The base-vs-PC comparison is worth having on its own: it shows that **the entire class of over-65535 FEN
counter values becomes harmless on the owner's build**, because the only code that cared about the counter
was the drawn-root shortcut the PC patch removes. So a FEN-generating harness that emits absurd counters
cannot damage a PC match, but can silently change what the base tree does.

## Reproduce
```
cd forge-combo29/swarm/13/checks
python3 check_01f8.py ~/b/rel/forge /tmp/c1     # base: 0 nodes past threshold
python3 check_01f8.py ~/b/pc/forge  /tmp/c2     # PC:   mate found at every value
```
Raw JSON: `out_01f8c/clampcheck.json` (base), `out_01f8_pc/clampcheck.json` (PC).
