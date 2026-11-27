"""Opus 2026-11-23: the control maker (A3e; FORMATS 1.2 [2.8], [2.9]; Fable's NOT YET F1 on the guard, 18:44).
Home turns one budget report into the two files the server guard reads: the PUBLIC record of the report (the
evidence) and the control record CONTROL.<k>.json. Standard library only.

    make_control.py --report REPORT --header RUN.json --policy plan.json --accepted DIR --kind KIND --out NEWDIR
                    [--state state.json] [--pilot pilot.json]

REPORT is the budget tool's output saved as a file (its exact bytes); RUN.json the day's header; plan.json the
policy file the budget tool read (the package's); state.json and pilot.json the two other files it read (their
exact bytes); DIR home's copy of the server's control/ folder (CONTROL.<j>.json and EVIDENCE.<sha>.json of the
accepted controls; an empty folder before the first); KIND pilot_decision, target, matches or fence; NEWDIR a folder
that does not exist yet.

VERSION 2 (Opus 2026-11-24; Astra 214130Z and Neon's NOT YET 20261123T222600Z section 4; known answers
tmp/opus_scratch/mc_prog2/KNOWN_ANSWERS_make_control_v2_by_opus.md on the PC, written before this code): M1 the
policy for every kind, M2 the run binding of state and pilot, M3 the freshness of the state, M4 the accepted folder
read as the guard reads its control/ folder, M5 the order of the kinds, M6 the match rows against the policy's queue.

THE EVIDENCE (F1: the budget's full output holds decimal numbers, FORMATS 0 allows none in a record): a canonical
record with exactly schema 2, report_sha256 (the sha256 of REPORT's bytes: the full output stays at home, local_only
and all), and the report's own outcome, reason, c4_rows, deficit_rows, cutoff_floor_s, dispatch_end_floor_s,
inputs, matches (each row without its fourth element, the seconds; null without a matches key) and reduced
(covered and target_rows; null without it), and state_now_s (M3: the state's now_s; null when no state is given).
Every value is COPIED unchanged: nothing is converted or rounded, and a value of another type is refused. Both
hashes, in words (Astra 214130Z): CONTROL.evidence is the sha256 of this PUBLIC record; the record's report_sha256
is the sha256 of the budget tool's full output.

THE RUN BINDING (M2): kinds pilot_decision, target and matches need --state and --pilot; every file given (state
first, then pilot) must have the sha256 the report names (inputs.state_sha256, inputs.pilot_sha256) and be a json
object whose run_fingerprint is the sha256 of RUN.json. Kind fence needs neither: a stop is never blocked by the
binding. The state's now_s must be a whole number (M3).

THE CONTROL: k = one more than the accepted chain in DIR (checked: the names in the guard's grammar, canonical, its
keys, k, this run, prev links, then each control's evidence record beside it with the sha256 it names); kinds
target and matches need an accepted pilot_decision, and no control follows one whose effect was the fence (M5); a
control with a state is refused when its now_s is below the newest state an accepted control rests on (M3); the
effect as the guard's G3 f finds it; decision = the outcome (for kind matches: the public matches, which must be the
policy's match_queue in its order in whole pairs, M6); the bounds: a schedule takes the lease start plus the
report's whole floors, each not later than the bounds in force; every other effect carries the bounds in force
unchanged (the newest accepted control's, or the header's hard cutoff for both before any); scope
{"highest_round": 9999, "target_rows": the policy's target, or its reduced_target_rows under an OWNER_CHOICE of
action reduced_target} for a schedule, else null. Every kind needs a report computed from this policy (M1); kinds
other than fence need one that names a pilot report.
F2 (Opus 26 Nov; known answers tmp/opus_scratch/v17/KNOWN_ANSWERS_F2_by_opus.md, written before): OWNER_CHOICE with
the policy's action "self_play" (the owner's 1A of 25 Nov: as many rows as fit into the day) is a schedule with the
policy's full target; the budget tool refuses a plan without a known action, and this tool still refuses one.

Written into NEWDIR, create-only, in this order: EVIDENCE.<sha>.json, its .zz, CONTROL.<k>.json, its .zz (zlib 6);
home sends them in the same order: the evidence first, the control LAST.
Exit 0 made; 2 arguments or a file that cannot be read, NEWDIR exists, DIR missing; 4 refused (the reason named):
the inputs do not give a control the guard accepts, or one out of order or on another run's files. A refusal
writes nothing.
"""
import argparse
import calendar
import hashlib
import json
import re
import sys
import time
import zlib
from pathlib import Path

