"""fuzz.py - differential fuzz of job 3 over one shared corpus (standard library only).

The corpus is defined by a seeds file, a master seed, a chunk index and a chunk size; the lock probe turns
these into a path chunk (random and semi-random legal playouts). Nothing of the corpus is stored: a chunk is
regenerated from its definition, and the ledgers keep its sha256.

  seeds  NAME [--edge SUITE.tsv]       compose out\\job3\\corpus\\seeds_NAME.txt and its receipt
  pilot  NAME                          20,000 positions through both tiers on the lock: rates, to plan only
  aux    NAME A-B [--cands X,Y]        tier A: every candidate probe replays chunks A..B against the lock probe
  uci    NAME A-B [--cands X,Y]        tier R: every release exe answers go perft 2 on chunks A..B
  crosstier NAME TAG...                the probe's legal list equals its release exe's go perft 1, per position
  keys   NAME:A-B [NAME:A-B ...]       distinct positions, quiet and in-check counts of the corpus
  count                                totals from the ledgers (only OK rows, one per candidate and chunk)

A file out\\job3\\job3_fuzz.hold makes a running fuzz wait between candidate runs; job3_fuzz.stop makes it
end after the chunk in hand. Both are this job's own files.
"""
import hashlib
import json
import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mg_compare  # noqa: E402
import mg_format  # noqa: E402
import pinguard3  # noqa: E402
import uci_session  # noqa: E402

OUT = r"D:\forge_jobs_20261109\fable2\out\job3"
PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MASTER = "4D47465A20261110"
CHUNK = 100000
CANDS = ["EVL", "PCM", "CKL", "WNP", "KPC", "BUN"]
FLOOR_GIB = 30.3
FENS12K = r"D:\forge_jobs_20261109\fable2\out\base\fens_12k_v2.txt"
START = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"
BENCH = [  # the eight positions of the engine's bench command (src/uci.cpp of the lock)
    START,
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
    "r4rk1/1pp1qppp/p1np1n2/8/2B1P1b1/2N2N2/PPP1QPPP/2KR3R w - - 0 10",
    "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    "r1bq1rk1/pp2bppp/2n1pn2/3p4/2PP4/2N1PN2/PP3PPP/R2QKB1R w KQ - 0 8",
    "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1",
    "6k1/5ppp/8/8/8/8/5PPP/3R2K1 b - - 0 1",
    "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/3PP3/2N1BN2/PPP1BPPP/R2Q1RK1 w - - 0 9",
]
# Edge seeds of corpus part 1 (before the edge suite existed): job 2's 24 targeted positions and the legal
# positions the planning review named. Corpus part 2 takes the whole edge suite instead (--edge).
EDGE_V1 = [
    "8/8/8/8/8/8/8/R2K3k w - - 0 1", "4k3/8/8/8/4P3/8/8/4R1K1 w - - 0 1", "7k/8/8/8/8/2P5/8/B5K1 w - - 0 1",
    "3k4/1P6/8/8/8/8/8/4K3 w - - 0 1", "8/8/8/2k5/3Pp3/8/8/4K3 b - d3 0 1", "4r2k/8/8/8/8/3n4/4Q3/4K3 w - - 0 1",
    "4r2k/8/8/8/1b6/8/4R3/4K3 w - - 0 1", "4k3/8/8/8/8/5n2/6B1/r3K3 w - - 0 1", "6k1/8/8/8/8/8/P4PPP/3r2K1 w - - 0 1",
    "k7/8/8/3b4/8/4b3/6P1/5n1K w - - 0 1", "4k3/8/8/8/4N3/8/8/4R1K1 w - - 0 1", "3k4/8/8/8/8/8/8/R3K3 w Q - 0 1",
    "7k/8/8/3pP3/8/8/8/B5K1 w - d6 0 1", "4k3/4r3/8/8/8/8/4Q3/4RK2 w - - 0 1", "4k3/4p3/8/8/4R3/8/8/4K3 w - - 0 1",
    "4k3/8/8/8/4B3/8/8/4Q1K1 w - - 0 1", "4k3/8/8/8/8/3n4/3P1P2/R3K2R w KQ - 0 1", "4k3/8/8/8/8/3p4/2P1K3/8 w - - 0 1",
    "4r1k1/8/8/b7/8/2N5/7R/4K3 w - - 0 1", "r1b1k1nr/pP3p1p/8/2pPp3/1p2P1p1/8/P1P2PpP/R1B1K1NR w KQkq c6 0 1",
    "4k3/8/8/8/8/8/1p4p1/R1N1KB1R b - - 0 1", "4k3/pp3ppp/8/8/8/8/PP3PPP/4K3 w - - 0 1", "8/8/8/k2pP2R/8/8/8/6K1 w - d6 0 1",
    "4k3/8/8/8/8/4B3/8/4R1K1 w - - 0 1",
    "r6K/4P3/8/8/8/8/8/k7 w - - 0 1", "3r3K/4P3/8/8/8/8/8/k7 w - - 0 1", "4k3/8/8/b7/8/8/1PP5/4K3 w - - 0 1",
    "8/8/8/1nk5/3Pp3/8/8/4K3 b - d3 0 1", "4k3/8/8/np4pn/PP4PP/8/8/4K3 w - - 0 1", "4k3/8/8/pp4pp/NP4PN/8/8/4K3 b - - 0 1",
    "8/1P6/8/8/8/1k6/8/7K w - - 0 1", "4r3/8/3k4/8/8/6N1/8/4K3 w - - 0 1", "8/8/5k2/8/4r3/2N5/8/4K3 w - - 0 1",
]


