"""select_candidate.py - the fixed candidate rule (frozen before fitting), independent of the tuner's code.

usage: python -I -B select_candidate.py <training_run_dir> <out_candidate.json> [--allow-nonlive]
Rule:
- The candidate is the final theta of a COMPLETE training run, whose ledger ends with a "complete" record.
- Its values are the engine integers exactly as recorded there: the nearest feasible integers to theta, i.e.
  rounding with a feasibility repair.
- They are re-checked against the run's bounds and enabled constraints.
- No intermediate checkpoint can be chosen: no checkpoint shopping, no peeking at screen or holdout.
- The training run must be a live one (RUN.json mode "live"). --allow-nonlive accepts a synthetic or replay run,
  for tests and demonstrations only. The spec records training_mode, and confirm_runner.py refuses such a
  candidate for replay unless the protocol allows it.
The training ledger is verified here with this file's own hash-chain code (no import of spsa/).
Output: a candidate spec (schema opus3-candidate-spec/1) with option lines for the gate exe (switches at 1 plus the
values) and the equivalent lock-exe line (values only), and spec_sha256 over everything else. Refuses to overwrite."""
import hashlib
import json
import sys
from pathlib import Path


def cj(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def h(b):
    return hashlib.sha256(b).hexdigest()


def fail(code, msg):
    print(json.dumps({"refused": True, "exit": code, "reason": msg}), file=sys.stderr)
    sys.exit(code)


def main(argv):
    args = [a for a in argv[1:] if a != "--allow-nonlive"]
    allow_nonlive = "--allow-nonlive" in argv[1:]
    if len(args) != 2:
        print(__doc__)
        return 10
    rd, outp = Path(args[0]), Path(args[1])
    if outp.exists():
        fail(10, f"refusing to overwrite {outp}")
    meta = json.loads((rd / "RUN.json").read_text(encoding="ascii"))
    cfg = meta["config"]
    if h(cj(cfg)) != meta["config_sha256"]:
        fail(30, "RUN.json config does not match its sha256")
    mode = meta.get("mode")
    if mode != "live" and not allow_nonlive:
        fail(10, f"training run is in mode {mode!r}: only a live run yields a confirmable candidate "
                 "(--allow-nonlive is for tests and demonstrations; the spec then records the mode)")
    raw = (rd / "ledger.jsonl").read_bytes()
    if raw and not raw.endswith(b"\n"):
        fail(30, "training ledger has an unterminated last line")
    recs, prev = [], "genesis"
    for i, line in enumerate(raw.split(b"\n")[:-1]):
        r = json.loads(line.decode("ascii"))
        body = {k: v for k, v in r.items() if k != "h"}
        if r.get("h") != h(cj(body)) or cj(r) != line or r.get("seq") != i or r.get("prev") != prev \
                or r.get("run_id") != meta["run_id"]:
            fail(30, f"training ledger record {i} fails verification")
        prev = r["h"]
        recs.append(r)
    if not recs or recs[-1]["type"] != "complete":
        fail(10, "training run is not COMPLETE (fixed rule: only the final theta of a complete run)")
    done = recs[-1]
    vals = dict(done["values"])
    params = {p["name"]: p for p in cfg["params"]}
    for n, v in vals.items():
        p = params[n]
        if p.get("enabled", True) and p.get("kind", "int") == "int" and not (p["min"] <= v <= p["max"]):
            fail(10, f"{n}={v} outside its tuned bound")
    for c in cfg.get("constraints", []):
        if c.get("enabled", True) and sum(k * vals[n] for n, k in c["coef"].items()) > c["le"]:
            fail(10, f"candidate violates {c['id']}")
    tuned = {n: vals[n] for n, p in params.items() if p.get("enabled", True)}
    spec = {"schema": "opus3-candidate-spec/1",
            "rule": "final theta of a COMPLETE live training run, engine integers as recorded in its complete record "
                    "(nearest feasible integers); bounds and enabled constraints re-checked; no other checkpoint "
                    "may be chosen",
            "training_run_id": meta["run_id"], "training_config_sha256": meta["config_sha256"],
            "training_mode": mode,
            "training_ledger_head": recs[-1]["h"], "training_complete": True, "training_k": done["k"],
            "training_openings_sha256": [cfg["identity"]["openings"]["sha256"].lower()],
            "values": vals, "tuned_values": tuned,
            "engine_options": dict({"RazorTune": 1, "QsTune": 1}, **tuned),
            "lock_equivalent_options": tuned,
            "note": "engine_options is for the gate build (switches at 1); lock_equivalent_options for the lock exe"}
    spec["spec_sha256"] = h(cj(spec))
    outp.write_bytes(json.dumps(spec, indent=1).encode("ascii") + b"\n")
    print(json.dumps(spec, indent=1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
