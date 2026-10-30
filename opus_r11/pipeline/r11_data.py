"""R11 data stage: Forge self-play FPOS shards (+ HCE) -> deduplicated nnue-pytorch .binpack files with a holdout.

Every step is restart-safe at shard granularity (a per-shard JSON done marker is written last, outputs go to
numbered .partN names first and are renamed when complete); a rerun skips finished work and picks up new shards.
  1 inventory  ready shards of every configured source; supersede rules (Astra replaces forge_push 003)
  2 register   new shards are APPENDED to state/registry.json: the dedup priority order never changes
  3 hce        missing .hce side inputs are generated (the hce tool is first qualified against production .hce)
  4 keys       per shard: 64-bit key of (32-byte board, side to move) per row + bad-row list -> keys/<id>.u64
  5 dedup      per pending shard: a row is kept iff no earlier row in registry order has its key
               (holdout shards are registered first, so a training copy of a holdout position is dropped)
               -> decisions/<id>.dest2 (2 bits per row: 0 drop, 1 train, 2 holdout, 3 bad)
  6 convert    r11_pos2binpack -> data/train/<id>.binpack (+ .hce), data/holdout/<id>.binpack (+ .hce)
  7 verify     r11_pos2binpack verify (the loader's own reader, square by square, side-car .hce)
  8 manifest   data/MANIFEST.json, train_files.txt, holdout_files.txt, SUMMARY.md

Usage: r11_data.py --config <cfg.json> [run|inventory|status] [--max-convert N]
Memory: the dedup works in key-range passes sized by data.dedup_mem_gb; everything else streams in chunks.
Inputs are only read. Nothing is ever deleted.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import subprocess
import sys
import time

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import r11_common as C  # noqa: E402

KEY_BYTES_PER_ROW = 32  # dedup pass peak per entry: key 8 + row 4 + slot 2 + argsort 8 + sorted keys 8 (+ slack)


def fsid(sid: str) -> str:
    return sid.replace(":", "__")


# ----------------------------------------------------------------------------------------------------------------
# inventory
# ----------------------------------------------------------------------------------------------------------------
def _info_records(path: str) -> int | None:
    if not os.path.isfile(path):
        return None
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line in f:
            m = re.match(r"^records=(\d+)\s*$", line.strip())
            if m:
                return int(m.group(1))
    return None


def _hce_path_for(src: dict, pos: str, data_dir: str) -> tuple[str | None, str | None, str]:
    """(hce path, text path to generate it from or None, origin label)."""
    h = src.get("hce") or {}
    base = os.path.basename(pos)
    if "dir" in h:
        stem = base[: -len(h.get("strip", ".pos"))] if base.endswith(h.get("strip", ".pos")) else base
        return os.path.join(h["dir"], stem + h.get("suffix", ".hce")), None, "source"
    if "generate_from_text" in h:
        a, b = h["generate_from_text"]
        if not base.endswith(a):
            raise C.StageFailed(f"{pos} does not end with {a}")
        text = pos[: -len(a)] + b
        gen_dir = h.get("gen_dir") or os.path.join(data_dir, "..", "hce_gen", src["name"])
        out = os.path.join(gen_dir, base[: -len(".pos")] + ".hce")
        return out, text, "generated"
    return None, None, "none"


def inventory(cfg: dict, log: C.Log) -> tuple[list[dict], dict, list[str]]:
    """Ready shards in configured source order, supersede map, notes about skipped shards."""
    d = cfg["data"]
    shards, notes, supersede = [], [], {}
    now = time.time()
    for src in d["sources"]:
        files = C.expand_glob(src["pos_glob"])
        ready_rule = src.get("ready", {})
        src_ready = []
        for pos in files:
            stem = os.path.basename(pos)[: -len(".pos")]
            sid = f"{src['name']}:{stem}"
            why = None
            if "info_suffix" in ready_rule:
                rec = _info_records(pos + ready_rule["info_suffix"])
                if rec is None:
                    why = "no .info"
                elif now - os.path.getmtime(pos) < ready_rule.get("min_age_s", 600):
                    why = "too new (still being written?)"
            if "marker_replace" in ready_rule:
                a, b = ready_rule["marker_replace"]
                if not os.path.isfile(pos[: -len(a)] + b):
                    why = f"no {b} marker yet"
            if why is None:
                try:
                    rows = C.fpos_rows(pos)
                except C.StageFailed as e:
                    why = str(e)
            if why is None and "info_suffix" in ready_rule:
                rec = _info_records(pos + ready_rule["info_suffix"])
                if rec != rows:
                    why = f".info records {rec} != header rows {rows}"
            if why is not None:
                notes.append(f"{sid}: not ready ({why})")
                continue
            hce, text, origin = _hce_path_for(src, pos, d["dir"])
            if origin == "source":
                if not os.path.isfile(hce):
                    notes.append(f"{sid}: not ready (missing {hce})")
                    continue
                if C.fhce_rows(hce) != rows:
                    notes.append(f"{sid}: not ready (hce rows != pos rows)")
                    continue
            if origin == "generated" and not os.path.isfile(text):
                notes.append(f"{sid}: not ready (missing text {text} for hce generation)")
                continue
            src_ready.append({"id": sid, "source": src["name"], "stem": stem, "pos": C.winpath(pos), "rows": rows,
                              "hce": C.winpath(hce) if hce else None, "hce_text": C.winpath(text) if text else None,
                              "hce_origin": origin})
        if src.get("supersedes") and src_ready:
            for target in src["supersedes"]:
                supersede[target] = [s["id"] for s in src_ready]
        shards.extend(src_ready)
    shards = [s for s in shards if s["id"] not in supersede]
    return shards, supersede, notes


# ----------------------------------------------------------------------------------------------------------------
# registry
# ----------------------------------------------------------------------------------------------------------------
def load_registry(path: str) -> dict | None:
    return C.read_json(path)


def save_registry(cfg: dict, reg: dict) -> None:
    C.write_json(os.path.join(cfg["data"]["dir"], "state", "registry.json"), reg)


def _pins_for(cfg: dict, source: str) -> dict:
    src = next((s for s in cfg["data"]["sources"] if s["name"] == source), {})
    return src.get("pins") or {}


def register(cfg: dict, shards: list[dict], supersede: dict, log: C.Log, sealed: C.SealedInputs) -> dict:
    """CR fix 10: every registered input carries its FULL sha256 (sha256_pos, sha256_hce for source .hce files);
    unconverted registered inputs are re-verified each run; entries written before fix 10 are upgraded (logged)."""
    d = cfg["data"]
    path = os.path.join(d["dir"], "state", "registry.json")
    reg = load_registry(path)
    holdout = list(d.get("holdout", []))
    if reg is None:
        ids = {s["id"] for s in shards}
        missing = [h for h in holdout if h not in ids]
        if missing:
            raise C.StageFailed(f"holdout shards not ready at registry creation: {missing}")
        reg = {"version": 1, "created": time.strftime("%Y-%m-%dT%H:%M:%S"), "holdout": holdout,
               "superseded": {}, "order": []}
    elif reg.get("holdout") != holdout:
        raise C.StageFailed(f"holdout list changed ({reg.get('holdout')} -> {holdout}); use a new data dir")
    known = {e["id"]: e for e in reg["order"]}
    for target, by in supersede.items():
        if target in known:
            raise C.StageFailed(f"{target} is already registered but is now superseded by {by}; use a new data dir")
        reg["superseded"][target] = by
    for sid, e in known.items():  # inputs of registered shards must not change until they are converted
        converted = os.path.isfile(out_marker(d, sid))
        if not os.path.isfile(e["pos"]):
            if converted:
                log.info(f"{sid}: input {e['pos']} is gone (already converted; fine)")
                continue
            raise C.StageFailed(f"input of registered, unconverted shard is missing: {e['pos']}")
        if "sha256_pos" not in e:  # registered before CR fix 10 (edge fingerprint only): record the full sha256 now
            e.pop("fp_pos", None)
            e["sha256_pos"] = sealed.sha256(e["pos"])
            if e.get("hce_origin") == "source" and e.get("hce"):
                e["sha256_hce"] = sealed.sha256(e["hce"])
            e["sha256_recorded"] = f"upgrade {time.strftime('%Y-%m-%dT%H:%M:%S')} (CR fix 10)"
            log.info(f"{sid}: full sha256 recorded (registry upgrade, CR fix 10)")
        elif not converted:
            sealed.verify(e["pos"], e["sha256_pos"], f"{sid} .pos")
    new = [s for s in shards if s["id"] not in known]
    new.sort(key=lambda s: (0 if s["id"] in holdout else 1))  # stable: holdout first, then configured order
    for s in new:
        e = dict(s)
        e["index"] = len(reg["order"])
        e["holdout"] = s["id"] in holdout
        e["sha256_pos"] = sealed.sha256(s["pos"])
        if e.get("hce_origin") == "source" and e.get("hce"):
            e["sha256_hce"] = sealed.sha256(e["hce"])
        pins = _pins_for(cfg, e["source"])
        for fpath, key in ((e["pos"], "sha256_pos"), (e.get("hce"), "sha256_hce")):
            pin = pins.get(os.path.basename(fpath)) if fpath else None
            if pin and e.get(key) != pin:
                raise C.StageFailed(f"{fpath} sha256 {e.get(key)} != pinned {pin}")
        e["registered"] = time.strftime("%Y-%m-%dT%H:%M:%S")
        reg["order"].append(e)
        log.info(f"registered #{e['index']} {e['id']} rows {e['rows']} holdout {e['holdout']} hce {e['hce_origin']} "
                 f"sha256 {e['sha256_pos'][:12]}")
    save_registry(cfg, reg)
    return reg


# ----------------------------------------------------------------------------------------------------------------
# supersede check (Astra: every row must be a row of the superseded shard, same board/stm/score/meta)
# ----------------------------------------------------------------------------------------------------------------
def _row_key2(k: np.ndarray, s: np.ndarray, m: np.ndarray) -> np.ndarray:
    """64-bit identity of (position key, stored score, meta byte)."""
    x = k ^ ((s.astype(np.int64).astype(np.uint64) & np.uint64(0xFFFF)) << np.uint64(8)) ^ m.astype(np.uint64)
    with np.errstate(over="ignore"):
        return C._fmix(x.copy())



def supersede_check(cfg: dict, reg: dict, all_ready: list[dict], log: C.Log, gov: C.Governor) -> None:
    d = cfg["data"]
    for target, by_ids in reg.get("superseded", {}).items():
        out = os.path.join(d["dir"], "state", f"supersede_{fsid(target)}.json")
        if os.path.isfile(out) and C.read_json(out, {}).get("ok"):
            continue
        tsrc, tstem = target.split(":", 1)
        src = next(s for s in d["sources"] if s["name"] == tsrc)
        tpos = next((p for p in C.expand_glob(src["pos_glob"]) if os.path.basename(p)[: -len(".pos")] == tstem), None)
        if tpos is None:
            log.info(f"supersede check {target}: target file not found; skipped (cannot verify)")
            C.write_json(out, {"target": target, "ok": False, "reason": "target file not found"})
            continue
        thce, _, _ = _hce_path_for(src, tpos, d["dir"])
        gov.wait_ok(f"supersede check {target}", need_ram_gb=1.0)
        nt = C.fpos_rows(tpos)
        tb = C.read_boards(tpos, nt, 0, nt)
        tm = C.read_meta(tpos, nt, 0, nt)
        tk = C.position_keys(tb, tm)
        del tb
        ts = C.read_scores(tpos, nt, 0, nt)
        th = C.read_hce(thce, 0, nt) if thce and os.path.isfile(thce) else None
        # Match on (position, score, meta): the target may hold the same position twice with different scores
        # (a filter that dropped the first copy keeps a later one). Rows identical in all three are
        # interchangeable, so the order check uses only rows whose triple is unique in the target.
        t2 = _row_key2(tk, ts, tm)
        order = np.argsort(t2, kind="stable")
        t2s = t2[order]
        uniq = np.ones(nt, bool)
        if nt > 1:
            same_next = t2s[1:] == t2s[:-1]
            uniq[1:] &= ~same_next
            uniq[:-1] &= ~same_next
        res = {"target": target, "target_rows": nt, "by": []}
        ok = True
        for bid in by_ids:
            e = next(x for x in reg["order"] if x["id"] == bid)
            n = e["rows"]
            b = C.read_boards(e["pos"], n, 0, n)
            m = C.read_meta(e["pos"], n, 0, n)
            k = C.position_keys(b, m)
            del b
            s = C.read_scores(e["pos"], n, 0, n)
            s2 = _row_key2(k, s, m)
            p = np.minimum(np.searchsorted(t2s, s2), nt - 1)
            found = t2s[p] == s2
            src_rows = order[p]
            r = {"id": bid, "rows": n, "found_exact": int(found.sum()),
                 "position_found": int(np.isin(k, tk).sum()),
                 "score_equal": int((found & (ts[src_rows] == s)).sum()),
                 "meta_equal": int((found & (tm[src_rows] == m)).sum())}
            if th is not None and e.get("hce") and os.path.isfile(e["hce"]):
                h = C.read_hce(e["hce"], 0, n)
                r["hce_equal"] = int((found & (th[src_rows] == h)).sum())
            # a filter keeps rows in their original order: check it on the rows with a unique triple
            fr = src_rows[found & uniq[p]]
            r["order_checked_rows"] = int(fr.size)
            r["monotonic"] = bool(np.all(np.diff(fr) > 0)) if fr.size > 1 else True
            r["ok"] = r["found_exact"] == n and r["monotonic"] and r.get("hce_equal", n) == n
            ok &= r["ok"]
            res["by"].append(r)
            log.info(f"supersede check {bid} vs {target}: " + json.dumps(r))
        res["ok"] = ok
        C.write_json(out, res)
        if not ok:
            raise C.StageFailed(f"supersede check failed for {target}: {res}")
        log.ok(f"supersede check {target}: every superseding row is a row of the target")


# ----------------------------------------------------------------------------------------------------------------
# hce generation
# ----------------------------------------------------------------------------------------------------------------
def qualify_hce_tool(cfg: dict, log: C.Log) -> None:
    d = cfg["data"]
    q = d.get("hce_qualify")
    out = os.path.join(d["dir"], "state", "hce_tool_qualified.json")
    tool = d["hce_tool"]
    tool_sha = C.sha256_file(tool)
    prev = C.read_json(out)
    if prev and prev.get("ok") and prev.get("tool_sha256") == tool_sha:
        return
    if not q:
        raise C.StageFailed("hce generation needs data.hce_qualify (text + production hce + lines)")
    work = os.path.join(d["dir"], "state", "hce_qualify")
    os.makedirs(work, exist_ok=True)
    tag = time.strftime("%Y%m%d_%H%M%S")
    sample = os.path.join(work, f"sample_{tag}.txt")
    C.require_disk(work, 64 * q["lines"] + 2 * q["lines"] + 4096, "hce tool qualification sample")  # CR fix 8
    with open(q["text"], "rb") as fin, open(sample, "wb") as fout:
        for i, line in enumerate(fin):
            if i >= q["lines"]:
                break
            fout.write(line)
    got = os.path.join(work, f"sample_{tag}.hce")
    r = subprocess.run([tool, sample, got], capture_output=True, text=True)
    if r.returncode != 0:
        raise C.StageFailed(f"hce tool failed on the qualification sample: {r.stderr.strip()[:300]}")
    a = C.read_hce(got, 0, q["lines"])
    b = C.read_hce(q["hce"], 0, q["lines"])
    eq = int((a == b).sum())
    res = {"tool": tool, "tool_sha256": tool_sha, "text": q["text"], "production_hce": q["hce"],
           "lines": q["lines"], "equal": eq, "ok": eq == q["lines"], "at": tag}
    C.write_json(out, res)
    if not res["ok"]:
        raise C.StageFailed(f"hce tool does not reproduce the production HCE: {eq}/{q['lines']} equal")
    log.ok(f"hce tool qualified: {eq}/{q['lines']} values equal to the production .hce ({tool_sha[:12]})")


def _fen_board(fen: str) -> tuple[bytes, int]:
    codes = {c: i + 1 for i, c in enumerate("PNBRQKpnbrqk")}
    place, stm = fen.split()[0:2]
    sq = [0] * 64
    rank = 7
    file = 0
    for ch in place:
        if ch == "/":
            rank -= 1
            file = 0
        elif ch.isdigit():
            file += int(ch)
        else:
            sq[rank * 8 + file] = codes[ch]
            file += 1
    return bytes(sq[2 * i] | (sq[2 * i + 1] << 4) for i in range(32)), (1 if stm == "b" else 0)


def generate_hce(cfg: dict, e: dict, log: C.Log, gov: C.Governor, sealed: C.SealedInputs) -> bool:
    """Make e['hce'] from e['hce_text'] with the qualified tool; check rows and a sample of boards. Records the full
    sha256 of the generated file and of its text in the registry entry (CR fix 10). Returns True if e changed."""
    if e["hce_origin"] != "generated":
        return False
    if os.path.isfile(e["hce"]):
        if "sha256_hce" in e:
            return False
        e["sha256_hce"] = sealed.sha256(e["hce"])  # generated + checked by this pipeline before CR fix 10
        e["sha256_hce_text"] = sealed.sha256(e["hce_text"]) if os.path.isfile(e["hce_text"]) else None
        log.info(f"{e['id']}: full sha256 of the generated .hce recorded (CR fix 10)")
        return True
    qualify_hce_tool(cfg, log)
    gov.wait_ok(f"hce generation {e['id']}", need_ram_gb=0.3)
    C.require_disk(e["hce"], 16 + 2 * e["rows"], f"hce generation {e['id']}")  # CR fix 8
    os.makedirs(os.path.dirname(e["hce"]), exist_ok=True)
    k = 1
    while os.path.exists(f"{e['hce']}.part{k}"):
        k += 1
    tmp = f"{e['hce']}.part{k}"
    t0 = time.time()
    r = subprocess.run([cfg["data"]["hce_tool"], e["hce_text"], tmp], capture_output=True, text=True)
    if r.returncode != 0:
        raise C.StageFailed(f"hce generation failed for {e['id']}: {r.stderr.strip()[:300]}")
    n = C.fhce_rows(tmp)
    if n != e["rows"]:
        raise C.StageFailed(f"generated hce rows {n} != pos rows {e['rows']} for {e['id']}")
    # the text must be the same rows in the same order as the .pos: compare 256 sampled boards
    rng = np.random.default_rng(11)
    idx = np.sort(rng.choice(e["rows"], size=min(256, e["rows"]), replace=False))
    want = set(int(i) for i in idx)
    lines = {}
    with open(e["hce_text"], "r", encoding="utf-8", errors="replace") as f:
        for i, line in enumerate(f):
            if i in want:
                lines[i] = line.split("|")[0].strip()
            if i > idx[-1]:
                break
    nb = C.read_boards(e["pos"], e["rows"], 0, e["rows"]) if e["rows"] <= 2_000_000 else None
    bad = 0
    for i in idx:
        board, stm = _fen_board(lines[int(i)])
        row = nb[i] if nb is not None else C.read_boards(e["pos"], e["rows"], int(i), 1)[0]
        meta = C.read_meta(e["pos"], e["rows"], int(i), 1)[0]
        if bytes(row) != board or (meta & 1) != stm:
            bad += 1
    if bad:
        os.remove(tmp)
        raise C.StageFailed(f"text rows do not match the .pos rows for {e['id']}: {bad}/256 sampled boards differ")
    os.replace(tmp, e["hce"])
    e["sha256_hce"] = sealed.sha256(e["hce"])
    e["sha256_hce_text"] = sealed.sha256(e["hce_text"])
    log.info(f"hce generated {e['id']}: {n} rows, 256/256 sampled boards match the .pos, {time.time() - t0:.1f} s")
    return True


# ----------------------------------------------------------------------------------------------------------------
# keys
# ----------------------------------------------------------------------------------------------------------------
def keys_paths(d: dict, sid: str) -> tuple[str, str, str]:
    base = os.path.join(d["dir"], "keys", fsid(sid))
    return base + ".u64", base + ".json", base + ".bad.npy"


def make_keys(cfg: dict, e: dict, log: C.Log, gov: C.Governor, sealed: C.SealedInputs) -> dict:
    d = cfg["data"]
    kpath, jpath, bpath = keys_paths(d, e["id"])
    meta = C.read_json(jpath)
    if meta and meta.get("rows") == e["rows"] and meta.get("sha256_pos") == e["sha256_pos"]:
        return meta
    os.makedirs(os.path.dirname(kpath), exist_ok=True)
    gov.wait_ok(f"keys {e['id']}", need_ram_gb=0.4, disk_path=d["dir"], need_disk_gb=e["rows"] * 8 / 2**30)
    sealed.verify(e["pos"], e["sha256_pos"], f"{e['id']} .pos (keys)")  # CR fix 10
    C.require_disk(d["dir"], 8 * e["rows"], f"keys cache {e['id']}")  # CR fix 8
    k = 1
    while os.path.exists(f"{kpath}.part{k}"):
        k += 1
    tmp = f"{kpath}.part{k}"
    t0 = time.time()
    n = e["rows"]
    step = int(d.get("chunk_rows", 2_000_000))
    bad_idx = []
    with open(tmp, "xb") as f:
        for start in range(0, n, step):
            cnt = min(step, n - start)
            b = C.read_boards(e["pos"], n, start, cnt)
            m = C.read_meta(e["pos"], n, start, cnt)
            C.position_keys(b, m).astype("<u8").tofile(f)
            bad = C.bad_rows(b, m)
            if bad.any():
                bad_idx.append(np.nonzero(bad)[0].astype(np.int64) + start)
    if os.path.getsize(tmp) != 8 * n:
        raise C.StageFailed(f"keys file size wrong for {e['id']}")
    bad_all = np.concatenate(bad_idx) if bad_idx else np.zeros(0, np.int64)
    if bad_all.size:
        np.save(bpath + ".tmp.npy", bad_all)
        os.replace(bpath + ".tmp.npy", bpath)
    os.replace(tmp, kpath)
    meta = {"id": e["id"], "rows": n, "bad": int(bad_all.size), "sha256_pos": e["sha256_pos"],
            "seconds": round(time.time() - t0, 2)}
    C.write_json(jpath, meta)
    log.info(f"keys {e['id']}: {n} rows, {bad_all.size} bad, {meta['seconds']} s")
    return meta


def load_bad(d: dict, sid: str) -> np.ndarray:
    _, _, bpath = keys_paths(d, sid)
    return np.load(bpath) if os.path.isfile(bpath) else np.zeros(0, np.int64)


def read_keys(d: dict, sid: str, start: int, count: int) -> np.ndarray:
    kpath, _, _ = keys_paths(d, sid)
    a = np.fromfile(kpath, dtype="<u8", count=count, offset=start * 8)
    if a.size != count:
        raise C.StageFailed(f"short read of keys {sid}")
    return a


# ----------------------------------------------------------------------------------------------------------------
# dedup
# ----------------------------------------------------------------------------------------------------------------
def decision_paths(d: dict, sid: str) -> tuple[str, str]:
    base = os.path.join(d["dir"], "decisions", fsid(sid))
    return base + ".dest2", base + ".json"


def dedup(cfg: dict, reg: dict, log: C.Log, gov: C.Governor, sealed: C.SealedInputs) -> None:
    d = cfg["data"]
    order = reg["order"]
    pending = [e for e in order if not os.path.isfile(decision_paths(d, e["id"])[1])]
    if not pending:
        return
    max_pend = max(e["index"] for e in pending)
    prev = [e for e in order if e not in pending and e["index"] < max_pend]
    step = int(d.get("chunk_rows", 2_000_000))
    budget = float(d.get("dedup_mem_gb", 1.0)) * 2**30
    total = sum(e["rows"] for e in pending)
    passes = max(1, math.ceil(total * KEY_BYTES_PER_ROW / budget))
    use_cache = bool(d.get("keys_cache", False))
    log.info(f"dedup: {len(pending)} pending shards ({total} rows), {len(prev)} earlier shards to check against, "
             f"{passes} key-range passes, keys {'from the cache' if use_cache else 'recomputed from the .pos files'}")
    # CR fix 10: every input the dedup reads must still be its registered version (full sha256, once per run)
    for e in pending + ([] if use_cache else prev):
        sealed.verify(e["pos"], e["sha256_pos"], f"{e['id']} .pos (dedup input)")
    bad = {e["id"]: load_bad(d, e["id"]) for e in pending + prev} if use_cache else {}
    found_bad: dict[str, list] = {e["id"]: [] for e in pending}

    def good_mask(sid: str, start: int, cnt: int) -> np.ndarray | None:
        bi = bad[sid]
        if bi.size == 0:
            return None
        sel = bi[(bi >= start) & (bi < start + cnt)] - start
        if sel.size == 0:
            return None
        g = np.ones(cnt, bool)
        g[sel] = False
        return g

    def chunk(e: dict, start: int, cnt: int, first_pass: bool) -> tuple[np.ndarray, np.ndarray | None]:
        """Keys of rows [start, start + cnt) and a good-row mask (None = all good)."""
        if use_cache:
            return read_keys(d, e["id"], start, cnt), good_mask(e["id"], start, cnt)
        b = C.read_boards(e["pos"], e["rows"], start, cnt)
        m = C.read_meta(e["pos"], e["rows"], start, cnt)
        k = C.position_keys(b, m)
        badm = C.bad_rows(b, m)
        if not badm.any():
            return k, None
        if first_pass and e["id"] in found_bad:
            found_bad[e["id"]].append(np.nonzero(badm)[0].astype(np.int64) + start)
        return k, ~badm

    kept_bits = {e["id"]: np.zeros((e["rows"] + 7) // 8, np.uint8) for e in pending}
    slot_index = np.array([e["index"] for e in pending], dtype=np.int64)
    t_all = time.time()
    for g in range(passes):
        lo = (g * 65536) // passes
        hi = ((g + 1) * 65536) // passes
        gov.wait_ok(f"dedup pass {g + 1}/{passes}", need_ram_gb=budget / 2**30)
        t0 = time.time()
        ks, rs, ss = [], [], []
        for si, e in enumerate(pending):
            n = e["rows"]
            for start in range(0, n, step):
                cnt = min(step, n - start)
                k, gm = chunk(e, start, cnt, first_pass=g == 0)
                pre = (k >> np.uint64(48)).astype(np.int64)
                m = (pre >= lo) & (pre < hi)
                if gm is not None:
                    m &= gm
                idx = np.nonzero(m)[0]
                ks.append(k[idx])
                rs.append((idx + start).astype(np.uint32))
                ss.append(np.full(idx.size, si, np.uint16))
        K = np.concatenate(ks) if ks else np.zeros(0, np.uint64)
        R = np.concatenate(rs) if rs else np.zeros(0, np.uint32)
        S = np.concatenate(ss) if ss else np.zeros(0, np.uint16)
        del ks, rs, ss
        o = np.argsort(K, kind="stable")  # collection order = registry order, so the earliest row stays first
        Ks = K[o]
        first = np.ones(Ks.size, bool)
        if Ks.size > 1:
            first[1:] = Ks[1:] != Ks[:-1]
        cand = o[first]
        ck = Ks[first]
        del K, Ks, o, first
        cs = S[cand]
        cr = R[cand]
        del S, R, cand
        dup = np.zeros(ck.size, bool)
        for e in prev:
            n = e["rows"]
            for start in range(0, n, step):
                cnt = min(step, n - start)
                k, gm = chunk(e, start, cnt, first_pass=False)
                pre = (k >> np.uint64(48)).astype(np.int64)
                m = (pre >= lo) & (pre < hi)
                if gm is not None:
                    m &= gm
                dk = k[m]
                if dk.size == 0 or ck.size == 0:
                    continue
                p = np.searchsorted(ck, dk)
                inb = p < ck.size
                p = p[inb]
                hit = p[ck[p] == dk[inb]]
                if hit.size:
                    later = slot_index[cs[hit]] > e["index"]  # only an EARLIER shard can shadow a row
                    dup[hit[later]] = True
        keep = ~dup
        for si, e in enumerate(pending):
            sel = cr[keep & (cs == si)]
            if sel.size:
                mask = np.zeros(e["rows"], bool)
                mask[sel] = True
                kept_bits[e["id"]] |= np.packbits(mask, bitorder="little")
        log.info(f"dedup pass {g + 1}/{passes}: prefixes [{lo}, {hi}), {ck.size} first occurrences, "
                 f"{int(dup.sum())} shadowed by earlier shards, {time.time() - t0:.1f} s")
        del ck, cs, cr, dup, keep
    for e in pending:
        n = e["rows"]
        kept = np.unpackbits(kept_bits[e["id"]], count=n, bitorder="little").astype(bool)
        dest = np.zeros(n, np.uint8)
        dest[kept] = C.DEST_HOLD if e["holdout"] else C.DEST_TRAIN
        if use_cache:
            bi = bad[e["id"]]
        else:
            bi = np.concatenate(found_bad[e["id"]]) if found_bad[e["id"]] else np.zeros(0, np.int64)
        dest[bi] = C.DEST_BAD
        dpath, jpath = decision_paths(d, e["id"])
        C.require_disk(dpath, (n + 3) // 4, f"decision file {e['id']}")  # CR fix 8
        os.makedirs(os.path.dirname(dpath), exist_ok=True)
        packed = C.pack_dest(dest)
        packed.tofile(dpath + ".tmp")
        back = C.unpack_dest(np.fromfile(dpath + ".tmp", np.uint8), n)  # CR fix 7: verify before the rename
        if not np.array_equal(back, dest):
            raise C.StageFailed(f"decision file {dpath}.tmp does not read back equal")
        os.replace(dpath + ".tmp", dpath)
        kc = int(kept.sum())
        C.write_json(jpath, {"id": e["id"], "index": e["index"], "rows": n, "kept": kc, "dropped": n - kc - int(bi.size),
                             "bad": int(bi.size), "holdout": e["holdout"], "sha256_pos": e["sha256_pos"],
                             "earlier_shards_checked": len([p for p in prev if p["index"] < e["index"]]) +
                             len([p for p in pending if p["index"] < e["index"]]),
                             "passes": passes, "at": time.strftime("%Y-%m-%dT%H:%M:%S")})
        log.info(f"decision {e['id']}: kept {kc} of {n} ({100.0 * kc / max(1, n):.3f}%), bad {bi.size}, "
                 f"{'holdout' if e['holdout'] else 'train'}")
    log.ok(f"dedup: {len(pending)} shards decided in {time.time() - t_all:.1f} s")


# ----------------------------------------------------------------------------------------------------------------
# convert + verify
# ----------------------------------------------------------------------------------------------------------------
def out_marker(d: dict, sid: str) -> str:
    return os.path.join(d["dir"], "out", fsid(sid) + ".json")


def _part_name(path: str) -> str:
    k = 1
    while os.path.exists(f"{path}.part{k}") or os.path.exists(f"{path}.part{k}.hce"):
        k += 1
    return f"{path}.part{k}"


def _run_tool(cmd: list[str]) -> dict:
    r = subprocess.run(cmd, capture_output=True, text=True)
    js = None
    for line in r.stdout.splitlines():
        if line.startswith("{"):
            js = json.loads(line)
    if js is not None and js.get("writer_bad", 0) > 0:  # CR fix 6 (the writer also exits 3)
        raise C.StageFailed(f"writer dropped {js['writer_bad']} rows marked train/holdout (the cheap row checks let them "
                            f"through, the converter rejected them): {' '.join(cmd)}\n{json.dumps(js)}")
    if r.returncode != 0 or js is None:
        raise C.StageFailed(f"tool failed ({r.returncode}): {' '.join(cmd)}\n{r.stdout[-500:]}\n{r.stderr[-500:]}")
    return js


def _drop_parts(paths: list[str], log: C.Log) -> None:
    """Failed or unverified .part files of THIS conversion are removed (CR: no unverified partial data stays)."""
    for p in paths:
        if os.path.exists(p):
            os.remove(p)
            log.info(f"removed unverified partial file {p}")


def convert(cfg: dict, e: dict, log: C.Log, gov: C.Governor, sealed: C.SealedInputs) -> dict:
    """CR fix 7: the writer writes .partN files, they are VERIFIED (counts, sizes, the loader's own reader square by
    square, the side-car .hce) and only then renamed to their final names; the done marker is written last."""
    d = cfg["data"]
    marker = out_marker(d, e["id"])
    done = C.read_json(marker)
    if done:
        return done
    dpath, djson = decision_paths(d, e["id"])
    dec = C.read_json(djson)
    need = dec["kept"] * 36 / 2**30
    if not gov.wait_ok(f"convert {e['id']}", need_ram_gb=0.2, disk_path=d["dir"], need_disk_gb=need):
        return {}
    split = "holdout" if e["holdout"] else "train"
    final = os.path.join(d["dir"], split, fsid(e["id"]) + ".binpack")
    final_hce = final[: -len(".binpack")] + ".hce"
    for p in (final, final_hce):
        if os.path.exists(p):
            raise C.StageFailed(f"{p} exists without a done marker; inspect it by hand (never overwritten)")
    C.require_disk(final, projected_bytes(d, e), f"conversion of {e['id']}", disk_floor_gb_data(cfg, final))  # CR fix 8
    os.makedirs(os.path.dirname(final), exist_ok=True)
    tmp = _part_name(final)
    tmp_hce = tmp + ".hce"
    with_hce = bool(e.get("hce")) and os.path.isfile(e["hce"])
    # CR fix 10: the writer reads the registered versions only (full sha256)
    sealed.verify(e["pos"], e["sha256_pos"], f"{e['id']} .pos")
    if with_hce:
        if "sha256_hce" not in e:
            raise C.StageFailed(f"{e['id']}: .hce has no registered sha256")
        sealed.verify(e["hce"], e["sha256_hce"], f"{e['id']} .hce")
    cmd = [d["writer_exe"], "convert", "--pos", e["pos"], "--dest", dpath, "--ply", str(d.get("ply", 40))]
    if with_hce:
        cmd += ["--hce", e["hce"]]
    if dec["kept"]:
        cmd += ["--hold" if e["holdout"] else "--train", tmp]
        if with_hce:
            cmd += ["--hce-hold" if e["holdout"] else "--hce-train", tmp_hce]
    t0 = time.time()
    try:
        js = _run_tool(cmd)
        recs = js["hold_records"] if e["holdout"] else js["train_records"]
        if js["writer_bad"] != 0:
            raise C.StageFailed(f"writer dropped {js['writer_bad']} rows of {e['id']} (CR fix 6: never a silent skip)")
        if js["dest_train"] + js["dest_hold"] != dec["kept"] or recs != dec["kept"]:
            raise C.StageFailed(f"writer counts disagree with the decision for {e['id']}: {js} vs kept {dec['kept']}")
        res = {"id": e["id"], "split": split, "records": recs, "writer": js, "writer_exe": d["writer_exe"],
               "writer_exe_sha256": C.sha256_file(d["writer_exe"]), "outputs": {}}
        if recs:
            if os.path.getsize(tmp) != (js["hold_bytes"] if e["holdout"] else js["train_bytes"]):
                raise C.StageFailed(f"output size mismatch for {e['id']}")
            if with_hce and C.fhce_rows(tmp_hce) != recs:
                raise C.StageFailed(f"side-car hce rows != records for {e['id']}")
            vcmd = [d["writer_exe"], "verify", "--pos", e["pos"], "--dest", C.winpath(dpath), "--code",
                    str(C.DEST_HOLD if e["holdout"] else C.DEST_TRAIN), "--file", C.winpath(tmp),
                    "--ply", str(d.get("ply", 40))]
            if with_hce:
                vcmd += ["--hce", e["hce"], "--hce-file", C.winpath(tmp_hce)]
            v = _run_tool(vcmd)
            if not v.get("ok") or v.get("expected") != recs:
                raise C.StageFailed(f"verify of the .part output failed for {e['id']}: {v}")
            res["verify"] = dict(v, verified_before_rename=True)
            res["outputs"]["binpack"] = {"path": C.winpath(final), "bytes": os.path.getsize(tmp),
                                         "sha256": C.sha256_file(tmp)}
            if with_hce:
                res["outputs"]["hce"] = {"path": C.winpath(final_hce), "bytes": os.path.getsize(tmp_hce),
                                         "sha256": C.sha256_file(tmp_hce)}
    except C.StageFailed:
        _drop_parts([tmp, tmp_hce], log)
        raise
    if recs:  # every check passed: rename, then the done marker
        os.replace(tmp, final)
        if with_hce:
            os.replace(tmp_hce, final_hce)
    res["seconds"] = round(time.time() - t0, 2)
    C.write_json(marker, res)
    log.info(f"converted {e['id']} -> {split}: {recs} records, verified before rename, {res['seconds']} s")
    return res


def disk_floor_gb_data(cfg: dict, path: str) -> float:
    """Bulk floor for data outputs: the drive floor plus data.disk_margin_gb (QA: >= 40 GB stay free after the run)."""
    base = C.disk_floor_gb(path, float(cfg.get("limits", {}).get("min_disk_free_gb", 40.0)))
    return base + float(cfg["data"].get("disk_margin_gb", 2.0))


def projected_bytes(d: dict, e: dict) -> int:
    """Exact output size of a decided shard: 34 bytes per record + 8 per 30,841-record chunk + the .hce side-car
    (an upper bound when the writer rejects rows the cheap checks let through)."""
    dec = C.read_json(decision_paths(d, e["id"])[1])
    kept = int(dec["kept"]) if dec else e["rows"]
    chunks = (kept + 30840) // 30841
    hce = 16 + 2 * kept if e.get("hce") else 0
    return 34 * kept + 8 * chunks + hce


def conversion_order(d: dict, todo: list[dict]) -> list[dict]:
    """Shards in value order: data.convert_order lists 'holdout' and source names (default: holdout, then the
    configured sources); inside a group the newest shard (highest registry index) comes first."""
    groups = d.get("convert_order") or (["holdout"] + [s["name"] for s in d["sources"]])

    def rank(e: dict) -> tuple[int, int]:
        g = "holdout" if e["holdout"] else e["source"]
        return (groups.index(g) if g in groups else len(groups), -e["index"])

    return sorted(todo, key=rank)


def write_manifest(cfg: dict, reg: dict, log: C.Log) -> dict:
    d = cfg["data"]
    rows = []
    totals = {"train": 0, "holdout": 0, "input_rows": 0, "dropped_duplicates": 0, "bad": 0, "writer_bad": 0}
    by_source = {}
    train_files, hold_files = [], []
    complete = True
    for e in reg["order"]:
        dec = C.read_json(decision_paths(d, e["id"])[1])
        out = C.read_json(out_marker(d, e["id"]))
        if not dec or not out:
            complete = False
            continue
        bs = by_source.setdefault(e["source"], {"shards": 0, "input_rows": 0, "kept": 0, "dropped": 0, "bad": 0})
        bs["shards"] += 1
        bs["input_rows"] += e["rows"]
        bs["kept"] += out["records"]
        bs["dropped"] += dec["dropped"]
        bs["bad"] += dec["bad"] + out["writer"]["writer_bad"]
        totals["input_rows"] += e["rows"]
        totals["dropped_duplicates"] += dec["dropped"]
        totals["bad"] += dec["bad"]
        totals["writer_bad"] += out["writer"]["writer_bad"]
        totals[out["split"]] += out["records"]
        if out["records"]:
            (hold_files if out["split"] == "holdout" else train_files).append(out["outputs"]["binpack"]["path"])
        rows.append({"index": e["index"], "id": e["id"], "split": out["split"], "input_rows": e["rows"],
                     "records": out["records"], "dropped": dec["dropped"], "bad": dec["bad"] + out["writer"]["writer_bad"],
                     "binpack": out["outputs"].get("binpack"), "hce": out["outputs"].get("hce"),
                     "verified": bool(out.get("verify", {}).get("ok"))})
    man = {"created": time.strftime("%Y-%m-%dT%H:%M:%S"), "complete": complete, "registry_shards": len(reg["order"]),
           "superseded": reg.get("superseded", {}), "holdout_shards": reg["holdout"], "totals": totals,
           "by_source": by_source, "ply": d.get("ply", 40), "writer_exe": d["writer_exe"],
           "writer_exe_sha256": C.sha256_file(d["writer_exe"]), "shards": rows}
    C.write_json(os.path.join(d["dir"], "MANIFEST.json"), man)
    C.write_text(os.path.join(d["dir"], "train_files.txt"), "".join(p + "\n" for p in train_files))
    C.write_text(os.path.join(d["dir"], "holdout_files.txt"), "".join(p + "\n" for p in hold_files))
    lines = ["# R11 data summary", "", f"created {man['created']}, complete: {complete}", "",
             "| source | shards | input rows | kept | dropped (dup) | bad |", "|---|---:|---:|---:|---:|---:|"]
    for s, v in by_source.items():
        lines.append(f"| {s} | {v['shards']} | {v['input_rows']:,} | {v['kept']:,} | {v['dropped']:,} | {v['bad']:,} |")
    lines += ["", f"train records {totals['train']:,} in {len(train_files)} files; holdout records "
              f"{totals['holdout']:,} in {len(hold_files)} files", "",
              f"superseded: {json.dumps(reg.get('superseded', {}))}", ""]
    C.write_text(os.path.join(d["dir"], "SUMMARY.md"), "\n".join(lines))
    return man


# ----------------------------------------------------------------------------------------------------------------
# driver
# ----------------------------------------------------------------------------------------------------------------
def resolve_writer(cfg: dict, log: C.Log) -> str:
    """data.writer_exe = "auto": the build of the current r11_pos2binpack.cpp (built now if missing)."""
    d = cfg["data"]
    if d["writer_exe"] != "auto":
        return d["writer_exe"]
    repo = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
    build = os.path.join(repo, "tools", "nnue_pytorch_amd", "r11", "build_r11_tools.py")
    clone = cfg.get("trainer", {}).get("clone", "F:/opus_scratch/r6/nnue-pytorch-amd")
    r = subprocess.run([sys.executable, "-I", "-B", build, "--clone", clone, "--out-dir", os.path.join(cfg["root"], "bin")],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise C.StageFailed(f"writer build failed: {r.stdout[-400:]} {r.stderr[-400:]}")
    exe = C.winpath(r.stdout.strip().splitlines()[-1])
    log.info(f"writer exe: {exe}")
    d["writer_exe"] = exe
    return exe


def run(cfg: dict, log: C.Log, gov: C.Governor, max_convert: int | None = None, inventory_only: bool = False) -> dict:
    d = cfg["data"]
    C.assert_writable_path(d["dir"])
    for src in d["sources"]:
        gen = (src.get("hce") or {}).get("gen_dir")
        if gen:
            C.assert_writable_path(gen)
    os.makedirs(d["dir"], exist_ok=True)
    resolve_writer(cfg, log)
    if not os.path.isfile(d["writer_exe"]):
        raise C.StageFailed(f"writer exe missing: {d['writer_exe']} (build it with build_r11_tools.py)")
    shards, supersede, notes = inventory(cfg, log)
    for n in notes:
        log.info(n)
    log.info(f"inventory: {len(shards)} ready shards, {sum(s['rows'] for s in shards)} rows, superseded {supersede}")
    if inventory_only:
        return {"shards": shards, "superseded": supersede, "notes": notes}
    sealed = C.SealedInputs()
    reg = register(cfg, shards, supersede, log, sealed)
    supersede_check(cfg, reg, shards, log, gov)
    if d.get("verify", "all") != "all":
        raise C.StageFailed("data.verify must be 'all': every output is verified before it is renamed (CR fix 7)")
    for e in reg["order"]:
        if generate_hce(cfg, e, log, gov, sealed):
            save_registry(cfg, reg)
        if d.get("keys_cache", False):
            make_keys(cfg, e, log, gov, sealed)
    dedup(cfg, reg, log, gov, sealed)
    # disk rule (QA, R11): the target drive must keep >= limits.min_disk_free_gb (+ data.disk_margin_gb) free
    # AFTER the run. Exact output sizes are known once the decisions exist.
    floor = disk_floor_gb_data(cfg, d["dir"])
    todo = [e for e in reg["order"] if not os.path.isfile(out_marker(d, e["id"]))]
    sizes = {e["id"]: projected_bytes(d, e) for e in todo}
    free = C.disk_free_gb(d["dir"])
    total_gb = sum(sizes.values()) / 2**30
    log.info(f"disk: {free:.1f} GB free on the target drive, {len(todo)} shards to convert = {total_gb:.2f} GB, "
             f"projected free after the full run {free - total_gb:.1f} GB (floor {floor:.0f} GB)")
    if free - total_gb < floor:
        log.info("disk: the full run does not fit above the floor; converting in value order "
                 f"{d.get('convert_order', ['holdout'])} while the floor holds, the rest waits for space")
    converted = 0
    stopped_for_disk = False
    for e in conversion_order(d, todo):
        if max_convert is not None and converted >= max_convert:
            log.info("stopping before the next conversion (--max-convert)")
            break
        need_gb = sizes[e["id"]] / 2**30
        free = C.disk_free_gb(d["dir"])
        if free - need_gb < floor:
            log.info(f"disk: stop before {e['id']} ({need_gb:.2f} GB): {free:.1f} GB free would drop below the "
                     f"{floor:.0f} GB floor")
            stopped_for_disk = True
            break
        r = convert(cfg, e, log, gov, sealed)
        if not r:
            break
        converted += 1
    if stopped_for_disk:
        left = [e for e in reg["order"] if not os.path.isfile(out_marker(d, e["id"]))]
        log.info(f"disk: {len(left)} shards ({sum(sizes[x['id']] for x in left) / 2**30:.2f} GB) wait for disk space; "
                 "a rerun continues where this one stopped")
    man = write_manifest(cfg, reg, log)
    t = man["totals"]
    msg = (f"data: {len(reg['order'])} shards, train {t['train']:,} holdout {t['holdout']:,} records, "
           f"dropped {t['dropped_duplicates']:,} duplicates, bad {t['bad'] + t['writer_bad']}, complete {man['complete']}")
    if man["complete"]:
        log.ok(msg)
    else:
        log.info(msg + " (incomplete: rerun to continue)")
    return man


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("cmd", nargs="?", default="run", choices=["run", "inventory", "status"])
    ap.add_argument("--max-convert", type=int)
    a = ap.parse_args(argv)
    cfg = C.read_json(a.config)
    C.set_idle_background(C.affinity_from_cfg(cfg))
    root = cfg["root"]
    C.write_pid_file(root, "data")
    log = C.Log(os.path.join(root, "logs", "pipeline.log"), "data")
    gov = C.Governor(root, C.limits_from(cfg), log)
    try:
        if a.cmd == "status":
            man = C.read_json(os.path.join(cfg["data"]["dir"], "MANIFEST.json"))
            print(json.dumps(man["totals"] if man else {}, indent=1))
            return 0
        run(cfg, log, gov, a.max_convert, inventory_only=a.cmd == "inventory")
        return 0
    except C.StageFailed as e:
        log.fail(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