def now():
    return time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(time.time() + 3600)) + " Vienna"


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def body_sha(transcript):
    """sha256 of a probe transcript after its identity frame: equal for two probes exactly when every record is equal."""
    spans, _ = mg_format.frames_tolerant(transcript)
    start = spans[0][0] + spans[0][1] if spans else 0
    return sha256(transcript[start:])


def probe(tag):
    return os.path.join(OUT, "aux2", tag, "mgprobe.exe")


def exe(tag):
    return os.path.join(OUT, "bin", tag, "engine.exe")


def seeds_path(name):
    return os.path.join(OUT, "corpus", f"seeds_{name}.txt")


def free_gib():
    import shutil
    return shutil.disk_usage("D:\\").free / (1 << 30)


def guard():
    f = free_gib()
    if f < FLOOR_GIB:
        raise SystemExit(f"NOT STARTED (disk guard): D: has {f:.2f} GiB free, under {FLOOR_GIB}")


def wait_hold():
    hold = os.path.join(OUT, "job3_fuzz.hold")
    told = False
    while os.path.exists(hold):
        if not told:
            print(f"{now()} holding (job3_fuzz.hold present)", flush=True)
            told = True
        time.sleep(3)


def stop_requested():
    return os.path.exists(os.path.join(OUT, "job3_fuzz.stop"))


def run_probe(argv, data=None, timeout=3600):
    """(stdout, stderr text, exit code or 'TIMEOUT') of a probe run; the child's placement is read back."""
    proc = subprocess.Popen(argv, stdin=subprocess.PIPE if data is not None else subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        pinguard3.check_child(proc._handle)
    except SystemExit:
        proc.kill()
        proc.wait()
        raise
    try:
        out, err = proc.communicate(data, timeout=timeout)
    except subprocess.TimeoutExpired:
        proc.kill()                      # this job's own child
        out, err = proc.communicate()
        return out, err.decode("ascii", "replace"), "TIMEOUT"
    return out, err.decode("ascii", "replace"), proc.returncode


def gen_chunk(name, chunk, positions=CHUNK):
    out, err, code = run_probe([probe("LOCK"), "gen", "--seeds", seeds_path(name), "--master", MASTER,
                                "--chunk", str(chunk), "--positions", str(positions)])
    if code != 0:
        raise SystemExit(f"gen failed for chunk {chunk}: exit {code}: {err[-300:]}")
    stats = json.loads(err.strip().splitlines()[-1])
    return out, stats


# ---------------------------------------------------------------- ledgers
AUX_COLS = ["when", "cand", "chunk", "seeds", "status", "positions", "in_check", "path_sha256", "ref_sha256",
            "cand_sha256", "lock_probe_sha256", "cand_probe_sha256", "harness_sha256", "seconds", "detail"]
UCI_COLS = ["when", "cand", "chunk", "seeds", "status", "positions", "perft_depth", "tie", "path_sha256", "input_sha256",
            "ref_out_sha256", "cand_out_sha256", "lock_exe_sha256", "cand_exe_sha256", "seconds", "detail"]


def ledger_path(tier):
    return os.path.join(OUT, "runs", f"fuzz_{tier}", "ledger.tsv")


def read_ledger(tier):
    path = ledger_path(tier)
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, "r", encoding="ascii") as f:
        head = f.readline().rstrip("\n").split("\t")
        for ln in f:
            parts = ln.rstrip("\n").split("\t")
            if len(parts) == len(head):
                rows.append(dict(zip(head, parts)))
    return rows


def append_ledger(tier, cols, row):
    path = ledger_path(tier)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    new = not os.path.exists(path)
    with open(path, "a", encoding="ascii", newline="\n") as f:
        if new:
            f.write("\t".join(cols) + "\n")
        f.write("\t".join(str(row.get(c, "")).replace("\t", " ").replace("\n", " ") for c in cols) + "\n")
        f.flush()
        os.fsync(f.fileno())


