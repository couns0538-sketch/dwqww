"""Opus 2026-11-24, stage b part 2 (FORMATS 2.3 and 2.4): THE ROUND OUTPUT at HOME. Python with python-chess 1.11.2
and the loop's own code (the folder holding nnloop/).

    publish.py --home DIR --fingerprint HEX64 --config TOML --pipeline DIR --tables DIR --tables-list FILE
               --converter EXE [--openings FILE] [--convert-seconds S = 600] [--floor-gb G = 30]
               [--alarm-games N = 10000]

Beside custody.py (a1), content.py (a2) and credit.py (b part 1), whose outputs it reads and never writes; run by the
home guard after credit.py, one stage at a time. Known answers written before the code:
tmp/opus_scratch/home_b2/KNOWN_ANSWERS_b2_by_opus.md on the PC. ONE PASS, for every round with a credit list
stage/r<NNNN>/credit.json and no rounds/r<NNNN>, rising:
 PARTIAL (2.3: it credits nothing): published only beside the home guard's DRAIN.json (home/DRAIN.json, canonical,
   schema 2, this run's fingerprint, at_utc, why "lease ended", "declared stop" or "source gone since ..", missing a
   list): report.json alone, kept_rows 0, drain_sha256. Without it (or with another run's) the round WAITS and the
   later rounds go on: a partial round credits nothing, so nothing later depends on its publication.
 COMPLETE: ONE ATTEMPT in the private staging folder rounds/.staging/r<NNNN> (one left by a killed pass is removed
   first: it was never published). The first thing that fails ends the attempt FAILED: the line
   {"at_utc":..,"result":"failed","round":r,"t":"stage_b_attempt","why":..} is appended to home/progress.jsonl in
   one write and never removed, staging is removed, nothing is published and the pass ends (exit 6; a later pass
   starts the round again from the beginning, every input checked again by its hash):
   1 PREFLIGHT (2.3 [2.4]): every line of --tables-list (sha256sum's form "<sha256>  <name>") names a file in --tables
     with that sha256, and the folder holds no .rtbw or .rtbz file the list does not name.
   2 ROOM: free space on the volume of rounds/ at least 4 x 120 bytes x the round's raw rows in, + --floor-gb GiB.
   3 THE GAMES of credit.json in its order (slot, counter): every "credited" id with rows is read again FROM its
     custody bytes (content's own kept() and transport(): every member hashed against its receipt, the raw bytes
     against the seal), parsed by record.py, its rows digest compared with credit.json's. Another digest, or an id
     the content index or its piece does not hold, HOLDS (exit 5: home's evidence contradicts itself). A kept member
     gone or a converter failure is a local outage: FAILED.
   4 THE CORRECTION (2.3 C3): every such game through the loop's OWN _after_game (nnloop/datagen_uci.py) with the
     config's [datagen] and the drawcount of the run's game line, the loop's tables replaced by a RECORDER of the
     tables in --tables that counts every probe and keeps every failure before raising it again (the loop's
     tablebase_verdict swallows a failure and lets the material rule decide: here it is a FAILED probe, never WDL
     0). Counted: games examined, outcomes changed by the loop's reason, games left out by rule, probes made, failed.
   5 THE FILTER (2.3 C4): the games' text in that order as ONE file raw/round.plain, the loop's OWN filter_round
     (nnloop/filterqc.py) in a child Python started with PYTHONHASHSEED=0 (its dedup uses hash()), which refuses to
     run with any other seed; the filter's archive raw_selfplay.binpack is not published. A round whose credited
     games hold no rows publishes its report alone.
   6 kept.plain.gz: the filter's filtered.plain (every row; a filtered row has score 32002) packed by gzip level 6
     with mtime 0 and no file name, read back and compared.
   7 report.json, canonical and without a time: the same inputs give the same bytes.
   8 staging flushed and renamed ONCE onto rounds/r<NNNN> while that name is free (else HOLDS); the parent flushed.
 ALARM (2.3): when the published complete rounds together examined at least --alarm-games games and changed no
 outcome: "ALARM publish: no outcome changed in N examined games" (exit 5); nothing is held back for it.
The last line: publish: published .. rounds (.. complete, .. partial) this pass; kept rows ..; waits: <rounds, or
none>; failed: <round: why, or none>. Exit codes: 0 a pass (also with rounds that wait, and with no run header at
home yet); 2 a wrong call; 3 the run header or a credit list of another run; 4 a file that cannot be read or written
outside an attempt; 5 a HOLD or the ALARM; 6 an attempt FAILED.
"""
import argparse
import gzip
import hashlib
import json
import os
import platform
import re
import shutil
import sqlite3
import subprocess
import sys
import time
import zlib
import lzma
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "run"))
sys.path.insert(0, str(HERE))
import record  # noqa: E402
from content import Content, Waits, game_values  # noqa: E402
from custody import HEX64  # noqa: E402
from worker import Stop, canon, file_sha256, fsync_dir, parse_canon, sha256_bytes, write_new  # noqa: E402