OUTCOMES = ("REACHED", "SELF_PLAY", "SELF_PLAY_AND_MATCHES", "OWNER_CHOICE", "STOP", "SHORT", "UNQUALIFIED")
KINDS = ("pilot_decision", "target", "matches", "fence")
CONTROL_KEYS = ["at_utc", "cutoff_utc", "decision", "dispatch_end_utc", "evidence", "k", "kind", "owner_policy",
                "prev", "run_fingerprint", "schema", "scope"]
HEX64 = re.compile(r"[0-9a-f]{64}")
UTC = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ")
CTL_NAME = re.compile(r"CONTROL\.([1-9][0-9]{0,8})\.json")       # the guard's grammar (replay_controls)
HIGHEST_ROUND = 9999


class Refused(Exception):
    pass


def canon(obj) -> bytes:
    return (json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False)
            + "\n").encode("ascii")


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _pairs(pairs):
    d = {}
    for k, v in pairs:
        if k in d:
            raise ValueError(f"the key {k!r} stands twice")
        d[k] = v
    return d


def _no_constant(text):
    raise ValueError(f"{text} is not a number")


def strict(data: bytes, what: str):
    try:
        return json.loads(data.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_no_constant)
    except ValueError as e:
        raise Refused(f"{what}: not json without a key twice or a NaN ({e})") from None


def canonical(data: bytes, what: str):
    obj = strict(data, what)
    if canon(obj) != data:
        raise Refused(f"{what}: not a canonical record")
    return obj


def T(t: int) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t))


def utc(text, what: str) -> int:
    if not isinstance(text, str) or not UTC.fullmatch(text):
        raise Refused(f"{what} is not a UTC time")
    return calendar.timegm(time.strptime(text, "%Y-%m-%dT%H:%M:%SZ"))


def whole(x) -> bool:
    return type(x) is int and x >= 0


def public(rep) -> dict:
    """The evidence: the report's own values, copied unchanged, refused when one has another type."""
    if not isinstance(rep, dict) or "error" in rep:
        raise Refused("the report is not a budget decision (an object without `error`)")
    if rep.get("outcome") not in OUTCOMES:
        raise Refused(f"the report's outcome {str(rep.get('outcome'))[:40]} is none of {', '.join(OUTCOMES)}")
    for k in ("c4_rows", "deficit_rows", "cutoff_floor_s"):
        if not whole(rep.get(k)):
            raise Refused(f"the report's {k} is not a whole number ({str(rep.get(k))[:40]}): nothing is rounded")
    disp = rep.get("dispatch_end_floor_s")
    if disp is not None and not whole(disp):
        raise Refused(f"the report's dispatch_end_floor_s is not a whole number or null ({str(disp)[:40]})")
    if not isinstance(rep.get("reason"), str):
        raise Refused("the report has no reason text")
    inp = rep.get("inputs")
    if not (isinstance(inp, dict) and sorted(inp) == ["pilot_sha256", "plan_sha256", "state_sha256"]
            and all(HEX64.fullmatch(str(inp[k])) for k in ("plan_sha256", "state_sha256"))
            and (inp["pilot_sha256"] is None or HEX64.fullmatch(str(inp["pilot_sha256"])))):
        raise Refused("the report's inputs are not plan_sha256, state_sha256 and pilot_sha256 (or null)")
    matches = None
    if "matches" in rep:
        rows = rep["matches"]
        if not (isinstance(rows, list) and all(isinstance(m, list) and len(m) == 4 and isinstance(m[0], str)
                                               and whole(m[1]) and whole(m[2]) for m in rows)):
            raise Refused("the report's matches are not rows [name, games, given, seconds] with whole games")
        matches = [m[:3] for m in rows]
    reduced = None
    if "reduced" in rep:
        red = rep["reduced"]
        if not (isinstance(red, dict) and type(red.get("covered")) is bool and whole(red.get("target_rows"))):
            raise Refused("the report's reduced has no covered (true or false) and whole target_rows")
        reduced = {"covered": red["covered"], "target_rows": red["target_rows"]}
    return {"c4_rows": rep["c4_rows"], "cutoff_floor_s": rep["cutoff_floor_s"], "deficit_rows": rep["deficit_rows"],
            "dispatch_end_floor_s": disp, "inputs": dict(inp), "matches": matches, "outcome": rep["outcome"],
            "reason": rep["reason"], "reduced": reduced, "schema": 2}