def done_ok(tier):
    return {(r["cand"], int(r["chunk"])) for r in read_ledger(tier) if r["status"] == "OK"}


def harness_sha():
    h = hashlib.sha256()
    for name in ("mgprobe.cpp", "mg_format.py", "mg_compare.py", "uci_session.py", "fuzz.py", "pinguard3.py"):
        h.update(open(os.path.join(PACK, "harness", name), "rb").read())
    return h.hexdigest()


def save_failure(kind, cand, chunk, files, detail):
    d = os.path.join(OUT, "fail", f"{kind}_{cand}_chunk{chunk:03d}_{time.strftime('%H%M%S')}")
    os.makedirs(d, exist_ok=True)
    for fname, data in files.items():
        with open(os.path.join(d, fname), "wb") as f:
            f.write(data if isinstance(data, bytes) else data.encode("ascii", "replace"))
    with open(os.path.join(d, "detail.txt"), "w", encoding="ascii", errors="replace", newline="\n") as f:
        f.write(detail + "\n")
    return d


def first_difference_text(ref, cand):
    """Readable dump of the first differing record pair (for the failure folder)."""
    try:
        rs, cs = mg_format.frames(ref), mg_format.frames(cand)
    except mg_format.Malformed as e:
        return f"cannot frame: {e}"
    for i in range(min(len(rs), len(cs))):
        a, b = ref[rs[i][0]:rs[i][0] + rs[i][1]], cand[cs[i][0]:cs[i][0] + cs[i][1]]
        if a != b:
            return (f"record {i}\n--- reference (lock probe)\n{mg_format.describe(mg_format.decode(a))}\n"
                    f"--- candidate\n{mg_format.describe(mg_format.decode(b))}\n")
    return "no differing record among the common ones"


# ---------------------------------------------------------------- tier A
def cmd_aux(name, first, last, cands):
    pinguard3.ensure()
    hsha = harness_sha()
    lock_sha = sha256_file(probe("LOCK"))
    cand_sha = {c: sha256_file(probe(c)) for c in cands}
    seeds_sha = sha256_file(seeds_path(name))
    print(f"{now()} tier A: seeds {name} sha256 {seeds_sha[:16]}, chunks {first}-{last}, candidates {','.join(cands)}, "
          f"master {MASTER}, chunk size {CHUNK}, harness {hsha[:16]}", flush=True)
    for chunk in range(first, last + 1):
        if stop_requested():
            print(f"{now()} stop file present: ending before chunk {chunk}", flush=True)
            return 0
        ok = done_ok("aux")
        todo = [c for c in cands if (c, chunk) not in ok]
        if not todo:
            continue
        guard()
        wait_hold()
        t0 = time.time()
        path, stats = gen_chunk(name, chunk)
        path_sha = sha256(path)
        ref, err, code = run_probe([probe("LOCK"), "run"], path)
        check = mg_compare.compare(ref, ref, expect_tag="LOCK", expect_positions=CHUNK) if code == 0 else None
        if code != 0 or check.status != "EQUAL" or check.positions != CHUNK:
            d = save_failure("aux_reference", "LOCK", chunk, {"path.txt": path, "stderr.txt": err},
                             f"lock probe exit {code}; {check.detail if check else ''}")
            print(f"{now()} chunk {chunk}: the REFERENCE run is not usable (harness error, no verdict); evidence {d}", flush=True)
            return 2
        ref_sha = body_sha(ref)
        t_ref = time.time() - t0
        line = [f"chunk {chunk} ref {t_ref:.0f}s in_check {stats['in_check']}"]
        for cand in todo:
            wait_hold()
            t1 = time.time()
            tr, cerr, ccode = run_probe([probe(cand), "run"], path)
            res = mg_compare.compare_bound(ref, path_sha, tr, path_sha, path.decode("ascii"), expect_tag=cand, expect_positions=CHUNK)
            if cand_sha[cand] == lock_sha:
                res = mg_compare.Result("HARNESS_ERROR", 0, "the candidate probe file is byte-identical to the lock probe: nothing would be tested")
            if ccode == "TIMEOUT":
                status = "TIMEOUT"
            elif ccode != 0:
                status = "CRASH"
            elif res.status == "EQUAL" and res.positions == CHUNK:
                status = "OK"
            elif res.status == "MISMATCH":
                status = "MISMATCH"
            else:
                status = "HARNESS_ERROR"
            detail = res.detail if status != "CRASH" else f"candidate probe exit {ccode}: {cerr[-400:]} | {res.detail}"
            if status != "OK":
                d = save_failure("aux", cand, chunk, {"path.txt": path, "candidate_stderr.txt": cerr,
                                                      "first_difference.txt": first_difference_text(ref, tr)}, detail)
                detail += f" | evidence {d}"
            append_ledger("aux", AUX_COLS, {
                "when": now(), "cand": cand, "chunk": chunk, "seeds": f"{name}:{seeds_sha[:16]}", "status": status,
                "positions": res.positions, "in_check": stats["in_check"], "path_sha256": path_sha, "ref_sha256": ref_sha,
                "cand_sha256": body_sha(tr), "lock_probe_sha256": lock_sha, "cand_probe_sha256": cand_sha[cand],
                "harness_sha256": hsha, "seconds": f"{time.time() - t1:.1f}", "detail": detail[:1500]})
            line.append(f"{cand} {status} {time.time() - t1:.0f}s")
            del tr
        sdir = os.path.join(OUT, "runs", "fuzz_aux", "chunks")
        os.makedirs(sdir, exist_ok=True)
        with open(os.path.join(sdir, f"chunk_{chunk:03d}.json"), "w", encoding="ascii", newline="\n") as f:
            json.dump({"chunk": chunk, "seeds": name, "seeds_sha256": seeds_sha, "master": MASTER, "positions": CHUNK,
                       "path_sha256": path_sha, "path_bytes": len(path), "ref_transcript_sha256": ref_sha,
                       "ref_transcript_bytes": len(ref), "gen_stats": stats, "when": now()}, f, indent=1)
        del ref
        print(f"{now()} " + " | ".join(line) + f" | total {time.time() - t0:.0f}s | D: {free_gib():.2f} GiB", flush=True)
    return 0


