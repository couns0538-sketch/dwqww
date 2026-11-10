"""confirm_runner.py - independent confirmation of a tuned candidate on a frozen holdout (no tuner code is imported).

usage (python -I -B; PowerShell entry point ..\\bin\\confirm.ps1):
  confirm_runner.py run <protocol.json> <candidate.json> <run_dir> [--mode dry-run|synthetic|replay] [--resume]
                        [--max-pairs N]
  confirm_runner.py verify <run_dir>
  confirm_runner.py audit-pgn <protocol.json> <candidate.json> <pgn> [<pgn> ...]   (QA's SPRT PGN, read-only)
Modes:
  dry-run (DEFAULT) validates the protocol, the candidate and the pins, reports whether the candidate is
          confirmable, and prints the exact fastchess command. Writes nothing.
  replay  recomputes the sequential decision from the PGNs named in protocol.replay. These are the games QA played
          with the dry-run's command, under QA's own scheduler.
  synthetic draws pair outcomes from a model with a known true effect. Tests only; the output is labelled
          SYNTHETIC and carries no Elo. It uses a separate registry file, so it can never consume a holdout.
  live    is refused (exit 40): this runner never starts an engine or a game.
Every mode prerequisite is validated before anything is written.
Fixed rules (protocol, frozen before fitting):
  - One confirmation per holdout group, ever (registry, written just before the first pair is recorded).
  - The candidate is the one select_candidate.py derived from a COMPLETE live training run whose config sha256
    the protocol pins.
  - Pentanomial normalized-Elo GSPRT with the protocol's bounds, alpha, beta and game cap:
    LLR >= upper -> "H1 accepted", LLR <= lower -> "H0 accepted", cap reached -> "cap, no decision (no claim)".
  - A crash, time loss or illegal move makes the run invalid.
State: start/pair/decision records in a hash-chained ledger (the source of truth) plus atomic checkpoints. Every
resume replays the ledger. Duplicates, unknown pairs, incomplete pairs, and stale or corrupt state are refused.
Exit codes: 0 ok, 10 bad protocol/candidate/mode, 11 changed, 20 identity, 30 corrupt, 31 bad results,
40 live refused, 41 holdout misuse (reuse, re-run, peeking, overlap with training), 77 injected crash (tests)."""
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
COMMENT = re.compile(r"\{([^}]*)\}")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
MODES = ("dry-run", "synthetic", "replay", "live")


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


def registry_paths(proto, kind):
    """Where single use is recorded. kind "real" is a confirmation that consumes the holdout; kind "synthetic" is
    a test or demonstration that never does (synthetic mode, or replay with the test-only allow_nonlive_candidate).
    Every line is written to two files: the protocol's registry, and a registry beside the holdout file itself.
    So editing the protocol's registry path does not reset the history. This is an accident guard, not a security
    boundary: someone who deletes both files, or copies the holdout elsewhere, can still re-run."""
    tag = "" if kind == "real" else ".synthetic"
    p = Path(proto["registry"])
    first = p if kind == "real" else p.with_name(p.stem + ".synthetic" + p.suffix)
    hold = Path(proto["identity"]["holdout"]["path"])
    second = hold.with_name(hold.name + f".registry{tag}.jsonl")
    return [first] if second.resolve() == first.resolve() else [first, second]


def registry_lines(reg):
    if not reg.exists():
        return []
    try:
        return [json.loads(x) for x in reg.read_text(encoding="ascii").splitlines() if x.strip()]
    except (UnicodeDecodeError, ValueError):
        raise Stop(30, f"registry {reg} is malformed")


