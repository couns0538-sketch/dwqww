"""Opus 2026-11-23: the day's decision and budget, written to SETUP_PLAN 2.2's settled D3, D4 and D5 and its failure
row 3 (Fable's FABLE-2311-SERVER-DEBATE-3, job 4). It replaces the draft of 10:28, which took a rate as given, knew
two outcomes, answered "time used up" as bad input, printed the need rounded down and let matches in as soon as the
target was covered (SETUP_PLAN section 5). Standard library only. Every decision is made in exact fractions: a
number written as 1.10 in a json file is read as the decimal 11/10, never as a binary float.

    budget.py <plan.json> <state.json> [<pilot.json>]

plan.json, written BEFORE the day (OWNER = policy, not a measurement):
  target_rows            the FULL target in C4 rows, e.g. 2000000000
  lease_end_s            the lease's absolute end, seconds after its real start (both UTC, as the provider shows them)
  closing_s              the measured closing time.  D = min(23 h, lease_end_s - max(1 h, closing_s))            (D5)
  game_margin_s          g = the pilot's longest game + this; dispatch of new games stops at D - g              (D5)
  pilot_rounds_declared  K >= 1 whole production-equivalent rounds the pilot times end to end                  (D3)
  floor_fraction         OWNER: the floor as a share of n (proposed 0.50)                                       (D4)
  match_margin           OWNER: matches only when r > match_margin x n (1.10; 2.5: strict)                      (D4)
  owner_choice           OWNER: {"name": ..., optional "reduced_target_rows": below the target} for floor <= r < n
  match_queue            [[name, even number of games], ...] in the declared order                    (D4, D11)
state.json, at the moment of the decision: now_s (seconds after the lease start), c4_rows (durable C4 at home: the
only credit), optional exclusive_s (what must still run exclusively; section 4). Any other key is printed back under
other_counts and never counted.
pilot.json, MEASURED by the pilot on the K rounds it started (D3):
  rounds_whole (declared rounds that reached durable C4 whole), queues_empty_at_start (true / false), carry_in_rows
  cohort_games, cohort_raw_rows, cohort_c4_rows, cohort_seconds (start of their first game to durable C4 of all K)
  games_per_h, c1_raw_rows_per_s, c2_raw_rows_per_s, c3_games_per_s, c4_kept_rows_per_s   (the stage capacities)
  longest_game_s, match_games_per_h (0 = not measured: matches get no share, D11)
The kept share is the cohort's own, cohort_c4_rows / cohort_raw_rows; no other source is taken.
Failure row 3 ("every input of the budget names its raw file; missing or stale: no start"): each file carries
"sources": {key: {"path": absolute path, "sha256": hex}} for its measured keys (plan lease_end_s and closing_s, state
c4_rows, every pilot key). A key that names no file, a path that is not absolute, a file that is missing, or a
file that cannot be read, or a
file whose bytes are no longer the ones its number was taken from (stale; read afresh at every decision) is a finding: in the plan or the state it makes the outcome UNQUALIFIED
before any row; in the pilot it is D3's UNQUALIFIED, and no match gets a share.

Outcomes, in this order (D4):
  REACHED       C4 >= target: no row needed and no self-play dispatched (self_play_s 0, the rest idle_s: Astra's
                boundary (a), 23 Nov); the declared match queue may use the time left BEFORE THE DISPATCH END
                (D11, D5: no new game of any kind at or after D - g; a pilot whose longest game is 0 gives none)
  SHORT         time used up with rows outstanding: the exact deficit
  UNQUALIFIED   D3's evidence is missing or not whole: nothing starts by script
  then r = min(end-to-end rate, every stage capacity), all in C4 rows a second ("the LOWER decides"), and
  n = (target - C4) / seconds left, the rate the FULL target needs:
  STOP                   r < floor_fraction x n: stop in the first hour so the machine can be given back. It
                         authorizes NOTHING: self_play_s 0, no matches, no forecast at D; what a full run would
                         have reached stands apart as forecast_if_run_scenario
  OWNER_CHOICE           floor <= r < n: the owner's predeclared choice; a reduced target is shown with its own n
  SELF_PLAY              n <= r <= match_margin x n: self-play only; the margin r / n - 1 is reported (SETUP_PLAN
                         2.5: the door is strict, at exactly 1.10 n no match second exists)
  SELF_PLAY_AND_MATCHES  r > match_margin x n: the queue, in its order, takes spare = left - match_margin x deficit
                         / r in complete pairs (2.5: the margin that opened the door stays self-play's reserve; a
                         queue lasting T is admitted only while r x (left - T) >= match_margin x deficit); the match
                         that does not fit whole gets the pairs that fit and the queue ends there. The outcome is
                         named by what is done: when no whole measured pair fits (the spare too short, a match rate
                         of 0, an empty queue) it is SELF_PLAY, and spare_s reports the spare seconds. The
                         queue's time also ends at the dispatch end: pairs fit min(spare, D - g - now) seconds.
Times: the control record carries WHOLE seconds, so the tool decides with the whole seconds it will carry: D is the
exact bound rounded DOWN, the dispatch end is D - g rounded DOWN, and left, the spare, the queue's time and SHORT
all follow from these two (at the encoded cutoff the time left is 0, at the encoded dispatch end no pair is new).
cutoff_floor_s and dispatch_end_floor_s are those two as integers; D_s and dispatch_stop_s show the same values;
bounds_exact keeps the exact source bounds as fractions, for the record only. new_dispatch_s is the time left
before the dispatch end. A finding of failure row 3 names the key and the kind of failure; the paths behind the
findings stand under local_only, which never leaves the home machine. A nonzero exclusive_s names its raw file
under state.sources like every measured key (failure row 3); an omitted or zero one needs none.
inputs names the sha256 of the exact bytes of each file read (plan, state, pilot; null where no pilot was given):
two pilots with equal rates are two pieces of evidence. No path of this machine is in it.
Prints one json object. Exit 0 REACHED, SELF_PLAY, SELF_PLAY_AND_MATCHES; 3 OWNER_CHOICE; 4 STOP; 5 SHORT;
6 UNQUALIFIED; 2 bad input (a missing key, a wrong type or range: the plan is checked whole, whatever the outcome;
a key that stands twice in one object, NaN, Infinity or a number beyond a float such as 1e500; a match without a name;
2.5, Neon's form: a count of rows or games that is not a whole number, a bool included: target_rows,
reduced_target_rows, c4_rows, carry_in_rows, cohort_games, cohort_raw_rows, cohort_c4_rows; rounds_whole above
pilot_rounds_declared).
Time trust after a restart of the host (D5) is the runner's: this tool takes now_s and lease_end_s as given.
"""
import hashlib
import json
import math
import os
import sys
from decimal import Decimal
from fractions import Fraction