def queue_rows(matches: list, policy) -> None:
    """M6: the rows are the policy's match_queue in its order, in whole pairs (the budget tool's fill: the queue
    ends at the first partial match)."""
    queue = policy.get("match_queue") if isinstance(policy, dict) else None
    ok = isinstance(queue, list) and len(matches) <= len(queue)
    for i, (name, games, given) in enumerate(matches if ok else []):
        q = queue[i]
        ok = (ok and isinstance(q, list) and q == [name, games] and 0 < given <= games and given % 2 == 0
              and (given == games or i == len(matches) - 1))
    if not ok:
        raise Refused("the report's matches are not the policy's match_queue in its order, in whole pairs")


def bound(data: bytes, want: str, what: str, fp: str) -> dict:
    """M2: the file the report was computed from (its sha256), and this run's (its run_fingerprint)."""
    if sha(data) != want:
        raise Refused(f"--{what} is not the {what} the report was computed from (inputs.{what}_sha256)")
    obj = strict(data, f"the {what}")
    if not isinstance(obj, dict) or obj.get("run_fingerprint") != fp:
        raise Refused(f"the {what} is another run's (run_fingerprint)")
    return obj


def effect(kind: str, outcome, policy: dict, reduced):
    """(effect, target cap) as the guard's G3 f finds it; Refused where the guard would hold."""
    if kind == "fence":
        return "fence", None
    if kind == "matches" or outcome == "UNQUALIFIED":
        return "none", None
    if outcome in ("REACHED", "STOP", "SHORT"):
        return "fence", None
    if outcome in ("SELF_PLAY", "SELF_PLAY_AND_MATCHES"):
        return "schedule", None
    oc = policy.get("owner_choice") if isinstance(policy, dict) else None
    act = oc.get("action") if isinstance(oc, dict) else None
    if act == "stop":
        return "fence", None
    if act == "self_play":                          # F2: the owner's 1A, as many rows as fit before the cutoff
        return "schedule", None
    if act != "reduced_target":
        raise Refused(f"OWNER_CHOICE, and the policy's action {str(act)[:40]} is not stop, reduced_target or "
                      f"self_play")
    cap = oc.get("reduced_target_rows")
    if type(cap) is not int or reduced is None or reduced["target_rows"] != cap:
        raise Refused(f"the report's reduced target is not the policy's reduced_target_rows {cap}")
    if reduced["covered"] or oc.get("if_uncovered") == "self_play":
        return "schedule", cap
    if oc.get("if_uncovered") == "stop":
        return "fence", None
    raise Refused("OWNER_CHOICE with an uncovered reduced target, and the policy names no if_uncovered (stop or "
                  "self_play)")


