"""space.py - parameter space, schedule, perturbation, constraints and update for opus3_spsa (extends R9).

Schedule and perturbation are R9's (opus_r9/tuner/r9_spsa.py, kept verbatim in r9_spsa.py next to this file):
  c0_i = c_end_i * N^gamma, a0_i = r_end_i * c_end_i^2 * (A + N)^alpha, A = A_ratio * N, N = pairs_planned
  c_k = c0 / (k + 1)^gamma, a_k = a0 / (k + 1 + A)^alpha, delta = +-1 from random.Random(f"{seed}:{k}")
  theta_i += a_k_i / c_k_i * R * delta_i   (R = wins - losses of plus over the batch)
Extensions (PLAN.md section 4):
  * kinds: "int" (engine value = round(theta) with Python's round, as R9) and "level" (theta in level-index units,
    engine value = levels[round(theta)]); disabled parameters stay at their fixed engine value;
  * linear coupled constraints sum(coef * engine value) <= le, checked on engine values;
  * bounds_mode "inner" (default): a coordinate's perturbation e is capped at half its range (cap recorded); if
    theta +- e*delta (as engine values) would break a bound or constraint, the whole perturbation shrinks by one
    common factor s (largest feasible s, direction kept, recorded); only if that needs s < s_min is theta first
    projected inward by s_min*e plus rounding slack (recorded as theta_moved); bounds_mode "r9_clamp": R9
    behaviour (plus/minus clamped independently; no constraints allowed);
  * E-006 fix: a coordinate whose plus and minus engine values are equal gets no update;
  * after the update theta is projected onto the feasible set (bounds and constraints, no margin).
The update step uses R9's a_k/c_k; a shrunk or capped perturbation never inflates the step.
Deterministic: IEEE doubles, no wall clock, no global RNG."""
import math
import random

SCHEMA = "opus3-spsa-config/1"
EPS = 1e-9


class SpaceError(Exception):
    pass


def py_round(x):
    """Engine integer as R9 computes it: int(round(x)) (Python rounds halves to even)."""
    return int(round(x))