PLAN_KEYS = ("target_rows", "lease_end_s", "closing_s", "game_margin_s", "pilot_rounds_declared", "floor_fraction",
             "match_margin", "owner_choice", "match_queue")
PILOT_KEYS = ("rounds_whole", "queues_empty_at_start", "carry_in_rows", "cohort_games", "cohort_raw_rows",
              "cohort_c4_rows", "cohort_seconds", "games_per_h", "c1_raw_rows_per_s", "c2_raw_rows_per_s",
              "c3_games_per_s", "c4_kept_rows_per_s", "longest_game_s", "match_games_per_h")
MEASURED = ("cohort_games", "cohort_raw_rows", "cohort_c4_rows", "cohort_seconds", "games_per_h",
            "c1_raw_rows_per_s", "c2_raw_rows_per_s", "c3_games_per_s", "c4_kept_rows_per_s", "longest_game_s")
SOURCED = {"plan": ("lease_end_s", "closing_s"), "state": ("c4_rows",), "pilot": PILOT_KEYS}
EXIT = {"REACHED": 0, "SELF_PLAY": 0, "SELF_PLAY_AND_MATCHES": 0, "OWNER_CHOICE": 3, "STOP": 4, "SHORT": 5,
        "UNQUALIFIED": 6}
WHOLE = ("target_rows", "reduced_target_rows", "c4_rows", "carry_in_rows", "cohort_games", "cohort_raw_rows",
         "cohort_c4_rows")


def q(x, name):
    """An exact number >= 0: an int, or a decimal as written. A bool, a string or a negative number is bad input; a
    count of rows or games (WHOLE) is an int (SETUP_PLAN 2.5, Neon's form: 1999999999.5 and true are bad input)."""
    if isinstance(x, bool) or not isinstance(x, (int, Decimal)) or x < 0:
        raise ValueError(f"{name}: a number >= 0, not {x!r}")
    if name in WHOLE and not isinstance(x, int):
        raise ValueError(f"{name}: a whole number of rows or games, not {x!r}")
    return Fraction(x)


def num(x, nd):
    return round(float(x), nd)


def need(rows, left):
    return {"n_exact": num(rows / left, 6), "n_ceil": math.ceil(rows / left)}