def chain(folder: Path, fp: str):
    """(k, prev, bounds in force or None, [(control, its evidence record)]): the accepted controls must be exactly
    1 .. m in the guard's grammar and link; then each one's evidence record must lie beside it (M4)."""
    names = [p.name for p in folder.glob("CONTROL.*.json")]
    if any(not CTL_NAME.fullmatch(x) for x in names):
        raise Refused(f"the accepted folder {folder.name}: a file name outside the grammar: {sorted(names)[:5]}")
    nums = sorted(int(CTL_NAME.fullmatch(x).group(1)) for x in names)
    if nums != list(range(1, len(nums) + 1)):
        raise Refused(f"the accepted controls in {folder.name} are not exactly 1 to {len(nums)}: {nums[:8]}")
    prev, recs = "first", []
    for j in nums:
        data = (folder / f"CONTROL.{j}.json").read_bytes()
        c = canonical(data, f"CONTROL.{j}.json")
        if not isinstance(c, dict) or sorted(c) != CONTROL_KEYS or c["schema"] != 2 or c["k"] != j:
            raise Refused(f"CONTROL.{j}.json: not a control record of FORMATS 1.2 with k {j}")
        if c["run_fingerprint"] != fp:
            raise Refused(f"CONTROL.{j}.json: another run's fingerprint")
        if c["prev"] != prev:
            raise Refused(f"CONTROL.{j}.json: prev does not link to control {j - 1}")
        prev = sha(data)
        recs.append(c)
    pairs = []
    for c in recs:                          # M4, after every chain check: version 1's causes stay
        ev = str(c["evidence"])
        p = folder / f"EVIDENCE.{ev}.json"
        data = p.read_bytes() if HEX64.fullmatch(ev) and p.is_file() else None
        if data is None or sha(data) != ev:
            raise Refused(f"CONTROL.{c['k']}.json: its evidence is not in the accepted folder with the sha256 it names")
        e = canonical(data, f"EVIDENCE.{ev[:12]}... of CONTROL.{c['k']}.json")
        if not isinstance(e, dict):
            raise Refused(f"EVIDENCE.{ev[:12]}... of CONTROL.{c['k']}.json: not a record")
        pairs.append((c, e))
    bounds = None if not recs else (utc(recs[-1]["cutoff_utc"], "cutoff_utc"),
                                    utc(recs[-1]["dispatch_end_utc"], "dispatch_end_utc"))
    return len(nums) + 1, prev, bounds, pairs


def create_only(path: Path, data: bytes) -> None:
    with open(path, "xb") as fh:
        fh.write(data)
    if path.read_bytes() != data:
        raise OSError(f"{path.name}: read back differs")


