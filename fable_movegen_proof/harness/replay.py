"""replay.py - run counted ledger rows again and compare every hash with the row (job 3, standard library only).

  aux NAME CHUNK CAND[,CAND...]   tier A: regenerate the chunk with the lock probe, run the lock probe and the
                                  candidate probe on it, compare the transcripts, and compare the sha256 of the
                                  path and of both transcript bodies with the counted row of fuzz_aux\\ledger.tsv
  uci NAME CHUNK CAND[,CAND...]   tier R: the same chunk as a UCI batch through the lock exe and the candidate
                                  exe; the sha256 of the batch input and of both outputs against fuzz_uci\\ledger.tsv

NAME is the seeds file of the chunk (v1 for chunks 0-99, v2 for 100-199). A replay writes
out\\job3\\runs\\replay\\<tier>_<CAND>_chunk<NNN>.json and changes no ledger: it checks a counted row, it is not a
new count. Exit 0 = every row was reproduced, 3 = something differs, 2 = no counted row for that candidate and chunk.
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fuzz  # noqa: E402
import mg_compare  # noqa: E402
import pinguard3  # noqa: E402
import uci_session  # noqa: E402


def counted_row(tier, cand, chunk):
    """The first OK row of a candidate and chunk: the one that counts."""
    return next((w for w in fuzz.read_ledger(tier) if w["cand"] == cand and int(w["chunk"]) == chunk and w["status"] == "OK"), None)


def save(tier, cand, chunk, receipt):
    d = os.path.join(fuzz.OUT, "runs", "replay")
    os.makedirs(d, exist_ok=True)
    with open(os.path.join(d, f"{tier}_{cand}_chunk{chunk:03d}.json"), "w", encoding="ascii", newline="\n") as f:
        json.dump(receipt, f, indent=1)


def reproduced(row, got, status_ok):
    """A row is reproduced when the comparison of this run is clean and every hash of this run is the row's."""
    same = {k: got[k] == row.get(k) for k in got}
    return bool(status_ok) and bool(same) and all(same.values()), same


def finish(tier, name, cand, chunk, row, got, compared, status_ok):
    ok, same = reproduced(row, got, status_ok)
    save(tier, cand, chunk, {"check": "replay", "tier": tier, "seeds": name, "chunk": chunk, "cand": cand, "status": "REPRODUCED" if ok else "DIFFERS",
                             "comparison": compared, "row_written": row["when"], "hashes_of_this_run": got, "equal_to_the_row": same, "when": fuzz.now(),
                             "meaning": "the counted ledger row was produced again from its definition: same input, same outputs, same binaries"})
    print(f"{fuzz.now()} replay tier {'A' if tier == 'aux' else 'R'} chunk {chunk} {cand}: {'REPRODUCED' if ok else 'DIFFERS'}; {compared}; "
          f"hashes equal to the row: {sum(same.values())} of {len(same)}" + ("" if ok else f"; not equal: {[k for k, v in same.items() if not v]}"), flush=True)
    return ok


def replay_aux(name, chunk, cands):
    rows = {c: counted_row("aux", c, chunk) for c in cands}
    if not all(rows.values()):
        print(f"no counted tier A row for chunk {chunk}: {[c for c, w in rows.items() if not w]}")
        return 2
    path, _ = fuzz.gen_chunk(name, chunk)
    path_sha = fuzz.sha256(path)
    ref, _, code = fuzz.run_probe([fuzz.probe("LOCK"), "run"], path)
    seeds = f"{name}:{fuzz.sha256_file(fuzz.seeds_path(name))[:16]}"
    all_ok = code == 0
    for cand in cands:
        tr, _, ccode = fuzz.run_probe([fuzz.probe(cand), "run"], path)
        res = mg_compare.compare_bound(ref, path_sha, tr, path_sha, path.decode("ascii"), expect_tag=cand, expect_positions=fuzz.CHUNK)
        got = {"seeds": seeds, "path_sha256": path_sha, "ref_sha256": fuzz.body_sha(ref), "cand_sha256": fuzz.body_sha(tr),
               "lock_probe_sha256": fuzz.sha256_file(fuzz.probe("LOCK")), "cand_probe_sha256": fuzz.sha256_file(fuzz.probe(cand)),
               "harness_sha256": fuzz.harness_sha()}
        all_ok &= finish("aux", name, cand, chunk, rows[cand], got, f"{res.status} {res.positions} records, probe exits {code} / {ccode}",
                         code == 0 and ccode == 0 and res.status == "EQUAL" and res.positions == fuzz.CHUNK)
        del tr
    return 0 if all_ok else 3