ROW_BYTES = 120                 # a written row is about 100 bytes; at most 4 copies of the text stand in staging
TABLE_LINE = re.compile(r"([0-9a-f]{64}) [ *]([A-Za-z0-9]+\.rtb[wz])")
WHY = re.compile(r"lease ended|declared stop|source gone since .+")
UTC = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z")
CREDIT_KEYS = sorted(("schema", "run_fingerprint", "round", "status", "range_seals", "games_in", "raw_rows_in", "ids",
                      "missing_ids", "set_aside_ids", "conflict_ids", "repeat_games"))
DRAIN_KEYS = sorted(("schema", "run_fingerprint", "at_utc", "why", "missing"))
ENTRY_KEYS = sorted(("game", "slot", "counter", "state", "rows", "rows_digest", "same_rows_as"))   # credit.py 410


class Hold(Exception):
    """Home's evidence contradicts itself: nothing more is published this pass (exit 5)."""


class Failed(Exception):
    """A local prerequisite failed during an attempt: the attempt line, and a later pass tries again (exit 6)."""


class Recorder:
    """python-chess's tables as the loop calls them (probe_wdl, probe_dtz): every probe counted, every failure kept
    before it is raised again."""

    def __init__(self, tb):
        self.tb, self.made, self.failed = tb, 0, []

    def _probe(self, fn, board):
        self.made += 1
        try:
            return fn(board)
        except Exception as e:  # noqa: BLE001  (a missing child table, a damaged or vanished file: all count)
            self.failed.append(f"{type(e).__name__}: {e} (board {board.fen()})")
            raise

    def probe_wdl(self, board):
        return self._probe(self.tb.probe_wdl, board)

    def probe_dtz(self, board):
        return self._probe(self.tb.probe_dtz, board)


