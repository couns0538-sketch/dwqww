"""Core of the Forge offline SPSA tuner (R3-4): gain schedule, perturbation, rounding, update, state.

Pure functions on plain data; standard library only, Python 3.10+. Nothing here starts a process.

Schedule (Spall; the fishtest form with a per-parameter c_end and r_end), for iteration k = 0 .. N-1:
    c_k = c / (k + 1) ** gamma          c = c_end * N ** gamma               (so c_{N-1} = c_end)
    a_k = a / (A + k + 1) ** alpha      a = r_end * c_end**2 * (A + N) ** alpha (so a_{N-1} = r_end * c_end**2)
    A = A_ratio * N, alpha = 0.602, gamma = 0.101 by default.
Iteration k: draw delta_i = +-1 per parameter, play theta+ = theta + c_k*delta against theta- = theta - c_k*delta
(engine units, rounded to integers at match time and clamped to [min, max]), and with
y = wins - losses of theta+ over the mini-match:
    theta_i <- clamp(theta_i + a_k / c_k * y * delta_i, min_i, max_i)
which is fishtest's update R * c * (W - L) * flip with R = a_k / c_k**2. One mini-match of P game pairs is one
iteration; y sums its pairs, so r_end keeps fishtest's meaning (the learning rate per game pair).
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import random
from dataclasses import dataclass

ALPHA = 0.602
GAMMA = 0.101
A_RATIO = 0.1
ROUNDING_MODES = ("deterministic", "randomized")
STATE_VERSION = 1


@dataclass(frozen=True)
class Param:
    """One tuned engine option (an integer UCI spin option), in engine units."""
    name: str
    start: float
    minimum: int
    maximum: int
    c_end: float
    r_end: float


@dataclass(frozen=True)
class Schedule:
    iterations: int
    A: float
    alpha: float = ALPHA
    gamma: float = GAMMA

    @staticmethod
    def make(iterations: int, A_ratio: float = A_RATIO, alpha: float = ALPHA, gamma: float = GAMMA) -> "Schedule":
        if iterations < 1:
            raise ValueError("iterations must be >= 1")
        if A_ratio < 0:
            raise ValueError("A_ratio must be >= 0")
        return Schedule(iterations, A_ratio * iterations, alpha, gamma)

    def constants(self, p: Param) -> tuple[float, float]:
        """(c, a) of parameter p."""
        c = p.c_end * self.iterations ** self.gamma
        a = p.r_end * p.c_end ** 2 * (self.A + self.iterations) ** self.alpha
        return c, a

    def gains(self, p: Param, k: int) -> tuple[float, float]:
        """(a_k, c_k) of parameter p at iteration k (0-based)."""
        if k < 0:
            raise ValueError("k must be >= 0")
        c, a = self.constants(p)
        return a / (self.A + k + 1) ** self.alpha, c / (k + 1) ** self.gamma


def clamp(x: float, lo: float, hi: float) -> float:
    return lo if x < lo else hi if x > hi else x


def round_value(x: float, mode: str, rng: random.Random) -> int:
    """Integer value at match time: 'deterministic' = nearest integer (halves away from -inf, i.e. floor(x+0.5));
    'randomized' = floor(x + U[0,1)), unbiased in expectation (fishtest's randomized rounding)."""
    if mode == "deterministic":
        return math.floor(x + 0.5)
    if mode == "randomized":
        return math.floor(x + rng.random())
    raise ValueError(f"unknown rounding mode {mode!r}")


def iteration_rng(seed: int, k: int) -> random.Random:
    """The RNG of iteration k: a pure function of (seed, k), so a resumed session draws the same numbers."""
    return random.Random(f"opus_spsa:{seed}:{k}")


def iteration_srand(seed: int, k: int) -> int:
    """fastchess -srand of iteration k (opening order): 31-bit, a pure function of (seed, k)."""
    digest = hashlib.sha256(f"opus_spsa:{seed}:{k}:srand".encode()).digest()
    return int.from_bytes(digest[:4], "big") & 0x7FFFFFFF


@dataclass(frozen=True)
class Perturbation:
    name: str
    a_k: float
    c_k: float
    delta: int      # +1 or -1
    plus: int       # integer value played by theta+
    minus: int      # integer value played by theta-


def perturb(theta: dict[str, float], params: list[Param], schedule: Schedule, k: int, rounding: str,
            rng: random.Random) -> list[Perturbation]:
    """Iteration k's +-1 directions (drawn first, in parameter order) and the integer values of theta+ / theta-
    (rounded, then clamped to the parameter's bounds)."""
    deltas = [1 if rng.getrandbits(1) else -1 for _ in params]
    out = []
    for p, delta in zip(params, deltas):
        a_k, c_k = schedule.gains(p, k)
        t = theta[p.name]
        plus = int(clamp(round_value(t + c_k * delta, rounding, rng), p.minimum, p.maximum))
        minus = int(clamp(round_value(t - c_k * delta, rounding, rng), p.minimum, p.maximum))
        out.append(Perturbation(p.name, a_k, c_k, delta, plus, minus))
    return out


def update(theta: dict[str, float], params: list[Param], perts: list[Perturbation], w_minus_l: int) -> dict[str, float]:
    """theta_i + a_k / c_k * (W - L) * delta_i, clamped to [min_i, max_i]; W - L counts theta+'s results."""
    new = dict(theta)
    for p, q in zip(params, perts):
        if p.name != q.name:
            raise ValueError("perturbations do not match the parameter order")
        new[p.name] = clamp(theta[p.name] + q.a_k / q.c_k * w_minus_l * q.delta, p.minimum, p.maximum)
    return new


@dataclass(frozen=True)
class MatchResult:
    """theta+'s results over one mini-match of `pairs` game pairs (colours reversed within a pair)."""
    wins: int
    losses: int
    draws: int
    ptnml: tuple[int, int, int, int, int]   # pairs scoring 0, 0.5, 1, 1.5, 2 points for theta+
    time_losses: int = 0
    abnormal: int = 0                        # games ending other than by the rules, time or adjudication
    terminations: tuple[tuple[str, int], ...] = ()

    @property
    def games(self) -> int:
        return self.wins + self.losses + self.draws

    @property
    def w_minus_l(self) -> int:
        return self.wins - self.losses


def check_result(result: MatchResult, pairs: int) -> None:
    """Raise if a result is not a complete mini-match of `pairs` pairs."""
    if min(result.wins, result.losses, result.draws) < 0 or min(result.ptnml) < 0:
        raise ValueError(f"negative count in {result}")
    if result.games != 2 * pairs:
        raise ValueError(f"{result.games} games, expected {2 * pairs}")
    if sum(result.ptnml) != pairs:
        raise ValueError(f"pentanomial {list(result.ptnml)} sums to {sum(result.ptnml)}, expected {pairs} pairs")
    # The pentanomial fixes the score: points = sum(i/2 * n_i) = wins + draws/2.
    if sum(i * n for i, n in enumerate(result.ptnml)) != 2 * result.wins + result.draws:
        raise ValueError(f"pentanomial {list(result.ptnml)} disagrees with W/L/D {result.wins}/{result.losses}/{result.draws}")


# ---------------------------------------------------------------------------------------------------------------
# Synthetic objective (tests, --synthetic): games drawn from a known quadratic Elo landscape.

def synthetic_elo(values: dict[str, float], optimum: dict[str, float], scale: dict[str, float], depth: float) -> float:
    """Elo of a parameter vector: -depth * sum(((x - opt) / scale)**2)."""
    return -depth * sum(((values[n] - optimum[n]) / scale[n]) ** 2 for n in optimum)


def expected_w_minus_l(elo_diff: float, games: int) -> float:
    """E[wins - losses] of `games` games at an Elo difference (logistic; draws do not matter for W - L)."""
    score = 1.0 / (1.0 + 10.0 ** (-elo_diff / 400.0))
    return games * (2.0 * score - 1.0)


class SyntheticMatch:
    """Plays theta+ against theta- on a quadratic Elo landscape. noise=False returns the expected W - L as whole
    numbers of decisive games (deterministic); noise=True samples each game (RNG seeded by the iteration's srand)."""

    def __init__(self, optimum: dict[str, float], scale: dict[str, float], depth: float = 10.0,
                 draw_rate: float = 0.4, noise: bool = True):
        self.optimum, self.scale, self.depth = dict(optimum), dict(scale), depth
        self.draw_rate, self.noise = draw_rate, noise

    def __call__(self, plus: dict[str, int], minus: dict[str, int], pairs: int, srand: int) -> MatchResult:
        diff = (synthetic_elo(plus, self.optimum, self.scale, self.depth)
                - synthetic_elo(minus, self.optimum, self.scale, self.depth))
        games = 2 * pairs
        if not self.noise:
            wl = int(round(expected_w_minus_l(diff, games)))
            wl = max(-games, min(games, wl))
            wins = max(wl, 0)
            losses = max(-wl, 0)
            draws = games - wins - losses
            return MatchResult(wins, losses, draws, _ptnml_from_games(_spread(wins, losses, draws), pairs))
        rng = random.Random(f"synthetic:{srand}")
        score = 1.0 / (1.0 + 10.0 ** (-diff / 400.0))
        p_draw = min(self.draw_rate, 2.0 * min(score, 1.0 - score))
        p_win = score - p_draw / 2.0
        points = []
        for _ in range(games):
            u = rng.random()
            points.append(2 if u < p_win else 1 if u < p_win + p_draw else 0)
        wins, draws = points.count(2), points.count(1)
        return MatchResult(wins, games - wins - draws, draws, _ptnml_from_games(points, pairs))


def _spread(wins: int, losses: int, draws: int) -> list[int]:
    """Game points (2 win, 1 draw, 0 loss) interleaved so pairs mix results (deterministic synthetic mode)."""
    return [2] * wins + [1] * draws + [0] * losses


def _ptnml_from_games(points: list[int], pairs: int) -> tuple[int, int, int, int, int]:
    counts = [0] * 5
    for j in range(pairs):
        counts[points[2 * j] + points[2 * j + 1]] += 1
    return tuple(counts)  # type: ignore[return-value]


# ---------------------------------------------------------------------------------------------------------------
# State (resumable): one JSON document, replaced atomically after every iteration.

def new_state(params: list[Param], fingerprint: str, pins: dict[str, str]) -> dict:
    return {
        "version": STATE_VERSION,
        "tool": "opus_spsa",
        "fingerprint": fingerprint,
        "pins": dict(pins),
        "next_iteration": 0,
        "theta": {p.name: float(p.start) for p in params},
        "totals": {"games": 0, "wins": 0, "losses": 0, "draws": 0, "ptnml": [0, 0, 0, 0, 0],
                   "time_losses": 0, "abnormal": 0},
        "last_record": None,
        "status": "new",
    }


def advance_state(state: dict, theta: dict[str, float], result: MatchResult, record: dict) -> dict:
    """The state after iteration record['iteration'] (= state['next_iteration'])."""
    if record["iteration"] != state["next_iteration"]:
        raise ValueError("record does not continue the state")
    new = json.loads(json.dumps(state))
    new["next_iteration"] = record["iteration"] + 1
    new["theta"] = {n: float(v) for n, v in theta.items()}
    t = new["totals"]
    t["games"] += result.games
    t["wins"] += result.wins
    t["losses"] += result.losses
    t["draws"] += result.draws
    t["ptnml"] = [a + b for a, b in zip(t["ptnml"], result.ptnml)]
    t["time_losses"] += result.time_losses
    t["abnormal"] += result.abnormal
    new["last_record"] = record
    new["status"] = "running"
    return new


def save_json_atomic(path: str, data: dict) -> None:
    """Write JSON (LF, sorted keys) to path.tmp, flush to disk, then replace path in one step."""
    tmp = path + ".tmp"
    payload = (json.dumps(data, indent=1, sort_keys=True) + "\n").encode("utf-8")
    with open(tmp, "wb") as f:
        f.write(payload)
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, path)


def load_json(path: str) -> dict:
    with open(path, "rb") as f:
        return json.loads(f.read().decode("utf-8"))


def fingerprint(data: dict) -> str:
    """sha256 of canonical JSON (the schedule- and match-defining part of a config)."""
    return hashlib.sha256(json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
