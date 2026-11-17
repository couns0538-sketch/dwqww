# The five acceptance cases, with pass/fail per build — the clearest statement of what remains unfixed

Maintained by seat 21 as the source for the STATUS FINAL block. Regenerate/verify with:

```
python3 forge-combo29/swarm/21/job43/acceptance.py ~/b/release/forge job43/base base
python3 forge-combo29/swarm/21/job43/acceptance.py ~/b/pc/forge    job43/pc   pc
```

Exit code 0 only when all five cases pass **and** the four pins are exact.

| case | root position | a conforming engine must answer | BASE build | PC build (r15 under PC20) |
|---|---|---|---|---|
| **S1** | halfmove counter 100, **with** a mate in 1 — `6k1/5ppp/8/8/8/8/5PPP/4R1K1 w - - 100 60` | a **mate** score | **FAIL** — `cp 0`, plays `f2f3` (misses the mate) | **PASS** — `mate 1`, plays `e1e8` |
| **S2** | halfmove counter 100, **no** mate — `8/8/8/4k3/8/8/4P3/4K3 w - - 100 60` | `cp 0` | **PASS** — `cp 0`, plays `e2e3` | **FAIL** — `cp 368`, plays `e2e3` (reports a win at a drawn root) |
| **S3** | insufficient material — `4k3/8/8/8/8/8/8/4K3 w - - 0 60` | `cp 0` | **PASS** — `cp 0`, plays `e1d1` | **PASS** — `cp 0`, plays `e1d1` |
| **S4** | threefold repetition, **with** a mate in 1 (same board reached 3× by `e1d1 g8h8 d1e1 h8g8`, twice) | a **mate** score | **FAIL** — `cp 0`, plays `f2f3` | **PASS** — `mate 1`, plays `e1e8` |
| **S5** | threefold repetition, **no** mate (K+P cycle `e1f1 e5d5 f1e1 d5e5`, twice) | `cp 0` | **PASS** — `cp 0`, plays `e2e3` | **FAIL** — `cp 292`, plays `e2e3` |

| build | spec | four honesty pins |
|---|---|---|
| base `6b98f217` | **FAILED** (S1, S4) | 312866 / 862329 / 3024920 / 4865609 — exact |
| PC `r15` under PC20 | **FAILED** (S2, S5) | 312866 / 862329 / 3024920 / 4865609 — exact |

## What the table says, in one sentence each

- **The base build cannot see a mate at a drawn root**, because it never searches one — that is why the
  PC patch exists at all.
- **The PC build reports a winning score at a drawn root**, because it now searches one but does not
  re-apply the fifty-move or repetition rule to the result — that is 21-F19.
- **Neither build satisfies the rule in `DESIGN_drawn_root.md`**, and each fails a *different* half of it,
  which is why the gap is real rather than a preference.
- **The pins are unmoved on both**, so a fix aimed at S1/S2/S4/S5 has no excuse for moving them.
- **Insufficient material is already right on both** (S3), so the fix must not disturb it.

## The rule that would pass all five

From `DESIGN_drawn_root.md`: at a root the rules call drawn, **search it**, then **report the draw score
unless the search finds a win for the side to move**. Applying it to this table: S1/S4 get their mate,
S2/S5 stay `cp 0`, S3 is untouched (insufficient material is adjudicated before the search), and the pins
are unaffected by a comparison added after the search returns.
