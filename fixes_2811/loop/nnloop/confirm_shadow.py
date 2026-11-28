"""Shadow of an early-stop rule for the loop's confirmation match (Opus, 2026-11-15 16:00; Fable's decision of 15:53 in
teamwork/FABLE_TO_OPUS.md: one round in shadow before rule C08 can become the rule).

Rule C08: an SPRT on the confirmation's games, normalized Elo 0 against 17.2 (about +10 plain Elo at the
confirmations' draw rate), alpha 0.08, beta 0.14 (LLR bounds ln(0.14/0.92) = -1.88 and ln(0.86/0.08) = +2.37),
checked after every completed pair from the 10th pair on, in the order the pairs finished; if it never crosses a bound,
the fixed rule (LOS >= confirm_min_los after all games) decides. Statistics as fastchess computes them (pentanomial
pairs; checked against its printouts in pipeline/experiments/confirm_replay.py): t = (mean - 1/2) / sqrt(2 var),
LLR = pairs * ((t - t0)^2 - (t - t1)^2), LOS = Phi((mean - 1/2) / sqrt(var / pairs)). Simulated with 10,000 matches
(survey/confirm_early_stop.md): false pass 10.6 % at 0 Elo (fixed 9.8 %), 78.9 % at +10 (fixed 80.5 %), about 1,100 to
1,250 games instead of 2,000; on the six real confirmations and 30 screen blocks no verdict differed.

The shadow reads the finished match's fastchess .out file (match.run_sprt returns its path as "log") and returns one
line for the loop's notes. It changes nothing: the loop still plays every game and decides by the fixed rule.
Pure Python (no numpy), never raises out of `summary_line`.

    python confirm_shadow.py <fastchess_*.out> [...]      the line for finished matches (a test on old rounds)
"""
from __future__ import annotations

import math
import re
import sys

GAME = re.compile(r"^Finished game (\d+) \((\S+) vs (\S+)\): (1-0|0-1|1/2-1/2)")
NT = 800.0 / math.log(10.0)
NELO0, NELO1 = 0.0, 17.2
ALPHA, BETA = 0.08, 0.14
LO, HI = math.log(BETA / (1.0 - ALPHA)), math.log((1.0 - BETA) / ALPHA)
MINP = 10
X = (0.0, 0.25, 0.5, 0.75, 1.0)


def _stats(c):
    n = sum(c)
    mu = sum(x * k for x, k in zip(X, c)) / n
    var = max(sum(x * x * k for x, k in zip(X, c)) / n - mu * mu, 1e-12)
    return n, mu, var


def _llr(c) -> float:
    n, mu, var = _stats(c)
    t = (mu - 0.5) / math.sqrt(2.0 * var)
    t0, t1 = NELO0 / NT, NELO1 / NT
    return n * ((t - t0) ** 2 - (t - t1) ** 2)


def _los(c) -> float:
    n, mu, var = _stats(c)
    z = (mu - 0.5) / math.sqrt(var / n)
    return 50.0 * (1.0 + math.erf(z / math.sqrt(2.0)))


def shadow(out_path: str, cand: str = "new_best", min_los: float = 90.0) -> dict:
    """The rule's decision on a finished match (games in the order they finished)."""
    half: dict[int, float] = {}
    counts = [0, 0, 0, 0, 0]
    finished = 0
    stop = None
    with open(out_path, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            m = GAME.match(line)
            if not m:
                continue
            g, white, black, res = int(m[1]), m[2], m[3], m[4]
            if cand not in (white, black):
                raise ValueError(f"game {g}: {white} vs {black}, no {cand}")
            finished += 1
            s = 0.5 if res == "1/2-1/2" else (1.0 if (res == "1-0") == (white == cand) else 0.0)
            k = (g + 1) // 2
            if k not in half:
                half[k] = s
                continue
            counts[int(round(2.0 * (half.pop(k) + s)))] += 1
            if stop is None and sum(counts) >= MINP:
                llr = _llr(counts)
                if llr >= HI or llr <= LO:
                    stop = {"verdict": "PASS" if llr >= HI else "FAIL", "pairs": sum(counts),
                            "games_finished": finished, "llr": round(llr, 3), "los": round(_los(counts), 2)}
    if sum(counts) == 0:
        raise ValueError("no complete pair in the file")
    los_end = _los(counts)
    fixed = "PASS" if los_end >= min_los else "FAIL"
    return {"pairs": sum(counts), "games": finished, "los_end": round(los_end, 2), "fixed": fixed,
            "c08": stop["verdict"] if stop else fixed, "stop": stop}


def summary_line(out_path, min_los: float = 90.0, cand: str = "new_best") -> str:
    try:
        r = shadow(str(out_path), cand, min_los)
    except Exception as e:  # noqa: BLE001 -- a shadow must never stop the loop
        return f"confirmation SHADOW (rule C08): not computed ({type(e).__name__}: {e})"
    if r["stop"]:
        st = r["stop"]
        where = (f"would have stopped after pair {st['pairs']} ({st['games_finished']} games finished) with "
                 f"{st['verdict']} (LLR {st['llr']}, LOS then {st['los']} %)")
    else:
        where = "would not have stopped early (the fixed rule decides at the end)"
    agree = "AGREES" if r["c08"] == r["fixed"] else "DISAGREES"
    return (f"confirmation SHADOW (rule C08, SPRT 0/17.2 normalized, alpha 0.08, beta 0.14): {where}; fixed rule: "
            f"{r['fixed']} (LOS {r['los_end']} % after {r['games']} games); C08 {agree}")


if __name__ == "__main__":
    for path in sys.argv[1:]:
        print(f"{path}: {summary_line(path)}")