# ---------------------------------------------------------------- tier R
def cmd_uci(name, first, last, cands, depth=2):
    pinguard3.ensure()
    lock_sha = sha256_file(exe("LOCK"))
    cand_sha = {c: sha256_file(exe(c)) for c in cands}
    seeds_sha = sha256_file(seeds_path(name))
    tmp = os.path.join(OUT, "tmp")
    print(f"{now()} tier R: seeds {name} sha256 {seeds_sha[:16]}, chunks {first}-{last}, candidates {','.join(cands)}, "
          f"go perft {depth}", flush=True)
    for chunk in range(first, last + 1):
        if stop_requested():
            print(f"{now()} stop file present: ending before chunk {chunk}", flush=True)
            return 0
        ok = done_ok("uci")
        todo = [c for c in cands if (c, chunk) not in ok]
        if not todo:
            continue
        guard()
        wait_hold()
        t0 = time.time()
        path, _stats = gen_chunk(name, chunk)
        path_sha = sha256(path)
        expect_file = os.path.join(tmp, f"uci_chunk_{chunk:03d}.expect")
        script, err, code = run_probe([probe("LOCK"), "uciscript", "--perft", str(depth), "--expect", expect_file], path)
        if code != 0:
            print(f"{now()} chunk {chunk}: uciscript failed (harness error): {err[-300:]}", flush=True)
            return 2
        expect_lines = open(expect_file, "r", encoding="ascii").read().split("\n")
        in_file = os.path.join(tmp, f"uci_chunk_{chunk:03d}.uci")
        n = uci_session.write_batch(in_file, [ln for ln in script.decode("ascii").splitlines() if ln])
        in_sha = sha256_file(in_file)
        ref_file = os.path.join(tmp, f"uci_chunk_{chunk:03d}.LOCK.out")
        run = uci_session.run_batch([exe("LOCK")], in_file, ref_file, timeout=14400)
        ref_text = open(ref_file, "r", encoding="ascii", errors="replace").read()
        ref_bad = uci_session._unusable(uci_session.parse_perft_output(ref_text), n)
        if run.status != "OK" or ref_bad or n != CHUNK:
            print(f"{now()} chunk {chunk}: the REFERENCE run is not usable (harness error, no verdict): run {run.status} "
                  f"{run.detail}; {ref_bad}; positions {n}; files kept in {tmp}", flush=True)
            return 2
        # every block of the lock exe must be the lock probe's legal list at that position: the position was reached
        tie = uci_session.check_tie(ref_text, expect_lines, n)
        if tie.status != "EQUAL":
            print(f"{now()} chunk {chunk}: the lock exe and the lock probe do not list the same moves (to analyse, no candidate verdict): "
                  f"{tie.detail}; files kept in {tmp}", flush=True)
            return 2
        os.remove(expect_file)
        ref_sha = sha256(ref_text.encode("ascii", "replace"))
        line = [f"chunk {chunk} lock {time.time() - t0:.0f}s tied {tie.positions}"]
        keep = False
        for cand in todo:
            wait_hold()
            t1 = time.time()
            out_file = os.path.join(tmp, f"uci_chunk_{chunk:03d}.{cand}.out")
            crun = uci_session.run_batch([exe(cand)], in_file, out_file, timeout=14400)
            text = open(out_file, "r", encoding="ascii", errors="replace").read()
            if text == ref_text:
                # the reference was parsed and found complete above; the same text holds the same blocks
                res = uci_session.Result("EQUAL", n, f"{n} perft blocks: output byte-identical to the lock's")
            else:
                res = uci_session.compare_perft_bound(ref_text, in_sha, text, in_sha, n)
            if crun.status == "TIMEOUT":
                status, detail = "TIMEOUT", crun.detail
            elif crun.status != "OK":
                status, detail = "CRASH", f"{crun.detail} | {res.detail}"
            elif res.status == "EQUAL" and res.positions == n:
                status, detail = "OK", res.detail
            elif res.status == "MISMATCH":
                status, detail = "MISMATCH", res.detail
            else:
                status, detail = "HARNESS_ERROR", res.detail
            if status != "OK":
                keep = True
                d = save_failure("uci", cand, chunk, {"path.txt": path, "candidate_out.txt": text[:4_000_000],
                                                      "note.txt": f"input {in_file}; lock output {ref_file}"}, detail)
                detail += f" | evidence {d}; batch files kept in {tmp}"
            else:
                os.remove(out_file)
                if os.path.exists(out_file + ".err"):
                    os.remove(out_file + ".err")
            append_ledger("uci", UCI_COLS, {
                "when": now(), "cand": cand, "chunk": chunk, "seeds": f"{name}:{seeds_sha[:16]}", "status": status,
                "positions": res.positions, "perft_depth": depth, "tie": f"lock exe = lock probe on {tie.positions}", "path_sha256": path_sha, "input_sha256": in_sha,
                "ref_out_sha256": ref_sha, "cand_out_sha256": sha256(text.encode("ascii", "replace")),
                "lock_exe_sha256": lock_sha, "cand_exe_sha256": cand_sha[cand], "seconds": f"{time.time() - t1:.1f}",
                "detail": detail[:1500]})
            line.append(f"{cand} {status} {time.time() - t1:.0f}s")
        if not keep:
            for p in (in_file, ref_file, ref_file + ".err"):
                if os.path.exists(p):
                    os.remove(p)
        print(f"{now()} " + " | ".join(line) + f" | total {time.time() - t0:.0f}s | D: {free_gib():.2f} GiB", flush=True)
    return 0