def make(a) -> str:
    report = Path(a.report).read_bytes()
    header, policy_bytes = Path(a.header).read_bytes(), Path(a.policy).read_bytes()
    given = {w: Path(p).read_bytes() for w, p in (("state", a.state), ("pilot", a.pilot)) if p is not None}
    acc = Path(a.accepted)
    if not acc.is_dir():
        raise FileNotFoundError(f"{acc}: the folder of the accepted controls does not exist (empty before the first)")
    out = Path(a.out)
    if out.exists():
        raise FileExistsError(f"{out} exists (a NEW folder)")
    ev = public(strict(report, "the report"))
    ev["report_sha256"] = sha(report)
    h = canonical(header, "RUN.json")
    if not isinstance(h, dict):
        raise Refused("RUN.json is not a header")
    lease, hard = utc(h.get("lease_start_utc"), "lease_start_utc"), utc(h.get("hard_cutoff_utc"), "hard_cutoff_utc")
    policy, psha, fp = strict(policy_bytes, "the policy"), sha(policy_bytes), sha(header)
    if ev["inputs"]["plan_sha256"] != psha:                                         # M1: every kind
        raise Refused("the report was not computed from this policy file (inputs.plan_sha256)")
    if a.kind != "fence":
        if ev["inputs"]["pilot_sha256"] is None:
            raise Refused(f"kind {a.kind}: the report names no pilot report (inputs.pilot_sha256 is null)")
        if sorted(given) != ["pilot", "state"]:
            raise Refused(f"kind {a.kind} needs --state and --pilot: the files the report was computed from")
    files = {w: bound(given[w], ev["inputs"][f"{w}_sha256"], w, fp) for w in ("state", "pilot") if w in given}
    now = files["state"].get("now_s") if "state" in files else None
    if "state" in files and not whole(now):
        raise Refused(f"the state's now_s is not a whole number ({str(now)[:40]}): nothing is rounded")
    ev["state_now_s"] = now
    eff, cap = effect(a.kind, ev["outcome"], policy, ev["reduced"])
    if a.kind == "matches" and not ev["matches"]:
        raise Refused("kind matches: the report assigns no matches")
    if ev["matches"] is not None:
        queue_rows(ev["matches"], policy)
    k, prev, force, accepted = chain(acc, fp)
    fenced = [c["k"] for c, e in accepted if effect(c["kind"], c["decision"], policy, e.get("reduced"))[0] == "fence"]
    if fenced:
        raise Refused(f"the day is fenced by CONTROL.{fenced[0]}.json: the guard reads no control after it")
    if a.kind in ("target", "matches") and not any(c["kind"] == "pilot_decision" for c, _ in accepted):
        raise Refused(f"kind {a.kind} before any pilot_decision: the decision after the pilot comes first")
    seen = [(e["state_now_s"], c["k"]) for c, e in accepted if whole(e.get("state_now_s"))]
    if now is not None and seen and now < max(seen)[0]:
        raise Refused(f"the report rests on an older state (now_s {now}) than accepted control {max(seen)[1]}'s "
                      f"({max(seen)[0]})")
    cut_in, disp_in = force or (hard, hard)
    scope = None
    if eff == "schedule":
        if ev["dispatch_end_floor_s"] is None:
            raise Refused("a schedule needs the report's dispatch_end_floor_s")
        cut, disp = lease + ev["cutoff_floor_s"], lease + ev["dispatch_end_floor_s"]
        if cut > cut_in or disp > disp_in or disp > cut:
            raise Refused(f"a bound later than the one in force (cutoff {T(cut)} against {T(cut_in)}, dispatch end "
                          f"{T(disp)} against {T(disp_in)}) or a dispatch end after the cutoff")
        target = cap if cap is not None else policy.get("target_rows")
        if type(target) is not int or target < 1:
            raise Refused(f"the policy's target {str(target)[:40]} is not a whole number >= 1")
        scope = {"highest_round": HIGHEST_ROUND, "target_rows": target}
    else:
        cut, disp = cut_in, disp_in
    evb = canon(ev)
    c = {"at_utc": T(int(time.time())), "cutoff_utc": T(cut),
         "decision": ev["matches"] if a.kind == "matches" else ev["outcome"], "dispatch_end_utc": T(disp),
         "evidence": sha(evb), "k": k, "kind": a.kind, "owner_policy": psha, "prev": prev, "run_fingerprint": fp,
         "schema": 2, "scope": scope}
    cb = canon(c)
    out.mkdir(parents=True)
    create_only(out / f"EVIDENCE.{sha(evb)}.json", evb)
    create_only(out / f"EVIDENCE.{sha(evb)}.json.zz", zlib.compress(evb, 6))
    create_only(out / f"CONTROL.{k}.json", cb)
    create_only(out / f"CONTROL.{k}.json.zz", zlib.compress(cb, 6))
    return (f"make_control: CONTROL.{k}.json {sha(cb)} (kind {a.kind}, decision {str(c['decision'])[:60]}, effect "
            f"{eff}, cutoff {c['cutoff_utc']}, dispatch end {c['dispatch_end_utc']}, scope {scope}) and "
            f"EVIDENCE.{sha(evb)[:12]}... in {out}; send the evidence first, the control last")


def main() -> int:
    p = argparse.ArgumentParser(allow_abbrev=False)
    for name in ("--report", "--header", "--policy", "--accepted", "--out"):
        p.add_argument(name, required=True)
    p.add_argument("--kind", required=True, choices=KINDS)
    p.add_argument("--state")
    p.add_argument("--pilot")
    a = p.parse_args()
    try:
        print(make(a))
        return 0
    except Refused as e:
        print(f"make_control: REFUSED (nothing written): {e}")
        return 4
    except OSError as e:
        print(f"make_control: {type(e).__name__}: {e}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
