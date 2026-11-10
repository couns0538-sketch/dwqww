"""opus3_spsa.py - resumable, hash-pinned, paired SPSA harness (extends R9's r9_spsa.py; see PROVENANCE.md).

usage (Python 3.10, run as python -I -B; the PowerShell entry point is ..\\bin\\spsa.ps1):
  opus3_spsa.py run <config.json> <run_dir> [--mode dry-run|synthetic|replay|live] [--resume] [--live]
                    [--max-batches N] [--max-pairs N] [--total-pairs N]
  opus3_spsa.py status <run_dir>          state, theta, budgets (read-only)
  opus3_spsa.py verify <run_dir>          full verification of ledger, checkpoints and identity (read-only)
  opus3_spsa.py rollback <run_dir> --to-ckpt N        new checkpoint with theta and k of checkpoint N (logged)
  opus3_spsa.py rollback <config.json> --baseline     prints the baseline (lock) option line; writes nothing
  opus3_spsa.py export <run_dir> --out <dir>          history.csv and candidate.json derived from the ledger

Modes: dry-run (DEFAULT) validates the config and pins, prints the exact fastchess command of the next batch and
writes nothing. synthetic plays seeded outcomes from a known model (no engine, no games). replay reads saved PGNs
listed in a hash-pinned manifest. live runs fastchess and REFUSES unless --live is given, config.live.enabled is
true and <run_dir>/LIVE_ACK.txt contains the config's sha256 (never used by this job).
State: RUN.json (immutable), ledger.jsonl (hash chain, source of truth), ckpt/ckpt_<seq>.json + HEAD.json (atomic).
Every resume replays the ledger and recomputes each plan and update; a recorded value that the config does not
reproduce is refused. A pair is identified by run/batch/index and counted once; an update is applied once.
Exit codes: 0 ok, 10 config invalid, 11 config changed, 20 identity changed, 30 corrupt state, 31 bad results
(duplicate, unknown, incomplete, stale), 40 live guard, 41 holdout referenced, 77 injected crash (tests)."""
import csv
import json
import math
import os
import random
import re
import shlex
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from ledger import (EXIT_CONFIG, EXIT_CONFIG_CHANGED, EXIT_CORRUPT, EXIT_HOLDOUT, EXIT_IDENTITY,  # noqa: E402
                    EXIT_LIVE_GUARD, EXIT_RESULTS, Checkpoints, Ledger, Refuse, canon, crash_point, sha256_bytes,
                    sha256_file, write_atomic)
from space import SCHEMA, Space, SpaceError  # noqa: E402

TAG_RE = re.compile(r'^\[(\w+) "([^"]*)"\]\s*$', re.M)
RESULTS = ("1-0", "0-1", "1/2-1/2")


# --- config and identity -------------------------------------------------------------------------------------------
def load_config(path):
    try:
        cfg = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    except (OSError, ValueError) as e:
        raise Refuse(EXIT_CONFIG, f"config unreadable: {e}")
    if cfg.get("schema") != SCHEMA:
        raise Refuse(EXIT_CONFIG, f"config schema must be {SCHEMA}")
    for key in ("name", "seed", "pairs_planned", "pairs_per_batch", "params", "identity", "engine", "openings"):
        if key not in cfg:
            raise Refuse(EXIT_CONFIG, f"config lacks {key}")
    try:
        Space(cfg)
    except (SpaceError, KeyError, TypeError, ValueError) as e:
        raise Refuse(EXIT_CONFIG, f"config parameters invalid: {e}")
    if cfg["openings"].get("role") != "train":
        raise Refuse(EXIT_HOLDOUT, "the tuner only reads a training partition (openings.role must be 'train')")
    forbidden = set(cfg["openings"].get("forbidden_sha256", []))
    if cfg["identity"]["openings"]["sha256"] in forbidden:
        raise Refuse(EXIT_HOLDOUT, "the openings file is a holdout/screen partition")
    return cfg


def config_sha(cfg):
    return sha256_bytes(canon(cfg))


def core_config_sha(cfg):
    """sha256 of the config without its "replay" section: a replay manifest names the run and core config it
    belongs to, while the config pins the manifest's own sha256 (no circular hashing)."""
    return sha256_bytes(canon({k: v for k, v in cfg.items() if k != "replay"}))


def run_id_of(cfg):
    return f"{cfg['name']}:{cfg.get('run_nonce', '0')}:{core_config_sha(cfg)[:12]}"


def check_identity(cfg):
    """Every pinned file must exist and hash to its pinned sha256 (exe, openings subset, fastchess, ...)."""
    got = {}
    for key, ent in sorted(cfg["identity"].items()):
        p = Path(ent["path"])
        if not p.exists():
            raise Refuse(EXIT_IDENTITY, f"pinned {key} missing: {p}")
        h = sha256_file(p)
        if h != ent["sha256"].lower():
            raise Refuse(EXIT_IDENTITY, f"pinned {key} changed: {p} sha256 {h} != {ent['sha256']}")
        got[key] = h
    return got


