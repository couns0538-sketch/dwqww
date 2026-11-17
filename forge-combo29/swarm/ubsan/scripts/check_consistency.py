#!/usr/bin/env python3
"""Check the numbers stated in FINDINGS.md / STATUS.md against evidence/.

A prose count beside a computed table is a stale claim waiting for its next
regeneration (trap from seat 67's report). This parses the stated numbers and
compares them with the evidence JSON, failing on any mismatch.

Verified able to fail: plant a wrong total in the report and this exits 1.
"""
import json
import re
import sys

ROOT = "/agent/repos/dwqww/forge-combo29/swarm/ubsan"


def load(name):
    return json.load(open(f"{ROOT}/evidence/{name}.json"))


def main():
    findings = open(f"{ROOT}/FINDINGS.md").read()
    status = open(f"{ROOT}/STATUS.md").read()
    # Prose wraps mid-phrase, so compare on a whitespace-normalised copy.
    findings_flat = re.sub(r"\s+", " ", findings)
    status_flat = re.sub(r"\s+", " ", status)
    wl = load("workload-summary")
    pf = load("planted-faults")
    sy = load("symbols")
    fa = load("float-arm-summary")
    fc = load("float-check-gating")
    ec = load("exit-drain-contrast")
    prov = load("provenance")

    checks = []

    def chk(name, ok, detail=""):
        checks.append({"check": name, "ok": bool(ok), "detail": detail})

    t = wl["totals"]

    # Presence is not consistency: a document can state the right total in one
    # place and a wrong one in another. So every "N,NNN probes" mention of the
    # SWEEP is checked, and the number is required to be the evidence value.
    # The widened float arm legitimately reports its own, smaller total, so
    # sentences containing "arm" or "float"/"widened" are excluded rather than
    # silently tolerated.
    def sweep_totals(text):
        vals = set()
        for m in re.finditer(r"([0-9][0-9,]{2,})\s+(?:bounded\s+)?probes", text):
            ctx = text[max(0, m.start() - 160):m.end() + 160].lower()
            if "arm" in ctx or "widened" in ctx or "float" in ctx:
                continue
            vals.add(int(m.group(1).replace(",", "")))
        return sorted(vals)

    vals = sorted(set(sweep_totals(findings_flat)) | set(sweep_totals(status_flat)))
    chk("every stated sweep probe total equals evidence",
        vals == [t["probes"]], f"stated {vals} vs evidence {t['probes']}")
    chk("total probes is 2408", t["probes"] == 2408, f"{t['probes']}")
    chk("sanitizer lines zero and stated", t["sanitizer_lines"] == 0 and "0 UBSan reports" in findings_flat,
        f"{t['sanitizer_lines']}")
    chk("at-exit lines zero", t["at_exit_sanitizer_lines"] == 0, f"{t['at_exit_sanitizer_lines']}")
    chk("no dead probes", t["dead_probes"] == 0, f"{t['dead_probes']}")
    chk("12 phases", t["phases"] == 12, f"{t['phases']}")

    depth = wl["phases"]["depth"]
    chk("depth phase probes = 1446", depth["probes"] == 1446, f"{depth['probes']}")
    chk("depth phase 720 searches stated", "720/720" in findings_flat, "")
    chk("all phases non-vacuous", wl["non_vacuity"]["_all_phases_non_vacuous"] is True,
        str(wl["non_vacuity"].get("_all_phases_non_vacuous")))
    for ph, v in wl["phases"].items():
        chk(f"phase {ph} non-vacuous", v["non_vacuous"] is True, str(v["non_vacuous"]))
        chk(f"phase {ph} drained to eof", v["drained_to_eof"] is True, str(v["drained_to_eof"]))

    caught = [p for p in pf["plants"] if p["caught"] == "YES"]
    chk("12 plants, all caught", len(pf["plants"]) == 12 and len(caught) == 12,
        f"{len(caught)}/{len(pf['plants'])}")
    chk("12/12 stated in findings", "12 of 12 caught" in findings_flat, "")
    chk("control not caught", pf["control"]["caught"] == "NO", pf["control"]["caught"])

    chk("ubsan symbols 15 vs 0", sy["ubsan_asan_build"]["__ubsan_"] == 15
        and sy["baseline_build"]["__ubsan_"] == 0,
        f"{sy['ubsan_asan_build']['__ubsan_']}/{sy['baseline_build']['__ubsan_']}")
    chk("asan symbols 35 vs 0", sy["ubsan_asan_build"]["__asan_"] == 35
        and sy["baseline_build"]["__asan_"] == 0,
        f"{sy['ubsan_asan_build']['__asan_']}/{sy['baseline_build']['__asan_']}")

    chk("float arm sanitizer lines 0", fa["totals"]["sanitizer_lines"] == 0,
        str(fa["totals"]["sanitizer_lines"]))
    chk("float arm probe count stated", f"{fa['totals']['probes']:,}" in findings_flat,
        str(fa["totals"]["probes"]))
    chk("plain undefined caught 0", fc["plain_undefined"]["sanitizer_lines"] == 0,
        str(fc["plain_undefined"]["sanitizer_lines"]))
    chk("named float caught 10", fc["named_float_checks"]["sanitizer_lines"] == 10,
        str(fc["named_float_checks"]["sanitizer_lines"]))

    arms = {a["harness"]: a for a in ec["arms"]}
    chk("bestmove-kill arm CLEAN", arms["bestmove-then-kill"]["verdict"] == "CLEAN",
        arms["bestmove-then-kill"]["verdict"])
    chk("drain arm REPORT", arms["drain-to-eof"]["verdict"] == "REPORT",
        arms["drain-to-eof"]["verdict"])
    chk("drain arm exit code 1", arms["drain-to-eof"]["exit_code"] == 1,
        str(arms["drain-to-eof"]["exit_code"]))

    # sha256 values quoted in both documents must match provenance
    for label, meta in prov["binaries"].items():
        short = meta["sha256"]
        chk(f"sha256 {label} quoted in findings", short in findings_flat, short[:16] + "...")
        chk(f"sha256 {label} quoted in status", short in status_flat, short[:16] + "...")

    chk("flag string quoted verbatim in findings",
        prov["sanitizer_flags"] in findings_flat, prov["sanitizer_flags"])
    chk("flag string quoted verbatim in status",
        prov["sanitizer_flags"] in status_flat, prov["sanitizer_flags"])
    chk("UBSAN_OPTIONS quoted in findings", prov["UBSAN_OPTIONS"] in findings_flat, "")
    chk("UBSAN_OPTIONS quoted in status", prov["UBSAN_OPTIONS"] in status_flat, "")

    pins = wl["non_vacuity"]["pins"]["values"]
    for k, want in (("bench 11 neton", 312866), ("bench 13 neton", 862329),
                    ("bench 16 neton", 3024920)):
        chk(f"pin {k}", pins.get(k) == want, f"{pins.get(k)}")
    chk("perft5 pin", wl["non_vacuity"]["perft"]["perft5"] == 4865609,
        str(wl["non_vacuity"]["perft"]["perft5"]))
    chk("no refused fixtures in perft", wl["non_vacuity"]["perft"].get("refused_fixtures") == 0,
        str(wl["non_vacuity"]["perft"].get("refused_fixtures")))

    failed = [c for c in checks if not c["ok"]]
    print(json.dumps({"checks": len(checks), "failed": len(failed),
                      "failures": failed}, indent=1))
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
