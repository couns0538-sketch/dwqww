# STATUS — swarm/exposure

**State: complete.** All four measurement questions answered; deliverable package built;
branch pushed; PR open to `main`.

Base commit audited: `6b98f217` (`Checkpoint standalone NNUE v3 work and evidence`).
Branch: `swarm/exposure`. Deliverables: `forge-combo29/swarm/exposure/`.

---

## Headline

**The report's "0 drawn roots in 4,600 random games" is a null from a corpus that cannot reach
the condition. Measured on engine games, which can: 8.78 firings per 1,000 plies (95% CI
[8.44, 9.14] Poisson; [7.80, 9.82] cluster bootstrap), 47.1% of games [44.6, 49.6].**

The report's reading that "harness sampling random positions is never affected; game replay is
affected" does **not** survive. The zero is real for random play and uninformative about the
guard: in a 4,600-game random corpus, **no game ever reached halfmove 100** (max 73) and only 3
ever contained a threefold position.

## The four questions

**1. Base rate and its CI.** Depth 10, 1,500 games, 279,737 plies, 2,457 firings.
47.1% of games (n = 1,500); 8.78 per 1,000 plies = 1 firing per 114 plies.
Replicated independently at 9.40 per 1,000 (1,000 games) and at depth 6 at 8.53 (500 games).
Full intervals in `FINDINGS.md` §2.

**2. Games decided by it.** Paired deterministic comparison, 250 identical openings, base vs
bail-disarmed instrument: 111 games reached a firing, **66 (59%) changed result**, of which
**48 went decisive → draw and 0 went draw → decisive**; 97 of 111 diverged at exactly the first
firing ply. Of those 48, the side to move at the firing **lost 34** and **won 14** of the base
games — so the bail hurt the side that played it in 34 and the direction is not uniform; see
`FINDINGS.md` §3. Per-position, **41 of 2,251 roots (1.8%) had the bail's move hand the opponent
a forced mate the searched move avoided**; 8 re-verified at depth 16, `8/8`.

**3. Clustering.** **Not openings** — 20 families range only 38.9%–52.9%, around the 47% mean.
**Decisively endgames** — 2 pieces (bare kings) is 0.04% of played positions but 4.84% of
firings (**128×**); 3–5 pieces is 18.2% of positions and 50.5% of firings (**2.8×**);
18+ pieces is 36.6% of positions and 6.6% of firings (0.2×).

**4. Firings per 1,000 plies with uncertainty.** 8.78, Poisson [8.44, 9.14], cluster [7.80, 9.82].
Quoting the cluster interval; design effect ≈ 2.9 because plies within a game are dependent.

## The finding that changes the ship verdict

**The shipped repair changes the move in 0 of 2,457 real drawn roots.** Seat 12's guard only
cancels the adjudication when a move mates immediately, and **0 of 2,457 roots have a mate-in-1**
— so the repair fixes the *reporting* (depth 8 → depth 1, which it does correctly) and leaves
the *move* untouched on every root that actually occurs.

This does not refute the earlier seats; it bounds them. "Removes the zero-node path **when a
mate exists**" is supported. "Fixes the move" is not.

## Verification performed

- **Four honesty pins on both builds:** 312,866 / 862,329 / 3,024,920 / perft 5 4,865,609.
- **Repair composes to the expected sha256:** `24912a43d315243f2f9dcb0ea032e7160633b99483c0a5e26541e870b2a26671`.
- **Predicate oracle:** 10/10 known-answer cases; **proved able to fail** by planting `>= 99`
  (fails as required, then restored to PASS).
- **Position-identity gate:** 2,457 of 2,457 rows; 0 errors (caught a real 35-of-40 failure first).
- **Mechanism:** 2,457 of 2,457 roots play the engine's generated `perft 1` head.
- **Determinism:** identical games from identical seeds at fixed depth.

## Corrections and defects found in this seat

Five harness defects, all recorded in `FINDINGS.md` §7 — the first two would each have produced
a confident zero of the same kind this audit is correcting, and the third (a **fake n**: 35
distinct games counted as 200) is the same class of fabrication the report warns about.

One **false claim of my own** was found and removed: an assertion that python-chess disagrees
with the engine on K+N v K. It does not — measured, zero disagreements in 4,000 random
bare-minor positions. The claim is gone from code and report.

## Files

```
forge-combo29/swarm/exposure/
  FINDINGS.md          the audit
  STATUS.md            this file
  BUILD.md             how to rebuild the three arms and rerun everything
  scripts/             uci, predicates, oracle, pins, play_all, cost, mechanism,
                       pairs, rates, final_numbers, random_null, analyze
  evidence/            raw JSON: cost_prod, pairs_s101, random_null, final_numbers,
                       rates, oracle, mech_prod, both patch files
  runs/                per-seed game corpora (depth 6 and 10, replication set)
  prod/                per-seed game corpora (depth 10, 1,500-game production set)
```

## Not done / limits

- Per-game causal tracing (the paired association is deterministic; each game's adjudication is
  not individually narrated).
- Human-game corpora; MultiPV > 1; clock modes.
- A *searched* drawn-root path was not shipped or validated — it is the recommendation in
  `FINDINGS.md` §5, not a result.
