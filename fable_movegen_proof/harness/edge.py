"""edge.py - build, validate and run the curated edge suite of job 3 (standard library only).

  build            bases + colour and file mirrors + positions mined from playouts; every entry's predicate is
                   checked by the independent oracle and every LEGAL entry must be accepted by the lock probe;
                   writes suite\\edge_suite.tsv and suite\\edge_expected.tsv, prints the coverage table
  run TAG...       all applicable fields of every entry, each tag against the lock:
                   tier A (auxiliary probes): moves, order, checkers, has_legal_move, eval, for every entry and
                     every child reached by one made move;
                   tier R (release executables): go perft 1 and go perft 2 on every entry, go perft 1 on every
                     child reached by `position fen <entry> moves <m>`;
                   rejected entries: the engine's refusal text and the unchanged board, compared explicitly;
                   unreachable entries: one process per entry, outputs and exit codes compared;
                   search signature (supplementary): go depth 12 with the net on and off, every info line;
                   three-way: the lock's move set and checkers against the oracle's.
  summary          one line per tag from the receipts

Classes: LEGAL (counts as legal-position evidence), REJECTED (set_fen refuses it) and UNREACHABLE (set_fen
accepts it but no legal game reaches it). Only LEGAL entries are legal coverage; a difference on the other two
is reported as a robustness difference.
"""
import hashlib
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chess_oracle as oracle  # noqa: E402
import edge_bases  # noqa: E402
import fuzz  # noqa: E402
import mg_compare  # noqa: E402
import mg_format  # noqa: E402
import pinguard3  # noqa: E402
import uci_session  # noqa: E402

OUT = fuzz.OUT
PACK = fuzz.PACK
SUITE = os.path.join(PACK, "suite", "edge_suite.tsv")
EXPECTED = os.path.join(PACK, "suite", "edge_expected.tsv")
MOVE_KEYS = {"has", "no", "pseudo", "gives_check", "no_check", "discovered", "double_after", "promos"}
STRIP_RX = re.compile(r" (nps|time) \d+")
SEARCH_DEPTH = 12
REQUIRED = ["check_knight", "check_pawn", "check_slider", "double_check", "double_check_given", "discovered_check",
            "pinned_evasion", "ep_removes_checker", "ep_illegal_rank_pin", "ep_illegal_diagonal_pin", "ep_discovered_check",
            "promotion_push", "promotion_capture", "promotion_gives_check", "underpromotion_check", "promotion_in_check",
            "castling_legal", "castling_through_attack", "castling_into_attack", "castling_out_of_check", "castling_blocked",
            "castling_gives_check", "high_move_count", "stalemate", "checkmate"]


def map_square(s, kind):
    f, r = s[0], s[1]
    if "c" in kind:
        r = str(9 - int(r))
    if "f" in kind:
        f = oracle.FILES[7 - oracle.FILES.index(f)]
    return f + r


def mirror_predicate(pred, kind):
    out = []
    for atom in pred.split(";"):
        key, eq, val = atom.partition("=")
        if key in MOVE_KEYS:
            val = map_square(val[:2], kind) + map_square(val[2:4], kind) + val[4:]
        out.append(key + eq + val)
    return ";".join(out)


def popcount(x):
    return bin(x).count("1")


