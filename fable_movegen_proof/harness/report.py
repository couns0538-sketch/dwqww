"""report.py - collect the compact evidence of job 3 into the pack and derive the tables and verdicts.

  python -I -B report.py            copies receipts, ledgers and logs from out\\job3 into fable_movegen_proof\\evidence,
                                    writes evidence\\TABLES.md and evidence\\VERDICTS.json, prints the verdict lines

Nothing is measured here: every number is read from a receipt or a ledger that a check wrote. The verdict rule
is the one of the approved plan (decisions D1 and D2):
  FAIL        a reproduced difference in a required field on a legal position, or a confirmed pin mismatch
  PASS        every release-exe gate complete without a difference, and 20,000,000 auxiliary-tier comparisons
              without a difference
  INCOMPLETE  no difference, but a required gate or the 20,000,000 count is unfinished
  BLOCKED     an input or a capability is missing
A row that is MISMATCH or CRASH is reported here as DIFFERENCE TO CONFIRM: only a reproduced and isolated
difference becomes FAIL, and that step is done by hand.
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fuzz  # noqa: E402

OUT = fuzz.OUT
PACK = fuzz.PACK
EV = os.path.join(PACK, "evidence")
CANDS = fuzz.CANDS
ALL = ["LOCK", "LOCKCOPY", "LOCKEQ"] + CANDS
TARGET = 20_000_000
NAMES = {"EVL": "EVADE_LEGAL", "PCM": "PAWN_CAPMASK v2", "CKL": "CHECKERS_KL v3 (mode 1)", "WNP": "WITNESS_NOPIN",
         "KPC": "KING_PAWN_CACHE v2", "BUN": "BUNDLE3 (EVL + PCM v2 + CKL v3)", "LOCK": "combo29 lock", "LOCKCOPY": "byte-identical copy of the lock",
         "LOCKEQ": "lock-equivalent (BUNDLE3 tree, switches 0)"}


def jload(path):
    return json.load(open(path, "r", encoding="ascii")) if os.path.exists(path) else None


def copy(src, dst_rel):
    if not os.path.exists(src):
        return False
    dst = os.path.join(EV, dst_rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    return True


def collect():
    if os.path.isdir(EV):
        shutil.rmtree(EV)                       # the evidence folder is regenerated from out\job3 every time
    os.makedirs(EV)
    r = os.path.join(OUT, "runs")
    for name in ("INPUTS.json", "INPUTS.txt"):
        copy(os.path.join(r, "freeze", name), f"freeze/{name}")
    for name in ("in.txt", "out_LOCK.txt"):
        copy(os.path.join(r, "observe", name), f"observe/{name}")
    for name in os.listdir(os.path.join(r, "selftest")):
        if name.endswith(".log"):
            copy(os.path.join(r, "selftest", name), f"selftest/{name}")
    for tag in ["LOCK"] + CANDS:
        copy(os.path.join(OUT, "aux", tag, "AUX_RECEIPT.json"), f"aux/{tag}_AUX_RECEIPT.json")
    for check in ("pins", "divide", "soak", "edge", "crosstier", "search_sig"):
        d = os.path.join(r, check)
        if os.path.isdir(d):
            for name in sorted(os.listdir(d)):
                if name.endswith(".json") and ".old_" not in name:
                    copy(os.path.join(d, name), f"{check}/{name}")
    d = os.path.join(r, "warm")
    if os.path.isdir(d):
        for name in sorted(os.listdir(d)):
            if name.endswith(".json") and ".old_" not in name:
                copy(os.path.join(d, name), f"warm/{name}")
        copy(os.path.join(d, "LOCK.transcript.txt"), "warm/LOCK.transcript.txt")
    for tier in ("aux", "uci", "warm"):
        copy(os.path.join(r, f"fuzz_{tier}", "ledger.tsv"), f"fuzz_{tier}/ledger.tsv")
    d = os.path.join(r, "fuzz_aux")
    if os.path.isdir(d):
        for name in sorted(os.listdir(d)):
            if name.startswith("KEYS_"):
                copy(os.path.join(d, name), f"fuzz_aux/{name}")
        cdir = os.path.join(d, "chunks")
        if os.path.isdir(cdir):                 # 200 small files become one table
            rows = ["chunk\tseeds\tpath_sha256\tref_transcript_sha256\tpositions\tin_check\tdouble_check\tmates\tstalemates\twith_ep_square\tplayouts\tcaptures\tpromotions\tcastles\ten_passants\tchecks_given\tcache_clears"]
            for name in sorted(os.listdir(cdir)):
                c = jload(os.path.join(cdir, name))
                g = c["gen_stats"]
                rows.append("\t".join(str(x) for x in (c["chunk"], c["seeds"], c["path_sha256"], c["ref_transcript_sha256"], g["positions"], g["in_check"],
                                                         g["double_check"], g["mates"], g["stalemates"], g["with_ep_square"], g["playouts"], g["captures"],
                                                         g["promotions"], g["castles"], g["en_passants"], g["checks_given"], g["cache_clears"])))
            os.makedirs(os.path.join(EV, "fuzz_aux"), exist_ok=True)
            with open(os.path.join(EV, "fuzz_aux", "chunks.tsv"), "w", encoding="ascii", newline="\n") as f:
                f.write("\n".join(rows) + "\n")
    for name in ("RELEASE_SUMMARY.json", "FUZZ_COUNT.json"):
        copy(os.path.join(r, name), name)
    for name in ("seeds_v1.json", "seeds_v2.json"):
        copy(os.path.join(OUT, "corpus", name), f"corpus/{name}")
    ldir = os.path.join(OUT, "logs")
    for name in sorted(os.listdir(ldir)):
        if os.path.getsize(os.path.join(ldir, name)) < 400_000:
            copy(os.path.join(ldir, name), f"logs/{name}")
    fdir = os.path.join(OUT, "fail")
    listing = sorted(os.listdir(fdir)) if os.path.isdir(fdir) else []
    with open(os.path.join(EV, "FAIL_FOLDERS.txt"), "w", encoding="ascii", newline="\n") as f:
        f.write("failure folders under out\\job3\\fail (empty means no failure evidence was ever written):\n" + "\n".join(listing) + "\n")
    return listing


def ledger_stats(tier):
    per = {}
    for row in fuzz.read_ledger(tier):
        c = per.setdefault(row["cand"], {"ok": set(), "positions": 0, "in_check": 0, "bad": []})
        k = int(row["chunk"])
        if row["status"] == "OK":
            if k not in c["ok"]:
                c["ok"].add(k)
                c["positions"] += int(row["positions"])
                c["in_check"] += int(row.get("in_check") or 0)
        else:
            c["bad"].append((k, row["status"], row["detail"][:300]))
    return per


def main():
    fails = collect()
    r = os.path.join(OUT, "runs")
    inputs = {e["tag"]: e for e in jload(os.path.join(r, "freeze", "INPUTS.json"))}
    green = [n for n in os.listdir(os.path.join(r, "selftest")) if n.startswith("GREEN")]
    selftest_line = ""
    if green:
        selftest_line = open(os.path.join(r, "selftest", sorted(green)[-1]), "r", encoding="ascii", errors="replace").read().strip().splitlines()[-1]
    release = (jload(os.path.join(r, "RELEASE_SUMMARY.json")) or {"tags": {}})["tags"]
    aux, uci = ledger_stats("aux"), ledger_stats("uci")
    warm_rows = fuzz.read_ledger("warm")
    T = []
    T.append("## Identity\n\n| Tag | What | Release exe MD5 | Release exe SHA256 | Probe SHA256 |\n|---|---|---|---|---|")
    for tag in ALL:
        if tag == "LOCKCOPY":
            continue
        e = inputs.get(tag, {})
        a = jload(os.path.join(OUT, "aux", tag, "AUX_RECEIPT.json")) or {}
        T.append(f"| {tag} | {NAMES[tag]} | `{e.get('exe_md5', '')}` | `{e.get('exe_sha256', '')}` | {'`' + a['exe_sha256'] + '`' if a else 'none (release tier only)'} |")
    T.append("\n## Pins (13 per executable)\n\n| Tag | bench net on d11/13/16/20/22 | bench net off d11/13/16/20/22 | startpos perft 5 | kiwipete perft 4 | kiwipete perft 5 | Result |\n|---|---|---|---|---|---|---|")
    for tag in ALL:
        p = jload(os.path.join(r, "pins", tag + ".json"))
        if not p or "bench" not in p or not p["bench"]:
            T.append(f"| {tag} | not run | | | | | {p['status'] if p else 'NOT RUN'} |")
            continue
        on = " / ".join(str(p["bench"][f"net_on_d{d}"]["nodes"]) for d in (11, 13, 16, 20, 22))
        off = " / ".join(str(p["bench"][f"net_off_d{d}"]["nodes"]) for d in (11, 13, 16, 20, 22))
        T.append(f"| {tag} | {on} | {off} | {p['perft']['startpos_perft5']['nodes']} | {p['perft']['kiwipete_perft4']['nodes']} | "
                 f"{p['perft']['kiwipete_perft5']['nodes']} | {p['status']} {p['matches']} |")
    lock_div = jload(os.path.join(r, "divide", "LOCK.json"))
    if lock_div:
        T.append("\n## Perft divide (every root move compared with the lock's)\n\n| Position | FEN | Depth | Root moves | Total (lock) | Published total | " + " | ".join(t for t in ALL if t != "LOCK") + " |\n|---|---|---|---|---|---|" + "---|" * (len(ALL) - 1))
        others = {t: jload(os.path.join(r, "divide", t + ".json")) for t in ALL if t != "LOCK"}
        for i, pos in enumerate(lock_div["positions"]):
            cells = []
            for t in ALL:
                if t == "LOCK":
                    continue
                o = others[t]
                if not o or o.get("status") != "DONE":
                    cells.append("not run")
                else:
                    q = o["positions"][i]
                    cells.append("same" if q["divide"] == pos["divide"] and q["total"] == pos["total"] and not q["other_lines"] else "DIFFERS")
            T.append(f"| {pos['name']} | `{pos['fen']}` | {pos['depth']} | {len(pos['divide'])} | {pos['total']} | {pos['published'] if pos['published'] else 'none used'} | " + " | ".join(cells) + " |")
    T.append("\n## Release-executable checks per tag\n\n| Tag | Pins | Perft divide | Warm transcript | Threads 2-4 soak | Edge suite |\n|---|---|---|---|---|---|")
    for tag in ALL:
        row = release.get(tag, {})
        e = jload(os.path.join(r, "edge", tag + ".json"))
        T.append(f"| {tag} | {row.get('pins', 'not run')} | {row.get('divide', 'not run')} | {row.get('warm', 'not run')} | {row.get('soak', 'not run')} | "
                 f"{e['status'] if e else ('reference' if tag == 'LOCK' else 'not run')} |")
    T.append("\n## Edge suite per tag\n\n| Tag | Legal entries | Tier A records identical | Tier R perft blocks identical | Rejected entries handled like the lock (A / R) | "
             "Unreachable entries like the lock (A / R) | Search signature depth, net on / off | Result |\n|---|---|---|---|---|---|---|---|")
    for tag in ALL:
        e = jload(os.path.join(r, "edge", tag + ".json"))
        if not e:
            continue
        ta = e["tier_a_legal"]
        ua = e.get("tier_a_unreachable")
        T.append(f"| {tag} | {e['legal_entries']} | {ta['status']} {ta.get('records', '')} | {e['tier_r_legal']['status']} {e['tier_r_legal']['perft_blocks']} | "
                 f"{e.get('tier_a_rejected', {}).get('identical_to_lock', 'n/a')} / {e['tier_r_rejected']['identical_to_lock']} | "
                 f"{all(v['identical_to_lock'] for v in ua.values()) if ua else 'n/a'} / {all(v['identical_to_lock'] for v in e['tier_r_unreachable'].values())} | "
                 f"d{e['search_signature']['net_on']['depth']}: {e['search_signature']['net_on']['identical_to_lock']} / {e['search_signature']['net_off']['identical_to_lock']} | {e['status']} |")
    T.append("\n## Fuzz, completed position comparisons\n\n| Candidate | Tier A (auxiliary probes, all fields) | chunks | in check | quiet | not OK | Tier R (release exe, go perft 2) | chunks | not OK |\n|---|---|---|---|---|---|---|---|---|")
    for c in CANDS:
        a, u = aux.get(c, {"ok": set(), "positions": 0, "in_check": 0, "bad": []}), uci.get(c, {"ok": set(), "positions": 0, "bad": []})
        T.append(f"| {c} | {a['positions']:,} | {len(a['ok'])} | {a['in_check']:,} | {a['positions'] - a['in_check']:,} | {len(a['bad'])} | {u['positions']:,} | {len(u['ok'])} | {len(u['bad'])} |")
    T.append("\nEvery tier A record holds the static eval with the net off and with the net on, so the eval coverage by mode equals the tier A count in both modes.")
    if warm_rows:
        T.append("\n## Cache-state variants (tier A, not counted in the fuzz total)\n\n| Candidate | never cleared: chunks OK | cleared before every playout: chunks OK | not OK |\n|---|---|---|---|")
        for c in CANDS:
            rows = [w for w in warm_rows if w["cand"] == c]
            T.append(f"| {c} | {sum(1 for w in rows if w['variant'] == 'never_cleared' and w['status'] == 'OK')} | "
                     f"{sum(1 for w in rows if w['variant'] == 'cleared_before_every_playout' and w['status'] == 'OK')} | {sum(1 for w in rows if w['status'] != 'OK')} |")
    sdir = os.path.join(r, "search_sig")
    if os.path.isdir(sdir):
        T.append("\n## Search signatures on corpus positions (release exe, supplementary)\n\n| Candidate | net on | net off | positions | depth |\n|---|---|---|---|---|")
        for c in CANDS:
            on, off = jload(os.path.join(sdir, f"{c}_neton.json")), jload(os.path.join(sdir, f"{c}_netoff.json"))
            if on and off:
                T.append(f"| {c} | {'identical' if on['identical_to_lock'] else 'DIFFERS'} | {'identical' if off['identical_to_lock'] else 'DIFFERS'} | {on['positions']} | {on['depth']} |")
    cdir = os.path.join(r, "crosstier")
    if os.path.isdir(cdir):
        T.append("\n## Cross-tier: probe legal list equals its release exe's go perft 1 list\n\n| Tag | Positions | Identical lists | Result |\n|---|---|---|---|")
        for tag in ["LOCK"] + CANDS:
            x = jload(os.path.join(cdir, tag + ".json"))
            if x:
                T.append(f"| {tag} | {x['positions']} | {x['identical_lists']} | {x['status']} |")

    verdicts = {}
    for c in CANDS:
        row = release.get(c, {})
        e = jload(os.path.join(r, "edge", c + ".json"))
        a, u = aux.get(c, {"ok": set(), "positions": 0, "in_check": 0, "bad": []}), uci.get(c, {"ok": set(), "positions": 0, "bad": []})
        wrows = [w for w in warm_rows if w["cand"] == c]
        gates = {
            "identity": inputs.get(c, {}).get("status") == "OK",
            "self_test": selftest_line.startswith("SELFTEST PASS"),
            "pins": str(row.get("pins", "")).startswith("MATCH 13/13"),
            "divide": str(row.get("divide", "")).startswith("MATCH"),
            "edge_suite": bool(e) and e["status"] == "MATCH",
            "warm_transcript": str(row.get("warm", "")).startswith("MATCH"),
            "threads_soak": str(row.get("soak", "")).startswith("STABLE"),
            "fuzz_tier_a_20M": a["positions"] >= TARGET and not a["bad"],
            "fuzz_tier_r_clean": not u["bad"],
            "cache_state_variants": bool(wrows) and all(w["status"] == "OK" for w in wrows),
        }
        differences = []
        if "MISMATCH" in str(row.get("pins", "")):
            differences.append("pins: " + row["pins"])
        for name in ("divide", "warm"):
            if "MISMATCH" in str(row.get(name, "")):
                differences.append(f"{name}: {row[name]}")
        if "UNSTABLE" in str(row.get("soak", "")):
            differences.append("soak: " + row["soak"])
        if e and e["legal_position_differences"]:
            differences += ["edge: " + x for x in e["legal_position_differences"]]
        differences += [f"fuzz tier A chunk {k}: {s}: {d}" for k, s, d in a["bad"] if s in ("MISMATCH", "CRASH")]
        differences += [f"fuzz tier R chunk {k}: {s}: {d}" for k, s, d in u["bad"] if s in ("MISMATCH", "CRASH")]
        differences += [f"cache-state variant chunk {w['chunk']} {w['variant']}: {w['status']}" for w in wrows if w["status"] in ("MISMATCH", "CRASH")]
        if not gates["identity"]:
            verdict = "BLOCKED"
        elif differences:
            verdict = "DIFFERENCE TO CONFIRM"
        elif all(gates.values()):
            verdict = "PASS"
        else:
            verdict = "INCOMPLETE"
        verdicts[c] = {"name": NAMES[c], "verdict": verdict, "gates": gates, "open_gates": [g for g, ok in gates.items() if not ok],
                       "differences": differences, "tier_a_completed": a["positions"], "tier_a_in_check": a["in_check"],
                       "tier_r_completed": u["positions"], "robustness_differences": (e or {}).get("robustness_differences", []),
                       "harness_errors": [f"tier A chunk {k}: {s}" for k, s, _ in a["bad"] if s not in ("MISMATCH", "CRASH")]
                       + [f"tier R chunk {k}: {s}" for k, s, _ in u["bad"] if s not in ("MISMATCH", "CRASH")]}
    T.insert(0, "## Verdict per candidate (derived from the receipts and ledgers)\n\n| Candidate | Verdict | Tier A completed | Tier R completed | Open gates | Differences |\n|---|---|---|---|---|---|\n"
             + "\n".join(f"| {c} ({v['name']}) | **{v['verdict']}** | {v['tier_a_completed']:,} | {v['tier_r_completed']:,} | {', '.join(v['open_gates']) or 'none'} | {len(v['differences'])} |"
                         for c, v in verdicts.items()) + "\n")
    with open(os.path.join(EV, "TABLES.md"), "w", encoding="ascii", errors="replace", newline="\n") as f:
        f.write("# Tables of job 3, generated by harness/report.py at " + fuzz.now() + "\n\nEvery number is read from a receipt or a ledger; nothing is measured here.\n\n" + "\n".join(T) + "\n")
    with open(os.path.join(EV, "VERDICTS.json"), "w", encoding="ascii", newline="\n") as f:
        json.dump({"written": fuzz.now(), "self_test": selftest_line, "target": TARGET, "verdicts": verdicts, "failure_folders": fails}, f, indent=1)
    print("self-test: " + selftest_line)
    for c, v in verdicts.items():
        print(f"{c}: {v['verdict']} | tier A {v['tier_a_completed']:,} | tier R {v['tier_r_completed']:,} | open: {', '.join(v['open_gates']) or 'none'} | differences: {len(v['differences'])}")
    print(f"failure folders: {len(fails)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