class Correction:
    """The loop's own after-game rules on the games of the run (2.3 C3)."""

    def __init__(self, dg, g: dict, tables: Path, drawcount: int):
        import chess
        import chess.syzygy
        self.chess, self.dg, self.g, self.drawcount = chess, dg, g, drawcount
        self.rec = Recorder(chess.syzygy.open_tablebase(str(tables), max_fds=64))
        dg._TB = self.rec                               # what the loop's _tablebase(g) hands to the adjudication
        self.examined, self.changed, self.left_out = 0, {}, {}

    def close(self) -> None:
        self.dg._TB = None
        self.rec.tb.close()

    def args_of(self, g: dict) -> tuple:
        """What play_game_sg hands to _after_game for this record (the loop's lines 394 to 453; Fable's loop_args)."""
        chess = self.chess
        board = chess.Board()
        for m in g["opening"]:
            board.push_uci(m)
        recs = []
        for row in g["rows"]:
            _, ply, score, bm, fen = row.split(" ", 4)
            recs.append((fen, bm, int(score), int(ply), fen.split(" ", 2)[1] == "w"))
        f = g["end"].split()
        i = f.index("moves")
        keys = ("result", "reason", "plies", "run", "searches", "nodes")
        end = {f[j]: f[j + 1] for j in range(1, i - 1) if f[j] in keys}
        result, reason, plies = int(end["result"]), end["reason"], int(end["plies"])
        if result == 0 and (self.g.get("adjudicate_bare_king", False) or self.g.get("adjudicate_tablebase", False)):
            for m in f[i + 1:]:
                mv = chess.Move.from_uci(m)
                if not board.is_legal(mv):
                    raise Hold(f"{g['id']}: the move {m} of its end line is illegal, and content accepted the game")
                board.push(mv)
        return board, recs, result, reason == "plylimit", reason == "drawadj" and self.drawcount > 0, plies

    def game(self, board, recs, result, ended_by_limit, draw_adjudicated, plies) -> tuple:
        """(text, rows) as the loop writes the game; Failed when a probe could not answer."""
        n = len(self.rec.failed)
        text, rows, _res, _plies = self.dg._after_game(board, recs, result, ended_by_limit, draw_adjudicated, plies,
                                                       self.g)
        if len(self.rec.failed) > n:
            raise Failed(f"a tablebase probe could not answer: {self.rec.failed[n]}")
        self.examined += 1
        if self.dg.LAST_ADJ is not None:
            self.changed[self.dg.LAST_ADJ[1]] = self.changed.get(self.dg.LAST_ADJ[1], 0) + 1
        if self.dg.LAST_SKIP is not None:
            self.left_out["ply limit skip"] = self.left_out.get("ply limit skip", 0) + 1
        return text, rows


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def pack(src: Path, dst: Path) -> str:
    """gzip level 6, mtime 0, no file name (the same text gives the same bytes); read back and compared."""
    h = hashlib.sha256()
    with open(src, "rb") as i, open(dst, "xb") as o:
        with gzip.GzipFile(filename="", mode="wb", compresslevel=6, fileobj=o, mtime=0) as z:
            for block in iter(lambda: i.read(1 << 22), b""):
                h.update(block)
                z.write(block)
        o.flush()
        os.fsync(o.fileno())
    back = hashlib.sha256()
    with gzip.open(dst, "rb") as z:
        for block in iter(lambda: z.read(1 << 22), b""):
            back.update(block)
    if back.digest() != h.digest():
        raise Failed("kept.plain.gz does not read back as the filter's output")
    return file_sha256(dst)