# ---------------------------------------------------------------- mining positions from playouts
def mine(per_category=8):
    """Positions with rare properties, taken from a chunk of playouts that is not part of the fuzz corpus.
    The lock probe finds them, the oracle rebuilds the FEN from the path and checks the property itself."""
    chunk = 9003
    path, _ = fuzz.gen_chunk("v1", chunk, 100000)
    tr, err, code = fuzz.run_probe([fuzz.probe("LOCK"), "run", "--null", "0"], path)
    if code != 0:
        raise SystemExit(f"mining: lock probe failed: {err[-200:]}")
    playouts = mg_format.parse_path(path.decode("ascii"))
    picks, used = {}, set()
    high = []

    def take(cat, d, pred):
        lst = picks.setdefault(cat, [])
        if len(lst) < per_category and d["key"] not in used:
            used.add(d["key"])
            lst.append((d["playout"], d["ply"], pred))

    for o, n in mg_format.frames(tr)[:-1]:
        d = mg_format.decode(tr[o:o + n])
        if d["kind"] != 0:
            continue
        ck = d["checkers_main"]
        nck = popcount(ck)
        allm, bits = d["all"], d["bits"]
        legal_i = [i for i, b in enumerate(bits) if b & 1]
        flags = [(m >> 24) & 0xFF for m in allm]
        if nck == 2:
            take("mined_double_check", d, "checkers=2")
        if not legal_i:
            take("mined_checkmate" if ck else "mined_stalemate", d, "mate" if ck else "stalemate")
            continue
        ep_legal = [i for i in legal_i if flags[i] & 16]
        ep_gen = [i for i in range(len(allm)) if flags[i] & 16]
        if ep_legal and not ck:
            take("mined_ep_legal", d, "ep_legal;checkers=0")
        if ep_gen and not ep_legal:
            take("mined_ep_illegal", d, "ep_illegal")
        if ep_legal and nck == 1:
            take("mined_ep_in_check", d, "checkers=1;ep_legal")
        for i in legal_i:
            m, fl, text = allm[i], flags[i], mg_format.uci(allm[i])
            to = (m >> 8) & 0xFF
            child = d["child_main"][i]
            gives = bool(bits[i] & 2)
            if fl & 32 and nck == 1:
                take("mined_promotion_in_check", d, f"checkers=1;has={text}")
            if fl & 32 and gives:
                take("mined_promotion_gives_check", d, f"gives_check={text}")
            if fl & 12 and gives:
                take("mined_castle_gives_check", d, f"gives_check={text}")
            if gives and not fl & (12 | 16 | 32) and not (child >> to) & 1:
                take("mined_discovered_check", d, f"discovered={text}")
            if popcount(child) == 2:
                take("mined_double_check_given", d, f"double_after={text}")
        for i in range(len(allm)):
            if flags[i] & 12 and not bits[i] & 1:
                take("mined_castle_attacked", d, "nocastle=" + ("K" if flags[i] & 4 else "Q"))
            if nck == 1 and not bits[i] & 1 and (ck >> ((allm[i] >> 8) & 0xFF)) & 1:
                picks.setdefault("mined_pinned_capture_of_checker", [])
                if len(picks["mined_pinned_capture_of_checker"]) < 3 * per_category and d["key"] not in used:
                    used.add(d["key"])
                    t = mg_format.uci(allm[i])
                    picks["mined_pinned_capture_of_checker"].append((d["playout"], d["ply"], f"checkers=1;pseudo={t};no={t}"))
        if len(legal_i) >= 55:
            high.append((len(legal_i), d["playout"], d["ply"], d["key"]))
    high.sort(reverse=True)
    seen = set()
    for cnt, pl, ply, key in high:
        if key not in seen and key not in used and len(picks.setdefault("mined_high_move_count", [])) < per_category:
            seen.add(key)
            picks["mined_high_move_count"].append((pl, ply, f"legal={cnt}"))

    entries, problems = [], []
    for cat in sorted(picks):
        kept = 0
        for pl, ply, pred in picks[cat]:
            seed, moves = playouts[pl]
            p = oracle.parse_fen(seed)
            ok = True
            for mv in moves[:ply]:
                m = oracle.find(p, mv, oracle.legal(p))
                if m is None:
                    problems.append(f"{cat}: the oracle does not have the path move {mv} at {oracle.fen(p)} (lock and oracle disagree)")
                    ok = False
                    break
                p = oracle.make(p, m)
            if not ok:
                continue
            f = oracle.fen(p)
            if cat == "mined_pinned_capture_of_checker":
                mv = pred.split("pseudo=")[1].split(";")[0]
                if p.b[oracle.sq(mv[:2])].upper() == "K" or kept >= per_category:
                    continue                       # a king taking a protected checker is not a pinned defender
            good, failed = oracle.check_predicate(f, pred)
            if not good:
                problems.append(f"{cat}: the oracle does not confirm {failed} at {f} (lock-derived label)")
                continue
            kept += 1
            entries.append({"id": f"{cat}_{kept:02d}", "class": "LEGAL", "category": cat, "predicate": pred, "fen": f,
                            "provenance": f"mined from playouts: seeds v1, chunk {chunk}, master {fuzz.MASTER}, playout {pl} ply {ply}: "
                                          f"position fen {seed}" + (" moves " + " ".join(moves[:ply]) if ply else ""),
                            "derived": ""})
    return entries, problems


