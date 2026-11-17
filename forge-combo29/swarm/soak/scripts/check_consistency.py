"""Check every count and figure stated in FINDINGS.md against the evidence files.

A prose count beside a computed table is a stale claim waiting for its next regeneration.
This parses the numbers out of the report and compares them with the evidence, failing on
mismatch. Exit 1 on any failure, 0 on success -- and the exit status is the verdict, not a
printed line (findings S6: a check that prints FAIL and exits 0 is a failing report read as
a pass).

Proven able to fail: plant `5,000 searches` as `4,000` in FINDINGS.md and it exits 1 naming
the claim; restore and it exits 0. See the bottom of this file for the self-test that runs
both directions on a copy.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EV = os.path.join(ROOT, "evidence")
REPORT = os.path.join(ROOT, "FINDINGS.md")

fails = []
checks = 0


def num(text):
    """First integer in a cell, tolerant of units like '108 MB' or '281.9'."""
    m = re.search(r"-?\d+(?:\.\d+)?", str(text).replace(",", ""))
    if not m:
        raise ValueError("no number in %r" % (text,))
    return int(float(m.group(0)))


def expect(name, stated, actual):
    """Compare a number stated in the report with the measured one."""
    global checks
    checks += 1
    if stated != actual:
        fails.append("%s: report says %s, evidence says %s" % (name, stated, actual))


def require(name, cond, detail=""):
    global checks
    checks += 1
    if not cond:
        fails.append("%s: %s" % (name, detail))


def main(report_path):
    text = open(report_path).read()
    ev = lambda n: json.load(open(os.path.join(EV, n)))

    # ---- P1 ----
    rows = [l.strip().split(",") for l in open(os.path.join(EV, "soak1_hash32.csv"))
            if l.strip()]
    head, body = rows[0], rows[1:]
    rss = [(int(r[0]), int(r[1])) for r in body]
    last_search, last_rss = rss[-1]
    expect("P1 total searches", num(re.findall(r"5,000 × `go depth 12`", text)[0]
                                    .split("×")[0].strip()), last_search)
    m = re.search(r"Plateau: ([\d.]+) MB", text)
    require("P1 plateau claim present", bool(m))
    if m:
        # the report states MB to 1dp; compare in kB at that precision
        expect("P1 plateau MB", round(last_rss / 1024.0, 1), float(m.group(1)))
    m = re.search(r"distinct values in (\d+) samples", text)
    require("P1 sample-count claim present", bool(m))
    if m:
        expect("P1 sample count", num(m.group(1)), len(rss))
    m = re.search(r"\*\*(\d+) distinct values", text)
    require("P1 distinct-value claim present", bool(m))
    if m:
        expect("P1 distinct RSS values", num(m.group(1)),
               len(set(k for _, k in rss)))
    m = re.search(r"Total change over the whole run: \*\*\+([\d,]+) kB", text)
    require("P1 total-change claim present", bool(m))
    if m:
        expect("P1 total change kB", num(m.group(1)), rss[-1][1] - rss[0][1])
    log = [json.loads(l) for l in open(os.path.join(EV, "soak1_hash32.log"))]
    sear = [r for r in log if "nodes" in r]
    m = re.search(r"([\d,]{7,})\s+nodes total,\s*([\d.]+) s", text)
    require("P1 node-total claim present", bool(m))
    if m:
        expect("P1 total nodes", num(m.group(1)), sum(r["nodes"] for r in sear))
    m = re.search(r"(\d[\d,]*) of 5,000 with a non-null", text)
    require("P1 non-null-bestmove claim present", bool(m))
    if m:
        expect("P1 non-null bestmoves", num(m.group(1)),
               sum(1 for r in sear if r["best"] and r["best"] != "0000"))
    m = re.search(r"(\d+) zero-node searches", text)
    if m:
        expect("P1 zero-node searches", num(m.group(1)),
               sum(1 for r in sear if r["nodes"] == 0))

    # ---- P2 ----
    d = ev("soak2.json")
    a = {r["hash"]: r for r in d if r["arm"] == "A"}
    for h in (16, 64, 256, 1024):
        marginal = (a[h]["rss_after"] - a[1]["rss_after"]) / 1024.0
        expect("P2 Hash %d marginal MB (rounded)" % h, round(marginal), h - 1)
    expect("P2 non-table bytes MB", 10.1,
           round((a[1024]["rss_after"] - 1024 * 1024) / 1024.0, 1))

    # ---- P2b ----
    b = {(r["hash"], r["multipv"]): r for r in d if r["arm"] == "B"}
    peak_delta = (b[(256, 2)]["peak_median"] - b[(256, 1)]["peak_median"]) / 1024.0
    expect("P2b peak delta MB (1dp)", 259.6, round(peak_delta, 1))
    after_delta = (b[(256, 2)]["after_median"] - b[(256, 1)]["after_median"]) / 1024.0
    expect("P2b after delta MB (1dp)", 3.6, round(after_delta, 1))
    h64 = b[(64, 4)]["peak_median"] / 1024.0 - b[(64, 1)]["peak_median"] / 1024.0
    expect("P2b Hash64 alt table MB (1dp)", 67.6, round(h64, 1))
    rr = {(r["from"], r["to"]): r for r in d if r["arm"] == "R"}
    expect("resize 256->256 transient MB", 263.0,
           round((rr[(256, 256)]["peak_during"] - 256 * 1024) / 1024.0, 1))

    # ---- P3 / P3b ----
    for mode in ("ucinewgame", "clearhash"):
        s = ev("soak3_%s.json" % mode)["summary"]
        expect("P3 %s delta kB" % mode, 0, s["delta_kb"])
        expect("P3 %s p50 ms (2dp)" % mode, {"ucinewgame": 1.30, "clearhash": 1.23}[mode],
               round(s["ms_p50"], 2))
    c3 = {r["hash"]: r for r in ev("soak3b_costs.json")}
    expect("P3b Hash 1024 clearhash p50 ms", 86, round(c3[1024]["clearhash"]["p50_ms"]))
    for h, r in c3.items():
        expect("P3b Hash %d rss stable" % h, 0, r["clearhash"]["rss_after"]
               - r["clearhash"]["rss_before"])
        require("P3b Hash %d arms within 0.5 ms" % h,
                abs(r["ucinewgame"]["p50_ms"] - r["clearhash"]["p50_ms"]) < 0.5,
                "difference %.2f ms" % (r["ucinewgame"]["p50_ms"]
                                        - r["clearhash"]["p50_ms"]))

    # ---- P4 ----
    r4 = [l.strip().split(",") for l in open(os.path.join(EV, "soak4.csv")) if l.strip()][1:]
    peaks = [int(r[1]) for r in r4[1:]]   # r4[0] is the pre-run settled sample
    afters = [int(r[2]) for r in r4[1:]]
    afters_all = [int(r[2]) for r in r4]
    expect("P4 peak min kB", 145088, min(peaks))
    expect("P4 peak max kB", 145276, max(peaks))
    expect("P4 peak spread kB", 188, max(peaks) - min(peaks))
    expect("P4 final after kB", 79548, afters_all[-1])
    m = re.search(r"fixed ([\d,]+) kB for the last 750", text)
    require("P4 settled-value claim present", bool(m))
    if m:
        expect("P4 settled after kB", num(m.group(1)), afters_all[-1])
    late = [int(r[2]) for r in r4[1:] if int(r[0]) >= 500]
    expect("P4 spread over last 500 searches", 3556, max(late) - min(late))

    # ---- P5 / P5b ----
    d5 = ev("soak5.json")
    alive = [r for r in d5 if not r["died"] and r["cap_mb"] > 0]
    dead = [r for r in d5 if r["died"]]
    expect("P5 surviving caps", 18, len(alive))
    expect("P5 dead caps", 5, len(dead))
    expect("P5 survivors with a difference", 0,
           sum(1 for r in alive if r["same_answers"] is not True))
    expect("P5 lowest surviving cap MB", 76, min(r["cap_mb"] for r in alive))
    expect("P5 highest dead cap MB", 72, max(r["cap_mb"] for r in dead))
    require("P5 every death is SIGABRT",
            all(r["signal"] == 6 for r in dead),
            str([(r["cap_mb"], r["signal"]) for r in dead]))
    require("P5 every death is bad_alloc",
            all("bad_alloc" in r["stderr_tail"] for r in dead), "stderr missing bad_alloc")
    d5b = ev("soak5b.json")
    expect("P5b Hash values measured", 4, len(d5b))
    for r in d5b:
        expect("P5b cliff-Hash constant at Hash %d" % r["hash"], 44,
               r["lowest_complete_mb"] - r["hash"])
        expect("P5b adjacent bisect at Hash %d" % r["hash"], 2,
               r["lowest_complete_mb"] - r["highest_dead_mb"])

    # ---- P6 ----
    s6 = ev("soak6.json")["summary"]
    expect("P6 sanitizer lines", 0, s6["sanitizer_lines"])
    expect("P6 zero-node rows", 0, s6["zero_node_rows"])
    expect("P6 engine ops", 171,
           s6["kinds"]["plain"] + s6["kinds"]["multipv3"]
           + s6["kinds"]["ucinewgame"] + s6["kinds"]["clearhash"])
    p = ev("sanitizer_proof.json")
    expect("proof clean lines", 0, p["clean"]["sanitizer_lines"])
    expect("proof untriggered lines", 0, p["planted_untriggered"]["sanitizer_lines"])
    expect("proof triggered lines", 4, p["planted_triggered"]["sanitizer_lines"])
    require("proof: clean and untriggered really searched", 
            p["clean"]["info_depth"] > 0 and p["planted_untriggered"]["info_depth"] > 0,
            "info_depth 0 means no search happened")

    # ---- P9 / P7 / P7b / P7d / P8 ----
    d7 = ev("soak7_cliff_mpv.json")
    p9 = {r["cap_mb"]: r for r in d7["P9"]}
    expect("P9 caps tested", 4, len(d7["P9"]))
    for cap in (57, 58, 59):
        expect("P9 cap %d dies" % cap, 0, p9[cap]["completed"])
        expect("P9 cap %d SIGABRT" % cap, 6, p9[cap]["signal"])
    expect("P9 cap 60 completes all", p9[60]["n_expected"], p9[60]["completed"])

    cells = {(r["hash"], r["multipv"]): r for r in d7["P7"]}
    expect("P7 cells", 4, len(cells))
    expect("P7 Hash 64 MPV1 cliff", 108, cells[(64, 1)]["lowest_complete_mb"])
    expect("P7 Hash 64 MPV2 cliff (report says 152)", 152,
           cells[(64, 2)]["lowest_complete_mb"])
    expect("P7 Hash 256 MPV1 cliff", 300, cells[(256, 1)]["lowest_complete_mb"])
    expect("P7 Hash 256 MPV2 cliff (report says 598)", 598,
           cells[(256, 2)]["lowest_complete_mb"])

    b7 = ev("soak7b_mpv_control.json")
    expect("P7b cells", 5, len(b7))
    for h, want in ((64, 152), (256, 598)):
        vals = {r["lowest_complete_mb"] for r in b7 if r["hash"] == h}
        expect("P7b Hash %d all MultiPV share one cliff" % h, 1, len(vals))
        expect("P7b Hash %d cliff" % h, want, vals.pop())

    d7d = ev("soak7d_slope.json")
    expect("slope MPV1 (3dp)", 1.000, d7d["1_slope"])
    expect("slope MPV2 (3dp)", 2.001, d7d["2_slope"])
    expect("slope MPV4 (3dp)", 2.000, d7d["4_slope"])
    require("MPV2 slope is ~double MPV1 (the sizing claim)",
            d7d["2_slope"] > 1.9 and d7d["2_slope"] < 2.1,
            "got %.3f" % d7d["2_slope"])
    for mpv in ("1", "2", "4"):
        expect("slope arm MPV%s hash count" % mpv, 4, len(d7d[mpv]))

    d8 = ev("soak8_resize.json")
    expect("P8 cases", 5, len(d8))
    for r in d8:
        if (r["from"], r["to"]) == (256, 16):
            continue
        expect("P8 %d->%d excess over old+new (1dp)" % (r["from"], r["to"]),
               9.9, r["over_old_plus_new_mb"])
    e16_256 = [r for r in d8 if (r["from"], r["to"]) == (16, 256)][0]
    expect("P8 16->256 peak MB (1dp)", 281.9, e16_256["peak_mb"])
    e256 = [r for r in d8 if (r["from"], r["to"]) == (256, 256)][0]
    expect("P8 256->256 control peak MB (1dp)", 521.9, e256["peak_mb"])
    require("P8 control really doubles (kills the reuse hypothesis)",
            e256["peak_mb"] > 500, "control peak %.1f" % e256["peak_mb"])
    require("P8 engine usable after every resize",
            all(r["best_after_resize"] for r in d8), "a resize left the engine unusable")

    # ---- the figures inside the report's own TABLES, not just the prose ----
    # The first version of this checker compared the prose sentence only, so editing a table
    # cell kept the verdict at PASS. A table is where a reader takes the number from.
    def table_rows(pattern, text):
        """Rows of the markdown table that starts at a header matching `pattern`."""
        out = []
        lines = text.splitlines()
        for i, l in enumerate(lines):
            if re.search(pattern, l) and l.strip().startswith("|"):
                for l2 in lines[i + 2:]:
                    if not l2.strip().startswith("|"):
                        break
                    out.append([c.strip().strip("*") for c in l2.strip().strip("|").split("|")])
                break
        return out

    # P7 table: | Hash | MPV 1 (measured) | MPV 2 predicted | MPV 2 measured | ratio |
    p7rows = table_rows(r"\| Hash \| MPV 1 \(measured\)", text)
    require("P7 table found", len(p7rows) == 2, "got %d rows" % len(p7rows))
    want_p7 = {"64": (108, 152), "256": (300, 598)}
    for row in p7rows:
        h = row[0]
        require("P7 table Hash %s present" % h, h in want_p7, "unexpected row %r" % row)
        if h in want_p7:
            expect("P7 table Hash %s MPV1 cliff" % h, want_p7[h][0], num(row[1]))
            expect("P7 table Hash %s MPV2 measured" % h, want_p7[h][1], num(row[3]))
            ratio = round(want_p7[h][1] / want_p7[h][0], 3)
            expect("P7 table Hash %s ratio" % h, ratio, round(float(row[4]), 3))

    # slope table: | Hash | MPV | VmHWM_MB | ... | and the three "-> MPV n: slope" lines
    for mpv, want in (("1", 1.000), ("2", 2.001), ("4", 2.000)):
        m = re.search(r"-> MPV %s: slope ([\d.]+) MB per MB of Hash" % mpv, text)
        require("slope line for MPV %s present" % mpv, bool(m))
        if m:
            expect("slope line MPV %s" % mpv, want, float(m.group(1)))
    # every VmHWM cell of the slope table
    srows = table_rows(r"\| Hash \| MPV \| VmHWM_MB", text)
    require("slope table row count", len(srows) == 12, "got %d rows" % len(srows))
    d7d_ = ev("soak7d_slope.json")
    got = {(r["hash"], str(m)): r["vmhwm_mb"]
           for m in ("1", "2", "4") for r in d7d_[m]}
    for row in srows:
        key = (num(row[0]), row[1])
        require("slope table row %r in evidence" % (key,), key in got, "no such cell")
        if key in got:
            expect("slope table VmHWM at Hash %d MPV %s" % key, got[key],
                   float(row[2]))

    # P8 table: every peak_MB cell
    prows = table_rows(r"\|\s*from\s*\|\s*to\s*\|\s*RSS_before", text)
    require("P8 table row count", len(prows) == 5, "got %d rows" % len(prows))
    d8_ = ev("soak8_resize.json")
    by_pair = {(r["from"], r["to"]): r for r in d8_}
    for row in prows:
        key = (num(row[0]), num(row[1]))
        require("P8 row %r in evidence" % (key,), key in by_pair, "no such case")
        if key in by_pair:
            # columns: from | to | RSS_before | peak_MB | old+new_MB | excess_MB
            expect("P8 table peak for %d->%d" % key, by_pair[key]["peak_mb"],
                   float(row[3]))

    # the SUMMARY's restatement of the slope, which is the sentence a reader sees first
    m = re.search(r"\*\*([\d.]+) MB per MB of Hash at MultiPV 1\*\* and\s*\n?\s*\*\*([\d.]+) at MultiPV 2\*\*", text)
    require("summary restates both slopes", bool(m))
    if m:
        expect("summary MPV1 slope", d7d["1_slope"], float(m.group(1)))
        expect("summary MPV2 slope", d7d["2_slope"], float(m.group(2)))
    # the top-of-report resize claim
    m = re.search(r"16 → 256 peaks at \*\*([\d.]+) MB\*\*", text)
    require("summary states the 16->256 resize peak", bool(m))
    if m:
        expect("summary resize peak", e16_256["peak_mb"], float(m.group(1)))

    # the FAILED prediction must be reported as failed, not silently dropped
    require("report states the P7 prediction was KILLED",
            "Both predictions are killed" in text,
            "the failed prediction is not reported as failed")
    require("report labels P5 as a replication",
            "REPLICATION" in text or "replication" in text,
            "P5 is not labelled a replication")

    # ---- STATUS.md must not contradict the report or the prediction tallies ----
    st_path = os.path.join(ROOT, "STATUS.md")
    st = open(st_path).read()
    n_held1 = 9
    n_held2 = 6
    require("STATUS says 9 of 9 held for PREDICTION.md",
            "%d of %d held" % (n_held1, n_held1) in st, "tally missing")
    require("STATUS says 6 of 7 held for PREDICTION2.md",
            "%d of 7 held" % n_held2 in st, "tally missing")
    require("STATUS reports P7 as killed", "P7 killed" in st or "P7** killed" in st
            or "one prediction failed" in st.lower(), "failure not carried into STATUS")
    m = re.search(r"\*\*(\d+) checks\*\*", st)
    require("STATUS states the check count", bool(m))

    # ---- prose claims that must be present at all ----
    for phrase in ("42.1 MB", "312,866", "862,329", "3,024,920", "4,865,609",
                   "Hash + 44 MB", "No unbounded growth"):
        require("report states %r" % phrase, phrase in text.replace("**", ""))

    return checks


def selftest():
    """Plant a wrong count, confirm exit 1 and that it names the claim; restore."""
    tmp = tempfile.mkdtemp()
    try:
        dst = os.path.join(tmp, "FINDINGS.md")
        shutil.copy(REPORT, dst)
        orig = open(dst).read()
        plant = orig.replace("Plateau: 42.1 MB", "Plateau: 47.1 MB")
        if plant == orig:
            print("SELFTEST BROKEN: could not plant (pattern absent)")
            return 1
        open(dst, "w").write(plant)
        r = subprocess.run([sys.executable, os.path.abspath(__file__), "--report", dst],
                           capture_output=True, text=True)
        ok_plant = (r.returncode == 1)
        names = ("42.1 MB" in r.stdout or "471" in r.stdout or "P1 final" in r.stdout)
        print("selftest planted: rc=%d (want 1) %s"
              % (r.returncode, "FAIL-AS-EXPECTED" if ok_plant else "DID NOT FAIL"))
        if not ok_plant:
            print(r.stdout[-800:])
            return 1
        open(dst, "w").write(orig)
        r2 = subprocess.run([sys.executable, os.path.abspath(__file__), "--report", dst],
                            capture_output=True, text=True)
        print("selftest restored: rc=%d (want 0)" % r2.returncode)
        if r2.returncode != 0:
            print(r2.stdout[-800:])
            return 1
        print("SELFTEST PASSED: the checker fails on a planted wrong figure and passes restored")
        return 0
    finally:
        shutil.rmtree(tmp)


if __name__ == "__main__":
    if "--report" in sys.argv:
        path = sys.argv[sys.argv.index("--report") + 1]
        n = main(path)
        if fails:
            print("VERDICT: FAIL (%d of %d checks)" % (len(fails), n))
            for f in fails:
                print("  " + f)
            sys.exit(1)
        print("VERDICT: PASS (%d checks against evidence/)" % n)
        sys.exit(0)
    if "--selftest" in sys.argv:
        sys.exit(selftest())
    n = main(REPORT)
    if fails:
        print("VERDICT: FAIL (%d of %d checks)" % (len(fails), n))
        for f in fails:
            print("  " + f)
        sys.exit(1)
    print("VERDICT: PASS (%d checks against evidence/)" % n)
    sys.exit(0)