class Publisher:
    def __init__(self, a):
        self.home, self.fp = Path(a.home), a.fingerprint
        self.C = Content(self.home, self.fp, a.converter, a.openings, a.convert_seconds)
        self.h = self.C.H.h
        self.cfg_path, self.pipeline, self.conv = Path(a.config), Path(a.pipeline), a.converter
        self.tables, self.tables_list = Path(a.tables), Path(a.tables_list)
        self.floor, self.alarm_games = int(a.floor_gb * 2**30), a.alarm_games
        self.rounds, self.progress = self.home / "rounds", self.home / "progress.jsonl"
        if self.h is None:
            return
        sys.path.insert(0, str(self.pipeline))
        from nnloop import datagen_uci
        from nnloop.common import load_config
        self.dg, self.cfg = datagen_uci, load_config(self.cfg_path)
        self.drawcount = game_values(self.h["game_line"])["drawcount"]
        lp = self.pipeline / "nnloop"
        self.frozen = {"filter_code": file_sha256(lp / "filterqc.py"), "correction_code": file_sha256(lp / "datagen_uci.py"),
                       "loop_common": file_sha256(lp / "common.py"), "config": file_sha256(self.cfg_path),
                       "tables_list": file_sha256(self.tables_list), "converter": file_sha256(self.conv),
                       "publisher": file_sha256(Path(__file__)), "python": platform.python_version(),
                       "net": self.h["net_sha256"], "options": self.h["options_sha256"],
                       "engine": self.h["engine_sha256"]}

    # ---- inputs -------------------------------------------------------------------------------------------------
    def credit_list(self, r: int) -> tuple:
        what = f"stage/r{r:04d}/credit.json"
        b = (self.home / what).read_bytes()
        try:
            c = parse_canon(b, what)
        except ValueError as e:
            raise Hold(str(e)) from None
        if not isinstance(c, dict) or sorted(c) != CREDIT_KEYS or c["schema"] != 2 or c["round"] != r \
                or c["status"] not in ("complete", "partial") or not isinstance(c["ids"], list) \
                or not all(type(c[k]) is int and c[k] >= 0 for k in ("games_in", "raw_rows_in", "repeat_games")) \
                or not all(isinstance(c[k], list) for k in ("range_seals", "missing_ids", "set_aside_ids", "conflict_ids")):
            raise Hold(f"{what} is not credit.py's list for round {r}")
        if c["run_fingerprint"] != self.fp:
            raise Stop(3, f"{what} is another run's credit list (a home folder serves one run)")
        for e in c["ids"]:                              # every entry as credit.py writes it, before any is used
            if not (isinstance(e, dict) and sorted(e) == ENTRY_KEYS and type(e["game"]) is str
                    and type(e["state"]) is str and all(type(e[k]) is int and e[k] >= 0 for k in ("slot", "counter", "rows"))
                    and (e["rows_digest"] is None or (type(e["rows_digest"]) is str
                                                      and HEX64.fullmatch(e["rows_digest"]) is not None))):
                raise Hold(f"{what}: an entry of ids is not as credit.py writes it: {str(e)[:160]}")
        return c, b

    def drain(self):
        """The sha256 of the home guard's DRAIN.json, or None (no drain, or another run's: the round waits)."""
        p = self.home / "DRAIN.json"
        if not p.exists():
            return None
        b = p.read_bytes()
        try:
            d = parse_canon(b, "DRAIN.json")
        except ValueError as e:
            raise Hold(str(e)) from None
        if not isinstance(d, dict) or sorted(d) != DRAIN_KEYS or d["schema"] != 2 or type(d["at_utc"]) is not str \
                or not UTC.fullmatch(d["at_utc"]) or type(d["why"]) is not str or not WHY.fullmatch(d["why"]) \
                or not isinstance(d["missing"], list):
            raise Hold("DRAIN.json is not the home guard's record of 2.3 (schema 2, run_fingerprint, at_utc, why, missing)")
        return sha256_bytes(b) if d["run_fingerprint"] == self.fp else None

    def attempts(self, r: int) -> int:
        n = 0
        for ln in (self.progress.read_bytes().split(b"\n") if self.progress.exists() else []):
            if not ln.strip():
                continue
            try:
                x = json.loads(ln)
            except ValueError:
                raise Stop(4, f"progress.jsonl holds a line that is not JSON: {ln[:80]!r}") from None
            n += isinstance(x, dict) and x.get("t") == "stage_b_attempt" and x.get("round") == r \
                and x.get("result") == "failed"
        return n

    def failed_line(self, r: int, why: str) -> None:
        line = canon({"t": "stage_b_attempt", "round": r, "at_utc": utc_now(), "result": "failed", "why": why[:2000]})
        fd = os.open(self.progress, os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_BINARY", 0), 0o644)
        try:
            os.write(fd, line)                          # ONE write: the line is whole or absent
            os.fsync(fd)
        finally:
            os.close(fd)

    # ---- the attempt --------------------------------------------------------------------------------------------
    def preflight(self) -> None:
        try:
            lines = self.tables_list.read_bytes().decode("ascii").split("\n")
            have = {p.name for p in self.tables.iterdir() if p.suffix in (".rtbw", ".rtbz")}
        except (OSError, UnicodeDecodeError) as e:
            raise Failed(f"the tables' list or folder cannot be read: {e}") from None
        want = {}
        for ln in lines[:-1]:
            m = TABLE_LINE.fullmatch(ln)
            if not m or m[2] in want:
                raise Failed(f"the tables' list has a line that is not '<sha256>  <table file>', or a name twice: {ln[:100]!r}")
            want[m[2]] = m[1]
        if lines[-1] != "" or not want:
            raise Failed("the tables' list is empty or its last line has no line end")
        if have != set(want):
            raise Failed(f"the tables folder does not hold exactly the list's files: missing {sorted(set(want) - have)[:5]}, "
                         f"not on the list {sorted(have - set(want))[:5]}")
        for name, sha in sorted(want.items()):
            if file_sha256(self.tables / name) != sha:
                raise Failed(f"the table file {name} is not the list's bytes (sha256)")

    def piece(self, key: str, stg: Path) -> dict:
        """counter -> game of a piece, read again from its custody bytes (content's own reading, hashes checked)."""
        k, i = int(key[1:4]), int(key[6:])
        name = f"p{i:06d}"
        r = self.C.H.record(k, i)
        try:
            files = self.C.kept(r, name)
            s = json.loads(files[".seal.json"])
            want = (s["raw_bytes"], s["raw_sha256"])
            raw = self.C.transport(k, name, files)
        except Waits as e:
            raise Failed(f"{key}: {e}") from None
        except (zlib.error, lzma.LZMAError, UnicodeDecodeError, ValueError, KeyError, TypeError) as e:
            raise Hold(f"{key}: its kept bytes no longer read as content read them: {e!r}") from None
        finally:
            shutil.rmtree(stg / "scratch", ignore_errors=True)
        if (len(raw), sha256_bytes(raw)) != want:
            if ".binpack" in files:                     # content's own reading (judge): home's converter differs now
                raise Failed(f"{key}: the binpack does not rebuild here to its seal's raw_bytes and raw_sha256, a "
                             "local outage (home's converter differs)")
            raise Hold(f"{key}: the bytes built again are not its seal's raw_bytes and raw_sha256")
        try:
            return {g["counter"]: g for g in record.parse(raw, self.fp)}
        except record.RecordError as e:
            raise Hold(f"{key}: its records no longer parse: {e}") from None

    def games(self, c: dict, stg: Path, corr: Correction) -> int:
        """Steps 3 and 4: the text of the round in raw/round.plain; the rows written."""
        con = sqlite3.connect(f"{self.C.db.resolve().as_uri()}?mode=ro", uri=True)
        rows, key, games = 0, None, {}
        try:
            with open(stg / "raw" / "round.plain", "xb") as out:
                for e in c["ids"]:
                    if e["state"] != "credited" or not e["rows"]:
                        continue
                    x = con.execute("SELECT piece, game, rows_digest FROM entries WHERE slot = ? AND counter = ?",
                                    (e["slot"], e["counter"])).fetchone()
                    if x is None or x[1] != e["game"] or x[2] != e["rows_digest"]:
                        raise Hold(f"{e['game']}: the content index does not hold it with credit.json's rows digest")
                    if x[0] != key:
                        key, games = x[0], self.piece(x[0], stg)
                    g = games.get(e["counter"])
                    if g is None or g["id"] != e["game"] or len(g["rows"]) != e["rows"] \
                            or record.rows_digest(g["rows"], g["end"]) != e["rows_digest"]:
                        raise Hold(f"{e['game']}: its custody bytes do not give credit.json's rows and rows digest")
                    text, n = corr.game(*corr.args_of(g))
                    out.write(text.encode("ascii"))
                    rows += n
                out.flush()
                os.fsync(out.fileno())
        finally:
            con.close()
        return rows

    def filter(self, stg: Path) -> dict:
        """Step 5: the loop's filter_round in a child whose hash() has seed 0."""
        env = {k: v for k, v in os.environ.items() if not k.upper().startswith("PYTHON")}
        env["PYTHONHASHSEED"] = "0"
        cmd = [sys.executable, "-s", "-B", str(Path(__file__).resolve()), "--filter-child", str(self.cfg_path.resolve()),
               str(self.pipeline.resolve()), str(stg / "raw"), str(stg / "filter"), self.conv]
        try:
            p = subprocess.run(cmd, cwd=str(stg), env=env, capture_output=True, text=True, timeout=4 * 3600)
        except subprocess.TimeoutExpired:
            raise Failed("the filter child did not end within 4 hours") from None
        if p.returncode != 0:
            raise Failed(f"the filter child ended with exit {p.returncode}: {(p.stdout + p.stderr).strip()[-600:]}")
        return json.loads((stg / "filter" / "qc.json").read_text(encoding="utf-8"))

    def attempt(self, r: int, c: dict, cb: bytes) -> int:
        stg = self.rounds / ".staging" / f"r{r:04d}"
        before = self.attempts(r)
        shutil.rmtree(stg, ignore_errors=True)          # a staging left by a killed pass: private, never published
        corr = None
        try:
            (stg / "raw").mkdir(parents=True)
            self.C.out = stg                            # content's transport scratch goes into this staging
            self.preflight()
            need, free = 4 * ROW_BYTES * c["raw_rows_in"] + self.floor, shutil.disk_usage(self.rounds).free
            if free < need:
                raise Failed(f"staging volume: needs {need} bytes free (4 x {ROW_BYTES} x {c['raw_rows_in']} raw rows "
                             f"+ the floor), has {free}")
            corr = Correction(self.dg, dict(self.cfg["datagen"]), self.tables, self.drawcount)
            raw_rows = self.games(c, stg, corr)
            x = {"games_examined": corr.examined, "outcomes_changed": corr.changed, "games_left_out": corr.left_out,
                 "probes_made": corr.rec.made, "probes_failed": len(corr.rec.failed), "raw_rows": raw_rows}
            if raw_rows:
                qc = self.filter(stg)
                marked = qc["marked_skip"]
                if qc["records"] != raw_rows or qc["kept"] + sum(marked.values()) != raw_rows:
                    raise Hold(f"the filter's counts do not add up: records {qc['records']}, kept {qc['kept']}, "
                               f"marked {sum(marked.values())}, rows written {raw_rows}")
                x.update(kept_rows=qc["kept"], marked=marked, kept_form="plain.gz",
                         kept_sha256=pack(stg / "filter" / "filtered.plain", stg / "kept.plain.gz"))
            for d in ("raw", "filter", "scratch"):
                shutil.rmtree(stg / d, ignore_errors=True)
            if sorted(p.name for p in stg.iterdir()) != (["kept.plain.gz"] if raw_rows else []):
                raise Failed(f"staging holds more than the kept object: {sorted(p.name for p in stg.iterdir())}")
            self.publish(r, stg, self.report(r, c, cb, before, **x))
            return x.get("kept_rows", 0)
        except OSError as e:
            raise Failed(f"an input or the staging folder could not be read or written: {e}") from None
        finally:
            if corr is not None:
                corr.close()
            shutil.rmtree(stg, ignore_errors=True)      # gone after the rename; after a failure it goes here

    def report(self, r: int, c: dict, cb: bytes, before: int, **x) -> bytes:
        rep = {"schema": 2, "run_fingerprint": self.fp, "round": r, "status": c["status"], "credit_sha256": sha256_bytes(cb),
               "range_seals": c["range_seals"], "games_in": c["games_in"], "raw_rows_in": c["raw_rows_in"],
               "missing_ids": c["missing_ids"], "set_aside_ids": c["set_aside_ids"], "conflict_ids": c["conflict_ids"],
               "repeat_games": c["repeat_games"], "games_examined": 0, "outcomes_changed": {}, "games_left_out": {},
               "probes_made": 0, "probes_failed": 0, "raw_rows": 0, "kept_rows": 0, "marked": {}, "kept_form": None,
               "kept_sha256": None, "frozen": self.frozen, "attempts_failed": before, "drain_sha256": None}
        rep.update(x)
        return canon(rep)

    def publish(self, r: int, stg: Path, report: bytes) -> None:
        write_new(stg / "report.json", report)
        fsync_dir(stg)
        dst = self.rounds / f"r{r:04d}"
        if dst.exists():
            raise Hold(f"rounds/r{r:04d} exists although this pass found the name free: another writer")
        os.rename(stg, dst)                             # ONE publication: the name is free (checked) and then taken
        fsync_dir(self.rounds)

    # ---- the pass -----------------------------------------------------------------------------------------------
    def alarm(self):
        examined = changed = 0
        for d in sorted(self.rounds.glob("r[0-9][0-9][0-9][0-9]")):
            try:
                rep = parse_canon((d / "report.json").read_bytes(), f"rounds/{d.name}/report.json")
            except (OSError, ValueError) as e:
                raise Hold(f"rounds/{d.name} is not a publication of this program: {e}") from None
            if not isinstance(rep, dict) or rep.get("run_fingerprint") != self.fp:
                raise Hold(f"rounds/{d.name}/report.json is not this run's")
            if rep["status"] == "complete":
                examined += rep["games_examined"]
                changed += sum(rep["outcomes_changed"].values())
        if examined >= self.alarm_games and changed == 0:
            return (f"ALARM publish: no outcome changed in {examined} examined games (2.3: the correction may be "
                    f"switched off or broken)")
        return None

    def one_pass(self) -> int:
        stage = self.home / "stage"
        todo = sorted(int(p.parent.name[1:]) for p in stage.glob("r[0-9][0-9][0-9][0-9]/credit.json")) \
            if stage.is_dir() else []
        (self.rounds / ".staging").mkdir(parents=True, exist_ok=True)
        t = {"complete": 0, "partial": 0, "kept": 0}
        waits, failed, code = [], "none", 0
        for r in todo:
            if (self.rounds / f"r{r:04d}").exists():
                continue
            try:
                c, cb = self.credit_list(r)
                if c["status"] == "partial":
                    ds = self.drain()
                    if ds is None:
                        waits.append(f"round {r} (partial: no DRAIN.json of this run)")
                        continue
                    stg = self.rounds / ".staging" / f"r{r:04d}"
                    shutil.rmtree(stg, ignore_errors=True)
                    stg.mkdir(parents=True)
                    try:
                        self.publish(r, stg, self.report(r, c, cb, self.attempts(r), drain_sha256=ds))
                    finally:
                        shutil.rmtree(stg, ignore_errors=True)
                    t["partial"] += 1
                    print(f"round {r}: published partial (DRAIN.json {ds[:12]})")
                else:
                    kept = self.attempt(r, c, cb)
                    t["complete"] += 1
                    t["kept"] += kept
                    print(f"round {r}: published complete, kept rows {kept}")
            except Hold as e:
                print(f"ALARM publish HOLDS round {r}: {e}")
                code = 5
                break
            except Failed as e:
                self.failed_line(r, str(e))
                print(f"FAILED round {r}: {e}")
                failed, code = f"round {r}: {e}", 6
                break
        try:
            alarm = self.alarm()
        except Hold as e:
            alarm, code = f"ALARM publish HOLDS: {e}", 5
        if alarm:
            print(alarm)
            code = code or 5
        print(f"publish: published {t['complete'] + t['partial']} rounds ({t['complete']} complete, {t['partial']} "
              f"partial) this pass; kept rows {t['kept']}; waits: {'; '.join(waits) or 'none'}; failed: {failed}")
        return code


def filter_child(argv: list) -> int:
    """publish.py --filter-child <config> <pipeline> <raw dir> <out dir> <converter>: the loop's filter_round in a
    process whose hash() has seed 0 (its dedup keys), with the converter given to the attempt."""
    if sys.flags.hash_randomization != 0 or len(argv) != 5:
        print("filter child: STOP: started without PYTHONHASHSEED=0 (hash randomization is on), or a wrong call")
        return 6
    cfg_path, pipeline, raw, out, conv = argv
    sys.path.insert(0, pipeline)
    from nnloop.common import load_config
    from nnloop.filterqc import filter_round
    cfg = load_config(cfg_path)
    cfg["sf_tools"]["cmd"] = conv
    filter_round(cfg, Path(raw), Path(out))
    return 0


def main() -> int:
    if sys.argv[1:2] == ["--filter-child"]:
        return filter_child(sys.argv[2:])
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    for name in ("home", "fingerprint", "config", "pipeline", "tables", "tables-list", "converter"):
        ap.add_argument("--" + name, required=True)
    ap.add_argument("--openings")
    ap.add_argument("--convert-seconds", type=float, default=600.0)
    ap.add_argument("--floor-gb", type=float, default=30.0)
    ap.add_argument("--alarm-games", type=int, default=10000)
    try:
        a = ap.parse_args()
    except SystemExit:
        return 2
    if not HEX64.fullmatch(a.fingerprint) or not Path(a.home).is_dir() or not Path(a.tables).is_dir() \
            or not all(Path(p).is_file() for p in (a.config, a.tables_list, a.converter)) \
            or not (Path(a.pipeline) / "nnloop" / "filterqc.py").is_file():
        print("publish: STOP (2): --home and --tables must be folders, --config, --tables-list and --converter files, "
              "--pipeline the folder holding nnloop/, --fingerprint 64 lowercase hex")
        return 2
    try:
        P = Publisher(a)
        if P.h is None:
            print("publish: no run header at home yet; nothing to do")
            return 0
        return P.one_pass()
    except Stop as e:
        print(f"publish: STOP ({e.code}): {e}")
        return e.code
    except OSError as e:
        print(f"publish: STOP (4): {e}")
        return 4


if __name__ == "__main__":
    sys.exit(main())