def option_line(cfg, values):
    eng = cfg["engine"]
    opts = dict(eng.get("fixed_options", {}))
    opts.update(eng.get("switch_options", {}))
    opts.update(values)
    return [f"option.{k}={'true' if v is True else 'false' if v is False else v}" for k, v in opts.items()]


def read_openings(cfg, key="openings"):
    """sha256 of every opening of a pinned openings file (index = position in the file)."""
    text = Path(cfg["identity"][key]["path"]).read_bytes().decode("utf-8", "replace").replace("\r\n", "\n")
    if cfg["openings"].get("format", "pgn") == "epd":
        items = [x for x in text.split("\n") if x.strip()]
    else:
        items = ["[Event " + g for g in text.split("[Event ")[1:]]
    if not items:
        raise Refuse(EXIT_CONFIG, "the openings file holds no opening")
    return [sha256_bytes(x.strip().encode("utf-8")) for x in items]


# --- PGN -----------------------------------------------------------------------------------------------------------
def parse_pgn_games(text):
    games = []
    for block in text.replace("\r\n", "\n").split("[Event ")[1:]:
        tags = dict(TAG_RE.findall("[Event " + block))
        games.append(tags)
    return games


def pairs_from_pgn(text, plus_name, minus_name, npairs):
    """fastchess -games 2 -repeat layout: both games of pair j carry Round j+1, colours swapped. Returns
    {j: [game, game]}; refuses duplicates, unknown rounds, foreign engines, bad results and incomplete pairs."""
    by_round = {}
    for g in parse_pgn_games(text):
        try:
            rnd = int(str(g.get("Round", "")).split(".")[0])
        except ValueError:
            raise Refuse(EXIT_RESULTS, f"PGN game without a numeric Round: {g.get('Round')!r}")
        by_round.setdefault(rnd, []).append(g)
    out = {}
    for rnd, gs in sorted(by_round.items()):
        j = rnd - 1
        if not 0 <= j < npairs:
            raise Refuse(EXIT_RESULTS, f"PGN round {rnd} is not a planned pair (1..{npairs})")
        if len(gs) != 2:
            raise Refuse(EXIT_RESULTS, f"PGN round {rnd} has {len(gs)} games (a pair needs exactly 2)")
        whites = sorted(g.get("White") for g in gs)
        if whites != sorted([plus_name, minus_name]):
            raise Refuse(EXIT_RESULTS, f"PGN round {rnd}: engines {whites} are not one game each as White")
        for g in gs:
            if {g.get("White"), g.get("Black")} != {plus_name, minus_name}:
                raise Refuse(EXIT_RESULTS, f"PGN round {rnd}: foreign engine names")
            if g.get("Result") not in RESULTS:
                raise Refuse(EXIT_RESULTS, f"PGN round {rnd}: unfinished or invalid result {g.get('Result')!r}")
        out[j] = [{"white": "plus" if g["White"] == plus_name else "minus", "result": g["Result"],
                   "termination": g.get("Termination", "?")} for g in gs]
    return out


def score_games(games):
    w = l = d = 0
    for g in games:
        if g["result"] == "1/2-1/2":
            d += 1
        elif (g["result"] == "1-0") == (g["white"] == "plus"):
            w += 1
        else:
            l += 1
    return w, l, d


# --- backends ------------------------------------------------------------------------------------------------------
class Synthetic:
    """Known strength model in synthetic units (no Elo is claimed): quadratic with optional cross terms, or flat."""

    def __init__(self, cfg):
        self.m = cfg["synthetic"]
        self.seed = self.m.get("seed", 1)

    def strength(self, vals):
        m = self.m
        if m.get("kind", "quadratic") == "flat":
            return 0.0
        z = {n: (vals[n] - o) / m["scale"][n] for n, o in m["opt"].items()}
        s = -m.get("K", 20.0) * sum(v * v for v in z.values())
        for a, b, rho in m.get("cross", []):
            s += m.get("K", 20.0) * rho * z[a] * z[b]
        return s

    def play(self, pair, plus, minus):
        diff = self.strength(plus) - self.strength(minus)
        p = 1.0 / (1.0 + 10.0 ** (-diff / 400.0))
        draw = self.m.get("draw", 0.5)
        wp = max(0.0, min(1.0, (1 - draw + 2 * p - 1) / 2))
        lp = max(0.0, min(1.0, (1 - draw - (2 * p - 1)) / 2))
        games = []
        for gi, white in enumerate(("plus", "minus")):
            x = random.Random(f"{self.seed}:{pair['pair_id']}:{gi}").random()
            plus_res = "w" if x < wp else "l" if x < wp + lp else "d"
            res = "1/2-1/2" if plus_res == "d" else ("1-0" if (plus_res == "w") == (white == "plus") else "0-1")
            games.append({"white": white, "result": res, "termination": "synthetic"})
        return games


