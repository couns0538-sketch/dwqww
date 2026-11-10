"""selftest.py - positive and negative controls of the job-3 harness (standard library only).

Nothing here alters an engine binary or engine source. Every negative control takes a REAL output of the lock
(a probe transcript or a UCI perft output), changes one thing in memory on the harness side, and requires the
comparator to refuse it and to name what differs. The positive controls run the lock against a verified
byte-for-byte copy of itself, and against the lock-equivalent build (another binary that must behave the same),
and require zero differences.

  python -I -B selftest.py            (run through scripts\\pin_run.ps1)
Exit 0 and a last line "SELFTEST PASS n/n" only if every control behaved as required.
"""
import copy
import hashlib
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard3  # noqa: E402

OUT = r"D:\forge_jobs_20261109\fable2\out\job3"
PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
AUX = os.path.join(OUT, "aux2")
LOCK_PROBE = os.path.join(AUX, "LOCK", "mgprobe.exe")
LOCK_PROBE_COPY = os.path.join(AUX, "LOCKCOPY", "mgprobe.exe")
LOCKEQ_PROBE = os.path.join(AUX, "LOCKEQ", "mgprobe.exe")
LOCK_EXE = os.path.join(OUT, "bin", "LOCK", "engine.exe")
LOCK_EXE_COPY = os.path.join(OUT, "bin", "LOCKCOPY", "engine.exe")
FENS12K = r"D:\forge_jobs_20261109\fable2\out\base\fens_12k_v2.txt"
WORK = os.path.join(OUT, "runs", "selftest")
MASTER = "5E1F7E5720261110"
N = 3000

RESULTS = []


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def record(name, ok, detail):
    RESULTS.append(ok)
    print(f"{'PASS' if ok else 'FAIL'}  {name}: {detail}", flush=True)


def control(name, want_status, want_words, result, forbid=()):
    """A control passes when the comparator's status is the wanted one and its text names the field."""
    text = result.detail.lower()
    ok = result.status == want_status and all(w.lower() in text for w in want_words) and not any(w.lower() in text for w in forbid)
    record(name, ok, f"status {result.status} (wanted {want_status}), diagnostic: {result.detail[:230]}")


def attempt(name, fn):
    """Run one control; a crash of the harness is a failed control with its reason."""
    try:
        fn()
    except Exception as e:  # noqa: BLE001
        record(name, False, f"the control crashed: {type(e).__name__}: {e}")


def run(argv, data=None):
    return subprocess.run(argv, input=data, capture_output=True, check=True).stdout


def build_fixtures():
    os.makedirs(WORK, exist_ok=True)
    if not os.path.exists(LOCK_PROBE_COPY):                      # the byte-for-byte copy is a harness-side fixture
        os.makedirs(os.path.dirname(LOCK_PROBE_COPY), exist_ok=True)
        shutil.copyfile(LOCK_PROBE, LOCK_PROBE_COPY)
    seeds = os.path.join(WORK, "seeds_selftest.txt")
    with open(FENS12K, "r", encoding="ascii") as f:
        fens = [ln.strip() for ln in f if ln.strip()][:200]
    bench = ["r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1", "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1"]
    edge = ["8/8/8/2k5/3Pp3/8/8/4K3 b - d3 0 1", "4k3/8/8/8/8/5n2/6B1/r3K3 w - - 0 1",
            "r1b1k1nr/pP3p1p/8/2pPp3/1p2P1p1/8/P1P2PpP/R1B1K1NR w KQkq c6 0 1"]
    with open(seeds, "w", encoding="ascii", newline="\n") as f:
        f.write("S\trnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\n")
        for x in bench:
            f.write("B\t" + x + "\n")
        for x in edge:
            f.write("E\t" + x + "\n")
        for x in fens:
            f.write("F\t" + x + "\n")
    path_a = run([LOCK_PROBE, "gen", "--seeds", seeds, "--master", MASTER, "--chunk", "0", "--positions", str(N)])
    path_b = run([LOCK_PROBE, "gen", "--seeds", seeds, "--master", MASTER, "--chunk", "1", "--positions", str(N)])
    ref = run([LOCK_PROBE, "run"], path_a)
    return seeds, path_a, path_b, ref


