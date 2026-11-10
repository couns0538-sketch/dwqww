"""confirm_runner.py - independent confirmation of a tuned candidate on a frozen holdout (no tuner code is imported).

usage (python -I -B; PowerShell entry point ..\\bin\\confirm.ps1):
  confirm_runner.py run <protocol.json> <candidate.json> <run_dir> [--mode dry-run|synthetic|replay|live] [--resume]
                        [--live] [--max-pairs N]
  confirm_runner.py verify <run_dir>
  confirm_runner.py audit-pgn <protocol.json> <candidate.json> <pgn> [<pgn> ...]   (QA's SPRT PGN, read-only)
Modes: dry-run (DEFAULT) validates protocol, candidate and pins and prints the fastchess command; writes nothing.
synthetic draws pair outcomes from a model with a known true effect (tests only; output is labelled SYNTHETIC and
carries no Elo). replay reads the PGNs named in the protocol's replay manifest. live needs --live,
protocol.live.enabled and <run_dir>/LIVE_ACK.txt holding the protocol sha256 (never used by this job).
Fixed rules (protocol, frozen before fitting): one confirmation per holdout group, ever (registry); the candidate is
the one select_candidate.py derived from a COMPLETE training run; pentanomial normalized-Elo GSPRT with the
protocol's bounds, alpha, beta and game cap: LLR >= upper -> "H1 accepted", LLR <= lower -> "H0 accepted",
cap reached -> "cap, no decision (no claim)". A crash, time loss or illegal move makes the run invalid.
State: start/pair/decision records in a hash-chained ledger (source of truth) + atomic checkpoints; every resume
replays the ledger; duplicates, unknown pairs, incomplete pairs, stale or corrupt state are refused.
Exit codes: 0 ok, 10 bad protocol/candidate, 11 changed, 20 identity, 30 corrupt, 31 bad results, 40 live guard,
41 holdout misuse (reuse, peeking, overlap with training), 77 injected crash (tests)."""
import hashlib
import json
import math
import os
import random
import re
import subprocess
import sys
import time
from pathlib import Path

LN10 = math.log(10.0)
TAG = re.compile(r'^\[(\w+) "([^"]*)"\]\s*$', re.M)


class Stop(Exception):
    def __init__(self, code, msg):
        super().__init__(msg)
        self.code = code


