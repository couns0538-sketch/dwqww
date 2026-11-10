"""selftest.py - positive and negative controls of the job-3 harness (standard library only).

Nothing here alters an engine binary. Every negative control takes a REAL output of the lock (a probe
transcript or a UCI perft output), changes one thing in memory on the harness side, and requires the
comparator to refuse it and to name what differs. The positive controls run the lock against a verified
byte-for-byte copy of itself and require zero differences.

  python -I -B selftest.py            (run through scripts\\pin_run.ps1)
Exit 0 and a last line "SELFTEST PASS n/n" only if every control behaved as required.
"""
import hashlib
import os
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pinguard3  # noqa: E402

OUT = r"D:\forge_jobs_20261109\fable2\out\job3"
PACK = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable
LOCK_PROBE = os.path.join(OUT, "aux", "LOCK", "mgprobe.exe")
LOCK_PROBE_COPY = os.path.join(OUT, "aux", "LOCKCOPY", "mgprobe.exe")
LOCK_EXE = os.path.join(OUT, "bin", "LOCK", "engine.exe")
LOCK_EXE_COPY = os.path.join(OUT, "bin", "LOCKCOPY", "engine.exe")
FENS12K = r"D:\forge_jobs_20261109\fable2\out\base\fens_12k_v2.txt"
WORK = os.path.join(OUT, "runs", "selftest")
MASTER = "5E1F7E5720261110"

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


def control(name, want_status, want_words, result):
    """A control passes when the comparator's status is the wanted one and its text names the field."""
    text = result.detail.lower()
    ok = result.status == want_status and all(w.lower() in text for w in want_words)
    record(name, ok, f"status {result.status} (wanted {want_status}), diagnostic: {result.detail[:230]}")