# ---------------------------------------------------------------- build
def build():
    pinguard3.ensure()
    entries, problems, seen = [], [], set()
    for bid, cat, pred, f, prov in edge_bases.LEGAL:
        variants = [("", bid, f, pred, "")]
        variants.append(("c", bid + "_cm", oracle.colour_mirror(f), mirror_predicate(pred, "c"), f"colour mirror of {bid}"))
        fm = oracle.file_mirror(f)
        if fm is not None:
            variants.append(("f", bid + "_fm", fm, mirror_predicate(pred, "f"), f"file mirror of {bid}"))
            variants.append(("fc", bid + "_fcm", oracle.colour_mirror(fm), mirror_predicate(pred, "fc"), f"file and colour mirror of {bid}"))
        for kind, eid, fen_text, p2, derived in variants:
            if fen_text in seen:
                continue                       # a symmetric position mirrors onto itself: counted once
            try:
                pos = oracle.parse_fen(fen_text)
                bad = oracle.static_problem(pos)
                good, failed = (False, [bad]) if bad else oracle.check_predicate(fen_text, p2)
            except (ValueError, IndexError) as e:
                good, failed = False, [f"{type(e).__name__}: {e}"]
            if not good:
                problems.append(f"{eid}: predicate fails {failed} for {fen_text}")
                continue
            seen.add(fen_text)
            entries.append({"id": eid, "class": "LEGAL", "category": cat, "predicate": p2, "fen": fen_text, "provenance": prov, "derived": derived})
    mined, mproblems = mine()
    problems += mproblems
    for e in mined:
        if e["fen"] not in seen:
            seen.add(e["fen"])
            entries.append(e)
    legal_entries = [e for e in entries if e["class"] == "LEGAL"]
    # every LEGAL entry must be accepted by the lock, and the lock's move set and checkers must be the oracle's
    path = "".join(f"P {i} X0 0 {e['fen']}\nM\n" for i, e in enumerate(legal_entries)).encode("ascii")
    tr, err, code = fuzz.run_probe([fuzz.probe("LOCK"), "run"], path)
    recs = [mg_format.decode(tr[o:o + n]) for o, n in mg_format.frames(tr)[1:-1]]
    expected_rows = []
    for e, d in zip(legal_entries, recs):
        pos = oracle.parse_fen(e["fen"])
        om = sorted(oracle.uci(m) for m in oracle.legal(pos))
        oc = [oracle.name(s) for s in oracle.checkers(pos)]
        e["moves"] = om
        expected_rows.append((e["id"], len(om), " ".join(om), " ".join(oc) or "-"))
        if d["kind"] == 2:
            problems.append(f"{e['id']}: the lock REJECTS this entry ({d['error']}): {e['fen']}")
            continue
        lm = sorted(mg_format.ucis(d["legal"]))
        lc = mg_format.squares(d["checkers_main"])
        if lm != om:
            problems.append(f"{e['id']}: lock and oracle move sets differ at {e['fen']}: lock only {sorted(set(lm) - set(om))}, oracle only {sorted(set(om) - set(lm))}")
        if lc != oc:
            problems.append(f"{e['id']}: lock and oracle checkers differ at {e['fen']}: lock {lc}, oracle {oc}")
    for bid, cat, expect, f, prov in edge_bases.REJECTED:
        entries.append({"id": bid, "class": "REJECTED", "category": cat, "predicate": expect, "fen": f, "provenance": prov, "derived": ""})
    for bid, cat, why, f, prov in edge_bases.UNREACHABLE:
        entries.append({"id": bid, "class": "UNREACHABLE", "category": cat, "predicate": why, "fen": f, "provenance": prov, "derived": ""})
    counts = {}
    for e in legal_entries:
        counts[e["category"]] = counts.get(e["category"], 0) + 1
    missing = [c for c in REQUIRED if counts.get(c, 0) == 0]
    print(f"LEGAL entries: {len(legal_entries)} distinct FENs; REJECTED {len(edge_bases.REJECTED)}; UNREACHABLE {len(edge_bases.UNREACHABLE)}")
    for c in sorted(counts):
        print(f"  {c:38} {counts[c]}")
    for p in problems:
        print("PROBLEM " + p)
    if missing:
        print("PROBLEM required categories without an entry: " + ", ".join(missing))
    if len(legal_entries) < 300:
        print(f"PROBLEM only {len(legal_entries)} legal entries, at least 300 are required")
    if problems or missing or len(legal_entries) < 300:
        print("BUILD FAILED: nothing written")
        return 3
    os.makedirs(os.path.dirname(SUITE), exist_ok=True)
    with open(SUITE, "w", encoding="ascii", newline="\n") as f:
        f.write("id\tclass\tcategory\tpredicate_or_expected\tfen\tprovenance\tderived\n")
        for e in entries:
            f.write("\t".join([e["id"], e["class"], e["category"], e["predicate"], e["fen"], e["provenance"], e["derived"]]) + "\n")
    with open(EXPECTED, "w", encoding="ascii", newline="\n") as f:
        f.write("id\toracle_legal_count\toracle_legal_moves_sorted\toracle_checkers\n")
        for row in expected_rows:
            f.write("\t".join(str(x) for x in row) + "\n")
    print(f"written {SUITE} sha256 {fuzz.sha256_file(SUITE)}")
    print(f"written {EXPECTED} sha256 {fuzz.sha256_file(EXPECTED)}")
    print("BUILD OK")
    return 0