def cj(o):
    return json.dumps(o, sort_keys=True, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("ascii")


def h(b):
    return hashlib.sha256(b).hexdigest()


def fh(p):
    x = hashlib.sha256()
    with open(p, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            x.update(c)
    return x.hexdigest()


def crash(point, n=None):
    spec = os.environ.get("OPUS3_CONFIRM_CRASH", "")
    if spec:
        name, _, at = spec.partition("@")
        if name == point and (not at or n is None or int(at) == n):
            os._exit(77)


def put(path, data, tag=None, n=None):
    tmp = Path(str(path) + ".tmp")
    with open(tmp, "wb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    if tag:
        crash(tag + "_tmp", n)
    for i in range(120):
        try:
            os.replace(tmp, path)
            break
        except PermissionError:
            if i == 119:
                raise
            time.sleep(min(0.05 * (i + 1), 0.5))
    if tag:
        crash(tag + "_renamed", n)


# --- statistics ---------------------------------------------------------------------------------------------------
def pentanomial(pairs):
    """counts of pair scores 0, 1/4, 1/2, 3/4, 1 (candidate's points / 2 per pair)."""
    c = [0, 0, 0, 0, 0]
    for p in pairs:
        c[int(round(p * 4))] += 1
    return c


PSEUDO = 1e-3  # per pentanomial cell: keeps the variance estimate positive for degenerate samples


def gsprt(penta, nelo0, nelo1):
    """Normalized-Elo GSPRT on pentanomial pair scores (normal approximation with the sample variance of the
    regularized counts, PSEUDO added to every cell): nt = nElo * ln(10) / 800; mu_j = 1/2 + nt_j * sqrt(2) * sd_pair;
    LLR = N * ((m - mu0)^2 - (m - mu1)^2) / (2 var). N is the real number of pairs."""
    n = sum(penta)
    if n < 2:
        return {"pairs": n, "llr": 0.0, "mean": None, "sd_pair": None}
    xs = [i / 4 for i in range(5)]
    reg = [c + PSEUDO for c in penta]
    nr = sum(reg)
    m = sum(c * x for c, x in zip(reg, xs)) / nr
    var = sum(c * (x - m) ** 2 for c, x in zip(reg, xs)) / nr
    sd = math.sqrt(var)
    mu0 = 0.5 + nelo0 * LN10 / 800 * math.sqrt(2) * sd
    mu1 = 0.5 + nelo1 * LN10 / 800 * math.sqrt(2) * sd
    llr = n * ((m - mu0) ** 2 - (m - mu1) ** 2) / (2 * var)
    se = sd / math.sqrt(n)
    return {"pairs": n, "llr": llr, "mean": m, "sd_pair": sd, "mean_ci95": [m - 1.96 * se, m + 1.96 * se]}


def decide(stat, proto, games):
    """Pre-registered stop rule. No bound decision before min_pairs pairs (default 50): the plug-in variance of a
    handful of pairs is not trustworthy. The game cap ends the run without a claim."""
    a, b = proto["sprt"]["alpha"], proto["sprt"]["beta"]
    lo, hi = math.log(b / (1 - a)), math.log((1 - b) / a)
    if stat["pairs"] < proto["sprt"].get("min_pairs", 50):
        return "cap, no decision (no claim)" if games >= proto["sprt"]["cap_games"] else None
    if stat["llr"] >= hi:
        return "H1 accepted"
    if stat["llr"] <= lo:
        return "H0 accepted"
    if games >= proto["sprt"]["cap_games"]:
        return "cap, no decision (no claim)"
    return None


# --- protocol, candidate, identity ----------------------------------------------------------------------------------
def load(path, schema):
    try:
        o = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        raise Stop(10, f"{path}: {e}")
    if o.get("schema") != schema:
        raise Stop(10, f"{path}: schema must be {schema}")
    return o


def check_identity(proto):
    out = {}
    for k, e in sorted(proto["identity"].items()):
        p = Path(e["path"])
        if not p.exists():
            raise Stop(20, f"pinned {k} missing: {p}")
        got = fh(p)
        if got != e["sha256"].lower():
            raise Stop(20, f"pinned {k} changed: {p}")
        out[k] = got
    return out


def check_holdout(proto, cand, run_dir):
    """Holdout misuse is refused (exit 41): the group must not have been read by the training run (peeking), the
    candidate must come from the frozen training partition, and a holdout group serves exactly ONE confirmation run
    directory, ever (registry): no second candidate, no re-run of the same candidate until a lucky result."""
    grp = proto["holdout"]
    trained = set(cand.get("training_openings_sha256", []))
    if grp["pgn_sha256"] in trained:
        raise Stop(41, "the holdout group was read by the training run (peeking)")
    if grp["pgn_sha256"] in set(proto.get("training_partitions_sha256", [])):
        raise Stop(41, "the protocol names a training partition as holdout")
    if not trained or trained - set(proto["training_partitions_sha256"]):
        raise Stop(41, "the candidate's training openings are not the frozen training partition")
    reg = Path(proto["registry"])
    if reg.exists():
        for line in reg.read_text(encoding="ascii").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            if r["holdout_pgn_sha256"] == grp["pgn_sha256"] and r["run_dir"] != str(Path(run_dir).resolve()):
                raise Stop(41, f"holdout group {grp['name']} already served confirmation {r['run_id']} in {r['run_dir']}"
                               " (one confirmation per group, ever)")


def register(proto, cand, run_id, run_dir):
    """Idempotent: one registry line per (run_id, run_dir)."""
    reg = Path(proto["registry"])
    reg.parent.mkdir(parents=True, exist_ok=True)
    rd = str(Path(run_dir).resolve())
    if reg.exists():
        for line in reg.read_text(encoding="ascii").splitlines():
            if line.strip():
                r = json.loads(line)
                if r["run_id"] == run_id and r["run_dir"] == rd:
                    return
    with open(reg, "ab") as f:
        f.write(cj({"run_id": run_id, "run_dir": rd, "holdout": proto["holdout"]["name"],
                    "holdout_pgn_sha256": proto["holdout"]["pgn_sha256"], "candidate_sha256": cand["spec_sha256"]}) + b"\n")
        f.flush()
        os.fsync(f.fileno())


def verify_candidate(cand):
    body = {k: v for k, v in cand.items() if k != "spec_sha256"}
    if h(cj(body)) != cand.get("spec_sha256"):
        raise Stop(10, "candidate spec_sha256 does not match its content")
    if not cand.get("training_complete"):
        raise Stop(10, "candidate is not from a COMPLETE training run (fixed selection rule)")


# --- ledger -----------------------------------------------------------------------------------------------------------
class Book:
    def __init__(self, d, run_id):
        self.d, self.run_id = Path(d), run_id
        self.p = self.d / "confirm_ledger.jsonl"
        self.recs = []

    def load(self, repair=True):
        self.recs = []
        if not self.p.exists():
            return self
        raw = self.p.read_bytes()
        lines = raw.split(b"\n")
        tail = lines.pop()
        for i, line in enumerate(lines):
            self.recs.append(self._check(line, i))
        if tail:
            try:
                self.recs.append(self._check(tail, len(lines)))
                ok = True
            except Stop:
                ok = False
            if not repair:
                raise Stop(30, "unterminated ledger tail (a resume repairs it)")
            if ok:
                with open(self.p, "ab") as f:
                    f.write(b"\n")
            else:
                (self.d / f"confirm_ledger.torn.{len(list(self.d.glob('confirm_ledger.torn.*')))}.bin").write_bytes(tail)
                with open(self.p, "r+b") as f:
                    f.truncate(len(raw) - len(tail))
        return self

    def _check(self, line, i):
        try:
            r = json.loads(line.decode("ascii"))
        except (UnicodeDecodeError, ValueError):
            raise Stop(30, f"ledger line {i + 1} malformed")
        body = {k: v for k, v in r.items() if k != "h"}
        if r.get("h") != h(cj(body)) or cj(r) != line:
            raise Stop(30, f"ledger line {i + 1}: hash/encoding mismatch")
        if r.get("n") != i or r.get("prev") != (self.recs[-1]["h"] if self.recs else "genesis"):
            raise Stop(30, f"ledger line {i + 1}: broken chain")
        if r.get("run_id") != self.run_id:
            raise Stop(31, f"ledger line {i + 1}: record of another run (stale)")
        return r

    def add(self, kind, payload):
        r = {"n": len(self.recs), "kind": kind, "run_id": self.run_id,
             "prev": self.recs[-1]["h"] if self.recs else "genesis"}
        r.update(payload)
        r["h"] = h(cj(r))
        with open(self.p, "ab") as f:
            f.write(cj(r) + b"\n")
            f.flush()
            os.fsync(f.fileno())
        self.recs.append(r)
        return r


def state_of(recs, proto):
    st = {"started": False, "pairs": {}, "decision": None}
    for r in recs:
        if r["kind"] == "start":
            if st["started"]:
                raise Stop(30, "two start records")
            st["started"] = True
        elif r["kind"] == "pair":
            if not st["started"] or st["decision"]:
                raise Stop(31, f"pair {r['j']} outside an open confirmation")
            if r["j"] in st["pairs"]:
                raise Stop(31, f"pair {r['j']} recorded twice")
            if r["j"] != len(st["pairs"]):
                raise Stop(31, f"pair {r['j']} out of order (pairs are recorded in index order)")
            g = r["games"]
            if len(g) != 2 or sorted(x["white"] for x in g) != ["base", "cand"]:
                raise Stop(31, f"pair {r['j']} is not two games with colours swapped")
            if score_pair(g) != r["score"]:
                raise Stop(31, f"pair {r['j']} score does not match its games")
            st["pairs"][r["j"]] = r
        elif r["kind"] == "decision":
            want = summary(st, proto)
            if r.get("verdict") != want["verdict"] or r.get("penta") != want["penta"]:
                raise Stop(30, "decision record not reproduced by its pairs")
            st["decision"] = r
        else:
            raise Stop(30, f"unknown record {r['kind']}")
    return st


def score_pair(games):
    pts = 0.0
    for g in games:
        if g["result"] == "1/2-1/2":
            pts += 0.5
        elif (g["result"] == "1-0") == (g["white"] == "cand"):
            pts += 1.0
    return pts / 2


def summary(st, proto):
    scores = [st["pairs"][j]["score"] for j in sorted(st["pairs"])]
    pen = pentanomial(scores)
    stat = gsprt(pen, proto["sprt"]["nelo0"], proto["sprt"]["nelo1"])
    invalid = sum(1 for r in st["pairs"].values() for g in r["games"] if g.get("termination") not in ("normal", "synthetic", "adjudication"))
    v = decide(stat, proto, 2 * len(scores))
    if invalid:
        v = "INVALID (crash/time loss/illegal move in the run)"
    return {"verdict": v, "penta": pen, "pairs": len(scores), "games": 2 * len(scores), "llr": stat["llr"],
            "mean_pair_score": stat["mean"], "mean_ci95": stat.get("mean_ci95")}


# --- backends -------------------------------------------------------------------------------------------------------
def synthetic_pair(proto, j):
    """Model with a known true per-game expected score (tests only): independent games, draw rate d."""
    m = proto["synthetic"]
    sd_g = math.sqrt((1 - m["draw"]) / 4)
    mu = 0.5 + m["true_nelo"] * LN10 / 800 * sd_g
    pw, pl = mu - m["draw"] / 2, 1 - mu - m["draw"] / 2
    games = []
    for gi, white in enumerate(("cand", "base")):
        x = random.Random(f"{m['seed']}:{j}:{gi}").random()
        cand_res = "w" if x < pw else ("l" if x < pw + pl else "d")
        res = "1/2-1/2" if cand_res == "d" else ("1-0" if (cand_res == "w") == (white == "cand") else "0-1")
        games.append({"white": white, "result": res, "termination": "synthetic"})
    return games


def pgn_pairs(text, cand_name, base_name):
    by = {}
    for blk in text.replace("\r\n", "\n").split("[Event ")[1:]:
        t = dict(TAG.findall("[Event " + blk))
        try:
            rnd = int(str(t.get("Round", "")).split(".")[0])
        except ValueError:
            raise Stop(31, "PGN game without numeric Round")
        by.setdefault(rnd, []).append(t)
    out = {}
    for rnd, gs in sorted(by.items()):
        if len(gs) != 2:
            raise Stop(31, f"PGN round {rnd} has {len(gs)} games (pairs need exactly 2)")
        if sorted(g.get("White") for g in gs) != sorted([cand_name, base_name]):
            raise Stop(31, f"PGN round {rnd}: not one game each as White")
        for g in gs:
            if g.get("Result") not in ("1-0", "0-1", "1/2-1/2"):
                raise Stop(31, f"PGN round {rnd}: unfinished result {g.get('Result')!r}")
        out[rnd - 1] = {"games": [{"white": "cand" if g["White"] == cand_name else "base", "result": g["Result"],
                                   "termination": g.get("Termination", "?")} for g in gs],
                        "fen": gs[0].get("FEN")}
    return out


def leakage(proto, fens):
    keys = set()
    for p in proto.get("training_keys_files", []):
        if fh(p["path"]) != p["sha256"].lower():
            raise Stop(20, f"training keys file changed: {p['path']}")
        keys |= {" ".join(x.split()[:3]) for x in Path(p["path"]).read_text(encoding="ascii").splitlines() if x}
    hits = [i for i, f in fens if f and " ".join(f.split()[:3]) in keys]
    return hits


# --- commands --------------------------------------------------------------------------------------------------------
def fastchess_cmd(proto, cand, start, rounds, base):
    m, ide = proto["match"], proto["identity"]
    copt = [f"option.{k}={v}" for k, v in cand["engine_options"].items()]
    std = ["option.Threads=1", "option.Hash=16", "option.OwnBook=false"]
    return ([ide["fastchess"]["path"], "-engine", "name=cand", f"cmd={ide['cand_exe']['path']}"] + std + copt +
            ["-engine", "name=base", f"cmd={ide['base_exe']['path']}"] + std +
            ["-each", f"tc={m['tc']}", "timemargin=1000", "proto=uci", "-openings", f"file={ide['holdout']['path']}",
             "format=pgn", "order=sequential", f"start={start}", "-games", "2", "-repeat", "-rounds", str(rounds),
             "-concurrency", str(m.get("concurrency", 1)), "-recover", "-pgnout", f"file={base}.pgn"])


def run(proto_path, cand_path, run_dir, args):
    proto = load(proto_path, "opus3-confirm-protocol/1")
    cand = load(cand_path, "opus3-candidate-spec/1")
    verify_candidate(cand)
    ident = check_identity(proto)
    if proto["identity"]["holdout"]["sha256"].lower() != proto["holdout"]["pgn_sha256"]:
        raise Stop(10, "protocol identity.holdout is not the named holdout group")
    check_holdout(proto, cand, run_dir)
    mode = args.get("mode", "dry-run")
    psha = h(cj(proto))
    run_id = f"confirm:{proto['holdout']['name']}:{cand['spec_sha256'][:12]}:{psha[:12]}"
    d = Path(run_dir)
    if mode == "dry-run":
        cmd = fastchess_cmd(proto, cand, 1, proto["sprt"]["cap_games"] // 2, d / "games" / "c000000")
        print(json.dumps({"mode": "dry-run", "wrote_files": 0, "started_processes": 0, "identity_ok": ident,
                          "run_id": run_id, "fastchess_command": subprocess.list2cmdline([str(x) for x in cmd])}, indent=1))
        return 0
    if mode == "live":
        ack = d / "LIVE_ACK.txt"
        if not args.get("live") or not proto.get("live", {}).get("enabled") or not ack.exists() or \
                ack.read_text(encoding="ascii", errors="replace").strip() != psha:
            raise Stop(40, f"live confirmation needs --live, protocol.live.enabled and {ack} containing {psha}")
    meta_p = d / "CONFIRM.json"
    if meta_p.exists():
        if not args.get("resume"):
            raise Stop(10, f"{d} exists: pass --resume")
        meta = json.loads(meta_p.read_text(encoding="ascii"))
        if meta["protocol_sha256"] != psha or meta["candidate_sha256"] != cand["spec_sha256"] or meta["mode"] != mode:
            raise Stop(11, "protocol, candidate or mode differ from this run's CONFIRM.json")
        if meta["identity"] != ident:
            raise Stop(20, "pinned identity differs from CONFIRM.json")
    elif args.get("resume"):
        raise Stop(10, "--resume given but no run")
    else:
        d.mkdir(parents=True, exist_ok=True)
        put(meta_p, cj({"schema": "opus3-confirm-run/1", "run_id": run_id, "protocol_sha256": psha, "mode": mode,
                        "candidate_sha256": cand["spec_sha256"], "identity": ident, "protocol": proto, "candidate": cand}))
        crash("after_meta")
    register(proto, cand, run_id, d)
    book = Book(d, run_id).load()
    if not book.recs:
        book.add("start", {"protocol_sha256": psha, "candidate_sha256": cand["spec_sha256"], "mode": mode})
        crash("after_start")
    st = state_of(book.recs, proto)
    ckpt(d, book, st, proto)
    limit = args.get("max_pairs")
    done = 0
    replay = None
    if mode == "replay":
        rp = proto["replay"]
        replay = {}
        for e in rp["pgns"]:
            if fh(e["path"]) != e["sha256"].lower():
                raise Stop(20, f"replay PGN changed: {e['path']}")
            replay.update({e["first_pair"] + k: v for k, v in
                           pgn_pairs(Path(e["path"]).read_text(encoding="utf-8", errors="replace"),
                                     rp.get("cand_name", "cand"), rp.get("base_name", "base")).items()})
    while st["decision"] is None:
        cur = summary(st, proto)
        if cur["verdict"] is not None:
            book.add("decision", {k: cur[k] for k in ("verdict", "penta", "pairs", "games")} | {"llr": cur["llr"]})
            crash("after_decision")
            st = state_of(book.recs, proto)
            ckpt(d, book, st, proto)
            break
        if limit is not None and done >= limit:
            break
        j = len(st["pairs"])
        if mode == "synthetic":
            games, src = synthetic_pair(proto, j), {"mode": "synthetic", "seed": proto["synthetic"]["seed"]}
        elif mode == "replay":
            if j not in replay:
                if any(k > j for k in replay):
                    raise Stop(31, f"replay has no complete pair {j} but later pairs exist (incomplete run)")
                break  # replay exhausted without a decision: reported, nothing claimed
            games, src = replay[j]["games"], {"mode": "replay"}
        else:
            raise Stop(10, "live play is not implemented in this job's runner; QA runs the SPRT with forge_queue.ps1 "
                           "and audits it with audit-pgn")
        r = book.add("pair", {"j": j, "games": games, "score": score_pair(games), "source": src})
        st["pairs"][j] = r
        done += 1
        crash("after_pair", j + 1)
        if (j + 1) % proto.get("checkpoint_every", 50) == 0:
            ckpt(d, book, st, proto)
    final = summary(st, proto)
    out = {"run_id": run_id, "mode": mode,
           "verdict": final["verdict"] or ("replay exhausted, no decision (no claim)" if mode == "replay"
                                           else "open (no decision yet)"), "pairs": final["pairs"],
           "games": final["games"], "penta": final["penta"], "llr": round(final["llr"], 4),
           "decision_recorded": st["decision"] is not None}
    if mode == "synthetic":
        out["label"] = "SYNTHETIC: model outcomes; no Elo is measured or claimed"
    print(json.dumps(out, indent=1))
    return 0


def ckpt(d, book, st, proto):
    """Checkpoint seq = number of checkpoints so far; content = ledger prefix + summary (no wall clock)."""
    cdir = d / "ckpt"
    cdir.mkdir(exist_ok=True)
    head = d / "HEAD.json"
    seq, prev = 0, "genesis"
    if head.exists():
        hd = json.loads(head.read_text(encoding="ascii"))
        data = (cdir / f"c_{hd['seq']:06d}.json").read_bytes()
        if h(data) != hd["sha256"]:
            raise Stop(30, "checkpoint does not match HEAD")
        seq, prev = hd["seq"] + 1, hd["sha256"]
        last = json.loads(data.decode("ascii"))
        if last["ledger_records"] == len(book.recs):
            return  # nothing new since the last checkpoint
        if last["ledger_records"] > len(book.recs) or book.recs[last["ledger_records"] - 1]["h"] != last["ledger_head"]:
            raise Stop(30, "checkpoint names a ledger prefix that is not in the ledger")
    for p in sorted(cdir.glob("c_*.json.tmp")):
        p.unlink()
    obj = {"seq": seq, "prev": prev, "ledger_records": len(book.recs), "ledger_head": book.recs[-1]["h"],
           "summary": summary(st, proto)}
    data = cj(obj)
    put(cdir / f"c_{seq:06d}.json", data, "ckpt", seq)
    put(head, cj({"seq": seq, "sha256": h(data)}))


def verify(run_dir):
    d = Path(run_dir)
    meta = json.loads((d / "CONFIRM.json").read_text(encoding="ascii"))
    proto = meta["protocol"]
    book = Book(d, meta["run_id"]).load(repair=False)
    st = state_of(book.recs, proto)
    prev = "genesis"
    files = sorted((d / "ckpt").glob("c_*.json"))
    for i, p in enumerate(files):
        data = p.read_bytes()
        o = json.loads(data.decode("ascii"))
        if o["seq"] != i or o["prev"] != prev:
            raise Stop(30, f"checkpoint chain broken at {p.name}")
        n = o["ledger_records"]
        if n > len(book.recs) or book.recs[n - 1]["h"] != o["ledger_head"]:
            raise Stop(30, f"{p.name} names a missing ledger prefix")
        prev = h(data)
    hd = json.loads((d / "HEAD.json").read_text(encoding="ascii"))
    if hd["sha256"] != prev:
        raise Stop(30, "HEAD does not name the newest checkpoint")
    print(json.dumps({"verify": "OK", "summary": summary(st, proto), "checkpoints": len(files)}, indent=1))
    return 0


def audit_pgn(proto_path, cand_path, pgns):
    """Read-only audit of QA's confirmation PGN(s): pairs, pentanomial, LLR recomputed, opening leakage."""
    proto = load(proto_path, "opus3-confirm-protocol/1")
    cand = load(cand_path, "opus3-candidate-spec/1")
    verify_candidate(cand)
    qa = proto["qa_gate"]
    pairs = {}
    off = 0
    for p in pgns:
        got = pgn_pairs(Path(p).read_text(encoding="utf-8", errors="replace"), qa["cand_name"], qa["base_name"])
        pairs.update({off + k: v for k, v in got.items()})
        off = max(pairs) + 1 if pairs else off
    leak = leakage(proto, [(j, v["fen"]) for j, v in pairs.items()])
    st_all = {"pairs": {j: {"score": score_pair(v["games"]), "games": v["games"]} for j, v in pairs.items()}}
    st_clean = {"pairs": {j: x for j, x in st_all["pairs"].items() if j not in set(leak)}}
    a, c = summary(st_all, proto), summary(st_clean, proto)
    print(json.dumps({"audit": "QA confirmation PGN (independent recomputation)", "all_pairs": a,
                      "pairs_without_training_positions": c, "leaked_pairs": len(leak),
                      "leak_fraction": (len(leak) / len(pairs)) if pairs else 0.0,
                      "protocol_rule": "claim only if QA's verdict and this recomputation agree and leakage <= 1%"},
                     indent=1))
    return 0


def main(argv):
    try:
        args, pos = {}, []
        i = 2
        while i < len(argv):
            a = argv[i]
            if a in ("--resume", "--live"):
                args[a[2:]] = True
            elif a in ("--mode", "--max-pairs"):
                args[a[2:].replace("-", "_")] = int(argv[i + 1]) if a == "--max-pairs" else argv[i + 1]
                i += 1
            else:
                pos.append(a)
            i += 1
        cmd = argv[1] if len(argv) > 1 else ""
        if cmd == "run" and len(pos) == 3:
            return run(pos[0], pos[1], pos[2], args)
        if cmd == "verify" and len(pos) == 1:
            return verify(pos[0])
        if cmd == "audit-pgn" and len(pos) >= 3:
            return audit_pgn(pos[0], pos[1], pos[2:])
        print(__doc__)
        return 10
    except Stop as e:
        print(json.dumps({"refused": True, "exit": e.code, "reason": str(e)}), file=sys.stderr)
        return e.code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