class Replay:
    def __init__(self, cfg, run_id):
        ent = cfg["replay"]
        mp = Path(ent["manifest"])
        if sha256_file(mp) != ent["manifest_sha256"].lower():
            raise Refuse(EXIT_IDENTITY, "replay manifest changed")
        self.man = json.loads(mp.read_text(encoding="utf-8-sig"))
        if self.man.get("run_id") != run_id or self.man.get("core_config_sha256") != core_config_sha(cfg):
            raise Refuse(EXIT_RESULTS, "replay manifest belongs to another run or config (stale)")
        self.base = mp.parent
        self.cache = {}

    def results(self, batch, npairs):
        if batch not in self.cache:
            ents = [b for b in self.man["batches"] if b["batch"] == batch]
            if len(ents) != 1:
                raise Refuse(EXIT_RESULTS, f"replay manifest has {len(ents)} entries for batch {batch}")
            p = self.base / ents[0]["pgn"]
            data = p.read_bytes()
            if sha256_bytes(data) != ents[0]["sha256"].lower():
                raise Refuse(EXIT_IDENTITY, f"replay PGN {p.name} changed")
            pairs = pairs_from_pgn(data.decode("utf-8", "replace"), self.man.get("plus_name", "plus"),
                                   self.man.get("minus_name", "minus"), npairs)
            self.cache[batch] = (pairs, ents[0]["sha256"].lower())
        return self.cache[batch]


def fastchess_cmd(cfg, plus, minus, start, rounds, base):
    m, eng = cfg["match"], cfg["engine"]
    def side(name, vals):
        return ["-engine", f"name={name}", f"cmd={cfg['identity']['engine_exe']['path']}"] + option_line(cfg, vals)
    return ([cfg["identity"]["fastchess"]["path"]] + side("plus", plus) + side("minus", minus) +
            ["-each", f"tc={m['tc']}", f"timemargin={m.get('timemargin', 1000)}", "proto=uci",
             "-openings", f"file={cfg['identity']['openings']['path']}", f"format={cfg['openings'].get('format', 'pgn')}",
             "order=sequential", f"start={start}", "-games", "2", "-repeat", "-rounds", str(rounds),
             "-concurrency", str(m.get("concurrency", 1)), "-recover", "-pgnout", f"file={base}.pgn"])


def live_guard(cfg, run_dir, args):
    csha = config_sha(cfg)
    ack = Path(run_dir) / "LIVE_ACK.txt"
    if not args.get("live"):
        raise Refuse(EXIT_LIVE_GUARD, "live mode needs --live")
    if not cfg.get("live", {}).get("enabled", False):
        raise Refuse(EXIT_LIVE_GUARD, "live mode needs config.live.enabled = true")
    if not ack.exists() or ack.read_text(encoding="ascii", errors="replace").strip() != csha:
        raise Refuse(EXIT_LIVE_GUARD, f"live mode needs {ack} containing the config sha256 {csha}")