def load_suite():
    rows = []
    with open(SUITE, "r", encoding="ascii") as f:
        head = f.readline().rstrip("\n").split("\t")
        for ln in f:
            rows.append(dict(zip(head, ln.rstrip("\n").split("\t"))))
    exp = {}
    with open(EXPECTED, "r", encoding="ascii") as f:
        f.readline()
        for ln in f:
            i, n, moves, ck = ln.rstrip("\n").split("\t")
            exp[i] = (int(n), moves.split(), [] if ck == "-" else ck.split())
    return rows, exp


# ---------------------------------------------------------------- run
def lock_run_problem(transcript, exit_code, expect_records=None):
    """Why a run of the LOCK probe on rejected or unreachable entries cannot serve as the reference, or ''.
    A dead lock probe (an error code, no output, a cut output, a missing record) must stop the edge run: without a
    sound reference there is nothing to compare a candidate with."""
    if exit_code != 0:
        return f"the lock probe ended with exit code {exit_code}"
    chk = mg_compare.compare(transcript, transcript, None, expect_tag="LOCK", allow_error_records=True)
    if chk.status != "EQUAL":
        return chk.detail
    n = len(mg_format.frames(transcript)) - 2
    if expect_records is not None and n != expect_records:
        return f"the lock probe wrote {n} records for {expect_records} entries"
    return ""


def tier_a_path(legal, exp):
    lines, roots, pid = ["H edge suite"], {}, 0
    for e in legal:
        lines += [f"P {pid} X0 0 {e['fen']}", "M"]
        roots[pid] = e["id"]
        pid += 1
        for mv in exp[e["id"]][1]:
            lines += [f"P {pid} X0 0 {e['fen']}", f"M {mv}"]
            pid += 1
    return ("\n".join(lines) + "\n").encode("ascii"), roots


def tier_r_lines(legal, exp):
    lines, roots, k = [], {}, 0
    for e in legal:
        lines += [f"position fen {e['fen']}", "go perft 1", f"position fen {e['fen']}", "go perft 2"]
        roots[k] = e["id"]
        k += 2
        for mv in exp[e["id"]][1]:
            lines += [f"position fen {e['fen']} moves {mv}", "go perft 1"]
            k += 1
    return lines, roots


