"""R11 self-test of the data stage on synthetic FPOS/FHCE shards (no PC data is read or written).

Checks, with expected values computed independently here (Python sets in registry order):
  1 holdout shard first; a training copy of a holdout position is dropped; duplicates inside and across shards keep
    the first occurrence; bad rows (two white kings, result code 3) are marked bad and never shadow anything;
  2 a superseding subset source replaces its target shard and passes the supersede check;
  3 a partial run (--max-convert 2) + resume gives byte-identical outputs to an uninterrupted run;
  4 an incremental run picks up a new shard, converts only it, leaves earlier outputs untouched, and drops its rows
    that equal earlier rows;
  5 a changed input of a registered, unconverted shard makes the stage FAIL;
  6 every output passes the writer's verify (loader reader, square by square, side-car .hce), and a planted
    one-byte corruption is rejected by verify;
  7 the multi-pass dedup (tiny memory budget) equals the single-pass result.
Usage: test_r11_data.py <writer_exe> <scratch_dir>   (scratch_dir must not exist yet)
Prints "R11 DATA SELFTEST PASS" and exits 0 when every check holds.
"""
from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "pipeline"))
import r11_common as C  # noqa: E402
import r11_data as D  # noqa: E402

RNG = np.random.default_rng(20261030)
FAILS: list[str] = []


def check(cond: bool, what: str) -> None:
    print(("ok   " if cond else "FAIL ") + what, flush=True)
    if not cond:
        FAILS.append(what)


def attacked(sq: np.ndarray, target: int, by_black: bool) -> bool:
    """Is square `target` attacked by the pieces of one colour (codes 1-6 white, 7-12 black)?"""
    tf, tr = target % 8, target // 8
    base = 6 if by_black else 0

    def at(f: int, r: int) -> int:
        return int(sq[r * 8 + f]) if 0 <= f < 8 and 0 <= r < 8 else -1

    pr = tr - 1 if not by_black else tr + 1  # a white pawn attacks upwards, so it stands one rank below
    if at(tf - 1, pr) == base + 1 or at(tf + 1, pr) == base + 1:
        return True
    for df, dr in ((1, 2), (2, 1), (-1, 2), (-2, 1), (1, -2), (2, -1), (-1, -2), (-2, -1)):
        if at(tf + df, tr + dr) == base + 2:
            return True
    for df in (-1, 0, 1):
        for dr in (-1, 0, 1):
            if (df or dr) and at(tf + df, tr + dr) == base + 6:
                return True
    for dirs, pieces in ((((1, 1), (1, -1), (-1, 1), (-1, -1)), (base + 3, base + 5)),
                         (((1, 0), (-1, 0), (0, 1), (0, -1)), (base + 4, base + 5))):
        for df, dr in dirs:
            f, r = tf + df, tr + dr
            while 0 <= f < 8 and 0 <= r < 8:
                c = at(f, r)
                if c:
                    if c in pieces:
                        return True
                    break
                f += df
                r += dr
    return False