# ---------------------------------------------------------------- cross-tier: probe list == release exe perft 1
def cmd_crosstier(name, tags, positions=2000):
    pinguard3.ensure()
    path, _ = gen_chunk(name, 9000, positions)          # a chunk number outside the fuzz range
    script, _, _ = run_probe([probe("LOCK"), "uciscript", "--perft", "1"], path)
    tmp = os.path.join(OUT, "tmp")
    in_file = os.path.join(tmp, "crosstier.uci")
    n = uci_session.write_batch(in_file, [ln for ln in script.decode("ascii").splitlines() if ln])
    code = 0
    for tag in tags:
        tr, _, _ = run_probe([probe(tag), "run"], path)
        lists = mg_format.legal_lists(tr)
        out_file = os.path.join(tmp, f"crosstier.{tag}.out")
        run = uci_session.run_batch([exe(tag)], in_file, out_file, timeout=3600)
        parsed = uci_session.parse_perft_output(open(out_file, "r", encoding="ascii", errors="replace").read())
        exe_lists = [[m for m, _ in b.moves] for b in parsed.blocks]
        same = sum(1 for a, b in zip(lists, exe_lists) if a == b)
        ok = run.status == "OK" and not parsed.anomalies and len(lists) == len(exe_lists) == n and same == n
        first_bad = next((i for i, (a, b) in enumerate(zip(lists, exe_lists)) if a != b), None)
        receipt = {"check": "crosstier", "tag": tag, "positions": n, "identical_lists": same, "status": "MATCH" if ok else "DIFFERS",
                   "probe_sha256": sha256_file(probe(tag)), "exe_sha256": sha256_file(exe(tag)), "path_sha256": sha256(path),
                   "seeds": name, "anomalies": parsed.anomalies[:3], "first_difference_index": first_bad, "when": now(),
                   "meaning": "the auxiliary probe's legal_moves() list and the release executable's go perft 1 list are the "
                              "same moves in the same order at every one of these positions"}
        d = os.path.join(OUT, "runs", "crosstier")
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, tag + ".json"), "w", encoding="ascii", newline="\n") as f:
            json.dump(receipt, f, indent=1)
        print(f"crosstier {tag}: {receipt['status']} {same}/{n} positions", flush=True)
        os.remove(out_file)
        if not ok:
            code = 3
    return code