def rejected_batch(rejected, path):
    with open(path, "w", encoding="ascii", newline="\n") as f:
        f.write("\n".join(uci_session.PREAMBLE) + "\n")
        for e in rejected:
            f.write(f"position startpos\nposition fen {e['fen']}\ngo perft 1\nisready\n")
        f.write("quit\n")


def check_rejected_output(text, rejected):
    """The lock's own handling of the rejected entries: refusal text present, board unchanged (start position)."""
    lines = [ln.strip() for ln in text.splitlines()]
    try:
        i = lines.index("readyok") + 1
    except ValueError:
        return ["no handshake"]
    bad = []
    for e in rejected:
        block = []
        while i < len(lines) and lines[i] != "readyok":
            block.append(lines[i])
            i += 1
        i += 1
        refusal = [ln for ln in block if ln.startswith("info string invalid FEN")]
        moves = [ln.split(":")[0] for ln in block if uci_session.MOVE_RX.match(ln)]
        if len(refusal) != 1 or e["predicate_or_expected"].lower() not in refusal[0].lower():
            bad.append(f"{e['id']}: refusal {refusal} does not contain '{e['predicate_or_expected']}'")
        if len(moves) != 20 or moves[0] != "a2a3" or "nodes 20" not in block:
            bad.append(f"{e['id']}: the board after the refusal is not the start position ({len(moves)} moves)")
    return bad


def search_rows(tag, legal, net):
    eng = uci_session.Engine([fuzz.exe(tag)])
    eng.handshake(["Threads=1", "Hash=16", "OwnBook=false", f"UseNNUE={net}"])
    rows = []
    for e in legal:
        eng.send("ucinewgame")
        eng.isready()
        eng.position(e["fen"])
        info, best = eng.go(f"depth {SEARCH_DEPTH}", timeout=3600)
        rows.append([STRIP_RX.sub("", ln) for ln in info] + [best])
    code = eng.close()
    return rows, code