def mutate_value(v):
    """Another value of the same kind (for the every-field control)."""
    if isinstance(v, bool):
        return not v
    if isinstance(v, int):
        return v + 1
    if isinstance(v, (bytes, bytearray)):
        b = bytearray(v)
        b[0] ^= 1
        return b
    if isinstance(v, list):
        w = list(v)
        w[0] ^= 1
        return w
    if isinstance(v, str):
        return v + "x"
    raise TypeError(type(v))


def tier_a_controls():
    import mg_compare
    import mg_format
    seeds, path_a, path_b, ref = build_fixtures()
    path_text = path_a.decode("ascii")
    cmp = mg_compare.compare

    spans = mg_format.frames(ref)
    rebuilt = b"".join(mg_format.frame(mg_format.encode(mg_format.decode(ref[o:o + n]))) for o, n in spans)
    record("A0 codec round trip", rebuilt == ref, f"{len(spans)} frames, {len(ref)} bytes, identical after decode+encode: {rebuilt == ref}")
    ident = mg_format.decode(ref[spans[0][0]:spans[0][0] + spans[0][1]])
    trailer = mg_format.decode(ref[spans[-1][0]:spans[-1][0] + spans[-1][1]])
    record("A0 lock transcript is sane", ident["kind"] == 253 and ident["tag"] == "LOCK" and trailer["kind"] == 254
           and trailer["records"] == len(spans) - 2 and trailer["hard"] == 0,
           f"identity tag {ident.get('tag')} harness {str(ident.get('harness'))[:16]} null mode {ident.get('flags')}; trailer records "
           f"{trailer.get('records')}, self-check failures {trailer.get('hard')}, incremental/refresh differences {trailer.get('soft')}")

    # positive controls
    same_exe = sha256_file(LOCK_PROBE) == sha256_file(LOCK_PROBE_COPY)
    res = cmp(ref, run([LOCK_PROBE_COPY, "run"], path_a), path_text, expect_tag="LOCK", expect_positions=N)
    record("A1 positive: lock probe vs its byte-identical copy", same_exe and res.status == "EQUAL" and res.positions == N,
           f"copy sha256 equal: {same_exe}; status {res.status}; positions compared {res.positions}")
    other_build = sha256_file(LOCK_PROBE) != sha256_file(LOCKEQ_PROBE)
    res = cmp(ref, run([LOCKEQ_PROBE, "run"], path_a), path_text, expect_tag="LOCKEQ", expect_positions=N)
    record("A1b positive: lock probe vs the lock-equivalent probe (another build, same behaviour)",
           other_build and res.status == "EQUAL" and res.positions == N,
           f"binaries differ: {other_build}; status {res.status}; positions compared {res.positions}; {res.detail[:120]}")

    # the record to corrupt: not in check, six or more legal moves, with a null-move block
    target = None
    for i, (o, n) in enumerate(spans[1:-1], start=1):
        r = mg_format.decode(ref[o:o + n])
        if r["kind"] == 0 and len(r["legal"]) >= 6 and r["checkers_main"] == 0 and r["null"] is not None and len(r["legal_caps"]) >= 1 \
                and len(r["quiets"]) >= 2 and i > 5:
            target = i
            break
    assert target is not None

    def splice(index, payload):
        o, n = spans[index]
        return ref[:o - 8] + mg_format.frame(payload) + ref[o + n:]

    def mutated(fn, index=None):
        k = target if index is None else index
        o, n = spans[k]
        r = mg_format.decode(ref[o:o + n])
        fn(r)
        return splice(k, mg_format.encode(r))

    def remove_move(r):
        del r["legal"][2]

    def add_move(r):
        r["legal"].append(r["legal"][0] ^ 0x0100)

    def swap_moves(r):
        r["legal"][1], r["legal"][2] = r["legal"][2], r["legal"][1]

    def flip_checkers(r):
        r["checkers_main"] ^= 1 << 27

    def eval_on(r):
        r["on_refresh"] += 1

    def eval_off(r):
        r["off"] += 1

    def flip_has(r):
        r["has_after"] ^= 1

    def child_flip(r):
        j = next(k for k, b in enumerate(r["bits"]) if b & 1)
        r["child_main"][j] ^= 1 << 9

    def swap_generated(r):
        r["all"][0], r["all"][1] = r["all"][1], r["all"][0]

    def flip_legal_bit(r):
        r["bits"][0] ^= 1

    def flip_gives_check(r):
        j = next(k for k, b in enumerate(r["bits"]) if b & 1)
        r["bits"][j] ^= 2

    def flip_first_query(r):
        r["one_bits"][0] ^= 1

    def flip_post_unmake(r):
        r["post_bits"][0] ^= 1

    def null_child(r):
        r["null"]["all"][0], r["null"]["all"][1] = r["null"]["all"][1], r["null"]["all"][0]

    def stale_probe(r):
        r["rev1_off"] += 1

    for name, status, words, fn in (
            ("A2 negative: one legal move removed", "MISMATCH", ["legal move set", "missing"], remove_move),
            ("A3 negative: one move added", "MISMATCH", ["legal move set", "extra"], add_move),
            ("A4 negative: two adjacent legal moves swapped", "MISMATCH", ["order"], swap_moves),
            ("A5 negative: one checkers bit flipped", "MISMATCH", ["checkers"], flip_checkers),
            ("A6 negative: static eval net on + 1", "MISMATCH", ["eval", "net on"], eval_on),
            ("A7 negative: static eval net off + 1", "MISMATCH", ["eval", "net off"], eval_off),
            ("A8 negative: has_legal_move flipped", "MISMATCH", ["has_legal_move"], flip_has),
            ("A9 negative: checkers after a make flipped", "MISMATCH", ["checkers after"], child_flip),
            ("A10 negative: generated list order swapped", "MISMATCH", ["generated"], swap_generated),
            ("A11 negative: is_legal bit flipped", "MISMATCH", ["is_legal"], flip_legal_bit),
            ("A12 negative: gives_check bit flipped", "MISMATCH", ["gives_check"], flip_gives_check),
            ("A12b negative: first-query is_legal answer flipped", "MISMATCH", ["first query"], flip_first_query),
            ("A12c negative: is_legal answer after make and unmake flipped", "MISMATCH", ["after make and unmake"], flip_post_unmake),
            ("A13 negative: null-move child list changed", "MISMATCH", ["null"], null_child),
            ("A14 negative: stale-cache probe value + 1", "MISMATCH", ["eval", "plies back"], stale_probe)):
        attempt(name, lambda name=name, status=status, words=words, fn=fn: control(name, status, words, cmp(ref, mutated(fn), path_text, expect_tag="LOCK")))

    # every field of a position record, one at a time: each change must be seen and named (no codec fallback)
    def every_field():
        o, n = spans[target]
        base = mg_format.decode(ref[o:o + n])
        missed, n_fields = [], 0
        keys = [k for k in base if k not in ("kind", "flags", "null")] + ["null." + k for k in base["null"]]
        for key in keys:
            r = copy.deepcopy(base)
            holder, k = (r["null"], key[5:]) if key.startswith("null.") else (r, key)
            holder[k] = mutate_value(holder[k])
            res = cmp(ref, splice(target, mg_format.encode(r)), path_text, expect_tag="LOCK")
            n_fields += 1
            if res.status != "MISMATCH" or "codec defect" in res.detail:
                missed.append(f"{key}: {res.status} {res.detail[:80]}")
        record("A15 negative: every field of a record changed in turn", not missed and n_fields >= 35,
               f"{n_fields} fields, each change reported as MISMATCH with its field named; not caught: {missed or 'none'}")
    attempt("A15 negative: every field of a record changed in turn", every_field)

    o, n = spans[target]
    o2, n2 = spans[target + 1]
    attempt("A16", lambda: control("A16 negative: wrong position at one index", "MISMATCH", ["position"],
                                   cmp(ref, ref[:o - 8] + ref[o2 - 8:o2 + n2] + ref[o + n:], path_text, expect_tag="LOCK")))
    lo, ln_ = spans[-2]
    attempt("A17", lambda: control("A17 negative: last record missing", "MALFORMED", ["missing"],
                                   cmp(ref, ref[:lo - 8] + ref[lo + ln_:], path_text, expect_tag="LOCK")))
    attempt("A18", lambda: control("A18 negative: transcript truncated", "MALFORMED", ["truncated"], cmp(ref, ref[:o + n // 2], path_text, expect_tag="LOCK")))
    attempt("A19", lambda: control("A19 negative: garbage bytes inserted", "MALFORMED", ["magic"],
                                   cmp(ref, ref[:o - 8] + b"garbage!" * 3 + ref[o - 8:], path_text, expect_tag="LOCK")))
    attempt("A20", lambda: control("A20 negative: empty candidate output", "MALFORMED", ["empty"], cmp(ref, b"", path_text, expect_tag="LOCK")))
    attempt("A21", lambda: control("A21 negative: broken reference", "HARNESS_ERROR", ["reference"], cmp(ref[:o + n // 2], ref, path_text, expect_tag="LOCK")))
    # a difference BEFORE a cut is a difference, not a run to repeat
    attempt("A22", lambda: control("A22 negative: a changed record, then the output cut", "MISMATCH", ["checkers"],
                                   cmp(ref, mutated(flip_checkers)[:spans[target + 40][0]], path_text, expect_tag="LOCK")))
    # identity of the two transcripts
    attempt("A23", lambda: control("A23 negative: transcript written by another probe than expected", "HARNESS_ERROR", ["identity"],
                                   cmp(ref, ref, path_text, expect_tag="EVL")))

    def other_harness(r):
        r["harness"] = "0" * 64
    attempt("A24", lambda: control("A24 negative: candidate probe built from another harness source", "HARNESS_ERROR", ["identity", "harness"],
                                   cmp(ref, mutated(other_harness, 0), path_text, expect_tag="LOCK")))
    lockeq_tr = run([LOCKEQ_PROBE, "run"], path_a)
    attempt("A25", lambda: control("A25 negative: the reference is not the lock probe", "HARNESS_ERROR", ["reference", "lock"],
                                   cmp(lockeq_tr, ref, path_text, expect_tag="LOCK")))
    no_null = run([LOCK_PROBE, "run", "--null", "0"], path_a)
    attempt("A26", lambda: control("A26 negative: candidate ran without the null-move block", "HARNESS_ERROR", ["identity", "null"],
                                   cmp(ref, no_null, path_text, expect_tag="LOCK")))
    attempt("A27", lambda: control("A27 negative: both ran without the null-move block", "HARNESS_ERROR", ["null"],
                                   cmp(no_null, no_null, path_text, expect_tag="LOCK")))
    attempt("A28", lambda: control("A28 negative: fewer positions than the chunk defines", "HARNESS_ERROR", ["positions"],
                                   cmp(ref, ref, path_text, expect_tag="LOCK", expect_positions=N + 1)))
    # input guard
    other = run([LOCK_PROBE, "run"], path_b)
    attempt("A29", lambda: control("A29 negative: outputs of two different inputs", "HARNESS_ERROR", ["inputs differ"],
                                   mg_compare.compare_bound(ref, hashlib.sha256(path_a).hexdigest(), other, hashlib.sha256(path_b).hexdigest(),
                                                            path_text, expect_tag="LOCK")))
    attempt("A30", lambda: control("A30 negative: other chunk compared directly", "MISMATCH", ["position"], cmp(ref, other, path_text, expect_tag="LOCK")))

    # records for a rejected FEN and for a path move the probe cannot play
    err_path = (b"H errors\nP 0 X0 0 8/8/8/8/8/8/4k3/4K3 w - - 0 1\nM\n"
                b"P 1 X0 0 rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\nM e2e4 e7e5 e1e3 g8f6\n"
                b"P 2 X0 0 rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1\nM d2d4\n")
    terr = run([LOCK_PROBE, "run"], err_path)
    espans = mg_format.frames(terr)
    kinds = [mg_format.decode(terr[a:a + b])["kind"] for a, b in espans]

    def emut(kind, fn):
        k = kinds.index(kind)
        a, b = espans[k]
        r = mg_format.decode(terr[a:a + b])
        fn(r)
        return terr[:a - 8] + mg_format.frame(mg_format.encode(r)) + terr[a + b:]

    def set_error(r):
        r["error"] = "another refusal"

    def set_uci(r):
        r["uci"] = "e1e2"
    record("A31 fixture: the lock probe writes a rejected-FEN record and an unplayable-move record", kinds.count(2) == 1 and kinds.count(1) == 1,
           f"record kinds {kinds}")
    attempt("A32", lambda: control("A32 positive: error records allowed where they are expected (rejected entries)", "EQUAL", [],
                                   cmp(terr, terr, None, expect_tag="LOCK", allow_error_records=True)))
    attempt("A33", lambda: control("A33 negative: a reference with error records in a fuzz comparison", "HARNESS_ERROR", ["reference"],
                                   cmp(terr, terr, None, expect_tag="LOCK")))
    attempt("A34", lambda: control("A34 negative: refusal text of a rejected FEN changed", "MISMATCH", ["rejection"],
                                   cmp(terr, emut(2, set_error), None, expect_tag="LOCK", allow_error_records=True)))
    attempt("A35", lambda: control("A35 negative: unplayable-move record changed", "MISMATCH", ["path move"],
                                   cmp(terr, emut(1, set_uci), None, expect_tag="LOCK", allow_error_records=True)))
    return seeds, path_a


def tier_r_controls(seeds, path_a):
    import uci_session
    expect_file = os.path.join(WORK, "batch_r.expect")
    batch = run([LOCK_PROBE, "uciscript", "--perft", "2", "--expect", expect_file], path_a).decode("ascii")
    lines = [ln for ln in batch.splitlines() if ln][:2 * 800]          # 800 positions
    expect = open(expect_file, "r", encoding="ascii").read().split("\n")[:800]
    in_path = os.path.join(WORK, "batch_r.uci")
    n_pos = uci_session.write_batch(in_path, lines)
    out_lock = os.path.join(WORK, "batch_r.lock.out")
    out_copy = os.path.join(WORK, "batch_r.copy.out")
    r1 = uci_session.run_batch([LOCK_EXE], in_path, out_lock, timeout=600)
    r2 = uci_session.run_batch([LOCK_EXE_COPY], in_path, out_copy, timeout=600)
    same_exe = sha256_file(LOCK_EXE) == sha256_file(LOCK_EXE_COPY)
    ref = open(out_lock, "r", encoding="ascii", errors="replace").read()
    cand = open(out_copy, "r", encoding="ascii", errors="replace").read()
    res = uci_session.compare_perft(ref, cand, n_pos)
    record("R1 positive: lock exe vs its byte-identical copy, go perft 2", same_exe and r1.status == "OK" and r2.status == "OK"
           and res.status == "EQUAL" and res.positions == n_pos,
           f"copy sha256 equal: {same_exe}; runs {r1.status}/{r2.status}; status {res.status}; positions compared {res.positions} of {n_pos}")

    # the tie between the release exe's perft blocks and the probe's legal lists, position by position
    attempt("R1b", lambda: control("R1b positive: every lock exe block is the lock probe's legal list in order", "EQUAL", [],
                                   uci_session.check_tie(ref, expect, n_pos)))
    bad_expect = list(expect)
    bad_expect[299] = " ".join(reversed(bad_expect[299].split()))
    attempt("R1c", lambda: control("R1c negative: probe list in another order at one position", "MISMATCH", ["position 300"],
                                   uci_session.check_tie(ref, bad_expect, n_pos)))
    attempt("R1d", lambda: control("R1d negative: probe lists of another chunk", "MISMATCH", ["position"],
                                   uci_session.check_tie(ref, expect[1:] + expect[:1], n_pos)))

    ref_lines = ref.splitlines()
    seen, start = 0, None
    for i, ln in enumerate(ref_lines):
        if ln.startswith("nodes "):
            seen += 1
            if seen == 300:
                start = i + 1
                break
    assert start is not None and uci_session.MOVE_RX.match(ref_lines[start]) and uci_session.MOVE_RX.match(ref_lines[start + 1])

    def edit(*fns):
        x = list(ref_lines)
        for fn in fns:
            fn(x)
        return "\n".join(x) + "\n"

    def nodes_index(x):
        end = start
        while not x[end].startswith("nodes "):
            end += 1
        return end

    # An engine always prints a total that fits its own lines, so the fixtures for "one move less" and
    # "one count changed" keep the block consistent; the inconsistent block is a control of its own.
    def drop_line(x):
        e = nodes_index(x)
        x[e] = f"nodes {int(x[e].split()[1]) - int(x[start].split(': ')[1])}"
        del x[start]

    def swap_lines(x):
        x[start], x[start + 1] = x[start + 1], x[start]

    def change_count(x):
        mv, cnt = x[start].split(": ")
        e = nodes_index(x)
        x[start] = f"{mv}: {int(cnt) + 1}"
        x[e] = f"nodes {int(x[e].split()[1]) + 1}"

    def inconsistent(x):
        mv, cnt = x[start].split(": ")
        x[start] = f"{mv}: {int(cnt) + 1}"

    def drop_block(x):
        end = start
        while not x[end].startswith("nodes "):
            end += 1
        del x[start:end + 1]

    def garbage(x):
        x.insert(start + 1, "Segmentation fault ~~~ 0x00")

    def invalid_fen(x):
        x.insert(start, "info string invalid FEN: kings may not be adjacent")

    def late_garbage(x):
        x.insert(len(x) - 40, "Segmentation fault ~~~ 0x00")

    cp = uci_session.compare_perft
    for name, status, words, fns in (
            ("R2 negative: one move line removed", "MISMATCH", ["legal move set", "missing"], (drop_line,)),
            ("R3 negative: two move lines swapped", "MISMATCH", ["order"], (swap_lines,)),
            ("R4 negative: one reply count changed", "MISMATCH", ["count"], (change_count,)),
            ("R4b negative: block whose counts do not add up", "MALFORMED", ["add up"], (inconsistent,)),
            ("R5 negative: one whole block missing", "MALFORMED", ["missing"], (drop_block,)),
            ("R6 negative: malformed line in a block", "MALFORMED", ["malformed"], (garbage,)),
            ("R7 negative: engine reported an invalid FEN", "MALFORMED", ["invalid fen"], (invalid_fen,)),
            ("R7b negative: a changed block, then a malformed line much later", "MISMATCH", ["order"], (late_garbage, swap_lines))):
        attempt(name, lambda name=name, status=status, words=words, fns=fns: control(name, status, words, cp(ref, edit(*fns), n_pos)))
    attempt("R8", lambda: control("R8 negative: broken reference output", "HARNESS_ERROR", ["reference"], cp(edit(drop_block), ref, n_pos)))

    # wrong position on the candidate's side: another input file
    lines2 = list(lines)
    lines2[2 * 299] = "position fen 4k3/8/8/8/8/8/8/4K2R w K - 0 1"
    in2 = os.path.join(WORK, "batch_r_wrongpos.uci")
    uci_session.write_batch(in2, lines2)
    out2 = os.path.join(WORK, "batch_r_wrongpos.out")
    uci_session.run_batch([LOCK_EXE_COPY], in2, out2, timeout=600)
    cand2 = open(out2, "r", encoding="ascii", errors="replace").read()
    attempt("R9", lambda: control("R9 negative: candidate was fed another input file", "HARNESS_ERROR", ["inputs differ"],
                                  uci_session.compare_perft_bound(ref, sha256_file(in_path), cand2, sha256_file(in2), n_pos)))
    attempt("R10", lambda: control("R10 negative: wrong position, outputs compared directly", "MISMATCH", ["position 300"], cp(ref, cand2, n_pos)))
    attempt("R10b", lambda: control("R10b negative: wrong position is also caught by the tie to the probe", "MISMATCH", ["position 300"],
                                    uci_session.check_tie(cand2, expect, n_pos)))

    # the engine's own rejection of a FEN must be seen, not swallowed
    lines3 = list(lines[:20])
    lines3[10] = "position fen 8/8/8/8/8/8/4k3/4K3 w - - 0 1"
    in3 = os.path.join(WORK, "batch_r_invalid.uci")
    n3 = uci_session.write_batch(in3, lines3)
    out3 = os.path.join(WORK, "batch_r_invalid.out")
    uci_session.run_batch([LOCK_EXE], in3, out3, timeout=300)
    t3 = open(out3, "r", encoding="ascii", errors="replace").read()
    attempt("R11", lambda: control("R11 negative: real engine rejects a FEN inside a batch", "HARNESS_ERROR", ["invalid fen"], cp(t3, t3, n3)))

    # an engine that stops in the middle: the real lock output cut inside a block, well after the first sync point
    cut_at = ref.index("\n", int(len(ref) * 0.8)) + 1
    cut = ref[:cut_at] + ref[cut_at:].split("\n", 1)[0][:4]
    attempt("R12a", lambda: control("R12a negative: output ends in the middle of a block (missing output)", "MALFORMED", ["missing", "identical"],
                                    cp(ref, cut, n_pos)))

    # stub engines: never answers, exits early, prints malformed lines. The early one prints made-up blocks, so the
    # control on it is that the parser sees the cut; what the comparator says about a real cut is control R12a.
    stub = os.path.join(PACK, "harness", "stub_engine.py")
    for mode, want, words, name in (
            ("hang", "TIMEOUT", ["timeout"], "R12 negative: engine never answers (timeout)"),
            ("early", "CUT SEEN", ["missing output"], "R13 negative: engine exits early (the parser sees the cut)"),
            ("garbage", "MALFORMED", ["malformed"], "R14 negative: engine prints malformed lines")):
        def one(mode=mode, want=want, words=words, name=name):
            outp = os.path.join(WORK, f"stub_{mode}.out")
            rr = uci_session.run_batch([PY, "-I", "-B", stub, mode], in_path, outp, timeout=8 if mode == "hang" else 120)
            text = open(outp, "r", encoding="ascii", errors="replace").read() if os.path.exists(outp) else ""
            if rr.status != "OK":
                res = uci_session.Result(rr.status, 0, f"run status {rr.status}: {rr.detail}")
            elif mode == "early":
                anomalies = uci_session.parse_perft_output(text).anomalies
                res = uci_session.Result("CUT SEEN" if anomalies else "NOT SEEN", 0, "; ".join(a for a, _ in anomalies) or "no anomaly reported")
            else:
                res = cp(ref, text, n_pos)
            control(name, want, words, res)
            alive = pinguard3.pid_alive(rr.pid)                     # asked of the operating system, by process id
            record(f"{name.split(' ')[0]}b the operating system no longer lists the child of this control", not alive,
                   f"pid {rr.pid} alive: {alive}")
        attempt(name, one)

    # the liveness question itself must be able to say yes
    def liveness():
        proc = subprocess.Popen([PY, "-I", "-B", stub, "hang"], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL)
        time.sleep(0.5)
        while_running = pinguard3.pid_alive(proc.pid)
        proc.kill()
        proc.wait()
        after = pinguard3.pid_alive(proc.pid)
        record("R15 control of the control: a running process is reported alive, an ended one is not", while_running and not after,
               f"alive while running: {while_running}; alive after it was ended: {after}")
    attempt("R15 liveness", liveness)

    def interactive():
        eng = uci_session.Engine([PY, "-I", "-B", stub, "hang"])
        try:
            eng.handshake([])
            eng.send("position startpos")
            try:
                eng.perft(1, timeout=5)
                record("R16 negative: interactive timeout", False, "no timeout was raised")
                return
            except uci_session.EngineTimeout as e:
                first = str(e)
            t0 = time.time()
            try:
                eng.isready(timeout=30)
                second = "no error: the session was used again"
            except uci_session.EngineError as e:
                second = str(e)
            refused = "not usable" in second.lower() and time.time() - t0 < 2      # refused at once, not a second timeout
            record("R16 negative: interactive timeout, and the session refuses further use", "timeout" in first.lower() and refused,
                   f"raised: {first[:110]}; next call: {second[:110]}")
        finally:
            eng.kill()
    attempt("R16 interactive", interactive)

    def perft_info_string():
        eng = uci_session.Engine([LOCK_EXE])
        try:
            eng.handshake(["Threads=1", "Hash=16", "OwnBook=false"])
            eng.send("position fen 8/8/8/8/8/8/4k3/4K3 w - - 0 1")
            try:
                eng.perft(1, timeout=60)
                record("R17 negative: interactive perft after a rejected FEN", False, "the refusal line was swallowed")
            except uci_session.EngineError as e:
                record("R17 negative: interactive perft after a rejected FEN", "invalid fen" in str(e).lower(), f"raised: {str(e)[:160]}")
        finally:
            eng.kill()
    attempt("R17 perft info string", perft_info_string)


def main():
    print(pinguard3.ensure(), flush=True)
    for p in (LOCK_PROBE, LOCKEQ_PROBE, LOCK_EXE, LOCK_EXE_COPY):
        if not os.path.exists(p):
            print(f"SELFTEST BLOCKED: missing {p}")
            return 2
    print(f"lock probe sha256 {sha256_file(LOCK_PROBE)}; lock exe sha256 {sha256_file(LOCK_EXE)}", flush=True)
    seeds = path_a = None
    try:
        seeds, path_a = tier_a_controls()
    except Exception as e:  # noqa: BLE001  a crash of the harness is a failed self-test, with its reason
        record("A-tier controls did not complete", False, f"{type(e).__name__}: {e}")
    try:
        if path_a is None:
            seeds, path_a, _, _ = build_fixtures()
        tier_r_controls(seeds, path_a)
    except Exception as e:  # noqa: BLE001
        record("R-tier controls did not complete", False, f"{type(e).__name__}: {e}")
    n, good = len(RESULTS), sum(1 for r in RESULTS if r)
    print(f"SELFTEST {'PASS' if good == n else 'FAIL'} {good}/{n}")
    return 0 if good == n else 3


if __name__ == "__main__":
    sys.exit(main())