# --- state -------------------------------------------------------------------------------------------------------
class Run:
    def __init__(self, cfg, run_dir, mode):
        self.cfg, self.dir, self.mode = cfg, Path(run_dir), mode
        self.space = Space(cfg)
        self.csha = config_sha(cfg)
        self.run_id = run_id_of(cfg)
        self.ledger = Ledger(self.dir, self.run_id)
        self.ckpts = Checkpoints(self.dir)
        self.openings = read_openings(cfg)
        self.screen_openings = read_openings(cfg, "screen_openings") if cfg.get("screen", {}).get("enabled") else None
        self.backend = None

    # replay of the ledger: the only way state is ever built
    def rebuild(self, on_ckpt=None):
        """State after replaying every ledger record (each plan and update is recomputed and must match).
        on_ckpt(index, state) is called after every checkpointable record (used by verify)."""
        st = {"k": 0, "batch": 0, "theta": None, "pending": None, "results": {}, "complete": False,
              "screen_pairs": 0}
        for idx, rec in enumerate(self.ledger.records):
            self._apply(st, rec)
            if on_ckpt and rec["type"] in CKPT_TYPES:
                on_ckpt(idx, st)
        if st["theta"] is None:
            raise Refuse(EXIT_CORRUPT, "ledger has no init record")
        return st

    def _apply(self, st, rec):
        if True:
            t = rec["type"]
            if t == "init":
                if rec["seq"] != 0 or rec.get("config_sha256") != self.csha or rec.get("names") != self.space.names \
                        or rec.get("theta") != self.space.start_theta():
                    raise Refuse(EXIT_CORRUPT, "init record does not match the config")
                st["theta"] = rec["theta"]
            elif t == "plan":
                if st["pending"] is not None or rec.get("batch") != st["batch"] or rec.get("role") not in ("train", "screen"):
                    raise Refuse(EXIT_CORRUPT, f"plan record of batch {rec.get('batch')} out of order")
                want = self.make_plan(st, rec["role"])
                if canon(want) != canon({k: rec.get(k) for k in want}):
                    raise Refuse(EXIT_CORRUPT, f"plan of batch {rec['batch']} is not reproduced by the config")
                st["pending"], st["results"] = rec, {}
            elif t == "pair":
                pend = st["pending"]
                if pend is None or rec["batch"] != pend["batch"]:
                    raise Refuse(EXIT_RESULTS, f"pair {rec.get('pair_id')} has no open plan")
                ids = [p["pair_id"] for p in pend["pairs"]]
                if rec["pair_id"] not in ids:
                    raise Refuse(EXIT_RESULTS, f"pair {rec['pair_id']} was not planned")
                if rec["pair_id"] in st["results"]:
                    raise Refuse(EXIT_RESULTS, f"pair {rec['pair_id']} recorded twice")
                if len(rec["games"]) != 2 or sorted(g["white"] for g in rec["games"]) != ["minus", "plus"]:
                    raise Refuse(EXIT_RESULTS, f"pair {rec['pair_id']} is not two games with colours swapped")
                if list(score_games(rec["games"])) != [rec["W"], rec["L"], rec["D"]]:
                    raise Refuse(EXIT_RESULTS, f"pair {rec['pair_id']} score does not match its games")
                st["results"][rec["pair_id"]] = rec
            elif t in ("update", "screen"):
                pend = st["pending"]
                if pend is None or rec["batch"] != pend["batch"] or len(st["results"]) != len(pend["pairs"]):
                    raise Refuse(EXIT_CORRUPT, f"{t} record of batch {rec['batch']} before all its pairs")
                if (t == "update") != (pend["role"] == "train"):
                    raise Refuse(EXIT_CORRUPT, f"{t} record closes a {pend['role']} batch")
                want = self.make_close(st)
                if canon(want) != canon({k: rec.get(k) for k in want}):
                    raise Refuse(EXIT_CORRUPT, f"{t} of batch {rec['batch']} is not reproduced by its pairs")
                self.apply_close(st, rec)
            elif t == "rollback":
                if st["pending"] is not None:
                    raise Refuse(EXIT_CORRUPT, "rollback record inside an open batch")
                st["theta"], st["k"] = rec["theta"], rec["k"]
            elif t == "complete":
                if st["pending"] is not None or st["k"] < self.cfg["pairs_planned"] or rec.get("theta") != st["theta"]:
                    raise Refuse(EXIT_CORRUPT, "complete record does not match the run")
                st["complete"] = True
            else:
                raise Refuse(EXIT_CORRUPT, f"unknown ledger record type {t}")
            if t != "init" and st["theta"] is None:
                raise Refuse(EXIT_CORRUPT, "ledger does not start with an init record")

    def make_plan(self, st, role):
        sp = self.space
        if role == "train":
            n, ops = self.cfg["pairs_per_batch"], self.openings
            p = sp.plan(st["theta"], st["k"])
            start = st["k"] % len(ops)
        else:  # screening: current theta against the baseline on the screen partition; never feeds an update
            n, ops = self.cfg["screen"]["pairs"], self.screen_openings
            p = {"k": st["k"], "plus": sp.engine_values(st["theta"]), "minus": self.baseline_values()}
            start = (st["screen_pairs"]) % len(ops)
        pairs = [{"pair_id": f"{self.run_id}/b{st['batch']:06d}/p{j:03d}", "j": j,
                  "opening_index": (start + j) % len(ops), "opening_sha256": ops[(start + j) % len(ops)]}
                 for j in range(n)]
        return {"batch": st["batch"], "role": role, "plan": p, "pairs": pairs}

    def make_close(self, st):
        pend = st["pending"]
        w = sum(r["W"] for r in st["results"].values())
        l = sum(r["L"] for r in st["results"].values())
        d = sum(r["D"] for r in st["results"].values())
        out = {"batch": pend["batch"], "W": w, "L": l, "D": d}
        if pend["role"] == "train":
            out["update"] = self.space.update(pend["plan"], w, l, len(pend["pairs"]))
        return out

    def apply_close(self, st, rec):
        if st["pending"]["role"] == "train":
            st["theta"], st["k"] = rec["update"]["theta_after"], rec["update"]["k_after"]
        else:
            st["screen_pairs"] += len(st["pending"]["pairs"])
        st["batch"] += 1
        st["pending"], st["results"] = None, {}

    def baseline_values(self):
        return {p["name"]: p["lock"] for p in self.cfg["params"]}

    def ckpt_state(self, st, nrec=None, head=None):
        nrec = len(self.ledger.records) if nrec is None else nrec
        head = self.ledger.head if head is None else head
        return {"schema": "opus3-spsa-ckpt/1", "run_id": self.run_id, "config_sha256": self.csha, "mode": self.mode,
                "k": st["k"], "batch": st["batch"], "theta": st["theta"], "complete": st["complete"],
                "pending": None if st["pending"] is None else {"batch": st["pending"]["batch"],
                                                                "role": st["pending"]["role"],
                                                                "plan_h": st["pending"]["h"],
                                                                "pairs": [p["pair_id"] for p in st["pending"]["pairs"]],
                                                                "done": sorted(st["results"])},
                "ledger": {"records": nrec, "head": head},
                "budgets": {"train_pairs": st["k"], "screen_pairs": st["screen_pairs"],
                            "pairs_planned": self.cfg["pairs_planned"]}}

    def checkpoint(self, st, tag, batch):
        """Checkpoint n is the state right after the n-th checkpointable ledger record (CKPT_TYPES), so the
        checkpoint sequence is a function of the ledger and identical for interrupted and uninterrupted runs."""
        head = self.ckpts.head()
        seq = 0 if head is None else head[0] + 1
        prev = "genesis" if head is None else head[2]
        self.ckpts.write(seq, self.ckpt_state(st), prev,
                         crash=lambda step: crash_point(f"{tag}{'6' if step == 'tmp' else '7'}", batch))