def random_rows(n: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Random positions the binpack writer accepts: one king each, no pawn on rank 1/8, side not to move not in
    check (chess::Position::trySet rejects that)."""
    boards = np.zeros((n, 32), np.uint8)
    stm = RNG.integers(0, 2, n)
    for i in range(n):
        while True:
            sq = np.zeros(64, np.uint8)
            wk, bk = RNG.choice(64, 2, replace=False)
            sq[wk], sq[bk] = 6, 12
            free = [s for s in range(64) if sq[s] == 0]
            for s in RNG.choice(free, size=int(RNG.integers(2, 12)), replace=False):
                code = int(RNG.choice([1, 2, 3, 4, 5, 7, 8, 9, 10, 11]))
                if code in (1, 7) and (s < 8 or s >= 56):
                    code = 2
                sq[s] = code
            black_to_move = bool(stm[i])
            # the king of the side NOT to move must not be attacked by the side to move
            other_king = bk if not black_to_move else wk
            if not attacked(sq, int(other_king), by_black=black_to_move):
                break
        boards[i] = sq[0::2] | (sq[1::2] << 4)
    scores = RNG.integers(-3000, 3001, n).astype(np.int16)
    meta = (stm | (RNG.integers(0, 3, n) << 1)).astype(np.uint8)
    return boards, scores, meta


def write_fpos(path: str, boards: np.ndarray, scores: np.ndarray, meta: np.ndarray, hce: np.ndarray | None = None) -> None:
    n = boards.shape[0]
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "wb") as f:
        f.write(b"FPOS" + (1).to_bytes(4, "little") + n.to_bytes(8, "little"))
        f.write(boards.tobytes())
        f.write(scores.astype("<i2").tobytes())
        f.write(meta.tobytes())
    with open(path + ".info", "w", newline="\n") as f:
        f.write(f"lines={n}\nrecords={n}\nbad=0\n")
    if hce is not None:
        hp = path[: -len(".pos")] + ".hce"
        with open(hp, "wb") as f:
            f.write(b"FHCE" + (1).to_bytes(4, "little") + n.to_bytes(8, "little"))
            f.write(hce.astype("<i2").tobytes())


def make_world(base: str) -> dict:
    """Synthetic sources a (3 shards), b (2 shards), sup (subset of a_002). Returns the shard arrays."""
    w = {}
    for name, n in (("a_001", 6000), ("a_002", 7000), ("a_003", 8000), ("b_001", 5000), ("b_002", 9000)):
        w[name] = list(random_rows(n))
    # duplicates: a_003 gets 300 rows of the holdout a_001 and 200 internal repeats; b_001 gets 150 rows of a_003
    b, s, m = w["a_003"]
    b[100:400], m[100:400] = w["a_001"][0][1000:1300], w["a_001"][2][1000:1300]
    b[5000:5200], m[5000:5200] = b[200:400], m[200:400]  # internal repeats (of rows that are holdout copies too)
    b[6000:6200], m[6000:6200] = b[2000:2200], m[2000:2200]
    bb, sb, mb = w["b_001"]
    bb[0:150], mb[0:150] = b[3000:3150], m[3000:3150]
    # bad rows: two white kings in b_002 rows 10..19, result code 3 in rows 20..24; a copy of a bad row's board in
    # b_001 row 4000 must still be kept (bad rows never shadow)
    b2, s2, m2 = w["b_002"]
    for i in range(10, 20):
        sq = np.zeros(64, np.uint8)
        sq[0], sq[63], sq[27] = 6, 12, 6
        b2[i] = sq[0::2] | (sq[1::2] << 4)
    m2[20:25] = (m2[20:25] & 1) | (3 << 1)
    bb[4000], mb[4000] = b2[22], (m2[22] & 1) | (1 << 1)
    for name, (b_, s_, m_) in w.items():
        src = name.split("_")[0]
        hce = RNG.integers(-2000, 2001, b_.shape[0]).astype(np.int16)
        w[name].append(hce)
        write_fpos(os.path.join(base, src, f"{name}.pos"), b_, s_, m_, hce)
    # superseding subset of a_002: every third row, original order, same scores/meta/hce
    b, s, m, h = w["a_002"]
    sel = np.arange(0, b.shape[0], 3)
    w["sup_x"] = [b[sel].copy(), s[sel].copy(), m[sel].copy(), h[sel].copy()]
    write_fpos(os.path.join(base, "sup", "sup_x.pos"), *w["sup_x"])
    return w


def config(root: str, src_dir: str, writer: str, mem_gb: float, keys_cache: bool = False,
           disk_floor_gb: float = 1.0) -> dict:
    return {
        "root": root,
        "limits": {"min_free_ram_gb": 0.5, "min_free_commit_gb": 0.5, "max_cpu_percent": 100.0,
                   "min_disk_free_gb": disk_floor_gb, "poll_seconds": 1.0},
        "data": {
            "dir": os.path.join(root, "data"), "writer_exe": writer,
            "sources": [
                {"name": "a", "pos_glob": os.path.join(src_dir, "a", "a_[0-9][0-9][0-9].pos"),
                 "ready": {"info_suffix": ".info", "min_age_s": 0},
                 "hce": {"dir": os.path.join(src_dir, "a"), "strip": ".pos", "suffix": ".hce"}},
                {"name": "b", "pos_glob": os.path.join(src_dir, "b", "b_[0-9][0-9][0-9].pos"),
                 "ready": {"info_suffix": ".info", "min_age_s": 0},
                 "hce": {"dir": os.path.join(src_dir, "b"), "strip": ".pos", "suffix": ".hce"}},
                {"name": "sup", "pos_glob": os.path.join(src_dir, "sup", "sup_x.pos"),
                 "hce": {"dir": os.path.join(src_dir, "sup"), "strip": ".pos", "suffix": ".hce"},
                 "supersedes": ["a:a_002"]},
            ],
            "holdout": ["a:a_001"], "dedup_mem_gb": mem_gb, "chunk_rows": 1500, "ply": 40, "verify": "all",
            "keys_cache": keys_cache, "disk_margin_gb": 0.0, "convert_order": ["holdout", "sup", "b", "a"],
        },
    }


def expected(w: dict, order: list[str]) -> dict:
    seen = set()
    res = {}
    for name in order:
        b, s, m, h = w[name]
        bad = C.bad_rows(b, m)
        kept = []
        for i in range(b.shape[0]):
            if bad[i]:
                continue
            k = (b[i].tobytes(), int(m[i] & 1))
            if k in seen:
                continue
            seen.add(k)
            kept.append(i)
        res[name] = {"kept": len(kept), "bad": int(bad.sum()), "rows": b.shape[0], "kept_idx": kept}
    return res


def run_stage(cfg: dict, max_convert=None) -> dict:
    log = C.Log(os.path.join(cfg["root"], "logs", "pipeline.log"), "data")
    gov = C.Governor(cfg["root"], C.limits_from(cfg), log)
    return D.run(cfg, log, gov, max_convert)


def outputs_sha(cfg: dict) -> dict:
    man = C.read_json(os.path.join(cfg["data"]["dir"], "MANIFEST.json"))
    return {r["id"]: (r["binpack"] or {}).get("sha256") for r in man["shards"]}


def main() -> int:
    writer, scratch = sys.argv[1], sys.argv[2]
    if os.path.exists(scratch):
        print(f"scratch dir {scratch} exists; give a new one")
        return 2
    src = os.path.join(scratch, "src")
    w = make_world(src)
    order = ["a_001", "a_003", "b_001", "b_002", "sup_x"]
    exp = expected(w, order)

    # 1 + 2 + 6: interrupted run (partial + resume), tiny memory budget -> several passes
    cfg = config(os.path.join(scratch, "run_partial"), src, writer, mem_gb=0.0004)
    man = run_stage(cfg, max_convert=2)
    check(not man["complete"], "partial run (--max-convert 2) reports incomplete")
    man = run_stage(cfg)
    check(man["complete"], "resumed run completes")
    reg = C.read_json(os.path.join(cfg["data"]["dir"], "state", "registry.json"))
    check([e["id"].split(":")[1] for e in reg["order"]] == order, f"registry order holdout-first: {[e['id'] for e in reg['order']]}")
    check(reg["superseded"] == {"a:a_002": ["sup:sup_x"]}, "a_002 superseded by sup_x")
    sup = C.read_json(os.path.join(cfg["data"]["dir"], "state", "supersede_a__a_002.json"))
    check(bool(sup and sup["ok"] and sup["by"][0]["hce_equal"] == w["sup_x"][0].shape[0]),
          "supersede check ok (found, score, meta, hce, order)")
    for r in man["shards"]:
        name = r["id"].split(":")[1]
        e = exp[name]
        dec = C.read_json(D.decision_paths(cfg["data"], r["id"])[1])
        check(dec["kept"] == e["kept"] and dec["bad"] == e["bad"],
              f"{name}: kept {dec['kept']} (expected {e['kept']}), bad {dec['bad']} (expected {e['bad']})")
        check(r["records"] == e["kept"], f"{name}: {r['records']} records written (writer_bad must be 0)")
        check(r["verified"], f"{name}: output verified by the loader reader")
        # exact row set: decoded dest map == expected kept rows
        dest = C.unpack_dest(np.fromfile(D.decision_paths(cfg["data"], r["id"])[0], np.uint8), e["rows"])
        want = np.zeros(e["rows"], np.uint8)
        want[e["kept_idx"]] = C.DEST_HOLD if name == "a_001" else C.DEST_TRAIN
        bad = C.bad_rows(w[name][0], w[name][2])
        want[bad] = C.DEST_BAD
        check(np.array_equal(dest, want), f"{name}: dest map equals the independent expectation row by row")
    t = man["totals"]
    check(t["holdout"] == exp["a_001"]["kept"], f"holdout records {t['holdout']} == unique rows of a_001")
    check(exp["a_003"]["kept"] <= w["a_003"][0].shape[0] - 300 - 200, "a_003 lost its holdout copies and repeats")

    # conversion followed the value order: holdout, sup, b (newest first), a
    log_text = open(os.path.join(cfg["root"], "logs", "pipeline.log"), encoding="utf-8").read()
    conv = [ln.split("converted ")[1].split(" ->")[0] for ln in log_text.splitlines() if "] INFO converted " in ln]
    check(conv == ["a:a_001", "sup:sup_x", "b:b_002", "b:b_001", "a:a_003"], f"conversion order by value: {conv}")

    # 3: an uninterrupted run with a big memory budget and the keys cache gives byte-identical outputs
    cfg1 = config(os.path.join(scratch, "run_single"), src, writer, mem_gb=1.0, keys_cache=True)
    run_stage(cfg1)
    check(outputs_sha(cfg) == outputs_sha(cfg1),
          "partial+resume (multi-pass, keys recomputed) == single run (one pass, keys cache): same sha256 per output")

    # 3b: disk floor: nothing is converted when every shard would cross the floor; the run stays resumable
    cfg_d = config(os.path.join(scratch, "run_disk"), src, writer, mem_gb=1.0, disk_floor_gb=1e6)
    man_d = run_stage(cfg_d)
    log_d = open(os.path.join(cfg_d["root"], "logs", "pipeline.log"), encoding="utf-8").read()
    check(not man_d["complete"] and man_d["totals"]["train"] == 0 and "disk: stop before" in log_d,
          "disk floor stops the conversion before any output is written")
    cfg_d["limits"]["min_disk_free_gb"] = 1.0
    man_d = run_stage(cfg_d)
    check(man_d["complete"] and outputs_sha(cfg_d) == outputs_sha(cfg1), "after space is back the rerun completes identically")

    # 3c: protected output folders are refused before anything is written
    cfg_p = config(os.path.join(scratch, "run_protected"), src, writer, mem_gb=1.0)
    cfg_p["data"]["dir"] = "F:/forge_j1_data/r11_selftest_must_not_exist"
    try:
        run_stage(cfg_p)
        check(False, "protected output folder must be refused")
    except C.StageFailed as e:
        check("protected" in str(e) and not os.path.exists(cfg_p["data"]["dir"]), f"protected folder refused: {e}")

    # 4: incremental shard b_003 (new rows + copies of earlier rows from a_001, b_002 and sup_x)
    before = outputs_sha(cfg)
    b3 = random_rows(4000)
    b3[0][0:100], b3[2][0:100] = w["a_001"][0][0:100], w["a_001"][2][0:100]
    b3[0][100:200], b3[2][100:200] = w["sup_x"][0][0:100], w["sup_x"][2][0:100]
    h3 = RNG.integers(-2000, 2001, 4000).astype(np.int16)
    w["b_003"] = list(b3) + [h3]
    write_fpos(os.path.join(src, "b", "b_003.pos"), *w["b_003"])
    man = run_stage(cfg)
    exp2 = expected(w, order + ["b_003"])
    after = outputs_sha(cfg)
    check(all(after[k] == v for k, v in before.items()), "incremental run left earlier outputs untouched")
    r3 = next(r for r in man["shards"] if r["id"] == "b:b_003")
    check(r3["records"] == exp2["b_003"]["kept"] and r3["records"] <= 4000 - 200,
          f"b_003 kept {r3['records']} == expected {exp2['b_003']['kept']} (copies of earlier rows dropped)")
    reg = C.read_json(os.path.join(cfg["data"]["dir"], "state", "registry.json"))
    check(reg["order"][-1]["id"] == "b:b_003", "new shard appended at the end of the registry")

    # 5: changed input of a registered, unconverted shard -> FAIL
    cfg5 = config(os.path.join(scratch, "run_changed"), src, writer, mem_gb=1.0)
    run_stage(cfg5, max_convert=0)
    victim = os.path.join(src, "b", "b_002.pos")
    saved = os.path.join(scratch, "b_002.pos.orig")
    shutil.copyfile(victim, saved)
    with open(victim, "r+b") as f:
        f.seek(100)
        byte = f.read(1)
        f.seek(100)
        f.write(bytes([byte[0] ^ 0x10]))
    try:
        run_stage(cfg5)
        check(False, "changed input must fail")
    except C.StageFailed as e:
        check("input changed" in str(e), f"changed input detected: {e}")
    shutil.copyfile(saved, victim)  # restore our own synthetic file (scratch only)

    # 6b: planted corruption is rejected by verify
    man = C.read_json(os.path.join(cfg["data"]["dir"], "MANIFEST.json"))
    r = next(x for x in man["shards"] if x["id"] == "a:a_003")
    bad_copy = os.path.join(scratch, "corrupt_a_003.binpack")
    shutil.copyfile(r["binpack"]["path"], bad_copy)
    with open(bad_copy, "r+b") as f:
        f.seek(8 + 34 * 10 + 5)
        byte = f.read(1)
        f.seek(8 + 34 * 10 + 5)
        f.write(bytes([byte[0] ^ 0x04]))
    e3 = next(x for x in reg["order"] if x["id"] == "a:a_003")
    v = subprocess.run([writer, "verify", "--pos", e3["pos"], "--dest", D.decision_paths(cfg["data"], "a:a_003")[0],
                        "--code", "1", "--file", bad_copy], capture_output=True, text=True)
    check(v.returncode != 0 and "VERIFY FAILED" in v.stdout, "planted 1-byte corruption rejected by verify")

    # 7b CR fix 10: the registry carries full sha256s; a wrong pin refuses registration
    reg = C.read_json(os.path.join(cfg["data"]["dir"], "state", "registry.json"))
    check(all(len(e.get("sha256_pos", "")) == 64 for e in reg["order"]) and
          all(len(e.get("sha256_hce", "")) == 64 for e in reg["order"] if e.get("hce_origin") == "source"),
          "every registered input has a full sha256 (pos and source hce)")
    cfg_pin = config(os.path.join(scratch, "run_pin"), src, writer, mem_gb=1.0)
    cfg_pin["data"]["sources"][2]["pins"] = {"sup_x.pos": "0" * 64}
    try:
        run_stage(cfg_pin)
        check(False, "a wrong pin must refuse registration")
    except C.StageFailed as e:
        check("pinned" in str(e), f"a wrong pin refuses registration: {str(e)[:100]}")

    # 8 CR fix 6: a row the cheap checks let through but the converter rejects (white pawn on a1) fails the shard
    wsrc = os.path.join(scratch, "src_writerdrop")
    wb, ws, wm = random_rows(50)
    sq = np.zeros(64, np.uint8)
    sq[4], sq[60], sq[0] = 6, 12, 1  # Ke1, ke8, Pa1: one king each, valid codes -> passes bad_rows()
    wb[7] = sq[0::2] | (sq[1::2] << 4)
    wm[7] = 0 | (1 << 1)  # white to move, draw
    check(not C.bad_rows(wb[7:8], wm[7:8]).any(), "the planted row passes the cheap row checks")
    write_fpos(os.path.join(wsrc, "a", "a_001.pos"), wb, ws, wm, RNG.integers(-100, 100, 50).astype(np.int16))
    b2, s2, m2 = random_rows(40)
    write_fpos(os.path.join(wsrc, "b", "b_001.pos"), b2, s2, m2, RNG.integers(-100, 100, 40).astype(np.int16))
    wsup = os.path.join(wsrc, "sup")
    os.makedirs(wsup)
    cfg_w = config(os.path.join(scratch, "run_writerdrop"), wsrc, writer, mem_gb=1.0)
    cfg_w["data"]["sources"] = cfg_w["data"]["sources"][:2]
    cfg_w["data"]["holdout"] = ["b:b_001"]
    try:
        run_stage(cfg_w)
        check(False, "a dropped row must fail the stage")
    except C.StageFailed as e:
        check("writer dropped" in str(e), f"writer drop fails the stage: {str(e)[:120]}")
    marker = D.out_marker(cfg_w["data"], "a:a_001")
    final = os.path.join(cfg_w["data"]["dir"], "train", "a__a_001.binpack")
    check(not os.path.exists(marker) and not os.path.exists(final), "no done marker and no final output for that shard")
    tdir = os.path.dirname(final)
    leftovers = [x for x in os.listdir(tdir)] if os.path.isdir(tdir) else []
    check(leftovers == [], f"CR fix 7: the failed conversion left no .part files behind ({leftovers})")
    man = C.read_json(os.path.join(cfg["data"]["dir"], "MANIFEST.json"))
    vb = [C.read_json(D.out_marker(cfg["data"], r["id"])).get("verify", {}).get("verified_before_rename")
          for r in man["shards"] if r["records"]]
    check(vb and all(vb), f"CR fix 7: every output was verified as .part before its rename ({len(vb)} outputs)")

    print(f"\n{len(FAILS)} failed checks")
    print("R11 DATA SELFTEST " + ("PASS" if not FAILS else "FAIL"))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main())
