"""report.py - collect the compact evidence of job 3 into the pack and derive the tables, the verdicts and PROOF.md.

  python -I -B report.py            copies receipts, ledgers and logs from out\\job3 into fable_movegen_proof\\evidence,
                                    writes evidence\\TABLES.md and evidence\\VERDICTS.json, renders PROOF.md from
                                    harness\\proof_template.md, prints the verdict lines

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
import contextlib
import io
import json
import os
import re
import shutil
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checks_release  # noqa: E402
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
GATE_TEXT = {"identity": "input identity", "self_test": "harness self-test", "pins": "13 pins", "divide": "perft divide", "edge_suite": "edge suite (both tiers)",
             "warm_transcript": "warm transcript", "threads_soak": "Threads soak", "fuzz_tier_a_20M": "20,000,000 auxiliary-tier fuzz comparisons",
             "fuzz_tier_r_clean": "release-exe fuzz without a failed chunk", "cache_state_variants": "cache-state variants",
             "probe_tied_to_exe": "probe move lists equal to its release executable's"}
EMPTY = {"ok": set(), "positions": 0, "in_check": 0, "bad": [], "foreign": 0, "harness": set()}


def jload(path):
    return json.load(open(path, "r", encoding="ascii")) if os.path.exists(path) else None


def copy(src, dst_rel):
    if not os.path.exists(src):
        return False
    dst = os.path.join(EV, dst_rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)
    return True


def copy_jsons(src_dir, dst_rel):
    if os.path.isdir(src_dir):
        for name in sorted(os.listdir(src_dir)):
            if name.endswith(".json") and ".old_" not in name:
                copy(os.path.join(src_dir, name), f"{dst_rel}/{name}")


def chunk_table(cdir, dst_rel):
    """The per-chunk files of a fuzz run become one table."""
    if not os.path.isdir(cdir):
        return
    rows = ["chunk\tseeds\tpath_sha256\tref_transcript_body_sha256\tpositions\tin_check\tdouble_check\tmates\tstalemates\twith_ep_square\tplayouts\tcaptures\tpromotions\tcastles\ten_passants\tchecks_given\tcache_clears"]
    for name in sorted(os.listdir(cdir)):
        c = jload(os.path.join(cdir, name))
        g = c["gen_stats"]
        rows.append("\t".join(str(x) for x in (c["chunk"], c["seeds"], c["path_sha256"], c["ref_transcript_sha256"], g["positions"], g["in_check"],
                                                 g["double_check"], g["mates"], g["stalemates"], g["with_ep_square"], g["playouts"], g["captures"],
                                                 g["promotions"], g["castles"], g["en_passants"], g["checks_given"], g["cache_clears"])))
    dst = os.path.join(EV, dst_rel)
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, "w", encoding="ascii", newline="\n") as f:
        f.write("\n".join(rows) + "\n")


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
    for tag in ["LOCK", "LOCKEQ"] + CANDS:
        copy(os.path.join(OUT, "aux2", tag, "AUX_RECEIPT.json"), f"probes/{tag}_AUX_RECEIPT.json")
        copy(os.path.join(OUT, "aux2", tag + "_cov", "AUX_RECEIPT.json"), f"probes/{tag}_cov_AUX_RECEIPT.json")
    for check in ("pins", "divide", "soak", "edge", "crosstier", "search_sig", "coverage", "wnp_targets", "replay"):
        copy_jsons(os.path.join(r, check), check)
    copy_jsons(os.path.join(r, "warm"), "warm")
    copy(os.path.join(r, "warm", "LOCK.transcript.txt"), "warm/LOCK.transcript.txt")
    for tier in ("aux", "uci", "warm"):
        copy(os.path.join(r, f"fuzz_{tier}", "ledger.tsv"), f"fuzz_{tier}/ledger.tsv")
        copy(os.path.join(r, "h1", f"fuzz_{tier}", "ledger.tsv"), f"h1_earlier_run/fuzz_{tier}/ledger.tsv")
    copy_jsons(os.path.join(r, "h1", "edge"), "h1_earlier_run/edge")
    copy_jsons(os.path.join(r, "h1", "crosstier"), "h1_earlier_run/crosstier")
    copy_jsons(os.path.join(r, "h1", "search_sig_20000_positions"), "h1_earlier_run/search_sig_20000_positions")
    d = os.path.join(r, "fuzz_aux")
    if os.path.isdir(d):
        for name in sorted(os.listdir(d)):
            if name.startswith("KEYS_"):
                copy(os.path.join(d, name), f"fuzz_aux/{name}")
        chunk_table(os.path.join(d, "chunks"), "fuzz_aux/chunks.tsv")
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
        f.write("failure folders under out\\job3\\fail (none listed below means no failure evidence was ever written):\n" + "\n".join(listing) + "\n")
    return listing


def ledger_stats(rows, bound=None):
    """Per candidate: the chunks with an OK row (each once), their positions, and every row that is not OK.
    `bound(row)` says whether a row was made with the frozen binaries; a row that was not is listed as foreign and
    never counted."""
    per = {}
    for row in rows:
        c = per.setdefault(row["cand"], {"ok": set(), "positions": 0, "in_check": 0, "bad": [], "foreign": 0, "harness": set()})
        k = int(row["chunk"])
        if bound is not None and not bound(row):
            c["foreign"] += 1
            continue
        if row.get("harness_sha256"):
            c["harness"].add(row["harness_sha256"])
        if row["status"] == "OK":
            if k not in c["ok"]:
                c["ok"].add(k)
                c["positions"] += int(row["positions"])
                c["in_check"] += int(row.get("in_check") or 0)
        else:
            c["bad"].append((k, row["status"], row["detail"][:300]))
    return per


def read_tsv(path):
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="ascii") as f:
        head = f.readline().rstrip("\n").split("\t")
        return [dict(zip(head, ln.rstrip("\n").split("\t"))) for ln in f if ln.strip()]


def aux_row_bound(w, probe_sha):
    """A tier A row (or a cache-variant row) counts only if it names the lock probe and this candidate's probe as
    the build receipts record them, and the two differ: lock against lock would always be equal."""
    lock, cand = probe_sha.get("LOCK"), probe_sha.get(w.get("cand"))
    return bool(lock) and bool(cand) and w.get("lock_probe_sha256") == lock and w.get("cand_probe_sha256") == cand and cand != lock


def uci_row_bound(w, exe_sha):
    """The same for a release-exe row and the frozen executables of INPUTS.json."""
    lock, cand = exe_sha.get("LOCK"), exe_sha.get(w.get("cand"))
    return bool(lock) and bool(cand) and w.get("lock_exe_sha256") == lock and w.get("cand_exe_sha256") == cand and cand != lock


def tier_a_gate(a, harness_now):
    """20,000,000 completed comparisons, no row that is not OK, every counted row written by the harness files as
    they are now."""
    return a["positions"] >= TARGET and not a["bad"] and a["harness"] == {harness_now}


def verdict_of(gates, differences):
    """BLOCKED without input identity; a reported difference is never a PASS; PASS needs every gate; otherwise
    INCOMPLETE. FAIL is not derived here: a difference is reproduced and isolated by hand first."""
    if not gates.get("identity"):
        return "BLOCKED"
    if differences:
        return "DIFFERENCE TO CONFIRM"
    return "PASS" if all(gates.values()) else "INCOMPLETE"


def selftest_runs(sdir):
    """Every self-test log, oldest first: (time written, file name, last line)."""
    runs = []
    for name in os.listdir(sdir) if os.path.isdir(sdir) else []:
        if name.endswith(".log"):
            p = os.path.join(sdir, name)
            lines = open(p, "r", encoding="ascii", errors="replace").read().strip().splitlines()
            runs.append((os.path.getmtime(p), name, lines[-1].strip() if lines else ""))
    return sorted(runs)


def selftest_passed(line):
    """True only for 'SELFTEST PASS n/n' with the same n twice."""
    m = re.fullmatch(r"SELFTEST PASS (\d+)/(\d+)", line.strip())
    return bool(m) and m.group(1) == m.group(2) and int(m.group(1)) > 0


def main():
    fails = collect()
    r = os.path.join(OUT, "runs")
    S, order = {}, []

    def sec(key, title, text):
        S[key] = text
        order.append((title, key))

    inputs = {e["tag"]: e for e in jload(os.path.join(r, "freeze", "INPUTS.json"))}
    # the self-test result is the last line of the newest log, whatever the file is called
    st_runs = selftest_runs(os.path.join(r, "selftest"))
    selftest_name, selftest_line = (st_runs[-1][1], st_runs[-1][2]) if st_runs else ("", "")
    # the summary of the release-exe checks is derived again from the receipts, so it cannot be older than they are
    with contextlib.redirect_stdout(io.StringIO()):
        checks_release.summary(ALL)
    release = (jload(os.path.join(r, "RELEASE_SUMMARY.json")) or {"tags": {}})["tags"]
    # a ledger row or a receipt counts only if it names the frozen executables and the probes of the build receipts
    probe_sha = {x: (jload(os.path.join(OUT, "aux2", x, "AUX_RECEIPT.json")) or {}).get("exe_sha256") for x in ["LOCK", "LOCKEQ"] + CANDS}
    exe_sha = {x: inputs.get(x, {}).get("exe_sha256") for x in ["LOCK", "LOCKEQ"] + CANDS}
    exe_sha["LOCKCOPY"] = exe_sha["LOCK"]
    harness_now = fuzz.harness_sha()
    aux = ledger_stats(fuzz.read_ledger("aux"), lambda w: aux_row_bound(w, probe_sha))
    uci = ledger_stats(fuzz.read_ledger("uci"), lambda w: uci_row_bound(w, exe_sha))
    h1_aux = ledger_stats(read_tsv(os.path.join(r, "h1", "fuzz_aux", "ledger.tsv")))
    h1_uci = ledger_stats(read_tsv(os.path.join(r, "h1", "fuzz_uci", "ledger.tsv")))
    warm_all = fuzz.read_ledger("warm")
    warm_rows = [w for w in warm_all if aux_row_bound(w, probe_sha)]
    uci_rows = [w for w in fuzz.read_ledger("uci") if uci_row_bound(w, exe_sha)]
    unbound = []                                  # receipts that do not name the frozen executable or probe

    def exe_bound(check, tag):
        """The receipt of a release-exe check names the frozen executable of its tag, and so does the lock's."""
        x, lx = jload(os.path.join(r, check, tag + ".json")), jload(os.path.join(r, check, "LOCK.json"))
        ok = bool(x) and bool(lx) and bool(exe_sha.get(tag)) and x.get("exe_sha256") == exe_sha[tag] and lx.get("exe_sha256") == exe_sha["LOCK"]
        if x and not ok:
            unbound.append(f"{check} {tag}")
        return ok

    # ---- identity
    t = ["| Tag | What | Release exe MD5 | Release exe SHA256 | Probe SHA256 (harness 2) | Effective candidate switches in the probe |", "|---|---|---|---|---|---|"]
    harness_shas = set()
    for tag in ALL:
        if tag == "LOCKCOPY":
            continue
        e = inputs.get(tag, {})
        a = jload(os.path.join(OUT, "aux2", tag, "AUX_RECEIPT.json")) or {}
        sw = ""
        if a:
            harness_shas.add(a["harness_sha256"])
            both = dict(a["effective_switches"]["board.cpp"])
            both.update(a["effective_switches"]["eval.cpp"])
            sw = ", ".join(f"{k.replace('FORGE_SPD_', '')}={v}" for k, v in both.items()
                           if any(x in k for x in ("EVADE_LEGAL", "PAWN_CAPMASK", "CHECKERS_KL", "WITNESS_NOPIN", "KING_PAWN_CACHE"))) or "none"
        t.append(f"| {tag} | {NAMES[tag]} | `{e.get('exe_md5', '')}` | `{e.get('exe_sha256', '')}` | {'`' + a['exe_sha256'] + '`' if a else 'none'} | {sw} |")
    t.append(f"\nHarness source `mgprobe.cpp` compiled into every probe: sha256 `{', '.join(sorted(harness_shas))}`. LOCKCOPY is a second file with the lock's bytes (same hashes), used as a control.")
    sec("IDENTITY_TABLE", "Identity", "\n".join(t))

    # ---- pins
    t = ["| Tag | bench net on d11/13/16/20/22 | bench net off d11/13/16/20/22 | startpos perft 5 | kiwipete perft 4 | kiwipete perft 5 | Result |", "|---|---|---|---|---|---|---|"]
    for tag in ALL:
        p = jload(os.path.join(r, "pins", tag + ".json"))
        if not p or not p.get("bench"):
            t.append(f"| {tag} | not run | | | | | {p['status'] if p else 'NOT RUN'} |")
            continue
        on = " / ".join(str(p["bench"][f"net_on_d{d}"]["nodes"]) for d in (11, 13, 16, 20, 22))
        off = " / ".join(str(p["bench"][f"net_off_d{d}"]["nodes"]) for d in (11, 13, 16, 20, 22))
        t.append(f"| {tag} | {on} | {off} | {p['perft']['startpos_perft5']['nodes']} | {p['perft']['kiwipete_perft4']['nodes']} | "
                 f"{p['perft']['kiwipete_perft5']['nodes']} | {p['status']} {p['matches']} |")
    sec("PINS_TABLE", "Pins (13 per executable)", "\n".join(t))

    # ---- divide
    lock_div = jload(os.path.join(r, "divide", "LOCK.json"))
    t = []
    if lock_div:
        others = {x: jload(os.path.join(r, "divide", x + ".json")) for x in ALL if x != "LOCK"}
        t = ["| Position | FEN | Depth | Root moves | Total (lock) | Published total | " + " | ".join(x for x in ALL if x != "LOCK") + " |", "|---|---|---|---|---|---|" + "---|" * (len(ALL) - 1)]
        for i, pos in enumerate(lock_div["positions"]):
            cells = []
            for x in ALL:
                if x == "LOCK":
                    continue
                o = others[x]
                if not o or o.get("status") != "DONE":
                    cells.append("not run")
                else:
                    q = o["positions"][i]
                    cells.append("same" if q["divide"] == pos["divide"] and q["total"] == pos["total"] and not q["other_lines"] else "DIFFERS")
            t.append(f"| {pos['name']} | `{pos['fen']}` | {pos['depth']} | {len(pos['divide'])} | {pos['total']} | {pos['published'] if pos['published'] else 'none used'} | " + " | ".join(cells) + " |")
    sec("DIVIDE_TABLE", "Perft divide (every root move compared with the lock's)", "\n".join(t))

    # ---- release checks
    rel_bound = {tag: {k: exe_bound(k, tag) for k in ("pins", "divide", "warm", "soak")} for tag in ALL}
    suite_sha = fuzz.sha256_file(os.path.join(PACK, "suite", "edge_suite.tsv"))

    def edge_bound(tag, e):
        """An edge receipt names the frozen executables, the suite file of the pack and the probe of the build receipt."""
        ok = (bool(e) and bool(exe_sha.get(tag)) and e.get("exe_sha256") == exe_sha[tag] and e.get("lock_exe_sha256") == exe_sha["LOCK"]
              and e.get("suite_sha256") == suite_sha and (tag == "LOCKCOPY" or (bool(probe_sha.get(tag)) and e.get("probe_sha256") == probe_sha[tag])))
        if e and not ok:
            unbound.append(f"edge {tag}")
        return ok

    edge = {tag: jload(os.path.join(r, "edge", tag + ".json")) for tag in ALL}
    edge_ok = {tag: edge_bound(tag, edge[tag]) for tag in ALL}
    t = ["| Tag | Pins | Perft divide | Warm transcript | Threads 2-4 soak | Edge suite |", "|---|---|---|---|---|---|"]
    for tag in ALL:
        row = release.get(tag, {})
        e = edge[tag]
        t.append(f"| {tag} | {row.get('pins', 'not run')} | {row.get('divide', 'not run')} | {row.get('warm', 'not run')} | {row.get('soak', 'not run')} | "
                 f"{e['status'] if e else ('reference' if tag == 'LOCK' else 'not run')} |")
    sec("RELEASE_TABLE", "Release-executable checks per tag", "\n".join(t))

    # ---- edge
    suite = read_tsv(os.path.join(PACK, "suite", "edge_suite.tsv"))
    n_legal = sum(1 for e in suite if e["class"] == "LEGAL")
    n_rej = sum(1 for e in suite if e["class"] == "REJECTED")
    n_unr = sum(1 for e in suite if e["class"] == "UNREACHABLE")
    S["EDGE_SENTENCE"] = (f"The suite has {n_legal} distinct legal positions, {n_rej} positions that `set_fen` rejects and {n_unr} that it accepts "
                          f"although no legal game reaches them.")
    cats = {}
    for e in suite:
        if e["class"] == "LEGAL":
            cats[e["category"]] = cats.get(e["category"], 0) + 1
    made = sum(v for k, v in cats.items() if not k.startswith("mined_"))
    mined = sum(v for k, v in cats.items() if k.startswith("mined_"))
    S["EDGE_CATEGORIES"] = (f"Legal entries by category ({made} from hand-made bases and their colour and file mirrors, {mined} mined from playouts): "
                            + ", ".join(f"{k} {v}" for k, v in sorted(cats.items())) + ". Rejected: "
                            + ", ".join(sorted({e["category"] for e in suite if e["class"] == "REJECTED"})) + ". Unreachable: "
                            + ", ".join(sorted({e["category"] for e in suite if e["class"] == "UNREACHABLE"})) + ".")
    t = ["| Tag | Legal entries | Tier A records identical | Tier R perft blocks identical | Rejected entries handled like the lock (A / R) | "
         "Unreachable entries like the lock (A / R) | Search signature depth, net on / off | Lock against oracle, differences | Result |", "|---|---|---|---|---|---|---|---|---|"]
    for tag in ALL:
        e = edge[tag]
        if not e:
            continue
        ta, ua = e["tier_a_legal"], e.get("tier_a_unreachable")
        t.append(f"| {tag} | {e['legal_entries']} | {ta['status']} {ta.get('records', '')} | {e['tier_r_legal']['status']} {e['tier_r_legal']['perft_blocks']} | "
                 f"{e.get('tier_a_rejected', {}).get('identical_to_lock', 'n/a')} / {e['tier_r_rejected']['identical_to_lock']} | "
                 f"{all(v['identical_to_lock'] for v in ua.values()) if ua else 'n/a'} / {all(v['identical_to_lock'] for v in e['tier_r_unreachable'].values())} | "
                 f"d{e['search_signature']['net_on']['depth']}: {e['search_signature']['net_on']['identical_to_lock']} / {e['search_signature']['net_off']['identical_to_lock']} | "
                 f"{len(e['lock_vs_oracle']['probe_differences']) + len(e['lock_vs_oracle']['exe_differences'])} | {e['status']} |")
    sec("EDGE_TABLE", "Edge suite per tag", "\n".join(t))

    # ---- fuzz
    tied = {}
    for row in uci_rows:
        if row["status"] == "OK" and row.get("tie", "").startswith("lock exe = lock probe"):
            tied.setdefault(row["cand"], set()).add(int(row["chunk"]))
    t = ["| Candidate | Tier A: auxiliary probes, all fields | chunks | in check | quiet | eval net off | eval net on | not OK | Tier R: release exe, go perft 2 | chunks | tied to the lock probe | not OK |",
         "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for c in CANDS:
        a, u = aux.get(c, EMPTY), uci.get(c, EMPTY)
        t.append(f"| {c} | {a['positions']:,} | {len(a['ok'])} | {a['in_check']:,} | {a['positions'] - a['in_check']:,} | {a['positions']:,} | {a['positions']:,} | {len(a['bad'])} | "
                 f"{u['positions']:,} | {len(u['ok'])} | {len(tied.get(c, ()))} | {len(u['bad'])} |")
    t.append("\nEvery tier A record holds the static eval with the net off and with the net on, so the eval coverage by mode equals the tier A count in both modes.")
    hs = sorted({h for c in CANDS for h in aux.get(c, EMPTY)["harness"]})
    foreign = sum(aux.get(c, EMPTY)["foreign"] + uci.get(c, EMPTY)["foreign"] for c in CANDS) + len(warm_all) - len(warm_rows)
    t.append(f"\nA row is counted only if it names the frozen executables or the probes of the build receipts; rows that do not: {foreign}. "
             f"The tier A rows also carry the sha256 of the six harness files together (mgprobe.cpp, mg_format.py, mg_compare.py, uci_session.py, "
             f"fuzz.py, pinguard3.py): {', '.join('`' + h + '`' for h in hs) or 'none'}. When this report was generated those files had the hash "
             f"`{harness_now}`, which is {'the same' if hs == [harness_now] else '**NOT the same**'}. The rows of the release-executable ledger carry the "
             f"executable, input and output hashes but not this one; they were written in the same hours by the same files.")
    sec("FUZZ_TABLE", "Fuzz, completed position comparisons (harness 2)", "\n".join(t))
    kdir = os.path.join(r, "fuzz_aux")
    keys = [jload(os.path.join(kdir, n)) for n in sorted(os.listdir(kdir)) if n.startswith("KEYS_")] if os.path.isdir(kdir) else []
    S["CORPUS_SENTENCES"] = "\n\n".join(
        f"Corpus {', '.join(k['parts'])}: {k['positions']:,} visited positions, {k['distinct_keys']:,} distinct by 64-bit position key and {k['repeated']:,} repeats; "
        f"{k['quiet']:,} quiet and {k['in_check']:,} in check, of which {k['double_check']:,} in double check; {k['mates']:,} checkmates and {k['stalemates']:,} stalemates; "
        f"{k['playouts']:,} playouts; moves played: {k['captures']:,} captures, {k['promotions']:,} promotions, {k['castles']:,} castlings, {k['en_passants']:,} en passant "
        f"captures, {k['checks_given']:,} checks; {k['rejected_seeds']} seeds rejected." for k in keys) or "The distinct-position count of the corpus has not been run."
    t = ["| Candidate | Tier A positions | not OK | Tier R positions | not OK |", "|---|---|---|---|---|"]
    for c in CANDS:
        a, u = h1_aux.get(c, EMPTY), h1_uci.get(c, EMPTY)
        t.append(f"| {c} | {a['positions']:,} | {len(a['bad'])} | {u['positions']:,} | {len(u['bad'])} |")
    sec("H1_TABLE", "Earlier run with harness 1 (same corpus, fewer recorded fields; not added to the counts)", "\n".join(t))
    t = ["| Candidate | never cleared: chunks OK | cleared before every playout: chunks OK | positions per chunk | not OK |", "|---|---|---|---|---|"]
    for c in CANDS:
        rows = [w for w in warm_rows if w["cand"] == c]
        t.append(f"| {c} | {len({w['chunk'] for w in rows if w['variant'] == 'never_cleared' and w['status'] == 'OK'})} | "
                 f"{len({w['chunk'] for w in rows if w['variant'] == 'cleared_before_every_playout' and w['status'] == 'OK'})} | 100,000 | {sum(1 for w in rows if w['status'] != 'OK')} |")
    if warm_rows:
        ch = sorted({int(w["chunk"]) for w in warm_rows})
        t.append(f"\nChunks replayed: {', '.join(str(k) for k in ch)}. `never cleared` removes every cache-clear mark of the chunk, so every evaluation after the "
                 f"first meets a warm pawn cache; `cleared before every playout` starts every playout cold. To reproduce a row, the whole chunk is replayed in order "
                 f"(`README.md`): the state depends on the sequence, not on one FEN.")
    sec("VARIANTS_TABLE", "Cache-state variants (tier A, not counted in the fuzz total)", "\n".join(t) if warm_rows else "The cache-state variants have not been run.")

    # ---- supplementary
    def supp_bound(name, tag, x, **want):
        """A supplementary receipt names the frozen executable or the probe of the build receipt in the given fields."""
        ok = bool(x) and all(bool(v) and x.get(k) == v for k, v in want.items())
        if x and not ok:
            unbound.append(f"{name} {tag}")
        return ok

    other = "made with other binaries, not counted"
    sdir = os.path.join(r, "search_sig")
    t = ["| Candidate | net on | net off | positions | depth | exit codes |", "|---|---|---|---|---|---|"]
    sig_diffs = []
    for c in CANDS:
        on, off = jload(os.path.join(sdir, f"{c}_neton.json")), jload(os.path.join(sdir, f"{c}_netoff.json"))
        if on and off and all(supp_bound("search signature", c, x, exe_sha256=exe_sha[c], lock_exe_sha256=exe_sha["LOCK"]) for x in (on, off)):
            t.append(f"| {c} | {'identical' if on['identical_to_lock'] else 'DIFFERS'} | {'identical' if off['identical_to_lock'] else 'DIFFERS'} | {on['positions']:,} | {on['depth']} | "
                     f"{on['exit']} / {off['exit']} |")
            sig_diffs += [f"{c} net {x['net']}: {x['first_difference']}" for x in (on, off) if not x["identical_to_lock"]]
            sig_diffs += [f"{c} net {x['net']}: the executable ended with exit code {x['exit']}" for x in (on, off) if x["exit"] != 0]
        else:
            t.append(f"| {c} | {other if on and off else 'not run'} | | | | |")
    sec("SEARCHSIG_TABLE", "Search signatures on corpus positions (release exe, supplementary)", "\n".join(t)
        + "\n\nOne process per run, Threads 1, Hash 16, every info line and bestmove of `go depth` compared; tables kept between positions and reset every 500.")
    cdir = os.path.join(r, "crosstier")
    t = ["| Tag | Positions | Identical lists | Result |", "|---|---|---|---|"]
    cross = {}
    for tag in ["LOCK", "LOCKEQ"] + CANDS:
        x = jload(os.path.join(cdir, tag + ".json"))
        cross[tag] = x if supp_bound("cross-tier", tag, x, probe_sha256=probe_sha.get(tag), exe_sha256=exe_sha.get(tag)) else None
        t.append(f"| {tag} | {x['positions']:,} | {x['identical_lists']:,} | {x['status']} |" if cross[tag] else f"| {tag} | {other if x else 'not run'} | | |")
    sec("CROSSTIER_TABLE", "Cross-tier: a probe's legal list equals its own release exe's go perft 1 list", "\n".join(t))
    vdir = os.path.join(r, "coverage")
    t = ["| Candidate | Switch | Instrumented lines in the `#if` region | Executed | Highest count | Never executed |", "|---|---|---|---|---|---|"]
    cov_inputs = ""
    for c in CANDS:
        x = jload(os.path.join(vdir, c + ".json"))
        if x and not cov_inputs:
            cov_inputs = "Inputs of the coverage runs: " + "; ".join(i["input"] for i in x["inputs"]) + "."
        for sw, e in (x or {}).get("switches", {}).items():
            t.append(f"| {c} | {sw} | {e['instrumented_lines']} | {e['executed_lines']} | {e['max_count']:,} | {len(e['never_executed'])} |")
    sec("COVERAGE_TABLE", "Do the test inputs execute the changed lines? (coverage builds of the unchanged source)", "\n".join(t) + ("\n\n" + cov_inputs if cov_inputs else ""))
    wdir = os.path.join(r, "wnp_targets")
    t = ["| Tag | Targets | Decisive for the lock | Identical records | Result |", "|---|---|---|---|---|"]
    extra = []
    wnp = {}
    if os.path.isdir(wdir):
        for tag in ["LOCKEQ"] + CANDS:
            x = jload(os.path.join(wdir, tag + ".json"))
            wnp[tag] = x if supp_bound("WITNESS_NOPIN targets", tag, x, probe_sha256=probe_sha.get(tag), lock_probe_sha256=probe_sha["LOCK"]) else None
            if x:
                t.append(f"| {tag} | {x['targets']:,} | {x['decisive_for_the_lock']:,} | {x['positions_identical']:,} | {x['status']} |" if wnp[tag]
                         else f"| {tag} | {other} | | | |")
        for name in sorted(os.listdir(wdir)):
            if name.startswith("SCAN_"):
                s = jload(os.path.join(wdir, name))
                extra.append(f"For comparison, fuzz chunks {s['chunks']} of seeds {s['seeds']} ({s['positions']:,} positions) contain {s['stalemates']} stalemates, "
                             f"{s['stalemates_with_a_generated_pawn_push']} of them with a generated pawn push, that is decisive for WITNESS_NOPIN.")
    sec("WNP_TABLE", "WITNESS_NOPIN targets (constructed stalemates with a pinned pawn push; reported on their own)", "\n".join(t) + ("\n\n" + " ".join(extra) if extra else ""))
    pdir = os.path.join(r, "replay")
    reps = [jload(os.path.join(pdir, n)) for n in sorted(os.listdir(pdir)) if n.endswith(".json")] if os.path.isdir(pdir) else []
    t = ["| Tier | Candidate | Chunk | Seeds | Row written | Replayed | Result | Hashes equal to the ledger row |", "|---|---|---|---|---|---|---|---|"]
    for x in reps:
        t.append(f"| {'A' if x['tier'] == 'aux' else 'R'} | {x['cand']} | {x['chunk']} | {x['seeds']} | {x['row_written'][11:19]} | {x['when'][11:19]} | {x['status']} | "
                 f"{sum(x['equal_to_the_row'].values())} of {len(x['equal_to_the_row'])} |")
    sec("REPLAY_TABLE", "Counted ledger rows run again from their definition", "\n".join(t) if reps else "No ledger row has been replayed.")

    # ---- verdicts
    verdicts = {}
    for c in CANDS:
        row = release.get(c, {})
        e = edge[c]
        a, u = aux.get(c, EMPTY), uci.get(c, EMPTY)
        wrows = [w for w in warm_rows if w["cand"] == c]
        variants_ok = [sum(1 for w in wrows if w["variant"] == v and w["status"] == "OK") for v in ("never_cleared", "cleared_before_every_playout")]
        gates = {
            "identity": inputs.get(c, {}).get("status") == "OK" and inputs.get("LOCK", {}).get("status") == "OK",
            "self_test": selftest_passed(selftest_line),
            "pins": str(row.get("pins", "")).startswith("MATCH 13/13") and rel_bound[c]["pins"],
            "divide": str(row.get("divide", "")).startswith("MATCH") and rel_bound[c]["divide"],
            "edge_suite": bool(e) and edge_ok[c] and e["status"] == "MATCH" and e["tier_a_legal"]["status"] == "EQUAL" and e["tier_r_legal"]["status"] == "EQUAL",
            "warm_transcript": str(row.get("warm", "")).startswith("MATCH") and rel_bound[c]["warm"],
            "threads_soak": str(row.get("soak", "")).startswith("STABLE") and rel_bound[c]["soak"],
            "fuzz_tier_a_20M": tier_a_gate(a, harness_now),
            "fuzz_tier_r_clean": not u["bad"] and u["positions"] > 0,
            "cache_state_variants": all(variants_ok) and all(w["status"] == "OK" for w in wrows) and {w["harness_sha256"] for w in wrows} == {harness_now},
            "probe_tied_to_exe": bool(cross.get(c)) and cross[c]["status"] == "MATCH" and bool(cross.get("LOCK")) and cross["LOCK"]["status"] == "MATCH",
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
        differences += [f"cache-state variant chunk {w['chunk']} {w['variant']}: {w['status']}: {w['detail'][:200]}" for w in wrows if w["status"] in ("MISMATCH", "CRASH")]
        differences += [f"search signature {x}" for x in sig_diffs if x.startswith(c + " ")]
        wt = wnp.get(c)
        if wt and wt["status"] != "MATCH":
            differences.append(f"WITNESS_NOPIN targets: {wt['status']}: {wt['detail'][:200]}")
        ct = cross.get(c)
        if ct and ct["status"] != "MATCH":
            differences.append(f"cross-tier: the probe and the release exe of {c} list different moves at index {ct['first_difference_index']}")
        differences += [f"replay of tier {'A' if x['tier'] == 'aux' else 'R'} chunk {x['chunk']}: {x['status']} ({x['comparison']})"
                        for x in reps if x["cand"] == c and x["status"] != "REPRODUCED"]
        verdict = verdict_of(gates, differences)
        verdicts[c] = {"name": NAMES[c], "verdict": verdict, "gates": gates, "open_gates": [g for g, ok in gates.items() if not ok],
                       "differences": differences, "tier_a_completed": a["positions"], "tier_a_in_check": a["in_check"],
                       "tier_r_completed": u["positions"], "robustness_differences": (e or {}).get("robustness_differences", []),
                       "wnp_targets": (wt or {}).get("status", "not run"),
                       "harness_errors": [f"tier A chunk {k}: {s}" for k, s, _ in a["bad"] if s not in ("MISMATCH", "CRASH")]
                       + [f"tier R chunk {k}: {s}" for k, s, _ in u["bad"] if s not in ("MISMATCH", "CRASH")]}
    vt = ["| Candidate | Verdict | Tier A comparisons completed (all fields) | Tier R comparisons completed (move lists) | Open gates | Differences |", "|---|---|---|---|---|---|"]
    for c, v in verdicts.items():
        vt.append(f"| {c}: {v['name']} | **{v['verdict']}** | {v['tier_a_completed']:,} | {v['tier_r_completed']:,} | "
                  f"{', '.join(GATE_TEXT[g] for g in v['open_gates']) or 'none'} | {len(v['differences'])} |")
    S["VERDICT_TABLE"] = "\n".join(vt)
    order.insert(0, ("Verdict per candidate (derived from the receipts and ledgers)", "VERDICT_TABLE"))

    # ---- sentences of the recap
    all_diffs = [f"{c}: {d}" for c, v in verdicts.items() for d in v["differences"]]
    robust = [f"{c}: {d}" for c, v in verdicts.items() for d in v["robustness_differences"]]
    by = {}
    for c, v in verdicts.items():
        by.setdefault(v["verdict"], []).append(c)
    if not all_diffs:
        S["FINDING_SENTENCE"] = ("In every check that ran, each of the six candidates behaved exactly like the lock: no difference in any compared field, "
                                 "on either tier." + ("" if not fails else " (Failure folders exist; see section 9.)"))
    else:
        S["FINDING_SENTENCE"] = f"{len(all_diffs)} differences were reported and are listed in section 9; each needs to be reproduced and isolated before it is a FAIL."
    S["VERDICT_SENTENCE"] = " ".join(f"{k}: {', '.join(x)}." for k, x in by.items())
    min_a = min((v["tier_a_completed"] for v in verdicts.values()), default=0)
    min_r = min((v["tier_r_completed"] for v in verdicts.values()), default=0)
    max_r = max((v["tier_r_completed"] for v in verdicts.values()), default=0)
    done_tags = lambda key: [x for x in ALL if str(release.get(x, {}).get(key, "")).startswith(("MATCH", "STABLE")) and rel_bound[x][key]]  # noqa: E731
    edge_done = [x for x in ALL if edge_ok[x] and edge[x].get("status") == "MATCH"]
    e0 = edge[CANDS[0]] or {}
    w0 = wnp.get("WNP") or {}
    S["COMPLETED_LIST"] = "\n".join([
        f"- Harness self-test: `{selftest_line}`, after red runs against comparators that cannot fail.",
        f"- Pins, 13 per executable: matched by {len(done_tags('pins'))} of {len(ALL)} executables (the lock, its copy, the lock-equivalent and the six candidates).",
        f"- Perft divide, ten runs on eight positions, every root move: equal to the lock for {len(done_tags('divide')) - 1} of {len(ALL) - 1} compared executables.",
        f"- Edge suite: {n_legal} legal positions, {n_rej} rejected, {n_unr} unreachable; {e0.get('tier_a_legal', {}).get('records', 0):,} probe records and "
        f"{e0.get('tier_r_legal', {}).get('perft_blocks', 0):,} release-exe perft blocks per tag; matching for {len(edge_done)} of {len(ALL) - 1} compared tags.",
        f"- Warm-state transcript: identical for {len(done_tags('warm')) - 1} of {len(ALL) - 1} compared executables. Threads 2-4 soak: stable for {len(done_tags('soak'))} of {len(ALL)}.",
        f"- Fuzz, auxiliary tier: at least {min_a:,} completed position comparisons per candidate, every field, both net modes.",
        f"- Fuzz, release executables: between {min_r:,} and {max_r:,} completed `go perft 2` comparisons per candidate, each chunk tied to the lock probe.",
        f"- Supplementary: cache-state variants, line coverage of every candidate's changed lines, {w0.get('targets', 0):,} constructed WITNESS_NOPIN targets, "
        f"search signatures on corpus positions, probe-against-executable move lists.",
    ])
    remains = []
    for c, v in verdicts.items():
        if v["open_gates"]:
            remains.append(f"- {c} is {v['verdict']}: open are {', '.join(GATE_TEXT[g] for g in v['open_gates'])}. Tier A stands at {v['tier_a_completed']:,} of {TARGET:,}. "
                           f"Next commands: `fuzz.py aux v1 0-99`, `fuzz.py aux v2 100-199`, then `report.py` (see `STATUS.md`).")
    if min_r < TARGET:
        remains.append(f"- The release-executable fuzz stands at {min_r:,} to {max_r:,} per candidate. Decision D2 does not require 20,000,000 there; "
                       f"to continue: `fuzz.py uci v1 0-99` and `fuzz.py uci v2 100-199` (finished chunks are skipped).")
    remains.append("- Checkers and static eval on the release executables themselves: not observable. Reading them there would need a debug command in the engine source, "
                   "that is a source change and new builds, which only Couns can approve. This job did not ask for it because decision D1 accepts the auxiliary probes.")
    if robust:
        remains.append(f"- Robustness differences on rejected or unreachable positions (not legal-position evidence): {'; '.join(robust)[:600]}.")
    remains.append("- The limits in section 10 apply to every PASS.")
    S["REMAINS_LIST"] = "\n".join(remains)
    S["SELFTEST_LINE"] = f"Result of the last run: `{selftest_line}` (`evidence/selftest/{selftest_name}`)."
    S["SELFTEST_RUNS"] = "\n".join(["| Log in `evidence/selftest/` | Written | Last line |", "|---|---|---|"] + [
        f"| `{name}` | {time.strftime('%H:%M:%S', time.gmtime(when + 3600))} | {line} |" for when, name, line in st_runs])
    S["BINDING_SENTENCE"] = ("Every receipt and ledger row used below names the executable or probe hashes of this table; a receipt or row that names another "
                             "binary is not counted. Such receipts: " + (", ".join(unbound) if unbound else "none") + f"; such ledger rows: {foreign}.")
    S["FIRST_MISMATCH"] = ("None. No check reported a difference, so there is no first offending FEN, field or replay to give." if not all_diffs
                           else "Reported differences (to be reproduced and isolated):\n\n" + "\n".join("- " + d for d in all_diffs))
    S["FAIL_FOLDERS"] = ("The failure folder `out\\job3\\fail` is empty: no run ever wrote failure evidence." if not fails
                         else "Failure folders under `out\\job3\\fail`: " + ", ".join(fails) + ".")
    S["WRITTEN"] = fuzz.now()

    with open(os.path.join(EV, "TABLES.md"), "w", encoding="ascii", errors="replace", newline="\n") as f:
        f.write("# Tables of job 3, generated by harness/report.py at " + fuzz.now() + "\n\nEvery number is read from a receipt or a ledger; nothing is measured here.\n")
        for title, key in order:
            f.write(f"\n## {title}\n\n{S[key]}\n")
        f.write(f"\n## Corpus\n\n{S['CORPUS_SENTENCES']}\n\n## Edge suite composition\n\n{S['EDGE_SENTENCE']} {S['EDGE_CATEGORIES']}\n")
    with open(os.path.join(EV, "VERDICTS.json"), "w", encoding="ascii", newline="\n") as f:
        json.dump({"written": fuzz.now(), "self_test": selftest_line, "self_test_log": selftest_name, "target": TARGET, "harness_sha256_now": harness_now,
                   "receipts_naming_other_binaries": unbound, "ledger_rows_naming_other_binaries": foreign, "verdicts": verdicts, "failure_folders": fails}, f, indent=1)
    template = open(os.path.join(PACK, "harness", "proof_template.md"), "r", encoding="ascii").read()
    missing = []
    for key in sorted(set(x.split("}}")[0] for x in template.split("{{")[1:])):
        if key not in S:
            missing.append(key)
        template = template.replace("{{" + key + "}}", S.get(key, f"(not available: {key})"))
    with open(os.path.join(PACK, "PROOF.md"), "w", encoding="ascii", errors="replace", newline="\n") as f:
        f.write(template)
    print("self-test: " + selftest_line)
    for c, v in verdicts.items():
        print(f"{c}: {v['verdict']} | tier A {v['tier_a_completed']:,} | tier R {v['tier_r_completed']:,} | open: {', '.join(v['open_gates']) or 'none'} | differences: {len(v['differences'])}")
    print(f"failure folders: {len(fails)}; template keys without a value: {missing or 'none'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