CKPT_TYPES = ("init", "plan", "update", "screen", "complete", "rollback")


def open_run(cfg_path, run_dir, mode, resume):
    cfg = load_config(cfg_path)
    d = Path(run_dir)
    if (d / "RUN.json").exists():
        if not resume:
            raise Refuse(EXIT_CONFIG, f"{d} exists: pass --resume to continue it")
        meta = json.loads((d / "RUN.json").read_text(encoding="ascii"))
        if meta["config_sha256"] != config_sha(cfg):
            raise Refuse(EXIT_CONFIG_CHANGED, "config differs from the run's RUN.json (a resume keeps its config)")
        if meta["mode"] != mode:
            raise Refuse(EXIT_CONFIG_CHANGED, f"run was created in mode {meta['mode']}, not {mode}")
        ident = check_identity(cfg)
        if ident != meta["identity"]:
            raise Refuse(EXIT_IDENTITY, "pinned identity differs from RUN.json")
    elif resume:
        raise Refuse(EXIT_CONFIG, f"--resume given but {d} has no run")
    return Run(cfg, d, mode)


def cmd_run(cfg_path, run_dir, args):
    mode = args.get("mode", "dry-run")
    if mode == "dry-run":
        return dry_run(cfg_path, run_dir)
    run = open_run(cfg_path, run_dir, mode, args.get("resume", False))
    cfg = run.cfg
    if mode == "live":
        live_guard(cfg, run_dir, args)
    run.dir.mkdir(parents=True, exist_ok=True)
    if not (run.dir / "RUN.json").exists():
        ident = check_identity(cfg)
        meta = {"schema": "opus3-spsa-run/1", "run_id": run.run_id, "config_sha256": run.csha, "mode": mode,
                "identity": ident, "config": cfg}
        write_atomic(run.dir / "RUN.json", canon(meta))
        crash_point("B0", 0)
    run.ledger.load()
    if not run.ledger.records:  # new run, or a crash between RUN.json and the init record
        ident = json.loads((run.dir / "RUN.json").read_text(encoding="ascii"))["identity"]
        run.ledger.append("init", {"config_sha256": run.csha, "identity": ident,
                                   "theta": run.space.start_theta(), "names": run.space.names})
        crash_point("B1", 0)
        run.checkpoint(run.rebuild(), "I", 0)
    st = run.rebuild()
    reconcile_checkpoints(run, st)
    if mode == "synthetic":
        run.backend = Synthetic(cfg)
    elif mode == "replay":
        run.backend = Replay(cfg, run.run_id)
    max_batches, max_pairs, total = args.get("max_batches"), args.get("max_pairs"), args.get("total_pairs")
    done_batches = done_pairs = 0
    screen = cfg.get("screen", {})
    while True:
        if st["complete"]:
            break
        if st["pending"] is None:
            if st["k"] >= cfg["pairs_planned"]:
                run.ledger.append("complete", {"k": st["k"], "theta": st["theta"],
                                               "values": run.space.engine_values(st["theta"])})
                crash_point("BC", st["batch"])
                st["complete"] = True
                run.checkpoint(st, "C", st["batch"])
                break
            if (max_batches is not None and done_batches >= max_batches) or \
               (max_pairs is not None and done_pairs >= max_pairs) or (total is not None and st["k"] >= total):
                break
            check_identity(cfg)
            role = "train"
            if screen.get("enabled") and st["batch"] > 0 and st["batch"] % (screen["every"] + 1) == screen["every"]:
                role = "screen"
            plan = run.make_plan(st, role)
            rec = run.ledger.append("plan", plan)
            crash_point("B2", st["batch"])
            st["pending"], st["results"] = rec, {}
            run.checkpoint(st, "P", st["batch"])
        pend = st["pending"]
        b = pend["batch"]
        missing = [p for p in pend["pairs"] if p["pair_id"] not in st["results"]]
        if missing:
            play_pairs(run, st, pend, missing)
        crash_point("B4", b)
        close = run.make_close(st)
        crec = run.ledger.append("update" if pend["role"] == "train" else "screen", close)
        crash_point("B5", b)
        run.apply_close(st, crec)
        run.checkpoint(st, "B", b)
        crash_point("B8", b)
        done_batches += 1
        done_pairs += len(pend["pairs"])
    print(json.dumps(summary(run, st), indent=1))
    return 0