def replay_uci(name, chunk, cands, depth=2):
    rows = {c: counted_row("uci", c, chunk) for c in cands}
    if not all(rows.values()):
        print(f"no counted tier R row for chunk {chunk}: {[c for c, w in rows.items() if not w]}")
        return 2
    tmp = os.path.join(fuzz.OUT, "tmp")
    path, _ = fuzz.gen_chunk(name, chunk)
    path_sha = fuzz.sha256(path)
    expect_file = os.path.join(tmp, f"replay_chunk_{chunk:03d}.expect")
    script, err, code = fuzz.run_probe([fuzz.probe("LOCK"), "uciscript", "--perft", str(depth), "--expect", expect_file], path)
    if code != 0:
        print(f"uciscript failed: {err[-300:]}")
        return 3
    expect_lines = open(expect_file, "r", encoding="ascii").read().split("\n")
    in_file = os.path.join(tmp, f"replay_chunk_{chunk:03d}.uci")
    n = uci_session.write_batch(in_file, [ln for ln in script.decode("ascii").splitlines() if ln])
    in_sha = fuzz.sha256_file(in_file)
    ref_file = os.path.join(tmp, f"replay_chunk_{chunk:03d}.LOCK.out")
    run = uci_session.run_batch([fuzz.exe("LOCK")], in_file, ref_file, timeout=14400)
    ref_text = open(ref_file, "r", encoding="ascii", errors="replace").read()
    tie = uci_session.check_tie(ref_text, expect_lines, n)
    seeds = f"{name}:{fuzz.sha256_file(fuzz.seeds_path(name))[:16]}"
    all_ok = run.status == "OK" and tie.status == "EQUAL" and n == fuzz.CHUNK
    for cand in cands:
        out_file = os.path.join(tmp, f"replay_chunk_{chunk:03d}.{cand}.out")
        crun = uci_session.run_batch([fuzz.exe(cand)], in_file, out_file, timeout=14400)
        text = open(out_file, "r", encoding="ascii", errors="replace").read()
        res = uci_session.compare_perft_bound(ref_text, in_sha, text, in_sha, n)
        got = {"seeds": seeds, "path_sha256": path_sha, "input_sha256": in_sha, "ref_out_sha256": fuzz.sha256(ref_text.encode("ascii", "replace")),
               "cand_out_sha256": fuzz.sha256(text.encode("ascii", "replace")), "lock_exe_sha256": fuzz.sha256_file(fuzz.exe("LOCK")),
               "cand_exe_sha256": fuzz.sha256_file(fuzz.exe(cand)), "tie": f"lock exe = lock probe on {tie.positions}"}
        all_ok &= finish("uci", name, cand, chunk, rows[cand], got, f"{res.status} {res.positions} perft blocks, runs {run.status} / {crun.status}, tie {tie.status}",
                         run.status == "OK" and crun.status == "OK" and tie.status == "EQUAL" and res.status == "EQUAL" and res.positions == n == fuzz.CHUNK)
        for p in (out_file, out_file + ".err"):
            if os.path.exists(p):
                os.remove(p)
    for p in (expect_file, in_file, ref_file, ref_file + ".err"):
        if os.path.exists(p):
            os.remove(p)
    return 0 if all_ok else 3


def main(argv):
    if len(argv) != 5 or argv[1] not in ("aux", "uci"):
        print(__doc__)
        return 1
    print(pinguard3.ensure(), flush=True)
    fuzz.guard()
    cands = argv[4].split(",")
    return (replay_aux if argv[1] == "aux" else replay_uci)(argv[2], int(argv[3]), cands)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