def check_holdout(proto, cand, run_dir, run_id, kind):
    """Holdout misuse is refused (exit 41).
    - The group must not have been read by the training run (peeking).
    - The candidate must come from the frozen training partition.
    - A holdout group serves exactly ONE confirmation, ever:
      - a group registered from another directory is refused, whatever the candidate;
      - in its registered directory, a run whose CONFIRM.json is gone is refused, because a deleted and restarted
        run would be a re-run until lucky;
      - in its registered directory with CONFIRM.json present, this is a resume, and the CONFIRM.json comparison
        that follows refuses a changed protocol or candidate (exit 11)."""
    grp = proto["holdout"]
    hs = grp["pgn_sha256"].lower()
    trained = {x.lower() for x in cand.get("training_openings_sha256", [])}
    parts = {x.lower() for x in proto.get("training_partitions_sha256", [])}
    if hs in trained:
        raise Stop(41, "the holdout group was read by the training run (peeking)")
    if hs in parts:
        raise Stop(41, "the protocol names a training partition as holdout")
    if not trained or trained - parts:
        raise Stop(41, "the candidate's training openings are not the frozen training partition")
    rd = str(Path(run_dir).resolve())
    for r in [x for reg in registry_paths(proto, kind) for x in registry_lines(reg)]:
        if str(r.get("holdout_pgn_sha256", "")).lower() != hs:
            continue
        same_dir = r.get("run_dir") == rd
        if same_dir and (Path(run_dir) / "CONFIRM.json").exists():
            continue  # a resume of the registered run; CONFIRM.json decides whether protocol and candidate match
        if r.get("run_id") != run_id:
            raise Stop(41, f"holdout group {grp['name']} already served confirmation {r.get('run_id')} in "
                           f"{r.get('run_dir')} (one confirmation per group, ever)")
        if not same_dir:
            raise Stop(41, f"confirmation {run_id} is registered in {r.get('run_dir')}; it cannot run again elsewhere")
        raise Stop(41, f"confirmation {run_id} was registered in {rd}, but its CONFIRM.json is gone: a re-run is "
                       "refused (one confirmation per group, ever)")


def replay_outcome(proto, replay):
    """The sequential decision the replay PGNs reach, computed in memory before anything is written: (verdict or
    None, contiguous pairs). A gap with later pairs present is an incomplete run (exit 31)."""
    st = {"pairs": {}}
    j = 0
    while j in replay:
        st["pairs"][j] = {"score": score_pair(replay[j]["games"]), "games": replay[j]["games"]}
        j += 1
        v = summary(st, proto)["verdict"]
        if v is not None:
            return v, j
    if any(k > j for k in replay):
        raise Stop(31, f"replay has no complete pair {j} but later pairs exist (incomplete run)")
    return None, j


def candidate_issues(proto, cand):
    """Why a candidate may not consume a holdout: it must come from a live training run whose config sha256
    (RUN.json config_sha256 of QA's live config) the protocol pins."""
    out = []
    if cand.get("training_mode") != "live":
        out.append(f"candidate comes from a {cand.get('training_mode', 'unrecorded')} training run, not a live one")
    pin = str(proto.get("training_config_sha256", "")).lower()
    if not HEX64.match(pin):
        out.append("the protocol does not pin training_config_sha256 (QA's live tuning config, RUN.json config_sha256)")
    elif str(cand.get("training_config_sha256", "")).lower() != pin:
        out.append("the candidate's training config differs from the protocol's training_config_sha256")
    return out


def check_mode(proto, mode):
    """Every mode prerequisite, checked before anything is written. Returns the parsed replay pairs (replay)."""
    if mode not in MODES:
        raise Stop(10, f"unknown mode {mode!r} (dry-run, synthetic or replay)")
    if mode == "live":
        raise Stop(40, "this runner never starts an engine or a game. QA plays the dry-run's exact fastchess command "
                       "under its own scheduler; this runner then recomputes the decision from that PGN with --mode "
                       "replay (protocol.replay), or audits QA's own gate PGN with audit-pgn")
    if mode == "synthetic":
        m = proto.get("synthetic")
        if not isinstance(m, dict) or not all(k in m for k in ("seed", "true_nelo", "draw")):
            raise Stop(10, "synthetic mode needs protocol.synthetic with seed, true_nelo and draw")
    if mode == "replay":
        rp = proto.get("replay")
        if not isinstance(rp, dict) or not rp.get("pgns"):
            raise Stop(10, "replay mode needs protocol.replay.pgns (path, sha256, first_pair per PGN)")
        replay = {}
        for e in rp["pgns"]:
            if not all(k in e for k in ("path", "sha256", "first_pair")):
                raise Stop(10, "each protocol.replay.pgns entry needs path, sha256 and first_pair")
            p = Path(e["path"])
            if not p.exists():
                raise Stop(20, f"replay PGN missing: {p}")
            if fh(p) != e["sha256"].lower():
                raise Stop(20, f"replay PGN changed: {p}")
            replay.update({e["first_pair"] + k: v for k, v in
                           pgn_pairs(p.read_text(encoding="utf-8", errors="replace"),
                                     rp.get("cand_name", "cand"), rp.get("base_name", "base")).items()})
        return replay
    return None


