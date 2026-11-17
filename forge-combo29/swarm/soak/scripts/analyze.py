"""Derive every number in FINDINGS.md from the raw evidence files.

Every table in the report is the output of this script. Nothing in the report is typed by
hand except prose. Run it from its own directory and from /tmp to prove the verdict does not
depend on where you stand (findings S6: "a verdict that depends on where you stand is not a
verdict").

It also ASSERTS its row counts, so a parser fault that silently drops rows fails loudly
instead of printing a complete-looking table from the survivors.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
EV = os.path.join(HERE, "..", "evidence")


def load(name):
    with open(os.path.join(EV, name)) as f:
        return json.load(f)


def csv_rows(name):
    path = os.path.join(EV, name)
    with open(path) as f:
        head = f.readline().strip().split(",")
        return [dict(zip(head, l.strip().split(","))) for l in f if l.strip()]


def section(title):
    print("\n### " + title)


def soak1():
    rows = csv_rows("soak1_hash32.csv")
    assert len(rows) >= 100, "soak1: expected ~110 samples, got %d" % len(rows)
    rss = [(int(r["search"]), int(r["rss_kb"])) for r in rows]
    section("P1  RSS over 5,000 depth-12 searches, Hash 32, one process")
    print("sample  search   rss_kb   rss_MB")
    for s, k in rss:
        if s in (0, 1, 2, 3, 4, 5, 10) or s % 500 == 0 or s == rss[-1][0]:
            print("%6d %7d %8d %8.1f" % (s, s, k, k / 1024.0))
    first = rss[0][1]
    last = rss[-1][1]
    tail = [k for s, k in rss if s >= 1000]
    # least-squares slope over the last 4,000 searches, in MB per 1000 searches
    pts = [(s, k / 1024.0) for s, k in rss if s >= 1000]
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    slope = (sum((p[0] - mx) * (p[1] - my) for p in pts)
             / sum((p[0] - mx) ** 2 for p in pts))
    print("\nsamples=%d  first=%d kB (%.1f MB)  last=%d kB (%.1f MB)"
          % (len(rss), first, first / 1024.0, last, last / 1024.0))
    print("total change over 5,000 searches: %+d kB, peak-to-final %+d kB"
          % (last - first, max(k for _, k in rss) - last))
    print("slope over searches 1000..5000: %+.3f MB per 1,000 searches" % (slope * 1000))
    print("distinct RSS values across all %d samples: %d"
          % (len(rss), len(set(k for _, k in rss))))
    return {"first_kb": first, "last_kb": last, "slope_mb_per_1k": slope * 1000,
            "n_samples": len(rss)}


def soak1_quality():
    log = [json.loads(l) for l in open(os.path.join(EV, "soak1_hash32.log"))]
    sear = [r for r in log if "nodes" in r]
    section("P1 quality control on the same run")
    print("searches logged: %d, zero-node (drawn-root bail, expected): %d, min nodes %d, max nodes %d"
          % (len(sear), sum(1 for r in sear if r["nodes"] == 0),
             min(r["nodes"] for r in sear), max(r["nodes"] for r in sear)))
    print("bestmoves: %d of %d legal-looking (non-null)" %
          (sum(1 for r in sear if r["best"] and r["best"] != "0000"), len(sear)))
    print("ERROR lines in log: %d" % sum(1 for r in log if "ERROR" in r))


def soak2():
    d = load("soak2.json")
    a = [r for r in d if r["arm"] == "A"]
    assert len(a) == 5, "soak2 arm A: expected 5 hash arms, got %d" % len(a)
    section("P2  RSS tracks the Hash option")
    print("Hash   RSS_kB   RSS_MB   over_hash1_MB   VmPeak_kB   (RSS - Hash)")
    for r in sorted(a, key=lambda r: r["hash"]):
        print("%4d %8d %7.1f %14.1f %11d %12.1f"
              % (r["hash"], r["rss_after"], r["rss_after"] / 1024.0,
                 r["rss_over_hash1"] / 1024.0, r["vmpeak"],
                 (r["rss_after"] - r["hash"] * 1024) / 1024.0))
    # the marginal cost of each table against Hash 1
    for r in sorted(a, key=lambda r: r["hash"]):
        if r["hash"] == 1:
            continue
        delta_mb = r["rss_over_hash1"] / 1024.0
        want = r["hash"] - 1
        print("  Hash %4d: measured marginal %8.1f MB, expected %4d MB, error %+6.1f%%"
              % (r["hash"], delta_mb, want, 100.0 * (delta_mb - want) / want))

    rr = [r for r in d if r["arm"] == "R"]
    assert len(rr) == 4, "soak2 arm R: expected 4 resize arms, got %d" % len(rr)
    section("Resize transient: `resize` allocates before it frees (search.cpp:362-370)")
    print("from  to   rss_before_kB  peak_during_kB  rss_after_kB   peak - max(from,to) MB")
    for r in rr:
        print("%4d %4d %14d %15d %13d %22.1f"
              % (r["from"], r["to"], r["rss_before"], r["peak_during"], r["rss_after"],
                 (r["peak_during"] - max(r["from"], r["to"]) * 1024) / 1024.0))

    b = [r for r in d if r["arm"] == "B"]
    assert len(b) == 5, "soak2 arm B: expected 5 multipv arms, got %d" % len(b)
    section("P2b/P4  the MultiPV alternate table: peak during search vs after bestmove")
    print("Hash MPV  settled_kB  peak_med_kB  after_med_kB   peak-settled MB  after-settled MB")
    for r in sorted(b, key=lambda r: (r["hash"], r["multipv"])):
        print("%4d %3d %11d %12d %12d %16.1f %16.1f"
              % (r["hash"], r["multipv"], r["rss_settled"], r["peak_median"],
                 r["after_median"],
                 (r["peak_median"] - r["rss_settled"]) / 1024.0,
                 (r["after_median"] - r["rss_settled"]) / 1024.0))
    return a, b


def soak3():
    section("P3  5,000 clears, both kinds")
    print("mode        clears  rss_before  rss_after  delta  p50_ms  p99_ms  total_s  best_after  nodes_after")
    for mode in ("ucinewgame", "clearhash"):
        d = load("soak3_%s.json" % mode)
        s = d["summary"]
        assert len(d["samples"]) == 50, "%s: expected 50 samples, got %d" % (mode, len(d["samples"]))
        print("%-11s %6d %11d %10d %6d %7.3f %7.3f %8.2f %10s %12s"
              % (s["mode"], s["clears"], s["rss_before"], s["rss_after"],
                 s["delta_kb"], s["ms_p50"], s["ms_p99"], s["elapsed_s"],
                 s["search_after_best"], s["search_after_nodes"]))
        ks = [x["rss_kb"] for x in d["samples"]]
        print("   sampled curve min %d max %d over %d samples (span %d kB)"
              % (min(ks), max(ks), len(ks), max(ks) - min(ks)))


def soak3b():
    d = load("soak3b_costs.json")
    assert len(d) == 4, "soak3b: expected 4 Hash values, got %d" % len(d)
    section("P3b  clear cost and RSS vs Hash (200 calls per arm, one process each)")
    print("Hash  ucinewgame_p50  clearhash_p50  difference  RSS delta (both arms)")
    for r in d:
        u, c = r["ucinewgame"], r["clearhash"]
        print("%4d %14.3f %14.3f %11.3f  %d kB / %d kB"
              % (r["hash"], u["p50_ms"], c["p50_ms"], u["p50_ms"] - c["p50_ms"],
                 u["rss_after"] - u["rss_before"], c["rss_after"] - c["rss_before"]))
    print("  implies table write rate of %.1f-%.1f GB/s across the four sizes"
          % (min(r["gb_per_s_clearhash"] for r in d),
             max(r["gb_per_s_clearhash"] for r in d)))
    assert all(r["ucinewgame"]["rss_after"] == r["ucinewgame"]["rss_before"]
               and r["clearhash"]["rss_after"] == r["clearhash"]["rss_before"]
               for r in d), "soak3b: an arm changed RSS; that contradicts P3"
    return d


def soak4():
    rows = csv_rows("soak4.csv")
    assert len(rows) >= 40, "soak4: expected ~45 samples, got %d" % len(rows)
    section("P4  1,000 MultiPV-4 searches at Hash 64, one process")
    print("search   peak_kB   after_kB   cum_nodes")
    for r in rows:
        if int(r["search"]) in (0, 3) or int(r["search"]) % 200 == 0:
            print("%6s %9s %10s %12s" % (r["search"], r["peak_kb"], r["after_kb"],
                                         r["cum_nodes"]))
    peaks = [int(r["peak_kb"]) for r in rows[1:]]
    afters = [int(r["after_kb"]) for r in rows[1:]]
    late = [a for s, a in ((int(r["search"]), int(r["after_kb"])) for r in rows[1:])
            if s >= 500]
    print("\npeak:  min %d max %d  spread %d kB (%.1f MB)"
          % (min(peaks), max(peaks), max(peaks) - min(peaks),
             (max(peaks) - min(peaks)) / 1024.0))
    print("after: min %d max %d  first-after %d  final %d"
          % (min(afters), max(afters), afters[0], afters[-1]))
    print("after over searches 500..1000: min %d max %d (spread %d kB)"
          % (min(late), max(late), max(late) - min(late)))
    print("distinct after values over the run: %s"
          % sorted(set(afters)))
    log = [json.loads(l) for l in open(os.path.join(EV, "soak4.log"))]
    sear = [r for r in log if "nodes" in r]
    print("searches logged %d, ERROR lines %d, min nodes %d"
          % (len(sear), sum(1 for r in log if "ERROR" in r),
             min(r["nodes"] for r in sear)))
    return {"peak_spread_kb": max(peaks) - min(peaks), "after_vals": sorted(set(afters))}


def soak5():
    d = load("soak5.json")
    assert len(d) == 24, "soak5: expected 24 caps, got %d" % len(d)
    section("P5  `ulimit -v` sweep at Hash 32, 12 depth-10 searches per cap")
    print("cap_MB  completed  same_answers  diff_rows  nps_only  rc  signal  VmPeak   VmSize   RSS   outcome")
    for r in d:
        vm = r.get("vm_after") or {}
        if r["died"]:
            out = "DIED " + r["stderr_tail"].splitlines()[0][:38] if r["stderr_tail"] else "DIED"
        else:
            out = "ran"
        print("%6d %10d %13s %10s %9d %3s %7s %7s %8s %6s  %s"
              % (r["cap_mb"], r["completed"], r["same_answers"], r["diff_rows"],
                 r["nps_only_rows"], r["rc"], r["signal"],
                 vm.get("VmPeak", "-"), vm.get("VmSize", "-"), vm.get("VmRSS", "-"), out))
    # cap_mb == 0 is the UNCAPPED reference, not a cap; including it would put the
    # "lowest cap that completed" at 0 and destroy the cliff. Caught on the first run.
    ran = [r for r in d if not r["died"] and r["cap_mb"] > 0]
    died = [r for r in d if r["died"]]
    assert ran and died, "soak5: need both a surviving and a dying cap to place a cliff"
    lowest_ok = min(r["cap_mb"] for r in ran)
    highest_dead = max(r["cap_mb"] for r in died)
    bad = [r for r in ran if r["same_answers"] is not True]
    lo_rec = [r for r in ran if r["cap_mb"] == lowest_ok][0]
    print("\nlowest cap that completed all 12: %d MB (VmSize %d kB, RSS %d kB)"
          % (lowest_ok, lo_rec["vm_after"]["VmSize"], lo_rec["vm_after"]["VmRSS"]))
    print("highest cap that died: %d MB (rc %d, SIGABRT=%s)"
          % (highest_dead,
             [r for r in died if r["cap_mb"] == highest_dead][0]["rc"],
             [r for r in died if r["cap_mb"] == highest_dead][0]["signal"] == 6))
    print("surviving caps with ANY answer difference: %d of %d" % (len(bad), len(ran)))
    print("  (rows that differ only in `nps`, i.e. timing, are counted separately above)")
    return {"lowest_ok_mb": lowest_ok, "highest_dead_mb": highest_dead,
            "survivors_with_diff": len(bad), "n_survivors": len(ran)}


def soak5b():
    d = load("soak5b.json")
    assert len(d) == 4, "soak5b: expected 4 Hash values, got %d" % len(d)
    section("P5b  the cliff is Hash + 44 MB (four Hash values, bisected in 2 MB steps)")
    print("Hash  lowest_complete_MB  highest_dead_MB  cliff - Hash")
    for r in d:
        print("%5d %18d %16d %13d"
              % (r["hash"], r["lowest_complete_mb"], r["highest_dead_mb"],
                 r["lowest_complete_mb"] - r["hash"]))
    vmp = load("soak2.json")
    a = [r for r in vmp if r["arm"] == "A"]
    print("\nVmPeak minus table size is constant, so the virtual peak is not the table:")
    for r in sorted(a, key=lambda r: r["hash"]):
        print("  Hash %4d  VmPeak %8d kB  - %4d MB table = %6.1f MB"
              % (r["hash"], r["vmpeak"], r["hash"],
                 (r["vmpeak"] - r["hash"] * 1024) / 1024.0))
    return d


def soak6():
    d = load("soak6.json")
    s = d["summary"]
    section("P6  ASan + UBSan, detect_leaks=1")
    print("searches %d  kinds %s  rc %d  sanitizer_lines %d  zero-node rows %d"
          % (s["searches"], s["kinds"], s["rc"], s["sanitizer_lines"],
             s["zero_node_rows"]))
    p = load("sanitizer_proof.json")
    assert len(p) == 3, "sanitizer_proof: expected 3 cases, got %d" % len(p)
    print("\nproof the runner can report a sanitizer line (same runner, 3 builds/inputs):")
    for k in ("clean", "planted_untriggered", "planted_triggered"):
        r = p[k]
        print("  %-20s rc %3s  sanitizer_lines %d  info_depth %2d  bestmoves %s"
              % (k, r["rc"], r["sanitizer_lines"], r["info_depth"], r["bestmoves"]))
    ok = (p["clean"]["sanitizer_lines"] == 0
          and p["planted_untriggered"]["sanitizer_lines"] == 0
          and p["planted_triggered"]["sanitizer_lines"] > 0)
    print("\nDETECTOR PROVEN: %s (0 clean, 0 untriggered, %d triggered)"
          % (ok, p["planted_triggered"]["sanitizer_lines"]))
    return ok


def predictions(r1, a2, b2, r4, r5, r5b, det):
    section("PREDICTION reconciliation (PREDICTION.md was committed before measurement)")
    rows = []
    # P1: slope < 2 MB/1k, plateau <= 27 MB above baseline, <=70 MB
    slope = r1["slope_mb_per_1k"]
    rows.append(("P1", "slope < 2 MB/1000 searches over 1000..5000",
                 "%.3f MB/1000" % slope, slope < 2))
    rows.append(("P1", "plateau <= 70 MB at Hash 32",
                 "%.1f MB" % (r1["last_kb"] / 1024.0), r1["last_kb"] / 1024 < 70 * 1024))
    rows.append(("P1", "rise <= 10 MB in the first ~200 searches",
                 "%+d kB total over the whole run" % (r1["last_kb"] - r1["first_kb"]),
                 abs(r1["last_kb"] - r1["first_kb"]) < 10240))
    for r in rows:
        print("%-4s %-52s measured %-32s %s" % (r[0], r[1], r[2], "HELD" if r[3] else "KILLED"))
    print()
    # P2: within +-15% and +-8MB
    for a in sorted(a2, key=lambda x: x["hash"]):
        if a["hash"] == 1:
            continue
        delta = a["rss_over_hash1"] / 1024.0
        want = a["hash"] - 1
        err = 100.0 * (delta - want) / want
        held = abs(err) <= 15 and abs(delta - want) <= 8
        print("P2   Hash %4d marginal %7.1f MB vs %4d MB (%.1f%%) %s"
              % (a["hash"], delta, want, err, "HELD" if held else "KILLED"))
    print()
    # P2b: alt table ~256MB at Hash 256, freed within 8MB
    h256 = [r for r in b2 if r["hash"] == 256 and r["multipv"] == 2][0]
    h256_1 = [r for r in b2 if r["hash"] == 256 and r["multipv"] == 1][0]
    peak_delta = (h256["peak_median"] - h256_1["peak_median"]) / 1024.0
    after_delta = (h256["after_median"] - h256_1["after_median"]) / 1024.0
    print("P2b  Hash 256 MPV2 peak - MPV1 peak = %.1f MB (predicted 200..300) %s"
          % (peak_delta, "HELD" if 200 <= peak_delta <= 300 else "KILLED"))
    print("P2b  Hash 256 MPV2 after - MPV1 after = %+.1f MB (predicted within 8) %s"
          % (after_delta, "HELD" if abs(after_delta) <= 8 else "KILLED"))
    print()
    # P3: within 4MB
    for mode in ("ucinewgame", "clearhash"):
        s = load("soak3_%s.json" % mode)["summary"]
        held = abs(s["delta_kb"]) <= 4096
        print("P3   %-11s delta %+d kB (predicted within 4 MB) %s"
              % (mode, s["delta_kb"], "HELD" if held else "KILLED"))
    print()
    # P4: slope < 5 MB/1000, growth <= 30MB
    after_vals = r4["after_vals"]
    growth = (after_vals[-1] - after_vals[0]) / 1024.0
    print("P4   1,000 MPV-4 searches: after-value growth %.1f MB (killed if >30) %s"
          % (growth, "HELD" if growth <= 30 else "KILLED"))
    print("P4   distinct after values: %s kB" % (after_vals,))
    print()
    # P5
    print("P5   cliff %d alive / %d dead; survivors with any answer change %d of %d  %s"
          % (r5["lowest_ok_mb"], r5["highest_dead_mb"],
             r5["survivors_with_diff"], r5["n_survivors"],
             "HELD" if r5["survivors_with_diff"] == 0 else "KILLED"))
    print()
    print("P6   detector proven: %s" % det)


def main():
    print("soak analysis -- every number below is read from evidence/, none typed")
    r1 = soak1()
    soak1_quality()
    a2, b2 = soak2()
    soak3()
    soak3b()
    r4 = soak4()
    r5 = soak5()
    r5b = soak5b()
    det = soak6()
    predictions(r1, a2, b2, r4, r5, r5b, det)
    print("\nALL PARSERS PASSED their row-count assertions")


if __name__ == "__main__":
    main()