def run(tags):
    pinguard3.ensure()
    fuzz.guard()
    suite, exp = load_suite()
    legal = [e for e in suite if e["class"] == "LEGAL"]
    rejected = [e for e in suite if e["class"] == "REJECTED"]
    unreach = [e for e in suite if e["class"] == "UNREACHABLE"]
    suite_sha = fuzz.sha256_file(SUITE)
    tmp = os.path.join(OUT, "tmp")
    rdir = os.path.join(OUT, "runs", "edge")
    os.makedirs(rdir, exist_ok=True)
    print(f"{fuzz.now()} edge suite {suite_sha[:16]}: {len(legal)} legal, {len(rejected)} rejected, {len(unreach)} unreachable", flush=True)

    # ---- the lock's side, once
    a_path, a_roots = tier_a_path(legal, exp)
    a_sha = fuzz.sha256(a_path)
    a_ref, _, code = fuzz.run_probe([fuzz.probe("LOCK"), "run"], a_path)
    a_check = mg_compare.compare(a_ref, a_ref, expect_tag="LOCK")
    if code != 0 or a_check.status != "EQUAL":
        raise SystemExit(f"edge: the lock probe run is not usable: exit {code}; {a_check.detail}")
    # three-way: the lock's move set and checkers against the oracle
    three_bad, n_three = [], 0
    for o, n in mg_format.frames(a_ref)[:-1]:
        d = mg_format.decode(a_ref[o:o + n])
        if d["kind"] == 0 and d["ply"] == 0 and d["playout"] in a_roots:
            eid = a_roots.pop(d["playout"])
            n_three += 1
            if sorted(mg_format.ucis(d["legal"])) != sorted(exp[eid][1]) or mg_format.squares(d["checkers_main"]) != exp[eid][2]:
                three_bad.append(eid)
    rj_path = ("".join(f"P {i} X0 0 {e['fen']}\nM\n" for i, e in enumerate(rejected))).encode("ascii")
    rj_ref, rj_err, rj_code = fuzz.run_probe([fuzz.probe("LOCK"), "run"], rj_path)
    bad = lock_run_problem(rj_ref, rj_code, len(rejected))
    if bad:
        raise SystemExit(f"edge: the lock probe run on the rejected entries is not usable (harness error, no verdict): {bad}; {rj_err[-200:]}")
    rj_recs = [mg_format.decode(rj_ref[o:o + n]) for o, n in mg_format.frames(rj_ref)[1:-1]]
    rj_bad = [f"{e['id']}: probe record kind {d['kind']} error [{d.get('error', '')}]" for e, d in zip(rejected, rj_recs)
              if d["kind"] != 2 or e["predicate_or_expected"].lower() not in d["error"].lower()]
    un_ref = {}
    for e in unreach:
        out, err, code = fuzz.run_probe([fuzz.probe("LOCK"), "run"], f"P 0 X0 0 {e['fen']}\nM\n".encode("ascii"))
        bad = lock_run_problem(out, code, 1)
        if bad:
            raise SystemExit(f"edge: the lock probe run on the unreachable entry {e['id']} is not usable (harness error, no verdict): {bad}; {err[-200:]}")
        un_ref[e["id"]] = (out, code)

    r_lines, r_roots = tier_r_lines(legal, exp)
    r_in = os.path.join(tmp, "edge_legal.uci")
    r_n = uci_session.write_batch(r_in, r_lines)
    r_in_sha = fuzz.sha256_file(r_in)
    r_ref_file = os.path.join(tmp, "edge_legal.LOCK.out")
    lrun = uci_session.run_batch([fuzz.exe("LOCK")], r_in, r_ref_file, timeout=3600)
    r_ref = open(r_ref_file, "r", encoding="ascii", errors="replace").read()
    r_check = uci_session.compare_perft(r_ref, r_ref, r_n)
    if lrun.status != "OK" or r_check.status != "EQUAL":
        raise SystemExit(f"edge: the lock exe run is not usable: {lrun.status} {lrun.detail}; {r_check.detail}")
    parsed = uci_session.parse_perft_output(r_ref)
    three_r_bad = [eid for k, eid in r_roots.items() if sorted(m for m, _ in parsed.blocks[k].moves) != sorted(exp[eid][1])]
    rj_in = os.path.join(tmp, "edge_rejected.uci")
    rejected_batch(rejected, rj_in)
    rj_ref_file = os.path.join(tmp, "edge_rejected.LOCK.out")
    rj_run = uci_session.run_batch([fuzz.exe("LOCK")], rj_in, rj_ref_file, timeout=600)
    if rj_run.status != "OK":
        raise SystemExit(f"edge: the lock exe run on the rejected entries is not usable (harness error, no verdict): {rj_run.status} {rj_run.detail}")
    rj_ref_text = open(rj_ref_file, "r", encoding="ascii", errors="replace").read()
    rj_r_bad = check_rejected_output(rj_ref_text, rejected)
    un_r_ref = {}
    for e in unreach:
        p = os.path.join(tmp, f"edge_unr_{e['id']}.uci")
        with open(p, "w", encoding="ascii", newline="\n") as f:
            f.write("\n".join(uci_session.PREAMBLE) + f"\nposition fen {e['fen']}\ngo perft 1\ngo perft 2\nisready\nquit\n")
        o = os.path.join(tmp, f"edge_unr_{e['id']}.LOCK.out")
        rr = uci_session.run_batch([fuzz.exe("LOCK")], p, o, timeout=600)
        un_r_ref[e["id"]] = (open(o, "r", encoding="ascii", errors="replace").read(), rr.status, rr.exit_code, p)
    s_ref = {net: search_rows("LOCK", legal, net) for net in ("true", "false")}
    lock_ok = not three_bad and not three_r_bad and not rj_bad and not rj_r_bad
    print(f"{fuzz.now()} lock side done: tier A {a_check.positions} records, tier R {r_n} perft blocks, three-way with the oracle on "
          f"{n_three} entries: probe differences {len(three_bad)}, exe differences {len(three_r_bad)}; rejected handling problems "
          f"{len(rj_bad) + len(rj_r_bad)}", flush=True)
    for x in three_bad + three_r_bad + rj_bad + rj_r_bad:
        print("LOCK-SIDE PROBLEM " + str(x), flush=True)

    code_all = 0
    for tag in tags:
        t0 = time.time()
        rec = {"check": "edge", "tag": tag, "suite_sha256": suite_sha, "legal_entries": len(legal), "rejected_entries": len(rejected),
               "unreachable_entries": len(unreach), "exe_sha256": fuzz.sha256_file(fuzz.exe(tag)), "lock_exe_sha256": fuzz.sha256_file(fuzz.exe("LOCK")),
               "when": fuzz.now(), "lock_vs_oracle": {"entries": n_three, "probe_differences": three_bad, "exe_differences": three_r_bad},
               "lock_rejected_handling_problems": rj_bad + rj_r_bad}
        legal_diff, robust_diff, errors = [], [], []
        has_probe = os.path.exists(fuzz.probe(tag))
        if has_probe:
            rec["probe_sha256"] = fuzz.sha256_file(fuzz.probe(tag))
            tr, cerr, ccode = fuzz.run_probe([fuzz.probe(tag), "run"], a_path)
            ptag = "LOCK" if tag == "LOCKCOPY" else tag          # the copy is the lock probe, byte for byte
            res = mg_compare.compare_bound(a_ref, a_sha, tr, a_sha, a_path.decode("ascii"), expect_tag=ptag)
            rec["tier_a_legal"] = {"status": res.status, "records": res.positions, "exit": ccode, "detail": res.detail[:800]}
            if ccode != 0 or res.status == "MISMATCH":
                legal_diff.append("tier A: " + res.detail[:400] + (f" (probe exit {ccode}: {cerr[-200:]})" if ccode != 0 else ""))
            elif res.status != "EQUAL":
                errors.append("tier A: " + res.detail[:300])
            tr, _, ccode = fuzz.run_probe([fuzz.probe(tag), "run"], rj_path)
            rres = mg_compare.compare(rj_ref, tr, None, expect_tag=ptag, allow_error_records=True)
            same = rres.status == "EQUAL" and ccode == 0
            rec["tier_a_rejected"] = {"identical_to_lock": same, "exit": ccode}
            if not same:
                robust_diff.append("tier A rejected entries: " + rres.detail[:300])
            un = {}
            for e in unreach:
                out, _, ccode = fuzz.run_probe([fuzz.probe(tag), "run"], f"P 0 X0 0 {e['fen']}\nM\n".encode("ascii"))
                ures = mg_compare.compare(un_ref[e["id"]][0], out, None, expect_tag=ptag, allow_error_records=True)
                same = ures.status == "EQUAL" and ccode == un_ref[e["id"]][1]
                un[e["id"]] = {"identical_to_lock": same, "exit": ccode, "lock_exit": un_ref[e["id"]][1]}
                if not same:
                    robust_diff.append(f"tier A unreachable {e['id']}: " + ures.detail[:300])
            rec["tier_a_unreachable"] = un
        else:
            rec["tier_a_legal"] = {"status": "NOT APPLICABLE", "detail": "no auxiliary probe for this tag"}
        # tier R
        r_out = os.path.join(tmp, f"edge_legal.{tag}.out")
        crun = uci_session.run_batch([fuzz.exe(tag)], r_in, r_out, timeout=3600)
        text = open(r_out, "r", encoding="ascii", errors="replace").read()
        res = uci_session.compare_perft_bound(r_ref, r_in_sha, text, r_in_sha, r_n)
        rec["tier_r_legal"] = {"status": res.status, "perft_blocks": res.positions, "run": crun.status, "detail": res.detail[:800]}
        if crun.status not in ("OK",) or res.status == "MISMATCH":
            legal_diff.append(f"tier R: run {crun.status} {crun.detail}; {res.detail[:400]}")
        elif res.status != "EQUAL":
            errors.append("tier R: " + res.detail[:300])
        rj_out = os.path.join(tmp, f"edge_rejected.{tag}.out")
        uci_session.run_batch([fuzz.exe(tag)], rj_in, rj_out, timeout=600)
        rj_text = open(rj_out, "r", encoding="ascii", errors="replace").read()
        rec["tier_r_rejected"] = {"identical_to_lock": rj_text == rj_ref_text, "own_handling_problems": check_rejected_output(rj_text, rejected)}
        if rj_text != rj_ref_text:
            robust_diff.append("tier R rejected entries: output differs from the lock's")
        unr = {}
        for e in unreach:
            ref_text, ref_status, ref_code, p = un_r_ref[e["id"]]
            o = os.path.join(tmp, f"edge_unr_{e['id']}.{tag}.out")
            rr = uci_session.run_batch([fuzz.exe(tag)], p, o, timeout=600)
            t = open(o, "r", encoding="ascii", errors="replace").read()
            same = (t, rr.status, rr.exit_code) == (ref_text, ref_status, ref_code)
            unr[e["id"]] = {"identical_to_lock": same, "run": rr.status, "exit": rr.exit_code, "lock_run": ref_status, "lock_exit": ref_code}
            if not same:
                robust_diff.append(f"tier R unreachable {e['id']}: output or exit differs from the lock's")
            os.remove(o)
        rec["tier_r_unreachable"] = unr
        # search signature (supplementary)
        sig = {}
        for net in ("true", "false"):
            rows, ecode = search_rows(tag, legal, net)
            ref_rows, _ = s_ref[net]
            k = next((i for i, (a, b) in enumerate(zip(ref_rows, rows)) if a != b), None)
            sig["net_" + ("on" if net == "true" else "off")] = {
                "identical_to_lock": rows == ref_rows, "searches": len(rows), "depth": SEARCH_DEPTH, "exit": ecode,
                "first_difference": None if k is None else {"entry": legal[k]["id"], "fen": legal[k]["fen"], "expected": ref_rows[k][-2:], "got": rows[k][-2:]}}
            if rows != ref_rows:
                legal_diff.append(f"search signature net {net}: differs at entry {legal[k]['id'] if k is not None else '?'}")
        rec["search_signature"] = sig
        rec["search_signature_note"] = "supplementary: search output does not stand in for move order, checkers or static eval"
        rec["legal_position_differences"] = legal_diff
        rec["robustness_differences"] = robust_diff
        rec["harness_errors"] = errors
        rec["status"] = ("DIFFERENCE" if legal_diff else "HARNESS_ERROR" if errors or not lock_ok else "MATCH") + (" + ROBUSTNESS DIFFERENCE" if robust_diff else "")
        rec["seconds"] = round(time.time() - t0, 1)
        with open(os.path.join(rdir, tag + ".json"), "w", encoding="ascii", newline="\n") as f:
            json.dump(rec, f, indent=1)
        for p in (r_out, r_out + ".err", rj_out, rj_out + ".err"):
            if os.path.exists(p) and not legal_diff:
                os.remove(p)
        print(f"{fuzz.now()} edge {tag}: {rec['status']} | tier A {rec['tier_a_legal']['status']} {rec['tier_a_legal'].get('records', '')} | "
              f"tier R {rec['tier_r_legal']['status']} {rec['tier_r_legal']['perft_blocks']} | rejected same {rec['tier_r_rejected']['identical_to_lock']} | "
              f"search on/off {sig['net_on']['identical_to_lock']}/{sig['net_off']['identical_to_lock']} | {rec['seconds']} s", flush=True)
        for x in legal_diff + robust_diff + errors:
            print("   " + x, flush=True)
        if legal_diff or errors:
            code_all = 3
    return code_all


def summary():
    rdir = os.path.join(OUT, "runs", "edge")
    for name in sorted(os.listdir(rdir)):
        if name.endswith(".json"):
            r = json.load(open(os.path.join(rdir, name), "r", encoding="ascii"))
            print(f"{r['tag']:8} {r['status']}: {r['legal_entries']} legal entries; tier A {r['tier_a_legal']['status']} {r['tier_a_legal'].get('records', '')}; "
                  f"tier R {r['tier_r_legal']['status']} {r['tier_r_legal']['perft_blocks']} blocks; lock vs oracle differences "
                  f"{len(r['lock_vs_oracle']['probe_differences']) + len(r['lock_vs_oracle']['exe_differences'])}")
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    if argv[1] == "build":
        return build()
    if argv[1] == "run":
        return run(argv[2:])
    if argv[1] == "summary":
        return summary()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