def play_pairs(run, st, pend, missing):
    p = pend["plan"]
    plus, minus = p["plus"], p["minus"]
    b = pend["batch"]
    if run.mode == "synthetic":
        for pair in missing:
            games = run.backend.play(pair, plus, minus)
            record_pair(run, st, pend, pair, games, {"mode": "synthetic", "model_seed": run.backend.seed})
    elif run.mode == "replay":
        pairs, sha = run.backend.results(b, len(pend["pairs"]))
        for pair in missing:
            if pair["j"] not in pairs:
                raise Refuse(EXIT_RESULTS, f"replay has no complete pair {pair['j'] + 1} for batch {b} (incomplete)")
            record_pair(run, st, pend, pair, pairs[pair["j"]], {"mode": "replay", "pgn_sha256": sha})
    elif run.mode == "live":
        live_play(run, st, pend, missing)
    else:
        raise Refuse(EXIT_CONFIG, f"unknown mode {run.mode}")


def record_pair(run, st, pend, pair, games, source):
    w, l, d = score_games(games)
    rec = run.ledger.append("pair", {"batch": pend["batch"], "pair_id": pair["pair_id"], "j": pair["j"],
                                     "games": games, "W": w, "L": l, "D": d, "source": source})
    st["results"][pair["pair_id"]] = rec
    crash_point("B3", pend["batch"], len(st["results"]))


def live_play(run, st, pend, missing):
    """Contiguous runs of missing pairs, one fastchess call each; results recorded only after fastchess exits."""
    games_dir = run.dir / "games"
    games_dir.mkdir(exist_ok=True)
    runs, cur = [], []
    for pair in missing:
        if cur and pair["j"] != cur[-1]["j"] + 1:
            runs.append(cur)
            cur = []
        cur.append(pair)
    if cur:
        runs.append(cur)
    for chunk in runs:
        attempt = len(list(games_dir.glob(f"b{pend['batch']:06d}_*.pgn")))
        base = games_dir / f"b{pend['batch']:06d}_j{chunk[0]['j']:03d}_a{attempt}"
        cmd = fastchess_cmd(run.cfg, pend["plan"]["plus"], pend["plan"]["minus"], chunk[0]["opening_index"] + 1,
                            len(chunk), base)
        with open(f"{base}.out", "x", encoding="utf-8") as out:
            rc = subprocess.call(cmd, stdout=out, stderr=subprocess.STDOUT, cwd=str(games_dir))
        data = Path(f"{base}.pgn").read_bytes() if Path(f"{base}.pgn").exists() else b""
        pairs = pairs_from_pgn(data.decode("utf-8", "replace"), "plus", "minus", len(chunk))
        if rc != 0 or len(pairs) != len(chunk):
            raise Refuse(EXIT_RESULTS, f"fastchess exit {rc}, {len(pairs)} of {len(chunk)} pairs; batch stays open")
        for i, pair in enumerate(chunk):
            record_pair(run, st, pend, pair, pairs[i], {"mode": "live", "pgn_sha256": sha256_bytes(data)})