class Space:
    def __init__(self, cfg):
        self.cfg = cfg
        self.N = int(cfg["pairs_planned"])
        if self.N <= 0:
            raise SpaceError("pairs_planned must be positive")
        self.alpha = float(cfg.get("alpha", 0.602))
        self.gamma = float(cfg.get("gamma", 0.101))
        self.A = float(cfg.get("A_ratio", 0.1)) * self.N
        self.seed = cfg.get("seed", 1)
        self.bounds_mode = cfg.get("bounds_mode", "inner")
        if self.bounds_mode not in ("inner", "r9_clamp"):
            raise SpaceError(f"unknown bounds_mode {self.bounds_mode}")
        self.s_min = float(cfg.get("s_min", 0.25))
        self.all_params = cfg["params"]
        all_names = [p["name"] for p in self.all_params]
        if len(set(all_names)) != len(all_names):
            raise SpaceError("duplicate parameter names")
        self.params = [p for p in self.all_params if p.get("enabled", True)]
        if not self.params:
            raise SpaceError("no enabled parameter")
        self.names = [p["name"] for p in self.params]
        self.idx = {n: i for i, n in enumerate(self.names)}
        self.fixed = {}
        for p in self.all_params:
            if not p.get("enabled", True):
                v = p["fixed"] if "fixed" in p else p.get("lock")
                if v is None:
                    raise SpaceError(f"disabled parameter {p['name']} needs 'fixed' or 'lock'")
                self.fixed[p["name"]] = v
        self.lo, self.hi, self.kinds = [], [], []
        for p in self.params:
            kind = p.get("kind", "int")
            if kind == "int":
                lo, hi = float(p["min"]), float(p["max"])
            elif kind == "level":
                if len(p["levels"]) < 2:
                    raise SpaceError(f"{p['name']}: a level parameter needs at least two levels")
                lo, hi = 0.0, float(len(p["levels"]) - 1)
            else:
                raise SpaceError(f"{p['name']}: unknown kind {kind}")
            if not hi - lo >= 1.0:
                raise SpaceError(f"{p['name']}: range narrower than one engine step")
            if p["c_end"] <= 0:
                raise SpaceError(f"{p['name']}: c_end must be positive")
            self.lo.append(lo)
            self.hi.append(hi)
            self.kinds.append(kind)
        self.c0 = [p["c_end"] * self.N ** self.gamma for p in self.params]
        self.a0 = [p.get("r_end", cfg.get("r_end", 0.002)) * p["c_end"] ** 2 * (self.A + self.N) ** self.alpha
                   for p in self.params]
        self.constraints = []
        for c in cfg.get("constraints", []):
            if not c.get("enabled", True):
                continue
            coef = {k: float(v) for k, v in c["coef"].items()}
            for k in coef:
                if k not in all_names:
                    raise SpaceError(f"constraint {c['id']}: unknown parameter {k}")
            self.constraints.append({"id": c["id"], "coef": coef, "le": float(c["le"])})
        if self.bounds_mode == "r9_clamp" and self.constraints:
            raise SpaceError("bounds_mode r9_clamp (R9 compatibility) does not support constraints")

    # --- R9 schedule -------------------------------------------------------------------------------------------
    def ck(self, k):
        return [c / (k + 1) ** self.gamma for c in self.c0]

    def ak(self, k):
        return [a / (k + 1 + self.A) ** self.alpha for a in self.a0]

    def delta(self, k):
        rng = random.Random(f"{self.seed}:{k}")  # str seeds hash deterministically (sha512), as in R9
        return [rng.choice((-1, 1)) for _ in self.params]

    # --- values -------------------------------------------------------------------------------------------------
    def start_theta(self):
        return [float(p["start_level"]) if p.get("kind", "int") == "level" else float(p["start"]) for p in self.params]

    def _clamp(self, i, v):
        return min(max(v, self.lo[i]), self.hi[i])

    def engine_value(self, i, x):
        if self.kinds[i] == "level":
            levels = self.params[i]["levels"]
            return levels[min(max(py_round(x), 0), len(levels) - 1)]
        return py_round(x)

    def engine_values(self, theta):
        vals = {n: self.engine_value(i, theta[i]) for i, n in enumerate(self.names)}
        vals.update(self.fixed)
        return vals

    def violations(self, vals):
        out = []
        for c in self.constraints:
            if sum(coef * vals[n] for n, coef in c["coef"].items()) > c["le"] + EPS:
                out.append(c["id"])
        for i, n in enumerate(self.names):
            p = self.params[i]
            if self.kinds[i] == "int" and not (p["min"] <= vals[n] <= p["max"]):
                out.append(f"bound:{n}")
        return out

    # --- projection ---------------------------------------------------------------------------------------------
    def _scale(self, i):
        return 1.0 if self.kinds[i] == "level" else float(self.params[i]["c_end"])

    def _slack(self, i, m):
        """Engine-unit change a perturbation of m theta-units (rounding included) can cause in coordinate i."""
        if m <= 0.0:
            return 0.0
        if self.kinds[i] == "int":
            return m
        lv = self.params[i]["levels"]
        step = max(abs(b - a) for a, b in zip(lv, lv[1:]))
        return (math.floor(m) + 1) * step

    def _lhs(self, c, x):
        total = 0.0
        for n, coef in c["coef"].items():
            if n in self.fixed:
                total += coef * self.fixed[n]
            else:
                i = self.idx[n]
                total += coef * (x[i] if self.kinds[i] == "int" else self.engine_value(i, x[i]))
        return total

    def _tight(self, c, m):
        return c["le"] - sum(abs(coef) * self._slack(self.idx[n], m[self.idx[n]])
                             for n, coef in c["coef"].items() if n in self.idx)

    def project(self, theta, margin=None, iters=400):
        """Cyclic projections (POCS) in c_end-scaled coordinates onto the box [lo+m, hi-m] and the half-spaces
        coef.x <= le - slack(m). Only "int" coordinates move for constraints; level coordinates are boxed only.
        Returns (theta, moved, feasible)."""
        m = margin or [0.0] * len(theta)
        x = list(theta)

        def box():
            for i in range(len(x)):
                lo, hi = self.lo[i] + m[i], self.hi[i] - m[i]
                if lo > hi:
                    lo = hi = (self.lo[i] + self.hi[i]) / 2.0
                x[i] = min(max(x[i], lo), hi)

        box()
        for _ in range(iters):
            worst = 0.0
            for c in self.constraints:
                excess = self._lhs(c, x) - self._tight(c, m)
                if excess > EPS:
                    worst = max(worst, excess)
                    mov = [(self.idx[n], coef) for n, coef in c["coef"].items()
                           if n in self.idx and self.kinds[self.idx[n]] == "int"]
                    norm = sum((coef * self._scale(j)) ** 2 for j, coef in mov)
                    for j, coef in mov:
                        x[j] -= (excess + EPS) * coef * self._scale(j) ** 2 / norm if norm else 0.0
            box()
            if worst <= EPS:
                break
        feasible = all(self._lhs(c, x) <= self._tight(c, m) + 1e-6 for c in self.constraints)
        moved = any(abs(a - b) > 1e-12 for a, b in zip(x, theta))
        return x, moved, feasible

    # --- one batch ---------------------------------------------------------------------------------------------
    def plan(self, theta, k):
        """Perturbation of the batch at pair count k from theta (JSON-safe dict)."""
        ck, delta = self.ck(k), self.delta(k)
        n = len(theta)
        if self.bounds_mode == "r9_clamp":
            th = list(theta)
            e = list(ck)
            plus_t = [self._clamp(i, th[i] + ck[i] * delta[i]) for i in range(n)]
            minus_t = [self._clamp(i, th[i] - ck[i] * delta[i]) for i in range(n)]
            s, moved, feasible, capped = 1.0, False, True, [0] * n
        else:
            # PLAN.md 4.3: shrink the whole perturbation first (direction kept); only if that would need s < s_min,
            # project theta inward by s_min * e (plus rounding slack) so the s_min perturbation is feasible.
            half = [(self.hi[i] - self.lo[i]) / 2.0 - 0.5 for i in range(n)]
            e = [min(ck[i], max(half[i], 0.5)) for i in range(n)]
            capped = [1 if e[i] < ck[i] else 0 for i in range(n)]
            th, moved, feasible = self.project(theta)

            def ok_at(s_, base):
                pv = self.engine_values([base[i] + s_ * e[i] * delta[i] for i in range(n)])
                mv = self.engine_values([base[i] - s_ * e[i] * delta[i] for i in range(n)])
                return not self.violations(pv) and not self.violations(mv)

            if ok_at(1.0, th):
                s = 1.0
            else:
                lo_s, hi_s = 0.0, 1.0
                for _ in range(40):
                    mid = (lo_s + hi_s) / 2.0
                    if ok_at(mid, th):
                        lo_s = mid
                    else:
                        hi_s = mid
                s = lo_s
                if s < self.s_min or not ok_at(s, th):
                    th, moved2, feasible = self.project(theta, [self.s_min * e[i] + 0.5 for i in range(n)])
                    moved = moved or moved2
                    s = self.s_min
                    if not ok_at(s, th):
                        lo_s, hi_s = 0.0, self.s_min
                        for _ in range(40):
                            mid = (lo_s + hi_s) / 2.0
                            if ok_at(mid, th):
                                lo_s = mid
                            else:
                                hi_s = mid
                        s = lo_s
            plus_t = [th[i] + s * e[i] * delta[i] for i in range(n)]
            minus_t = [th[i] - s * e[i] * delta[i] for i in range(n)]
        plus, minus = self.engine_values(plus_t), self.engine_values(minus_t)
        eff = [1 if plus[nm] != minus[nm] else 0 for nm in self.names]
        viol = sorted(set(self.violations(plus) + self.violations(minus)))
        return {"k": k, "theta_plan": th, "theta_moved": moved, "inner_feasible": feasible, "s": s,
                "s_below_min": s < self.s_min, "capped": capped, "c_k": ck, "e": e, "delta": delta,
                "plus": plus, "minus": minus, "eff": eff, "violations": viol}

    def update(self, plan, wins, losses, pairs):
        """theta after the batch: R9's update on coordinates whose plus and minus differ, then projection."""
        k = plan["k"]
        ck, ak = self.ck(k), self.ak(k)
        g = [ak[i] / ck[i] for i in range(len(ck))]
        r = wins - losses
        th = list(plan["theta_plan"])
        new = [th[i] + (g[i] * r * plan["delta"][i] if plan["eff"][i] else 0.0) for i in range(len(th))]
        if self.bounds_mode == "r9_clamp":
            new = [self._clamp(i, v) for i, v in enumerate(new)]
            moved, feasible = False, True
        else:
            new, moved, feasible = self.project(new)
        return {"k_before": k, "k_after": k + pairs, "R": r, "a_over_c": g, "theta_before": th, "theta_after": new,
                "projected": moved, "feasible": feasible, "active": self.constraint_activity(new)}

    def constraint_activity(self, theta):
        """Constraints within one end-of-run perturbation (c_end) of being tight at theta (diagnostics)."""
        out = []
        for c in self.constraints:
            width = sum(abs(coef) * self.params[self.idx[n]]["c_end"] for n, coef in c["coef"].items()
                        if n in self.idx and self.kinds[self.idx[n]] == "int")
            if self._lhs(c, theta) >= c["le"] - width:
                out.append(c["id"])
        return out