# ---------------------------------------------------------------- cache-state variants of a chunk (tier A)
WARM_COLS = ["when", "cand", "chunk", "variant", "seeds", "status", "positions", "path_sha256", "ref_sha256", "cand_sha256",
             "lock_probe_sha256", "cand_probe_sha256", "harness_sha256", "detail"]


def cmd_warmseq(name, first, last, cands):
    """The same chunks again with two other cache histories: never cleared (every evaluation meets a warm
    cache) and cleared before every playout (many cold starts). These are replays of fuzz positions under
    another cache state, so they have their own ledger and do not count towards the fuzz total."""
    pinguard3.ensure()
    hsha = harness_sha()
    lock_sha = sha256_file(probe("LOCK"))
    seeds_sha = sha256_file(seeds_path(name))
    for chunk in range(first, last + 1):
        guard()
        base, _ = gen_chunk(name, chunk)
        lines = [ln for ln in base.decode("ascii").splitlines() if ln != "C"]
        variants = {"never_cleared": ("\n".join(lines) + "\n").encode("ascii"),
                    "cleared_before_every_playout": ("\n".join(("C\n" + ln) if ln.startswith("P ") else ln for ln in lines) + "\n").encode("ascii")}
        for variant, path in variants.items():
            path_sha = sha256(path)
            ref, err, code = run_probe([probe("LOCK"), "run"], path)
            check = mg_compare.compare(ref, ref, expect_tag="LOCK", expect_positions=CHUNK) if code == 0 else None
            if code != 0 or check.status != "EQUAL":
                print(f"{now()} warmseq chunk {chunk} {variant}: reference not usable (harness error)", flush=True)
                return 2
            line = [f"warmseq chunk {chunk} {variant}"]
            for cand in cands:
                tr, cerr, ccode = run_probe([probe(cand), "run"], path)
                res = mg_compare.compare_bound(ref, path_sha, tr, path_sha, path.decode("ascii"), expect_tag=cand, expect_positions=CHUNK)
                status = "OK" if ccode == 0 and res.status == "EQUAL" and res.positions == CHUNK else \
                    "CRASH" if ccode != 0 else "MISMATCH" if res.status == "MISMATCH" else "HARNESS_ERROR"
                detail = res.detail
                if status != "OK":
                    d = save_failure("warmseq", cand, chunk, {"path.txt": path, "candidate_stderr.txt": cerr,
                                                              "first_difference.txt": first_difference_text(ref, tr)}, detail)
                    detail += f" | evidence {d}"
                append_ledger("warm", WARM_COLS, {
                    "when": now(), "cand": cand, "chunk": chunk, "variant": variant, "seeds": f"{name}:{seeds_sha[:16]}", "status": status,
                    "positions": res.positions, "path_sha256": path_sha, "ref_sha256": body_sha(ref), "cand_sha256": body_sha(tr),
                    "lock_probe_sha256": lock_sha, "cand_probe_sha256": sha256_file(probe(cand)), "harness_sha256": hsha, "detail": detail[:1200]})
                line.append(f"{cand} {status}")
            print(f"{now()} " + " | ".join(line), flush=True)
    return 0


# ---------------------------------------------------------------- search signatures on corpus positions (tier R, supplementary)
def search_sequence(tag, position_lines, net, depth):
    """Every info line (without time and nps) and the bestmove of go depth D at each position, one process,
    Threads 1, tables kept between positions and reset by ucinewgame every 500 positions."""
    import re
    strip = re.compile(r" (nps|time) \d+")
    eng = uci_session.Engine([exe(tag)])
    eng.handshake(["Threads=1", "Hash=16", "OwnBook=false", f"UseNNUE={net}"])
    rows = []
    for i, pos in enumerate(position_lines):
        if i % 500 == 0:
            eng.send("ucinewgame")
            eng.isready()
        eng.send(pos)
        info, best = eng.go(f"depth {depth}", timeout=3600)
        rows.append("|".join(strip.sub("", ln) for ln in info) + "|" + best)
    code = eng.close()
    return rows, code


