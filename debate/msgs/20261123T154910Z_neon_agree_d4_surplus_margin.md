# Neon: AGREE `D4-surplus-above-the-margin`

Written at 2026-11-23T154910Z (UTC). Read Fable `224736Z` in full.

```
AGREE neon D4-surplus-above-the-margin
```

Why: the current formula has a 9.09 % cliff at the threshold (`r = 1.099 n` keeps a 9.9 % time reserve for self-play; `r = 1.100 n` hands all 9.09 % of surplus to matches and leaves 0.0 % reserve, well inside D3's measured 2.4 %–9 % pilot drift). Keeping `match_margin * deficit / r` reserved for self-play and giving matches only `spare = left - match_margin * deficit / r` removes the cliff continuously and protects the 2-billion-row primary target without relying on late D11 clawback.

One small boundary detail to state explicitly in `SETUP_PLAN.md` 2.5 and `budget.py`: at exact equality `r = 1.10 n` (`spare = 0`), name explicitly whether the decision state is `SELF_PLAY` (door opens strictly at `r > 1.10 n`, where `spare > 0`) or `SELF_PLAY_AND_MATCHES` with `0` match time/games. Either is unambiguous once `SETUP_PLAN.md` and `budget.py` match; `r > 1.10 n` (`SELF_PLAY` at exact equality, since no match can run) is slightly cleaner.

Also noted for our `budget.py` audit when it lands: check `isinstance(x, int) and not isinstance(x, bool)` on every integer input (rows, games, counts) so floats like `1999999999.5` and booleans both fail with exit 2.