def check_opening_budget(proto):
    """Each pair uses one holdout opening (fastchess -repeat, order=sequential). A cap needing more pairs than the
    group has openings would silently replay openings and correlate pairs, so it is refused (exit 10) in every
    mode, including dry-run. Reuse needs allow_opening_reuse = true in the protocol, which is a written QA decision."""
    text = Path(proto["identity"]["holdout"]["path"]).read_text(encoding="utf-8", errors="replace")
    n_open = len(re.findall(r'^\[Event ', text, re.M))
    need = proto["sprt"]["cap_games"] // 2
    if need > n_open and not proto.get("allow_opening_reuse", False):
        raise Stop(10, f"cap_games {proto['sprt']['cap_games']} needs {need} openings but holdout "
                       f"{proto['holdout']['name']} has {n_open}: openings would repeat. Lower cap_games to <= "
                       f"{2 * n_open} or set allow_opening_reuse (a written QA decision).")
    return n_open


def register(proto, cand, run_id, run_dir, mode, kind):
    """Idempotent: one fsynced line per (run_id, run_dir) in each registry file. Called just before the first pair
    is recorded, after every mode prerequisite has passed, so a refused or failed start never consumes the holdout."""
    rd = str(Path(run_dir).resolve())
    for reg in registry_paths(proto, kind):
        reg.parent.mkdir(parents=True, exist_ok=True)
        if any(r.get("run_id") == run_id and r.get("run_dir") == rd for r in registry_lines(reg)):
            continue
        with open(reg, "ab") as f:
            f.write(cj({"run_id": run_id, "run_dir": rd, "holdout": proto["holdout"]["name"],
                        "holdout_pgn_sha256": proto["holdout"]["pgn_sha256"].lower(),
                        "candidate_sha256": cand["spec_sha256"], "mode": mode, "kind": kind}) + b"\n")
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
                    f.flush()
                    os.fsync(f.fileno())
            else:
                (self.d / f"confirm_ledger.torn.{len(list(self.d.glob('confirm_ledger.torn.*')))}.bin").write_bytes(tail)
                with open(self.p, "r+b") as f:
                    f.truncate(len(raw) - len(tail))
                    f.flush()
                    os.fsync(f.fileno())
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


def start_position(text):
    """EPD (pieces, side, castling, legal e.p.: the partition's key) of the position the engines started from.
    That is the FEN tag if present (EPD books), then every leading move annotated {book}, which is how fastchess
    writes the moves of a PGN book (no FEN tag). Returns (epd, source, book_plies). Fails closed (exit 31)."""
    try:
        import chess
        import chess.pgn
    except ImportError:
        raise Stop(10, "the start-position check needs python-chess (installed in the grok-pc venv)")
    import io
    head, _, moves = text.partition("\n\n")
    tags = dict(TAG.findall(head))
    fen = tags.get("FEN")
    try:
        board = chess.Board(fen) if fen else chess.Board()
    except ValueError:
        raise Stop(31, f"PGN game with an invalid FEN tag: {fen!r}")
    if "{book}" not in moves.replace("{ book }", "{book}"):
        if not fen:
            raise Stop(31, "PGN game with no FEN tag and no {book} moves: its opening cannot be determined")
        return board.epd(), "fen", 0
    cut = len(moves)
    for m in COMMENT.finditer(moves):
        if m.group(1).strip() != "book":
            cut = m.start()
            break
    game = chess.pgn.read_game(io.StringIO(head + "\n\n" + moves[:cut] + " *\n"))
    if game is None:
        raise Stop(31, "PGN game whose book moves cannot be parsed")
    board = game.board()
    n = 0
    for node in game.mainline():
        if node.comment.strip() != "book":
            break
        board.push(node.move)
        n += 1
    if getattr(game, "errors", None):
        raise Stop(31, f"PGN game whose book moves cannot be parsed: {game.errors[0]!r}")
    return board.epd(), "book", n