def reconcile_checkpoints(run, st):
    """Crash recovery of the checkpoint chain, refusing anything that is not one of the crash states:
    leftover *.tmp files are removed (crash before rename); a checkpoint one step newer than HEAD whose predecessor
    hash is HEAD's is adopted (crash after rename, before the HEAD update); HEAD missing is accepted only with no
    checkpoint or exactly ckpt_000000 (first checkpoint renamed, HEAD not yet written). Every adopted checkpoint must
    name a ledger prefix that exists. Then the one checkpoint a crash can lose (after its record was appended) is
    written from the ledger-derived state, so the checkpoint sequence equals an uninterrupted run's."""
    removed = run.ckpts.clean_tmp()
    files = run.ckpts.files()
    head = run.ckpts.head()
    if head is None:
        if files and [p.name for p in files] != ["ckpt_000000.json"]:
            raise Refuse(EXIT_CORRUPT, "HEAD.json is missing while several checkpoints exist")
        seq, sha, obj = -1, "genesis", None
    else:
        seq, obj, sha = head
    for p in files:
        n = int(p.stem.split("_")[1])
        if n == seq + 1:
            o2, s2 = run.ckpts.read(n)
            if o2.get("prev_ckpt_sha256") != sha or o2.get("seq") != n:
                raise Refuse(EXIT_CORRUPT, f"{p.name} does not follow checkpoint {seq}")
            seq, obj, sha = n, o2, s2
            write_atomic(run.ckpts.head_path, canon({"seq": seq, "sha256": sha}))
        elif n > seq + 1:
            raise Refuse(EXIT_CORRUPT, f"{p.name} is more than one step past HEAD")
    if obj is not None:
        led = obj["ledger"]
        if obj.get("run_id") != run.run_id or obj.get("config_sha256") != run.csha:
            raise Refuse(EXIT_CORRUPT, f"checkpoint {seq} belongs to another run or config")
        if led["records"] > len(run.ledger.records) or \
                (led["records"] and run.ledger.records[led["records"] - 1]["h"] != led["head"]):
            raise Refuse(EXIT_CORRUPT, f"checkpoint {seq} names a ledger prefix that is not in ledger.jsonl")
    count = sum(1 for r in run.ledger.records if r["type"] in CKPT_TYPES)
    have = seq + 1
    last = run.ledger.records[-1] if run.ledger.records else None
    if have == count - 1 and last is not None and last["type"] in CKPT_TYPES:
        tag = {"init": "I", "plan": "P", "update": "B", "screen": "B", "complete": "C", "rollback": "R"}[last["type"]]
        run.checkpoint(st, tag, st["batch"])
    elif have != count:
        raise Refuse(EXIT_CORRUPT, f"{have} checkpoints for {count} checkpointable ledger records")
    return removed


def summary(run, st):
    return {"run_id": run.run_id, "mode": run.mode, "k": st["k"], "batch": st["batch"], "complete": st["complete"],
            "pending": None if st["pending"] is None else st["pending"]["batch"],
            "theta": dict(zip(run.space.names, st["theta"])), "values": run.space.engine_values(st["theta"]),
            "ledger_records": len(run.ledger.records), "ledger_head": run.ledger.head,
            "repairs": run.ledger.repairs}


def dry_run(cfg_path, run_dir):
    """Validate, check pins, print the next batch's fastchess command; write nothing, start nothing."""
    cfg = load_config(cfg_path)
    ident = check_identity(cfg)
    d = Path(run_dir)
    st = {"k": 0, "batch": 0, "theta": Space(cfg).start_theta(), "pending": None, "results": {},
          "complete": False, "screen_pairs": 0}
    run = Run(cfg, d, "live")
    if (d / "RUN.json").exists():
        run.ledger.load(readonly=True)
        st = run.rebuild()
    plan = st["pending"] or run.make_plan(st, "train")
    p = plan["plan"]
    base = d / "games" / f"b{plan['batch']:06d}_j000_a0"
    cmd = fastchess_cmd(cfg, p["plus"], p["minus"], plan["pairs"][0]["opening_index"] + 1, len(plan["pairs"]), base)
    out = {"mode": "dry-run", "started_processes": 0, "wrote_files": 0, "identity_ok": ident,
           "live_enabled_in_config": cfg.get("live", {}).get("enabled", False), "batch": plan["batch"],
           "plus": p["plus"], "minus": p["minus"], "fastchess_command": subprocess.list2cmdline([str(x) for x in cmd])}
    print(json.dumps(out, indent=1))
    return 0


def open_readonly(run_dir):
    d = Path(run_dir)
    try:
        meta = json.loads((d / "RUN.json").read_text(encoding="ascii"))
    except (OSError, ValueError):
        raise Refuse(EXIT_CORRUPT, f"{d / 'RUN.json'} unreadable")
    if config_sha(meta["config"]) != meta["config_sha256"]:
        raise Refuse(EXIT_CORRUPT, "RUN.json config does not match its sha256")
    run = Run(meta["config"], d, meta["mode"])
    run.ledger.load(readonly=True)
    return run, meta


def cmd_status(run_dir):
    run, _ = open_readonly(run_dir)
    print(json.dumps(summary(run, run.rebuild()), indent=1))
    return 0


def cmd_verify(run_dir):
    run, meta = open_readonly(run_dir)
    ident = check_identity(run.cfg)
    if ident != meta["identity"]:
        raise Refuse(EXIT_IDENTITY, "pinned identity differs from RUN.json")
    led = run.ledger
    expected = []
    st = run.rebuild(on_ckpt=lambda i, s: expected.append(canon(run.ckpt_state(s, i + 1, led.records[i]["h"]))))
    prev = "genesis"
    files = run.ckpts.files()
    if len(files) != len(expected):
        raise Refuse(EXIT_CORRUPT, f"{len(files)} checkpoints for {len(expected)} checkpointable ledger records "
                                   "(a resume writes the one a crash can lose)")
    for i, p in enumerate(files):
        obj, sha = run.ckpts.read(i)
        if p.name != f"ckpt_{i:06d}.json" or obj.get("prev_ckpt_sha256") != prev or obj.get("seq") != i:
            raise Refuse(EXIT_CORRUPT, f"checkpoint chain broken at {p.name}")
        body = {k: v for k, v in obj.items() if k not in ("seq", "prev_ckpt_sha256")}
        if canon(body) != expected[i]:
            raise Refuse(EXIT_CORRUPT, f"{p.name} differs from the ledger-derived state")
        prev = sha
    head = run.ckpts.head()
    if head is None or head[2] != prev:
        raise Refuse(EXIT_CORRUPT, "HEAD does not name the newest checkpoint")
    print(json.dumps({"verify": "OK", "checkpoints": len(files), "ledger_records": len(led.records),
                      "state": summary(run, st)}, indent=1))
    return 0