def cmd_search(name, chunk, count, depth, tags):
    """Supplementary: the search output of the release executables on corpus positions. It is the only way the
    code of WITNESS_NOPIN and KING_PAWN_CACHE runs inside a release executable. It does not stand in for move
    order, checkers or static eval."""
    pinguard3.ensure()
    path, _ = gen_chunk(name, chunk)
    script, _, _ = run_probe([probe("LOCK"), "uciscript", "--perft", "1"], path)
    positions = [ln for ln in script.decode("ascii").splitlines() if ln.startswith("position ")][:count]
    d = os.path.join(OUT, "runs", "search_sig")
    os.makedirs(d, exist_ok=True)
    code_all = 0
    for net in ("true", "false"):
        ref, _ = search_sequence("LOCK", positions, net, depth)
        ref_sha = sha256("\n".join(ref).encode("ascii"))
        for tag in tags:
            rows, ecode = search_sequence(tag, positions, net, depth)
            k = next((i for i, (a, b) in enumerate(zip(ref, rows)) if a != b), None)
            same = rows == ref
            receipt = {"check": "search_signature", "tag": tag, "net": "on" if net == "true" else "off", "seeds": name, "chunk": chunk,
                       "positions": len(positions), "depth": depth, "identical_to_lock": same, "exit": ecode,
                       "rows_sha256": sha256("\n".join(rows).encode("ascii")), "lock_rows_sha256": ref_sha,
                       "exe_sha256": sha256_file(exe(tag)), "lock_exe_sha256": sha256_file(exe("LOCK")), "path_sha256": sha256(path),
                       "first_difference": None if k is None else {
                           "index": k, "position": positions[k], "expected": ref[k][-300:], "got": rows[k][-300:],
                           "sequence_note": f"tables are kept since the last ucinewgame at index {k - k % 500}: replay positions {k - k % 500}..{k} in order"},
                       "note": "supplementary evidence; one process per run, Threads 1, Hash 16, ucinewgame every 500 positions", "when": now()}
            with open(os.path.join(d, f"{tag}_net{receipt['net']}.json"), "w", encoding="ascii", newline="\n") as f:
                json.dump(receipt, f, indent=1)
            print(f"{now()} search signature {tag} net {receipt['net']}: {'IDENTICAL' if same else 'DIFFERS at index ' + str(k)} "
                  f"({len(positions)} positions, depth {depth})", flush=True)
            if not same:
                code_all = 3
    return code_all


# ---------------------------------------------------------------- seeds, pilot, keys, count
def cmd_seeds(name, edge_file=None):
    edge = list(EDGE_V1)
    edge_note = "job 2's 24 targeted positions and 9 legal positions named by the planning review"
    if edge_file:
        edge = []
        with open(edge_file, "r", encoding="ascii") as f:
            head = f.readline().rstrip("\n").split("\t")
            for ln in f:
                row = dict(zip(head, ln.rstrip("\n").split("\t")))
                if row.get("class") == "LEGAL":
                    edge.append(row["fen"])
        edge_note = f"the {len(edge)} LEGAL entries of {edge_file} (sha256 {sha256_file(edge_file)})"
    with open(FENS12K, "r", encoding="ascii") as f:
        fens = [ln.strip() for ln in f if ln.strip()]
    path = seeds_path(name)
    if os.path.exists(path):
        raise SystemExit(f"refusing: {path} exists")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="ascii", newline="\n") as f:
        f.write("S\t" + START + "\n")
        for x in BENCH:
            f.write("B\t" + x + "\n")
        for x in edge:
            f.write("E\t" + x + "\n")
        for x in fens:
            f.write("F\t" + x + "\n")
    receipt = {"name": name, "path": path, "sha256": sha256_file(path), "start_position": 1, "bench": len(BENCH), "edge": len(edge),
               "edge_source": edge_note, "fens12k": len(fens), "fens12k_file": FENS12K, "fens12k_sha256": sha256_file(FENS12K),
               "master_seed": MASTER, "chunk_positions": CHUNK,
               "selection": "per playout: seed class 70 % fens12k, 20 % edge, 5 % bench, 5 % start position, seed uniform in the class; "
                            "policy 0 uniform over the legal moves, policy 1 weighted (en passant 16, capture 4, promotion 8, castling 8, "
                            "double push 2, king move 2, gives check 6, multiplied), each with probability 1/2; length 8-80 plies "
                            "(20-160 from the start position and bench seeds) or until no legal move; a cache-clear mark before a "
                            "playout with probability 1/16; chunk seed = master xor (chunk+1)*0x9E3779B97F4A7C15 through SplitMix64 "
                            "into xoshiro256**",
               "when": now()}
    with open(path[:-4] + ".json", "w", encoding="ascii", newline="\n") as f:
        json.dump(receipt, f, indent=1)
    print(json.dumps(receipt, indent=1))
    return 0


