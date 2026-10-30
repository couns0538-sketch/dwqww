"""R11 CR fix 5: holdout + dedup-order test on the REAL data stage output. Nothing is used for training until it passes.

Checks (registry, decisions and, when present, the converted outputs of <data.dir>):
  1 registry: the configured holdout shards (forge_selfplay_013, _014) are entries #0 and #1 and flagged holdout;
    no other entry is holdout; superseded shards are not registered;
  2 decisions: holdout shards carry no TRAIN code (only HOLD / DROP / BAD), every other shard no HOLD code;
  3 outputs: train_files.txt names no file of a holdout shard, holdout_files.txt only holdout-shard files;
  4 no leak: no TRAIN row of any shard has the position key of ANY row of the holdout shards (full scan, every row);
  5 dedup order on a slice of the key space (top-16-bit key prefix < --sample-prefixes of 65536): every key has
    exactly one kept row (TRAIN/HOLD) unless all its rows are bad, and the kept row is the FIRST occurrence in
    registry order (shard index, row); plus no key is kept twice.
On PASS it writes <data.dir>/HOLDOUT_TEST.json with the sha256 of the registry, of all decision files and of the two
file lists; the train stage refuses R11 data whose current hashes differ from a passing record.
Usage: test_r11_holdout_real.py --config <cfg.json> [--sample-prefixes 2048] [--no-verify-inputs]
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "pipeline"))
import r11_common as C  # noqa: E402
import r11_data as D  # noqa: E402

FAILS: list[str] = []


def check(cond: bool, what: str) -> bool:
    print(("ok   " if cond else "FAIL ") + what, flush=True)
    if not cond:
        FAILS.append(what)
    return cond


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--sample-prefixes", type=int, default=2048)
    ap.add_argument("--no-verify-inputs", action="store_true")
    a = ap.parse_args(argv)
    cfg = C.read_json(a.config)
    C.set_idle_background(C.affinity_from_cfg(cfg))
    d = cfg["data"]
    t0 = time.time()
    reg = C.read_json(os.path.join(d["dir"], "state", "registry.json"))
    if not reg:
        print("FAIL no registry")
        return 1
    order = reg["order"]
    hold_ids = list(d.get("holdout", []))
    # 1 registry
    check([e["id"] for e in order[: len(hold_ids)]] == hold_ids and all(e["holdout"] for e in order[: len(hold_ids)]),
          f"holdout shards {hold_ids} are registry entries #0..#{len(hold_ids) - 1} and flagged holdout")
    check(not any(e["holdout"] for e in order[len(hold_ids):]), "no other registry entry is holdout")
    check(not any(e["id"] in reg.get("superseded", {}) for e in order), f"superseded shards are not registered: "
          f"{list(reg.get('superseded', {}))}")
    decided = [e for e in order if os.path.isfile(D.decision_paths(d, e["id"])[1])]
    check(len(decided) == len(order), f"every registered shard has a decision ({len(decided)}/{len(order)})")
    sealed = C.SealedInputs()
    if not a.no_verify_inputs:
        for e in order:
            sealed.verify(e["pos"], e["sha256_pos"], f"{e['id']} .pos")
        check(True, f"all {len(order)} inputs match their registered full sha256")
    # 2 decisions + collect the holdout keys
    step = int(d.get("chunk_rows", 2_000_000))
    hold_keys = []
    dests = {}
    for e in order:
        dp, dj = D.decision_paths(d, e["id"])
        dest = C.unpack_dest(np.fromfile(dp, np.uint8), e["rows"])
        dests[e["id"]] = dest
        if e["holdout"]:
            check(not (dest == C.DEST_TRAIN).any(), f"{e['id']}: no TRAIN code ({int((dest == C.DEST_HOLD).sum())} "
                                                    f"holdout rows)")
        elif (dest == C.DEST_HOLD).any():
            check(False, f"{e['id']}: HOLD code in a training shard")
    check(not FAILS, "decision codes: TRAIN only outside the holdout shards, HOLD only inside")
    for e in order[: len(hold_ids)]:
        for start in range(0, e["rows"], step):
            cnt = min(step, e["rows"] - start)
            hold_keys.append(C.position_keys(C.read_boards(e["pos"], e["rows"], start, cnt),
                                             C.read_meta(e["pos"], e["rows"], start, cnt)))
    hk = np.unique(np.concatenate(hold_keys)) if hold_keys else np.zeros(0, np.uint64)
    print(f"holdout positions (unique keys over ALL rows of the holdout shards): {hk.size}", flush=True)
    # 4 + 5 one pass over every shard
    lo_sample = a.sample_prefixes
    leak = 0
    ks, idx, rows, codes = [], [], [], []
    for e in order:
        dest = dests[e["id"]]
        for start in range(0, e["rows"], step):
            cnt = min(step, e["rows"] - start)
            k = C.position_keys(C.read_boards(e["pos"], e["rows"], start, cnt), C.read_meta(e["pos"], e["rows"], start, cnt))
            dd = dest[start:start + cnt]
            if not e["holdout"]:
                tr = k[dd == C.DEST_TRAIN]
                if tr.size and hk.size:
                    p = np.minimum(np.searchsorted(hk, tr), hk.size - 1)
                    leak += int((hk[p] == tr).sum())
            sel = np.nonzero((k >> np.uint64(48)).astype(np.int64) < lo_sample)[0]
            ks.append(k[sel])
            idx.append(np.full(sel.size, e["index"], np.int32))
            rows.append((sel + start).astype(np.int64))
            codes.append(dd[sel])
    check(leak == 0, f"no TRAIN row shares a position with any row of the holdout shards (hits {leak})")
    K = np.concatenate(ks)
    I = np.concatenate(idx)
    R = np.concatenate(rows)
    S = np.concatenate(codes)
    o = np.lexsort((R, I, K))  # by key, then registry index, then row = the global first-occurrence order
    K, I, R, S = K[o], I[o], R[o], S[o]
    good = S != C.DEST_BAD
    kept = (S == C.DEST_TRAIN) | (S == C.DEST_HOLD)
    first_good = np.zeros(K.size, bool)  # first non-bad row of each key
    seen_key = None
    # vectorised: position of the first good row per key
    gi = np.nonzero(good)[0]
    if gi.size:
        kg = K[gi]
        start_of_key = np.ones(gi.size, bool)
        start_of_key[1:] = kg[1:] != kg[:-1]
        first_good[gi[start_of_key]] = True
    wrong_kept = int((kept & ~first_good).sum())
    missing_kept = int((first_good & ~kept).sum())
    uk, counts = np.unique(K[kept], return_counts=True)
    check(wrong_kept == 0 and missing_kept == 0 and int((counts > 1).sum()) == 0,
          f"dedup order on {K.size:,} rows (key prefixes [0, {lo_sample}) of 65536): the kept row is always the first "
          f"good occurrence in registry order (wrong kept {wrong_kept}, first occurrence not kept {missing_kept}, keys kept "
          f"twice {int((counts > 1).sum())})")
    del seen_key
    # 3 outputs
    man = C.read_json(os.path.join(d["dir"], "MANIFEST.json"))
    hold_set = set(hold_ids)
    tf = [ln.strip() for ln in open(os.path.join(d["dir"], "train_files.txt"), encoding="utf-8") if ln.strip()] \
        if os.path.isfile(os.path.join(d["dir"], "train_files.txt")) else []
    hf = [ln.strip() for ln in open(os.path.join(d["dir"], "holdout_files.txt"), encoding="utf-8") if ln.strip()] \
        if os.path.isfile(os.path.join(d["dir"], "holdout_files.txt")) else []
    hold_names = {D.fsid(h) + ".binpack" for h in hold_set}
    check(not any(os.path.basename(p) in hold_names for p in tf), f"train_files.txt ({len(tf)} files) names no holdout shard")
    check(all(os.path.basename(p) in hold_names for p in hf), f"holdout_files.txt ({len(hf)} files) names only holdout shards")
    res = {"pass": not FAILS, "fails": FAILS, "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "seconds": round(time.time() - t0, 1), "holdout": hold_ids, "holdout_unique_positions": int(hk.size),
           "leak_hits": leak, "dedup_sample_rows": int(K.size), "sample_prefixes": lo_sample,
           "manifest_complete": bool(man and man.get("complete")), **D.data_hashes(d, reg)}
    if not FAILS:
        C.write_json(os.path.join(d["dir"], "HOLDOUT_TEST.json"), res)
    print(json.dumps({k: v for k, v in res.items() if k != "fails"}, indent=1))
    print("R11 HOLDOUT TEST " + ("PASS" if not FAILS else "FAIL"))
    return 0 if not FAILS else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