def sha256_of(path, cache):
    """The file's sha256, read once a DECISION (Neon 162055Z: a cache that outlives one call of decide() lets a raw
    file that changed between two calls pass). None when the file cannot be read."""
    if path not in cache:
        h = hashlib.sha256()
        try:
            with open(path, "rb") as fh:
                for block in iter(lambda: fh.read(1 << 20), b""):
                    h.update(block)
            cache[path] = h.hexdigest()
        except OSError:
            cache[path] = None
    return cache[path]


def unsourced(obj, where, cache, local):
    """Failure row 3: each measured key names its raw file, and the file still holds the bytes it was taken from.
    The findings name the key and the kind of failure; the path goes to `local` only (Astra 165415Z: a report
    packed for the server carries no path of the home machine)."""
    src, bad = obj.get("sources"), []
    keys = SOURCED[where]
    if where == "state" and obj.get("exclusive_s") not in (None, 0):
        keys = keys + ("exclusive_s",)          # Astra 165715Z: a nonzero exclusive time names its raw file too
    for k in keys:
        s = src.get(k) if isinstance(src, dict) else None
        if not (isinstance(s, dict) and isinstance(s.get("path"), str) and isinstance(s.get("sha256"), str)):
            what = "no raw file named"
        elif not os.path.isabs(s["path"]):
            what = "the raw file's path is not absolute"
        elif not os.path.isfile(s["path"]):
            what = "raw file missing"
        elif sha256_of(s["path"], cache) is None:
            what = "raw file unreadable"
        elif sha256_of(s["path"], cache) != s["sha256"].lower():
            what = "raw file changed since the number was taken (stale)"
        else:
            continue
        bad.append(f"{where}.{k}: {what}")
        local.append([f"{where}.{k}", what, s.get("path") if isinstance(s, dict) else None])
    return bad


def fill(queue, spare, gph):
    """The declared queue in order, in complete pairs, inside `spare` seconds at `gph` games an hour."""
    pairs = math.floor(spare * gph / 7200) if gph > 0 and spare > 0 else 0
    done = []
    for name, games in queue:
        give = min(games, 2 * pairs)
        if give == 0:
            break
        done.append([name, games, give, Fraction(give) * 3600 / gph])
        pairs -= give // 2
        if give < games:
            break
    return done


def finish(res, matches, left, r, c4):
    used = sum((m[3] for m in matches), Fraction(0))
    res.update(matches=[[a, b, c, num(s, 1)] for a, b, c, s in matches], matches_s=num(used, 1),
               self_play_s=num(left - used, 1))
    if r is not None:  # a scenario at the measured rate, never a bound (D13): only durable C4 is certain
        res["forecast_c4_at_D_scenario"] = int(c4 + r * (left - used))
    return res