def pgn_pairs(text, cand_name, base_name):
    by = {}
    for blk in text.replace("\r\n", "\n").split("[Event ")[1:]:
        t = dict(TAG.findall("[Event " + blk))
        try:
            rnd = int(str(t.get("Round", "")).split(".")[0])
        except ValueError:
            raise Stop(31, "PGN game without numeric Round")
        epd, src, plies = start_position("[Event " + blk)
        t["_start"], t["_src"], t["_plies"] = epd, src, plies
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
        if gs[0]["_start"] != gs[1]["_start"]:
            raise Stop(31, f"PGN round {rnd}: the two games start from different positions")
        out[rnd - 1] = {"games": [{"white": "cand" if g["White"] == cand_name else "base", "result": g["Result"],
                                   "termination": g.get("Termination", "?")} for g in gs],
                        "start": gs[0]["_start"], "start_source": gs[0]["_src"], "book_plies": gs[0]["_plies"]}
    return out


def leakage(proto, starts):
    """Pairs whose start position is a training or screen position. The rule uses the conservative 3-field key
    (pieces, side, castling); the exact 4-field partition key is reported too. They differ only by the e.p. square:
    2 of G1's 2408 openings share a 3-field key with a training opening."""
    keys3, keys4 = set(), set()
    for p in proto.get("training_keys_files", []):
        if fh(p["path"]) != p["sha256"].lower():
            raise Stop(20, f"training keys file changed: {p['path']}")
        for x in Path(p["path"]).read_text(encoding="ascii").splitlines():
            if x.strip():
                keys4.add(" ".join(x.split()[:4]))
                keys3.add(" ".join(x.split()[:3]))
    hits3 = [i for i, s in starts if " ".join(s.split()[:3]) in keys3]
    hits4 = [i for i, s in starts if " ".join(s.split()[:4]) in keys4]
    return hits3, hits4


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
    mode = args.get("mode", "dry-run")
    replay = check_mode(proto, mode)  # every mode prerequisite first: nothing is written before this passes
    ident = check_identity(proto)
    if proto["identity"]["holdout"]["sha256"].lower() != proto["holdout"]["pgn_sha256"].lower():
        raise Stop(10, "protocol identity.holdout is not the named holdout group")
    psha = h(cj(proto))
    run_id = f"confirm:{proto['holdout']['name']}:{cand['spec_sha256'][:12]}:{psha[:12]}"
    d = Path(run_dir)
    issues = candidate_issues(proto, cand)
    test_only = mode == "synthetic" or (mode == "replay" and bool(issues) and proto.get("allow_nonlive_candidate", False))
    kind = "synthetic" if test_only else "real"
    check_holdout(proto, cand, d, run_id, kind)
    n_open = check_opening_budget(proto)
    if mode == "dry-run":
        cmd = fastchess_cmd(proto, cand, 1, proto["sprt"]["cap_games"] // 2, d / "games" / "c000000")
        print(json.dumps({"mode": "dry-run", "wrote_files": 0, "started_processes": 0, "identity_ok": ident,
                          "run_id": run_id, "holdout_openings": n_open, "max_pairs": proto["sprt"]["cap_games"] // 2,
                          "candidate_confirmable": not issues, "candidate_issues": issues,
                          "fastchess_command": subprocess.list2cmdline([str(x) for x in cmd])}, indent=1))
        return 0
    if mode == "replay" and issues and not proto.get("allow_nonlive_candidate", False):
        raise Stop(10, "candidate is not confirmable: " + "; ".join(issues))
    if mode == "replay":
        verdict, n_pairs = replay_outcome(proto, replay)
        if verdict is None and 2 * n_pairs < proto["sprt"]["cap_games"]:
            raise Stop(10, f"the replay PGNs hold {n_pairs} pairs and reach no decision before the cap "
                           f"({proto['sprt']['cap_games'] // 2} pairs). An interim replay would consume the holdout: "
                           "play the remaining games first, then replay once with all PGNs")
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
    book = Book(d, run_id).load()
    if not book.recs:
        book.add("start", {"protocol_sha256": psha, "candidate_sha256": cand["spec_sha256"], "mode": mode})
        crash("after_start")
    st = state_of(book.recs, proto)
    ckpt(d, book, st, proto)
    if st["pairs"]:
        register(proto, cand, run_id, d, mode, kind)  # idempotent; restores a lost line
    limit = args.get("max_pairs")
    done = 0
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
            games, src = replay[j]["games"], {"mode": "replay", "start": replay[j]["start"]}
        else:
            raise Stop(10, f"mode {mode} cannot record pairs")
        if j == 0:
            register(proto, cand, run_id, d, mode, kind)  # the holdout is consumed when its first pair is recorded
            crash("after_register")
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
    if mode == "replay":
        starts = [(j, st["pairs"][j]["source"]["start"]) for j in sorted(st["pairs"])]
        l3, l4 = leakage(proto, starts)
        out.update({"leakage_checked": bool(proto.get("training_keys_files")), "leaked_pairs": len(l3),
                    "leaked_pairs_exact_epd": len(l4), "leak_fraction": (len(l3) / len(starts)) if starts else 0.0,
                    "candidate_issues": issues})
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
    if h(cj(proto)) != meta["protocol_sha256"]:
        raise Stop(30, "CONFIRM.json protocol does not match its protocol_sha256")
    if meta["candidate"].get("spec_sha256") != meta["candidate_sha256"]:
        raise Stop(30, "CONFIRM.json candidate does not match its candidate_sha256")
    verify_candidate(meta["candidate"])
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
    """Read-only audit of QA's confirmation PGN(s): pairs, pentanomial and LLR recomputed, and opening leakage
    against the training and screen keys. Start positions come from the FEN tag (EPD books such as UHO) or from the
    {book} moves (PGN books such as 8moves_v3, which carry no FEN tag); a game whose start cannot be rebuilt fails
    the audit (exit 31)."""
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
    if not proto.get("training_keys_files"):
        raise Stop(10, "audit needs protocol.training_keys_files (train and screen .keys) for the leakage check")
    l3, l4 = leakage(proto, [(j, v["start"]) for j, v in pairs.items()])
    leak = set(l3)
    st_all = {"pairs": {j: {"score": score_pair(v["games"]), "games": v["games"]} for j, v in pairs.items()}}
    st_clean = {"pairs": {j: x for j, x in st_all["pairs"].items() if j not in leak}}
    a, c = summary(st_all, proto), summary(st_clean, proto)
    sources = {}
    for v in pairs.values():
        sources[v["start_source"]] = sources.get(v["start_source"], 0) + 1
    print(json.dumps({"audit": "QA confirmation PGN (independent recomputation)", "all_pairs": a,
                      "pairs_without_training_positions": c, "leaked_pairs": len(l3),
                      "leaked_pairs_exact_epd": len(l4), "leak_fraction": (len(l3) / len(pairs)) if pairs else 0.0,
                      "start_positions_from": sources, "candidate_issues": candidate_issues(proto, cand),
                      "protocol_rule": "claim only if QA's verdict and this recomputation agree, leakage <= 1% "
                                       "(3-field key) and candidate_issues is empty"},
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