def cmd_rollback(target, args):
    if args.get("baseline"):
        cfg = load_config(target)
        base = {p["name"]: p["lock"] for p in cfg["params"]}
        off = {k: 0 for k in cfg["engine"].get("switch_options", {})}
        line = [f"option.{k}={v}" for k, v in off.items()]
        out = {"baseline_option_line": " ".join(line), "baseline_values": base,
               "note": "lock exe: no options; gate exe: switches at 0 restore the lock values"}
        print(json.dumps(out, indent=1))
        return 0
    run, meta = open_readonly(target)
    if check_identity(run.cfg) != meta["identity"]:
        raise Refuse(EXIT_IDENTITY, "pinned identity differs from RUN.json")
    st = run.rebuild()
    reconcile_checkpoints(run, st)
    if st["pending"] is not None:
        raise Refuse(EXIT_CORRUPT, "cannot roll back inside an open batch; resume it first")
    obj, sha = run.ckpts.read(int(args["to_ckpt"]))
    run.ledger.append("rollback", {"to_ckpt": int(args["to_ckpt"]), "to_ckpt_sha256": sha, "theta": obj["theta"],
                                   "k": obj["k"]})
    st = run.rebuild()
    run.checkpoint(st, "R", st["batch"])
    print(json.dumps(summary(run, st), indent=1))
    return 0


def cmd_export(run_dir, out_dir):
    o = Path(out_dir)
    run, _ = open_readonly(run_dir)
    led = run.ledger
    st = run.rebuild()
    o.mkdir(parents=True, exist_ok=True)
    with open(o / "history.csv", "x", encoding="ascii", newline="") as f:
        w = csv.writer(f)
        w.writerow(["batch", "k_after", "W", "L", "D", "R"] + run.space.names)
        for r in led.records:
            if r["type"] == "update":
                u = r["update"]
                w.writerow([r["batch"], u["k_after"], r["W"], r["L"], r["D"], u["R"]] + [repr(x) for x in u["theta_after"]])
    cand = {"schema": "opus3-candidate/1", "run_id": run.run_id, "config_sha256": run.csha,
            "complete": st["complete"], "k": st["k"], "theta": dict(zip(run.space.names, st["theta"])),
            "values": run.space.engine_values(st["theta"]), "ledger_head": led.head}
    (o / "candidate.json").write_bytes(canon(cand) + b"\n")
    print(json.dumps(cand, indent=1))
    return 0


def parse_args(argv):
    args = {}
    i = 0
    flags = {"--resume": "resume", "--live": "live", "--baseline": "baseline"}
    vals = {"--mode": "mode", "--max-batches": "max_batches", "--max-pairs": "max_pairs", "--total-pairs": "total_pairs",
            "--to-ckpt": "to_ckpt", "--out": "out"}
    pos = []
    while i < len(argv):
        a = argv[i]
        if a in flags:
            args[flags[a]] = True
        elif a in vals:
            if i + 1 >= len(argv):
                raise Refuse(EXIT_CONFIG, f"{a} needs a value")
            v = argv[i + 1]
            args[vals[a]] = int(v) if vals[a] in ("max_batches", "max_pairs", "total_pairs") else v
            i += 1
        else:
            pos.append(a)
        i += 1
    return pos, args


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return EXIT_CONFIG
    cmd = argv[1]
    pos, args = parse_args(argv[2:])
    try:
        if cmd == "run" and len(pos) == 2:
            return cmd_run(pos[0], pos[1], args)
        if cmd == "status" and len(pos) == 1:
            return cmd_status(pos[0])
        if cmd == "verify" and len(pos) == 1:
            return cmd_verify(pos[0])
        if cmd == "rollback" and len(pos) == 1:
            return cmd_rollback(pos[0], args)
        if cmd == "export" and len(pos) == 1 and "out" in args:
            return cmd_export(pos[0], args["out"])
        print(__doc__)
        return EXIT_CONFIG
    except Refuse as e:
        print(json.dumps({"refused": True, "exit": e.code, "reason": str(e)}), file=sys.stderr)
        return e.code


if __name__ == "__main__":
    sys.exit(main(sys.argv))