def decide(plan, state, pilot=None):
    miss = [k for k in PLAN_KEYS if k not in plan] + [f"state.{k}" for k in ("now_s", "c4_rows") if k not in state]
    if pilot is not None:
        miss += [f"pilot.{k}" for k in PILOT_KEYS if k not in pilot]
    if miss:
        raise KeyError("missing: " + ", ".join(miss))
    target, lease_end, closing, gm, floor_f, margin = (q(plan[k], k) for k in (
        "target_rows", "lease_end_s", "closing_s", "game_margin_s", "floor_fraction", "match_margin"))
    K, choice, queue = plan["pilot_rounds_declared"], plan["owner_choice"], plan["match_queue"]
    if not (target > 0 and type(K) is int and K >= 1 and 0 < floor_f < 1 and margin >= 1 and isinstance(choice, dict)
            and isinstance(choice.get("name"), str) and choice["name"].strip()):
        raise ValueError("plan: target_rows > 0, pilot_rounds_declared an integer >= 1, 0 < floor_fraction < 1, "
                         "match_margin >= 1, owner_choice with a name")
    reduced = choice.get("reduced_target_rows")
    if reduced is not None and not 0 < q(reduced, "reduced_target_rows") < target:
        raise ValueError("plan: reduced_target_rows must lie between 0 and target_rows")
    if not isinstance(queue, list) or not all(isinstance(m, list) and len(m) == 2 and isinstance(m[0], str)
                                              and m[0].strip() and type(m[1]) is int and m[1] > 0 and m[1] % 2 == 0
                                              for m in queue):
        raise ValueError("plan: match_queue is [[a name, even number of games > 0], ...]")
    now, c4 = q(state["now_s"], "now_s"), q(state["c4_rows"], "c4_rows")
    excl = q(state.get("exclusive_s", 0), "exclusive_s")
    P = None
    if pilot is not None:
        if not isinstance(pilot["queues_empty_at_start"], bool) or type(pilot["rounds_whole"]) is not int:
            raise ValueError("pilot: queues_empty_at_start is true or false, rounds_whole an integer")
        P = {k: q(pilot[k], k) for k in PILOT_KEYS if k != "queues_empty_at_start"}
        if P["cohort_c4_rows"] > P["cohort_raw_rows"]:
            raise ValueError("pilot: more kept rows than raw rows")
        if P["rounds_whole"] > K:
            raise ValueError("pilot: rounds_whole is above the plan's pilot_rounds_declared")
    cache, local = {}, []                       # one decision reads every raw file afresh
    found = unsourced(plan, "plan", cache, local) + unsourced(state, "state", cache, local)
    pfound = unsourced(pilot, "pilot", cache, local) if pilot is not None else []
    D_exact = min(Fraction(23 * 3600), lease_end - max(Fraction(3600), closing))
    # Astra 165415Z, 165505Z: the control carries WHOLE seconds, so every window below is computed from the whole
    # seconds it will carry (the exact bounds rounded DOWN), never from a fraction the machine is not given
    D = Fraction(math.floor(D_exact))
    left = D - now - excl
    deficit = max(Fraction(0), target - c4)
    stop_exact = D_exact - P["longest_game_s"] - gm if P else None
    stop_new = Fraction(math.floor(D - P["longest_game_s"] - gm)) if P else None    # D5: no NEW game at or after it
    new_s = max(Fraction(0), stop_new - now - excl) if P else Fraction(0)
    res = {"outcome": None, "reason": "", "c4_rows": int(c4), "deficit_rows": int(deficit), "D_s": num(D, 1),
           "dispatch_stop_s": num(stop_new, 1) if P else None, "left_s": num(left, 1),
           # the same two whole seconds as integers, for the control record; bounds_exact keeps the exact source
           # bounds for the record of where they came from (never sent as a bound)
           "cutoff_floor_s": int(D), "dispatch_end_floor_s": int(stop_new) if P else None,
           "new_dispatch_s": num(new_s, 1) if P else None,
           "bounds_exact": {"D_s": str(D_exact), "dispatch_end_s": str(stop_exact) if P else None},
           "other_counts": {k: v for k, v in state.items() if k not in ("now_s", "c4_rows", "exclusive_s", "sources")}}
    if local:                                   # stays on the home machine: the paths behind the findings
        res["local_only"] = {"raw_files": local}
    if found:
        res.update(outcome="UNQUALIFIED", reason="failure row 3: " + "; ".join(found) + "; nothing starts by script")
        return res
    if deficit == 0:
        res.update(outcome="REACHED", reason="C4 holds the target: no row needed; the match queue may use the time "
                                             "left before the dispatch end")
        spare = max(left, Fraction(0))
        rate = P["match_games_per_h"] if P and not pfound and P["longest_game_s"] > 0 else 0
        matches = fill(queue, min(spare, new_s), rate)   # Astra 161757Z 1: no new pair at or after the dispatch end
        res = finish(res, matches, spare, None, c4)
        # Astra's boundary (a), 23 Nov: once the target is durable no self-play is dispatched; the rest is idle
        res.update(self_play_s=0.0, idle_s=num(spare - sum((m[3] for m in matches), Fraction(0)), 1))
        return res
    if left <= 0:
        res.update(outcome="SHORT", reason=f"time used up with {int(deficit)} C4 rows outstanding")
        return res
    why = None
    if P is None:
        why = "no pilot record"
    elif pfound:
        why = "failure row 3: " + "; ".join(pfound)
    elif P["rounds_whole"] < K:
        why = f"{int(P['rounds_whole'])} of {K} declared rounds reached durable C4 whole"
    elif not pilot["queues_empty_at_start"]:
        why = "the queues were not empty when the timed rounds started"
    elif P["carry_in_rows"] > 0:
        why = f"{int(P['carry_in_rows'])} carried-in rows inside the timed window"
    elif any(P[k] == 0 for k in MEASURED):
        why = "not measured (0): " + ", ".join(k for k in MEASURED if P[k] == 0)
    if why:
        res.update(outcome="UNQUALIFIED", reason=f"D3: {why}; nothing starts by script")
        return res
    assert P is not None  # the chain above returned when there is no pilot
    share, per_game = P["cohort_c4_rows"] / P["cohort_raw_rows"], P["cohort_raw_rows"] / P["cohort_games"]
    rates = {"end_to_end": P["cohort_c4_rows"] / P["cohort_seconds"],
             "production": P["games_per_h"] / 3600 * per_game * share,
             "C1": P["c1_raw_rows_per_s"] * share, "C2": P["c2_raw_rows_per_s"] * share,
             "C3": P["c3_games_per_s"] * per_game * share, "C4": P["c4_kept_rows_per_s"]}
    r = min(rates.values())
    n = deficit / left
    res.update(need(deficit, left))
    res.update(r=num(r, 3), r_from=next(k for k, v in rates.items() if v == r),
               rates={k: num(v, 3) for k, v in rates.items()}, kept_share=num(share, 6),
               floor_rows_per_s=num(floor_f * n, 3), matches_from_rows_per_s=num(margin * n, 3),
               margin=num(r / n - 1, 6),       # the decision uses these exact values, never the rounded ones above
               exact={"r": str(r), "n": str(n), "floor": str(floor_f * n), "matches_from": str(margin * n)})
    if r < floor_f * n:
        # Astra 161757Z 2: STOP authorizes no play at all; the figure of a full run is named as what it is
        res.update(outcome="STOP", reason="r is under the floor: stop in the first hour so the machine can be given "
                                          "back; no self-play and no match is authorized",
                   matches=[], matches_s=0.0, self_play_s=0.0, forecast_if_run_scenario=int(c4 + r * left))
        return res
    if r < n:
        res.update(outcome="OWNER_CHOICE", reason="floor <= r < n: the owner's predeclared choice, no improvising",
                   owner_choice=choice["name"])
        if reduced is not None:
            rest = max(Fraction(0), Fraction(reduced) - c4)
            res["reduced"] = dict(target_rows=int(reduced), covered=r >= rest / left, **need(rest, left))
        return finish(res, [], left, r, c4)
    if r <= margin * n:                         # 2.5: the door is strict
        res.update(outcome="SELF_PLAY", reason="n <= r <= match_margin x n: self-play only")
        return finish(res, [], left, r, c4)
    spare = left - margin * deficit / r         # 2.5: the margin that opened the door stays self-play's reserve
    matches = fill(queue, min(spare, new_s), P["match_games_per_h"])    # and no new pair after the dispatch end
    res["spare_s"] = num(spare, 3)
    if not matches:                             # 2.5: named by what is done
        res.update(outcome="SELF_PLAY", reason="r > match_margin x n and no whole measured pair fits the spare before "
                                               "the dispatch end (too short, no match rate, an empty queue, or the "
                                               "dispatch end has come): self-play only")
        return finish(res, [], left, r, c4)
    res.update(outcome="SELF_PLAY_AND_MATCHES",
               reason="r > match_margin x n: the declared queue takes the spare above the margin in complete pairs")
    return finish(res, matches, left, r, c4)