def build_fixtures():
    import mg_format
    os.makedirs(WORK, exist_ok=True)
    seeds = os.path.join(WORK, "seeds_selftest.txt")
    with open(FENS12K, "r", encoding="ascii") as f:
        fens = [ln.strip() for ln in f if ln.strip()][:200]
    bench = [
        "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    ]
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
    path_a = subprocess.run([LOCK_PROBE, "gen", "--seeds", seeds, "--master", MASTER, "--chunk", "0",
                             "--positions", "3000"], capture_output=True, check=True).stdout
    path_b = subprocess.run([LOCK_PROBE, "gen", "--seeds", seeds, "--master", MASTER, "--chunk", "1",
                             "--positions", "3000"], capture_output=True, check=True).stdout
    ref = subprocess.run([LOCK_PROBE, "run"], input=path_a, capture_output=True, check=True).stdout
    return mg_format, seeds, path_a, path_b, ref


def tier_a_controls():
    import mg_compare
    mg_format, seeds, path_a, path_b, ref = build_fixtures()
    path_text = path_a.decode("ascii")

    # codec: decoding and re-encoding every record gives back the same bytes
    spans = mg_format.frames(ref)
    rebuilt = b"".join(mg_format.frame(mg_format.encode(mg_format.decode(ref[o:o + n]))) for o, n in spans)
    record("A0 codec round trip", rebuilt == ref, f"{len(spans)} frames, {len(ref)} bytes, identical after decode+encode: {rebuilt == ref}")
    first = mg_format.decode(ref[spans[0][0]:spans[0][0] + spans[0][1]])
    trailer = mg_format.decode(ref[spans[-1][0]:spans[-1][0] + spans[-1][1]])
    record("A0 lock transcript is sane", trailer["kind"] == 254 and trailer["records"] == len(spans) - 1 and trailer["hard"] == 0
           and first["kind"] == 0, f"trailer records {trailer.get('records')}, self-check failures {trailer.get('hard')}, "
           f"incremental/refresh differences {trailer.get('soft')}")

    # positive control: the lock probe against a byte-for-byte copy of itself
    same_exe = sha256_file(LOCK_PROBE) == sha256_file(LOCK_PROBE_COPY)
    copy = subprocess.run([LOCK_PROBE_COPY, "run"], input=path_a, capture_output=True, check=True).stdout
    res = mg_compare.compare(ref, copy, path_text)
    record("A1 positive: lock probe vs its byte-identical copy", same_exe and res.status == "EQUAL" and res.positions == 3000,
           f"copy sha256 equal: {same_exe}; status {res.status}; positions compared {res.positions}")

    # pick a record to corrupt: not in check, at least 6 legal moves, a legal capture-free quiet list, with null block
    target = None
    for i, (o, n) in enumerate(spans[:-1]):
        r = mg_format.decode(ref[o:o + n])
        if r["kind"] == 0 and len(r["legal"]) >= 6 and r["checkers_main"] == 0 and r["null"] is not None and i > 5:
            target = i
            break
    assert target is not None

    def mutated(fn, index=None):
        k = target if index is None else index
        o, n = spans[k]
        r = mg_format.decode(ref[o:o + n])
        fn(r)
        return ref[:o - 8] + mg_format.frame(mg_format.encode(r)) + ref[o + n:]

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

    def null_child(r):
        r["null"]["all"][0], r["null"]["all"][1] = r["null"]["all"][1], r["null"]["all"][0]

    def stale_probe(r):
        r["rev1_off"] += 1

    control("A2 negative: one legal move removed", "MISMATCH", ["legal move set", "missing"], mg_compare.compare(ref, mutated(remove_move), path_text))
    control("A3 negative: one move added", "MISMATCH", ["legal move set", "extra"], mg_compare.compare(ref, mutated(add_move), path_text))
    control("A4 negative: two adjacent legal moves swapped", "MISMATCH", ["order"], mg_compare.compare(ref, mutated(swap_moves), path_text))
    control("A5 negative: one checkers bit flipped", "MISMATCH", ["checkers"], mg_compare.compare(ref, mutated(flip_checkers), path_text))
    control("A6 negative: static eval net on + 1", "MISMATCH", ["eval", "net on"], mg_compare.compare(ref, mutated(eval_on), path_text))
    control("A7 negative: static eval net off + 1", "MISMATCH", ["eval", "net off"], mg_compare.compare(ref, mutated(eval_off), path_text))
    control("A8 negative: has_legal_move flipped", "MISMATCH", ["has_legal_move"], mg_compare.compare(ref, mutated(flip_has), path_text))
    control("A9 negative: checkers after a make flipped", "MISMATCH", ["checkers after"], mg_compare.compare(ref, mutated(child_flip), path_text))
    control("A10 negative: generated list order swapped", "MISMATCH", ["generated"], mg_compare.compare(ref, mutated(swap_generated), path_text))
    control("A11 negative: is_legal bit flipped", "MISMATCH", ["is_legal"], mg_compare.compare(ref, mutated(flip_legal_bit), path_text))
    control("A12 negative: gives_check bit flipped", "MISMATCH", ["gives_check"], mg_compare.compare(ref, mutated(flip_gives_check), path_text))
    control("A13 negative: null-move child list changed", "MISMATCH", ["null"], mg_compare.compare(ref, mutated(null_child), path_text))
    control("A14 negative: stale-cache probe value + 1", "MISMATCH", ["eval", "plies back"], mg_compare.compare(ref, mutated(stale_probe), path_text))

    # wrong position: the candidate holds another position's record at this index
    o, n = spans[target]
    o2, n2 = spans[target + 1]
    wrong = ref[:o - 8] + ref[o2 - 8:o2 + n2] + ref[o + n:]
    control("A15 negative: wrong position at one index", "MISMATCH", ["position"], mg_compare.compare(ref, wrong, path_text))
    # missing output: the last position record is gone while the trailer still announces it
    o, n = spans[-2]
    control("A16 negative: last record missing", "MALFORMED", ["missing"], mg_compare.compare(ref, ref[:o - 8] + ref[o + n:], path_text))
    # truncated in the middle of a record, and garbage in the middle
    o, n = spans[target]
    control("A17 negative: transcript truncated", "MALFORMED", ["truncated"], mg_compare.compare(ref, ref[:o + n // 2], path_text))
    control("A18 negative: garbage bytes inserted", "MALFORMED", ["magic"], mg_compare.compare(ref, ref[:o - 8] + b"garbage!" * 3 + ref[o - 8:], path_text))
    control("A19 negative: empty candidate output", "MALFORMED", ["empty"], mg_compare.compare(ref, b"", path_text))
    # a reference that is itself broken is a harness error, never a candidate verdict
    control("A20 negative: broken reference", "HARNESS_ERROR", ["reference"], mg_compare.compare(ref[:o + n // 2], ref, path_text))
    # input guard: two outputs made from different inputs must not be compared at all
    other = subprocess.run([LOCK_PROBE, "run"], input=path_b, capture_output=True, check=True).stdout
    res = mg_compare.compare_bound(ref, hashlib.sha256(path_a).hexdigest(), other, hashlib.sha256(path_b).hexdigest(), path_text)
    control("A21 negative: outputs of two different inputs", "HARNESS_ERROR", ["inputs differ"], res)
    # and if someone compares them anyway, the records disagree
    control("A22 negative: other chunk compared directly", "MISMATCH", ["position"], mg_compare.compare(ref, other, path_text))
    return seeds, path_a


def tier_r_controls(seeds, path_a):
    import uci_session
    batch = subprocess.run([LOCK_PROBE, "uciscript", "--perft", "2"], input=path_a, capture_output=True, check=True).stdout.decode("ascii")
    lines = [ln for ln in batch.splitlines() if ln][:2 * 800]          # 800 positions
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

    ref_lines = ref.splitlines()
    # index of the first move line of the 300th perft block
    seen, start = 0, None
    for i, ln in enumerate(ref_lines):
        if ln.startswith("nodes "):
            seen += 1
            if seen == 300:
                start = i + 1
                break
    assert start is not None and uci_session.MOVE_RX.match(ref_lines[start]) and uci_session.MOVE_RX.match(ref_lines[start + 1])

    def edit(fn):
        x = list(ref_lines)
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

    control("R2 negative: one move line removed", "MISMATCH", ["legal move set", "missing"], uci_session.compare_perft(ref, edit(drop_line), n_pos))
    control("R3 negative: two move lines swapped", "MISMATCH", ["order"], uci_session.compare_perft(ref, edit(swap_lines), n_pos))
    control("R4 negative: one reply count changed", "MISMATCH", ["count"], uci_session.compare_perft(ref, edit(change_count), n_pos))
    control("R4b negative: block whose counts do not add up", "MALFORMED", ["add up"], uci_session.compare_perft(ref, edit(inconsistent), n_pos))
    control("R5 negative: one whole block missing", "MALFORMED", ["missing"], uci_session.compare_perft(ref, edit(drop_block), n_pos))
    control("R6 negative: malformed line in a block", "MALFORMED", ["malformed"], uci_session.compare_perft(ref, edit(garbage), n_pos))
    control("R7 negative: engine reported an invalid FEN", "MALFORMED", ["invalid fen"], uci_session.compare_perft(ref, edit(invalid_fen), n_pos))
    control("R8 negative: broken reference output", "HARNESS_ERROR", ["reference"], uci_session.compare_perft(edit(drop_block), ref, n_pos))

    # wrong position on the candidate's side: another input file. The input guard must refuse, and the
    # outputs, compared anyway, must differ.
    lines2 = list(lines)
    lines2[2 * 299] = "position fen 4k3/8/8/8/8/8/8/4K2R w K - 0 1"
    in2 = os.path.join(WORK, "batch_r_wrongpos.uci")
    uci_session.write_batch(in2, lines2)
    out2 = os.path.join(WORK, "batch_r_wrongpos.out")
    uci_session.run_batch([LOCK_EXE_COPY], in2, out2, timeout=600)
    cand2 = open(out2, "r", encoding="ascii", errors="replace").read()
    res = uci_session.compare_perft_bound(ref, sha256_file(in_path), cand2, sha256_file(in2), n_pos)
    control("R9 negative: candidate was fed another input file", "HARNESS_ERROR", ["inputs differ"], res)
    control("R10 negative: wrong position, outputs compared directly", "MISMATCH", ["position 300"], uci_session.compare_perft(ref, cand2, n_pos))

    # the engine's own rejection of a FEN must be seen, not swallowed (real lock exe, invalid FEN in the input)
    lines3 = list(lines[:20])
    lines3[10] = "position fen 8/8/8/8/8/8/4k3/4K3 w - - 0 1"
    in3 = os.path.join(WORK, "batch_r_invalid.uci")
    n3 = uci_session.write_batch(in3, lines3)
    out3 = os.path.join(WORK, "batch_r_invalid.out")
    uci_session.run_batch([LOCK_EXE], in3, out3, timeout=300)
    t3 = open(out3, "r", encoding="ascii", errors="replace").read()
    control("R11 negative: real engine rejects a FEN inside a batch", "HARNESS_ERROR", ["invalid fen"], uci_session.compare_perft(t3, t3, n3))

    # stub engines: never answers, exits early, prints malformed lines
    stub = os.path.join(PACK, "harness", "stub_engine.py")
    for mode, want, words, name in (
            ("hang", "TIMEOUT", ["timeout"], "R12 negative: engine never answers (timeout)"),
            ("early", "MALFORMED", ["missing"], "R13 negative: engine exits early (missing output)"),
            ("garbage", "MALFORMED", ["malformed"], "R14 negative: engine prints malformed lines")):
        outp = os.path.join(WORK, f"stub_{mode}.out")
        run = uci_session.run_batch([PY, "-I", "-B", stub, mode], in_path, outp, timeout=8 if mode == "hang" else 120)
        text = open(outp, "r", encoding="ascii", errors="replace").read() if os.path.exists(outp) else ""
        if run.status != "OK":
            res = uci_session.Result(run.status, 0, f"run status {run.status}: {run.detail}")
        else:
            res = uci_session.compare_perft(ref, text, n_pos)
        control(name, want, words, res)
        alive = run.alive_after
        record(f"{name.split(':')[0]}b no process of this control is left running", not alive, f"child still alive: {alive}")

    # interactive session: a stub that never answers must give a timeout, not a hang of the harness
    try:
        eng = uci_session.Engine([PY, "-I", "-B", stub, "hang"])
        eng.handshake([])
        eng.send("position startpos")
        try:
            eng.perft(1, timeout=5)
            record("R15 negative: interactive timeout", False, "no timeout was raised")
        except uci_session.EngineTimeout as e:
            record("R15 negative: interactive timeout", "timeout" in str(e).lower(), f"raised: {e}")
        finally:
            eng.kill()
    except Exception as e:  # noqa: BLE001
        record("R15 negative: interactive timeout", False, f"unexpected {type(e).__name__}: {e}")


def main():
    print(pinguard3.ensure(), flush=True)
    for p in (LOCK_PROBE, LOCK_PROBE_COPY, LOCK_EXE, LOCK_EXE_COPY):
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
            _, seeds, path_a, _, _ = build_fixtures()
        tier_r_controls(seeds, path_a)
    except Exception as e:  # noqa: BLE001
        record("R-tier controls did not complete", False, f"{type(e).__name__}: {e}")
    n, good = len(RESULTS), sum(1 for r in RESULTS if r)
    print(f"SELFTEST {'PASS' if good == n else 'FAIL'} {good}/{n}")
    return 0 if good == n else 3


if __name__ == "__main__":
    sys.exit(main())
