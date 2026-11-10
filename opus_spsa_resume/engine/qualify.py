"""qualify.py - identity battery for the tune-gate builds (UCI, bench, perft, gate semantics). No games.

usage: python -I -B qualify.py <lock.exe> <off.exe> <gate.exe> <out_dir> [--ctl <ctl.exe>]
Runs uci_driver.py (Idle, CPUs 12-15) and writes one JSON per check plus summary.json into <out_dir>:
  uci option lists (off == lock; gate == lock + RazorTune/QsTune lines),
  bench d11/13/16/20/22 net on and off for lock, ctl, off, gate (switches 0) and gate (switches 1 at defaults),
  perft 5 startpos / kiwipete for lock, off, gate,
  gate semantics: values set while a switch is 0 change nothing; switch 1 applies them (and equals the lock exe
  with the same values); switch 0 again restores the pins; the order of setoption calls does not matter."""
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRIVER = HERE / "uci_driver.py"
PINS_ON = {"11": 312866, "13": 862329, "16": 3024920, "20": 12389307, "22": 34048354}
PINS_OFF = {"11": 375354, "13": 907205, "16": 2448617, "20": 13573040, "22": 24506465}
PERFT = {"startpos": 4865609, "kiwipete": 193690690}


def drive(*args):
    p = subprocess.run([sys.executable, "-I", "-B", str(DRIVER)] + [str(a) for a in args], capture_output=True,
                       text=True, timeout=7200)
    if p.returncode != 0:
        raise SystemExit(f"driver failed {args[:2]}: {p.stderr[-400:]}")
    return json.loads(p.stdout)


def save(out, name, obj):
    (out / f"{name}.json").write_text(json.dumps(obj, indent=1) + "\n", encoding="ascii")
    return obj