def _no_constant(name):
    raise ValueError(f"json: {name} is not a number this tool takes")


def _decimal(text):
    d = Decimal(text)
    if not math.isfinite(float(d)):             # 1e500 is a number in json and Infinity as a float
        raise ValueError(f"json: {text} is not a number this tool takes")
    return d


def _no_duplicates(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError(f"json: the key {k!r} stands twice")
        d[k] = v
    return d


def load(path):
    """(the parsed object, the sha256 of the exact bytes it was parsed from). Neon 162055Z 2: a key that stands
    twice, NaN and Infinity are bad input, never silently one of the two values."""
    with open(path, "rb") as fh:
        data = fh.read()
    obj = json.loads(data.decode("utf-8"), parse_float=_decimal, parse_constant=_no_constant,
                     object_pairs_hook=_no_duplicates)
    return obj, hashlib.sha256(data).hexdigest()


if __name__ == "__main__":
    try:
        if len(sys.argv) not in (3, 4):
            raise ValueError("usage: budget.py <plan.json> <state.json> [<pilot.json>]")
        (plan_, hp), (state_, hs) = load(sys.argv[1]), load(sys.argv[2])
        pilot_, hpi = load(sys.argv[3]) if len(sys.argv) == 4 else (None, None)
        out = decide(plan_, state_, pilot_)
        # Astra 162047Z: the result names the exact bytes it was computed from (two pilots with equal rates are two
        # pieces of evidence); no path of this machine is in it, and a pilot that was not given has no sha256
        out["inputs"] = {"plan_sha256": hp, "state_sha256": hs, "pilot_sha256": hpi}
        text = json.dumps(out, default=float, allow_nan=False)     # a number that is not finite is bad input too
    except (OSError, ValueError, KeyError, IndexError, TypeError, AttributeError, ArithmeticError) as e:
        print(json.dumps({"error": f"{type(e).__name__}: {e}"}))
        sys.exit(2)
    print(text)
    sys.exit(EXIT[out["outcome"]])