def cmd_pilot(name):
    pinguard3.ensure()
    n = 20000
    t = time.time()
    path, stats = gen_chunk(name, 9001, n)
    t_gen = time.time() - t
    t = time.time()
    ref, _, _ = run_probe([probe("LOCK"), "run"], path)
    t_run = time.time() - t
    t = time.time()
    res = mg_compare.compare(ref, ref, expect_tag="LOCK")
    t_cmp = time.time() - t
    print(f"pilot tier A: gen {t_gen:.2f}s, lock probe run {t_run:.2f}s ({n / t_run:.0f} positions/s), compare {t_cmp:.2f}s, "
          f"transcript {len(ref) / 1e6:.1f} MB ({len(ref) / n:.0f} bytes/position), {res.status} {res.positions}, in check {stats['in_check']}")
    tmp = os.path.join(OUT, "tmp")
    for depth in (1, 2):
        script, _, _ = run_probe([probe("LOCK"), "uciscript", "--perft", str(depth)], path)
        in_file = os.path.join(tmp, f"pilot_d{depth}.uci")
        k = uci_session.write_batch(in_file, [ln for ln in script.decode("ascii").splitlines() if ln])
        out_file = os.path.join(tmp, f"pilot_d{depth}.out")
        t = time.time()
        run = uci_session.run_batch([exe("LOCK")], in_file, out_file, timeout=3600)
        t_exe = time.time() - t
        size = os.path.getsize(out_file)
        print(f"pilot tier R: go perft {depth}: lock exe {t_exe:.2f}s wall, {run.cpu:.2f}s cpu ({k / t_exe:.0f} positions/s), output {size / 1e6:.1f} MB, run {run.status}")
        for p in (in_file, out_file, out_file + ".err"):
            if os.path.exists(p):
                os.remove(p)
    print("pilot numbers plan the schedule only; they are not results")
    return 0


def cmd_keys(parts):
    pinguard3.ensure()
    argv = [probe("LOCK"), "keys", "--master", MASTER, "--positions", str(CHUNK)]
    for p in parts:
        name, rng = p.split(":")
        argv += ["--part", f"{seeds_path(name)}:{rng}"]
    out, err, code = run_probe(argv, timeout=7200)
    if code != 0:
        raise SystemExit(f"keys failed: {err[-300:]}")
    stats = json.loads(out.decode("ascii").strip().splitlines()[-1])
    stats["parts"] = parts
    stats["quiet"] = stats["positions"] - stats["in_check"]
    stats["when"] = now()
    d = os.path.join(OUT, "runs", "fuzz_aux")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, "KEYS_" + "_".join(p.replace(":", "-") for p in parts) + ".json"), "w", encoding="ascii", newline="\n") as f:
        json.dump(stats, f, indent=1)
    print(json.dumps(stats))
    return 0


def cmd_count():
    result = {}
    for tier in ("aux", "uci"):
        rows = read_ledger(tier)
        per = {}
        for r in rows:
            c = per.setdefault(r["cand"], {"ok_chunks": set(), "positions": 0, "in_check": 0, "not_ok": []})
            key = int(r["chunk"])
            if r["status"] == "OK":
                if key not in c["ok_chunks"]:          # a chunk counts once, however often it was run
                    c["ok_chunks"].add(key)
                    c["positions"] += int(r["positions"])
                    c["in_check"] += int(r.get("in_check") or 0)
            else:
                c["not_ok"].append(f"chunk {key} {r['status']}")
        result[tier] = {k: {"completed_positions": v["positions"], "ok_chunks": len(v["ok_chunks"]), "in_check": v["in_check"],
                            "not_ok": v["not_ok"]} for k, v in sorted(per.items())}
        for k, v in sorted(per.items()):
            print(f"tier {'A' if tier == 'aux' else 'R'} {k}: {v['positions']:,} completed position comparisons in {len(v['ok_chunks'])} chunks"
                  + (f", in check {v['in_check']:,}" if tier == "aux" else "") + (f"; NOT OK: {v['not_ok']}" if v["not_ok"] else ""))
    with open(os.path.join(OUT, "runs", "FUZZ_COUNT.json"), "w", encoding="ascii", newline="\n") as f:
        json.dump({"when": now(), "counts": result}, f, indent=1)
    return 0


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 1
    cmd = argv[1]
    cands = CANDS
    if "--cands" in argv:
        cands = argv[argv.index("--cands") + 1].split(",")
    if cmd == "seeds":
        return cmd_seeds(argv[2], argv[argv.index("--edge") + 1] if "--edge" in argv else None)
    if cmd == "pilot":
        return cmd_pilot(argv[2])
    if cmd in ("aux", "uci"):
        a, b = argv[3].split("-")
        return (cmd_aux if cmd == "aux" else cmd_uci)(argv[2], int(a), int(b), cands)
    if cmd == "warmseq":
        a, b = argv[3].split("-")
        return cmd_warmseq(argv[2], int(a), int(b), cands)
    if cmd == "search":
        # search NAME CHUNK COUNT DEPTH [--cands ...]
        return cmd_search(argv[2], int(argv[3]), int(argv[4]), int(argv[5]), cands)
    if cmd == "crosstier":
        return cmd_crosstier(argv[2], argv[3:])
    if cmd == "keys":
        return cmd_keys(argv[2:])
    if cmd == "count":
        return cmd_count()
    print(__doc__)
    return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