def main(argv):
    lock, off, gate, out = Path(argv[1]), Path(argv[2]), Path(argv[3]), Path(argv[4])
    ctl = Path(argv[argv.index("--ctl") + 1]) if "--ctl" in argv else None
    out.mkdir(parents=True, exist_ok=True)
    res = {}
    # 1. UCI option lists
    o = {k: save(out, f"uciopts_{k}", drive("uciopts", e))["options"] for k, e in (("lock", lock), ("off", off), ("gate", gate))}
    extra = [x for x in o["gate"] if x not in o["lock"]]
    res["uci_off_equals_lock"] = o["off"] == o["lock"]
    res["uci_gate_is_lock_plus_switches"] = [x for x in o["gate"] if x in o["lock"]] == o["lock"] and extra == [
        "option name RazorTune type spin default 0 min 0 max 1", "option name QsTune type spin default 0 min 0 max 1"]
    res["uci_gate_extra_lines"] = extra
    # 2. bench pins
    exes = [("lock", lock, []), ("off", off, []), ("gate_sw0", gate, []),
            ("gate_sw1_defaults", gate, ["--opt", "RazorTune=1", "--opt", "QsTune=1"])]
    if ctl:
        exes.insert(1, ("ctl", ctl, []))
    bench = {}
    for name, exe, opts in exes:
        for nn, pins in (("on", PINS_ON), ("off", PINS_OFF)):
            b = save(out, f"bench_{name}_{nn}", drive("bench", exe, "--depths", "11,13,16,20,22", "--nnue", nn, *opts))
            nodes = b["sets"][0]["nodes"]
            bench[f"{name}_{nn}"] = {"nodes": nodes, "equals_pins": nodes == pins}
    res["bench"] = bench
    # 3. perft
    pf = {}
    for name, exe in (("lock", lock), ("off", off), ("gate", gate)):
        for pos, want in PERFT.items():
            r = save(out, f"perft_{name}_{pos}", drive("perft", exe, "--depth", "5", "--pos", pos))
            pf[f"{name}_{pos}"] = {"nodes": r["nodes"], "equals_pin": r["nodes"] == want}
    res["perft"] = pf
    # 4. gate semantics (bench d13/d16 in one engine process per sequence)
    seqs = {
        "razor_values_then_switch": "RazorBase=300,RazorMultiplier=250;RazorTune=1;RazorTune=0",
        "razor_switch_then_values": "RazorTune=1;RazorBase=300,RazorMultiplier=250;RazorTune=0",
        "qs_values_then_switch": "QsFutilityMargin=200,QsSeeMargin=140;QsTune=1;QsTune=0",
        "qs_switch_then_values": "QsTune=1;QsFutilityMargin=200,QsSeeMargin=140;QsTune=0",
        "both_families": "RazorBase=135,QsFutilityMargin=176;RazorTune=1,QsTune=1;RazorTune=0;QsTune=0",
    }
    sem = {}
    for name, seq in seqs.items():
        r = save(out, f"gate_seq_{name}", drive("bench", gate, "--depths", "13,16", "--opt-seq", seq))
        sem[name] = [s["nodes"] for s in r["sets"]]
    lockv = {
        "razor": save(out, "lock_razor_300_250", drive("bench", lock, "--depths", "13,16", "--opt", "RazorBase=300",
                                                         "--opt", "RazorMultiplier=250"))["sets"][0]["nodes"],
        "qs": save(out, "lock_qs_200_140", drive("bench", lock, "--depths", "13,16", "--opt", "QsFutilityMargin=200",
                                                   "--opt", "QsSeeMargin=140"))["sets"][0]["nodes"],
        "both": save(out, "lock_both_135_176", drive("bench", lock, "--depths", "13,16", "--opt", "RazorBase=135",
                                                       "--opt", "QsFutilityMargin=176"))["sets"][0]["nodes"],
        "qs176": save(out, "lock_qs_176", drive("bench", lock, "--depths", "13,16",
                                                 "--opt", "QsFutilityMargin=176"))["sets"][0]["nodes"],
    }
    pins2 = {"13": PINS_ON["13"], "16": PINS_ON["16"]}
    checks = {}
    for fam, a, b in (("razor", "razor_values_then_switch", "razor_switch_then_values"),
                      ("qs", "qs_values_then_switch", "qs_switch_then_values")):
        for nm in (a, b):
            s = sem[nm]
            if nm.endswith("values_then_switch"):
                checks[f"{nm}: values at switch 0 change nothing"] = s[0] == pins2
                checks[f"{nm}: switch 1 applies the values (== lock with the same values)"] = s[1] == lockv[fam] and s[1] != pins2
            else:
                checks[f"{nm}: switch 1 at defaults changes nothing"] = s[0] == pins2
                checks[f"{nm}: values while switch 1 apply (== lock with the same values)"] = s[1] == lockv[fam]
            checks[f"{nm}: switch 0 restores the pins"] = s[2] == pins2
    s = sem["both_families"]
    checks["both: values at switch 0 change nothing"] = s[0] == pins2
    checks["both: both switches 1 == lock with both values"] = s[1] == lockv["both"]
    checks["both: RazorTune 0 leaves only the qsearch value (== lock with QsFutilityMargin 176 only)"] = \
        s[2] == lockv["qs176"] and s[2] not in (lockv["both"], pins2)
    checks["both: QsTune 0 then restores the pins"] = s[3] == pins2
    res["gate_semantics"] = {"sequences": sem, "lock_with_values": lockv, "checks": checks}
    ok = res["uci_off_equals_lock"] and res["uci_gate_is_lock_plus_switches"] and \
        all(v["equals_pins"] for v in bench.values()) and all(v["equals_pin"] for v in pf.values()) and all(checks.values())
    res["all_pass"] = ok
    save(out, "summary", res)
    print(json.dumps({"all_pass": ok, "uci_off_equals_lock": res["uci_off_equals_lock"],
                      "uci_gate_extra": extra, "bench_all_pins": all(v["equals_pins"] for v in bench.values()),
                      "perft_all_pins": all(v["equals_pin"] for v in pf.values()),
                      "gate_checks_failed": [k for k, v in checks.items() if not v]}, indent=1))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
