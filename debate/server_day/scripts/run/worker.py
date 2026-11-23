"""Fable 2026-11-23, W5 (c), (e), (f, F4) and (i, N12, N15, N17, A23) of FINAL_PLAN_2311.md: ONE worker of the
server day. One engine process that stays alive plays game after game and writes what the engine printed,
unchanged, into closed pieces. Standard library only.

    worker.py --exe E --net N --manifest MANIFEST.json --known-startup startup.json
              --spool DIR --run-id R --worker K --root-seed S
              [--games N] [--until EPOCH] [--piece-games G = 500] [--game-seconds T = 600] [--openings FILE]
              [--trace] [--rehearsal --plant <kind>:I]

The option list, the game line and the start-up probes are READ FROM THE MANIFEST (made on the PC from the live
config by tools/make_workloads.py): nothing of them is typed a second time here.

What it does, in order:
 1 START-UP, refused with exit code 5 when anything is not as frozen:
   - the net file has the manifest's size and sha256;
   - every option of the manifest is in the engine's own `uci` list, a number inside its bounds, a switch true or
     false, no name twice; `UseNNUE false` is refused; NNUEArchFile comes before NNUEArch (N15 (2), N17);
   - the options are sent in the manifest's order; every answer line is read; one refusal line stops the start
     (N15 (1)); the option lines really sent are compared with the manifest's, line by line;
   - the net that answers is the one asked for: the engine's `NNUE v3 active` line carries the checksum of the
     known answers, and `eval` on the manifest's probe positions reads `hce 0 nnue X total X` with the known
     values (N17);
   - the live searcher: new game, start position, `go depth` as in the manifest: depth, nodes, table fill and
     best move equal to the known answers (W5 (b)).
 2 GAMES. The game number g of this worker gives the id <run>-w<K>-g<g>. Its opening is a function of the root
   seed and the id alone (F4): 8 plies, each chosen among the engine's own legal moves in sorted order by
   sha256(root seed, id, ply). A game id played again after a crash is the same game. Before every game:
   `ucinewgame`, `isready`, `position startpos moves ...`, then the frozen game line (N12). Every line up to
   `sgend` is kept. A refusal line, `sgerror`, a silent or dead engine: the game is thrown away, the engine is
   started again with the whole start-up check, the same id is played again; three failures in a row end the
   worker with exit code 6.
   THE BINDING (A23): after the game the position line is taken from the list of lines REALLY WRITTEN to the
   engine and compared, token by token, with the opening reserved for this id. Exactly one position line may
   stand between the game's start and its game line. Anything else: the game is not credited, the journal gets a
   REFUSED line, the worker ends with exit code 7 (a fault of ours, not of the engine: a restart cannot cure it).
   The record (run/record.py) carries the reservation, the line as written, the rows, the end line and one digest
   over all of them with the id.
 3 PIECES. Games are appended to <spool>/w<K>/open/p<n>.raw; after G games the piece is closed (moved to closed/,
   then its sha256 file beside it, then the journal's `closed` line). The journal names, for every finished game,
   the piece and the byte where the game ends: after a crash the open piece is cut back to the last journalled
   game, a closing that was cut off is finished, and the worker goes on. At the end (the stop file <spool>/STOP,
   --until, --games) the last, partly filled piece is closed too (A11).
 4 A heartbeat file is rewritten after every game (the supervisor reads its age).
Exit codes: 0 ended as asked; 2 wrong call; 4 the spool does not fit its journal; 5 start-up refused; 6 three
engine failures in a row; 7 a game's binding was refused.

Plants (only with --rehearsal; the journal says so; such pieces are not data), each at game number I:
 no_newgame, writeminply9   N12's two cases: the known answers of game I must change;
 swap_final, mvoes, cut2    A23: the opening of the NEXT id / a misspelt `moves` / the last two plies cut off is
                            written instead of the reserved line: exit code 7, nothing credited;
 kill_engine                the engine is ended once in the middle of game I: a legitimate retry, credited once.

Its test: serverday/tests/test_worker.py (cases T1 to T11; teamwork/W5_PLAN_by_fable.md).
"""
import argparse
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import record  # noqa: E402
from uciproc import Engine, EngineError, EngineRefused  # noqa: E402

RANDOM_PLIES = 8                 # the loop's opening rule: the first 8 plies are uniformly random legal moves
PLANTS = ("no_newgame", "writeminply9", "swap_final", "mvoes", "cut2", "kill_engine")


class StartRefused(RuntimeError):
    pass


class BindingRefused(RuntimeError):
    pass


class Stop(RuntimeError):
    """The worker cannot go on; .code is its exit code."""

    def __init__(self, code: int, text: str):
        super().__init__(text)
        self.code = code


def now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def game_id(run_id: str, worker: int, seq: int) -> str:
    return f"{run_id}-w{worker:03d}-g{seq:08d}"


def opening_index(root_seed: str, gid: str, ply: int, n: int) -> int:
    h = hashlib.sha256(f"{root_seed}|{gid}|{ply}".encode("ascii")).digest()
    return int.from_bytes(h[:8], "big") % n


def legal_moves(eng: Engine, moves: list) -> list:
    eng.command(record.position_line(moves))
    return sorted(ln.split(":")[0] for ln in eng.command("go perft 1") if re.fullmatch(r"[a-h][1-8][a-h][1-8][qrbn]?: 1", ln))


def append_line(path: Path, text: str) -> None:
    with open(path, "ab") as f:
        f.write((text + "\n").encode("utf-8"))
        f.flush()
        os.fsync(f.fileno())


def file_sha256(path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


class Worker:
    def __init__(self, a):
        self.a = a
        self.plant = (None, 0)
        self.plant_used = False
        if a.plant:
            kind, _, idx = a.plant.partition(":")
            if not a.rehearsal or kind not in PLANTS or not idx.isdigit():
                raise Stop(2, f"--plant <{' | '.join(PLANTS)}>:I, and only together with --rehearsal")
            self.plant = (kind, int(idx))
        man_bytes = Path(a.manifest).read_bytes()
        man = json.loads(man_bytes.decode("ascii"))
        self.manifest_sha = hashlib.sha256(man_bytes).hexdigest()
        self.options = list(man["options"])
        self.selfgame = man["selfgame_line"]
        self.probes = list(man["startup_probes"])
        self.depth = int(man["startup_depth"])
        self.net_want = (int(man["net_bytes"]), man["net_sha256"])
        self.known = json.loads(Path(a.known_startup).read_text(encoding="ascii"))
        self.net = str(Path(a.net).resolve()).replace("\\", "/")
        self.fixed = None
        if a.openings:
            self.fixed = [ln.split() for ln in Path(a.openings).read_text(encoding="ascii").splitlines() if ln.strip()]
        self.dir = Path(a.spool) / f"w{a.worker:03d}"
        (self.dir / "open").mkdir(parents=True, exist_ok=True)
        (self.dir / "closed").mkdir(parents=True, exist_ok=True)
        self.journal = self.dir / "journal.txt"
        self.log = open(self.dir / "worker.log", "a", encoding="utf-8", buffering=1)
        self.eng = None

    def say(self, text: str) -> None:
        self.log.write(f"[{now()}] {text}\n")

    # ---- 1: the start-up check ------------------------------------------------------------------------------
    def start_engine(self) -> None:
        if self.eng is not None:
            self.eng.kill()
            self.eng = None
        net = Path(self.net)
        if not net.is_file() or net.stat().st_size != self.net_want[0] or file_sha256(net) != self.net_want[1]:
            raise StartRefused(f"the net file {net.name} is missing or is not the manifest's ({self.net_want[0]} bytes, "
                               f"sha256 {self.net_want[1][:16]}...)")
        self.eng = eng = Engine(self.a.exe, log=self.log if self.a.trace else None)
        try:
            have = eng.uci_options()
            names = []
            for ln in self.options:
                m = re.fullmatch(r"setoption name (\S+) value (\S+)", ln)
                if not m:
                    raise StartRefused(f"not an option line: {ln[:80]}")
                name, val = m[1], m[2]
                names.append(name)
                if name not in have:
                    raise StartRefused(f"the engine's uci list has no option {name}")
                o = have[name]
                if o["type"] == "spin":
                    if not re.fullmatch(r"-?\d+", val) or not int(o["min"]) <= int(val) <= int(o["max"]):
                        raise StartRefused(f"{name} = {val} is outside {o.get('min')} .. {o.get('max')}")
                elif o["type"] == "check" and val not in ("true", "false"):
                    raise StartRefused(f"{name} = {val} is neither true nor false")
                if name == "UseNNUE" and val != "true":
                    raise StartRefused("UseNNUE false together with a net file")
            if len(set(names)) != len(names):
                raise StartRefused("an option stands twice in the list")
            if "NNUEArchFile" not in names or "NNUEArch" not in names or names.index("NNUEArchFile") > names.index("NNUEArch"):
                raise StartRefused("the list does not hold NNUEArchFile before NNUEArch")
            if have.get("UseNNUE", {}).get("default") != "true" and "UseNNUE" not in names:
                raise StartRefused("UseNNUE is not on by default and the list does not switch it on")
            want_sent = [ln.replace("@@NET@@", self.net) for ln in self.options]
            mark = len(eng.sent)
            answers = []
            for ln in want_sent:
                answers += eng.command(ln)
            answers += eng.ready()
            if [s for s in eng.sent[mark:] if s != "isready"] != want_sent:
                raise StartRefused("the option lines that were sent are not the manifest's list")
            active = [ln for ln in answers if ln.startswith("info string NNUE v3 active:")]
            want_net = self.known["net"][0]
            m = re.search(r" hidden (\d+) king_buckets (\d+).* checksum ([0-9a-f]+) ", active[-1]) if active else None
            got_net = [int(m[1]), int(m[2]), m[3]] if m else None
            if got_net is None or got_net != want_net:
                raise StartRefused(f"the net that is active is {got_net}, the frozen one is {want_net}")
            evals = []
            for probe in self.probes:
                ev = [ln for ln in eng.command(probe) + eng.command("eval") if ln.startswith("info string eval ")]
                m = re.fullmatch(r"info string eval hce (-?\d+) nnue (-?\d+) total (-?\d+)", ev[0]) if len(ev) == 1 else None
                if not m or m[1] != "0" or m[2] != m[3]:
                    raise StartRefused(f"`eval` after `{probe[:50]}` does not read `hce 0 nnue X total X`: {ev}")
                evals.append([int(m[1]), int(m[2]), int(m[3])])
            if evals != self.known["eval"]:
                raise StartRefused(f"the probe positions evaluate to {evals}, the known answers are {self.known['eval']}")
            want = self.known["search"][0]                       # [depth, nodes, hashfull, bestmove]
            if want[0] != self.depth:
                raise StartRefused(f"the known answers are for depth {want[0]}, the manifest asks for depth {self.depth}")
            eng.command("ucinewgame")
            eng.command("position startpos")
            eng.send(f"go depth {self.depth}")
            last, best = None, None
            for ln in eng.read_until(lambda s: s.startswith("bestmove"), 600, "the start-up search"):
                if ln.startswith("info ") and " depth " in ln and " nodes " in ln and " hashfull " in ln:
                    t = ln.split()
                    last = [int(t[t.index("depth") + 1]), int(t[t.index("nodes") + 1]), int(t[t.index("hashfull") + 1])]
                if ln.startswith("bestmove"):
                    best = ln.split()[1]
            got = [*(last or [None, None, None]), best]
            if got != want:
                raise StartRefused(f"the start-up search gave {got}, the known answers are {want}")
            sent = hashlib.sha256(("\n".join(self.options) + "\n").encode("ascii")).hexdigest()
            self.say(f"start-up ok: {len(self.options)} options (sha256 {sent[:16]}), net {got_net}, evals {evals}, search {got}")
            append_line(self.journal, f"engine_started {now().replace(' ', 'T')} pid {eng.p.pid} manifest_sha256 {self.manifest_sha} "
                                      f"options_sha256 {sent} net_sha256 {self.net_want[1]} net_checksum {got_net[2]} "
                                      f"search {got[0]} {got[1]} {got[2]} {got[3]}")
            eng.sent.clear()
        except EngineRefused as e:
            raise StartRefused(str(e)) from None

    # ---- 2: one game ----------------------------------------------------------------------------------------
    def opening(self, gid: str, seq: int):
        """(moves, whole): the opening reserved for this id; whole is False when the game ended inside it."""
        moves: list = []
        fixed = self.fixed[(seq - 1) % len(self.fixed)] if self.fixed else None
        for ply in range(len(fixed) if fixed is not None else RANDOM_PLIES):
            legal = legal_moves(self.eng, moves)
            if not legal:                                       # mate or stalemate inside the random plies
                return moves, False
            if fixed is not None:
                if fixed[ply] not in legal:
                    raise Stop(2, f"the fixed opening {' '.join(fixed)} holds an illegal move at ply {ply}")
                moves.append(fixed[ply])
            else:
                moves.append(legal[opening_index(self.a.root_seed, gid, ply, len(legal))])
        return moves, True

    def play(self, gid: str, seq: int):
        """Returns (the game's record as text, rows). Raises EngineError or BindingRefused."""
        eng = self.eng
        assert eng is not None
        moves, whole = self.opening(gid, seq)
        if not whole:
            return record.text(gid, moves, "none", [], f"openingend plies {len(moves)} reason nomoves"), 0
        line = record.position_line(moves)
        planted = self.plant[0] if self.plant[1] == seq and not self.plant_used else None
        if planted == "swap_final":
            line = record.position_line(self.opening(game_id(self.a.run_id, self.a.worker, seq + 1), seq + 1)[0])
        elif planted == "mvoes":
            line = line.replace(" moves ", " mvoes ")
        elif planted == "cut2":
            line = record.position_line(moves[:-2])
        sg = self.selfgame
        if planted == "writeminply9":
            sg = re.sub(r"writeminply \d+", "writeminply 9", sg)
        mark = len(eng.sent)
        if planted != "no_newgame":
            eng.command("ucinewgame")
        eng.command(line)
        eng.send(sg)
        if planted == "kill_engine":
            self.plant_used = True
            time.sleep(0.02)
            eng.p.kill()
        lines = eng.read_until(lambda s: s.startswith(("sgend ", "sgerror ")), self.a.game_seconds, f"game {gid}")
        rows = [ln for ln in lines if ln.startswith("sg ")]
        end = lines[-1]
        if len(rows) + 1 != len(lines):
            other = [ln for ln in lines[:-1] if not ln.startswith("sg ")][0]
            raise EngineError(f"game {gid}: a line that is neither a row nor the end: {other[:120]}")
        if not re.match(r"sgend result -?\d+ reason \S+ plies \d+ ", end):
            raise EngineError(f"game {gid}: an end line that cannot be read: {end[:120]}")
        # A23: what was REALLY written for this game, against the reservation, spelt out a second time
        written = eng.sent[mark:]
        pos = [s for s in written if s.split(" ", 1)[0] == "position"]
        if len(pos) != 1 or not written or written[-1].split(" ", 1)[0] != "selfgame":
            raise BindingRefused(f"{len(pos)} position lines between the game's start and its game line")
        if pos[0].split(" ") != record.position_tokens(moves):
            raise BindingRefused(f"reserved `{' '.join(record.position_tokens(moves))}`, written `{pos[0]}`")
        return record.text(gid, moves, pos[0], rows, end), len(rows)

    # ---- 3: pieces and the journal --------------------------------------------------------------------------
    def recover(self):
        """State from the journal: (games done, number of the open piece, games in it)."""
        done = closed = in_piece = 0
        end = 0
        if self.journal.exists():
            for ln in self.journal.read_text(encoding="utf-8").splitlines():
                t = ln.split()
                if t and t[0] == "done":
                    if t[t.index("piece") + 1] != f"p{closed:06d}":
                        raise Stop(4, f"the journal names {t[t.index('piece') + 1]} for {t[1]} while p{closed:06d} is the open piece")
                    done, in_piece, end = done + 1, in_piece + 1, int(t[t.index("end") + 1])
                elif t and t[0] == "closed":
                    closed, in_piece, end = closed + 1, 0, 0
        name = f"p{closed:06d}.raw"
        piece, moved = self.dir / "open" / name, self.dir / "closed" / name
        if end and not piece.exists() and moved.exists() and moved.stat().st_size == end:
            self.say(f"recover: {name} was moved to closed/ and its line in the journal is missing: the closing is finished")
            self.close_piece(closed, in_piece)
            closed, in_piece, end = closed + 1, 0, 0
            piece = self.dir / "open" / f"p{closed:06d}.raw"
        if not piece.exists() and end:
            raise Stop(4, f"the journal names {end} bytes in {piece.name} and the file is missing")
        if piece.exists() and piece.stat().st_size < end:
            raise Stop(4, f"the journal names {end} bytes in {piece.name} and the file holds {piece.stat().st_size}")
        if piece.exists() and piece.stat().st_size != end:      # a game written but not journalled: cut it off
            self.say(f"recover: {piece.name} is {piece.stat().st_size} bytes, the journal ends at {end}: cut back")
            with open(piece, "r+b") as f:
                f.truncate(end)
                f.flush()
                os.fsync(f.fileno())
        return done, closed, in_piece

    def close_piece(self, n: int, games: int) -> None:
        """Moved first, then its checksum file, then the journal's line: each step can be done again."""
        name = f"p{n:06d}.raw"
        src, dst = self.dir / "open" / name, self.dir / "closed" / name
        if games == 0:
            if src.exists() and src.stat().st_size == 0:
                src.unlink()
            return
        if src.exists():
            os.replace(src, dst)
        data = dst.read_bytes()
        digest = hashlib.sha256(data).hexdigest()
        rows = sum(1 for ln in data.split(b"\n") if ln.startswith(b"sg "))
        part = self.dir / "closed" / f"p{n:06d}.sha256.part"
        part.write_bytes(f"{digest}  {name}\ngames {games} rows {rows} bytes {len(data)}\n".encode("ascii"))
        os.replace(part, self.dir / "closed" / f"p{n:06d}.sha256")
        append_line(self.journal, f"closed p{n:06d} games {games} rows {rows} bytes {len(data)} sha256 {digest}")

    def run(self) -> int:
        a = self.a
        done, piece_n, in_piece = self.recover()
        if in_piece >= a.piece_games:                           # ended between a game and its piece's closing
            self.close_piece(piece_n, in_piece)
            piece_n, in_piece = piece_n + 1, 0
        self.say(f"worker {a.worker} of run {a.run_id}: {done} games in the journal; plant {self.plant}")
        if self.plant[0]:
            append_line(self.journal, f"PLANT {self.plant[0]} at game {self.plant[1]} (a rehearsal: these pieces are not data)")
        try:
            self.start_engine()
        except (StartRefused, EngineError) as e:
            self.say(f"START REFUSED: {e}")
            print(f"worker {a.worker}: START REFUSED: {e}")
            if self.eng is not None:
                self.eng.kill()
            return 5
        stop_file = Path(a.spool) / "STOP"
        fails = played = rows_total = 0
        rc = 0
        try:
            while True:
                self.eng.sent.clear()                           # nothing of an earlier game is kept (memory, and A23)
                if stop_file.exists() or (a.until and time.time() >= a.until) or (a.games and done >= a.games):
                    break
                seq = done + 1
                gid = game_id(a.run_id, a.worker, seq)
                try:
                    text, rows = self.play(gid, seq)
                except BindingRefused as e:
                    append_line(self.journal, f"REFUSED {gid} binding: {e}")
                    self.say(f"game {gid} NOT CREDITED, binding refused: {e}")
                    print(f"worker {a.worker}: BINDING REFUSED for {gid}: {e}")
                    rc = 7
                    break
                except EngineError as e:
                    fails += 1
                    self.say(f"game {gid} thrown away ({fails} in a row): {e}")
                    if fails >= 3:
                        rc = 6
                        break
                    try:
                        self.start_engine()
                    except (StartRefused, EngineError) as e2:
                        self.say(f"START REFUSED after a failure: {e2}")
                        print(f"worker {a.worker}: START REFUSED after a failure: {e2}")
                        rc = 5
                        break
                    continue
                fails = 0
                piece = self.dir / "open" / f"p{piece_n:06d}.raw"
                with open(piece, "ab") as f:
                    f.write(text.encode("ascii"))
                    f.flush()
                    os.fsync(f.fileno())
                    end = f.tell()
                append_line(self.journal, f"done {gid} piece p{piece_n:06d} end {end} rows {rows} "
                                          f"sha256 {hashlib.sha256(text.encode('ascii')).hexdigest()}")
                done, in_piece, played, rows_total = done + 1, in_piece + 1, played + 1, rows_total + rows
                (self.dir / "heartbeat").write_text(f"{time.time():.0f} games {done} rows_this_start {rows_total}\n", encoding="ascii")
                if in_piece >= a.piece_games:
                    self.close_piece(piece_n, in_piece)
                    piece_n, in_piece = piece_n + 1, 0
            self.close_piece(piece_n, in_piece)                 # the last, partly filled piece is sealed too
            kept = len(self.eng.sent) if self.eng is not None else 0
            code = self.eng.quit() if self.eng is not None else None
            self.say(f"ended with {rc}: {played} games and {rows_total} rows in this start, {done} games in all; "
                     f"engine exit code {code}; sent_kept {kept}")
            print(f"worker {a.worker}: ended with {rc}: {played} games, {rows_total} rows in this start; {done} games in all")
            return rc
        finally:
            if self.eng is not None:
                self.eng.kill()


def main() -> int:
    ap = argparse.ArgumentParser()
    for name in ("exe", "net", "manifest", "known-startup", "spool", "run-id", "root-seed"):
        ap.add_argument("--" + name, required=True)
    ap.add_argument("--worker", type=int, required=True)
    ap.add_argument("--games", type=int, default=0)
    ap.add_argument("--until", type=float, default=0.0)
    ap.add_argument("--piece-games", type=int, default=500)
    ap.add_argument("--game-seconds", type=float, default=600.0)
    ap.add_argument("--openings", default="")
    ap.add_argument("--trace", action="store_true", help="every line to and from the engine into worker.log (rehearsals: it doubles the bytes)")
    ap.add_argument("--rehearsal", action="store_true")
    ap.add_argument("--plant", default="")
    a = ap.parse_args()
    if not re.fullmatch(r"[A-Za-z0-9_]+", a.run_id) or not re.fullmatch(r"[A-Za-z0-9_]+", a.root_seed) \
            or a.piece_games < 1 or not 0 <= a.worker <= 999:
        print("STOP: run id and root seed are letters, digits and _ only; --piece-games is at least 1; --worker is 0 to 999")
        return 2
    try:
        return Worker(a).run()
    except Stop as e:
        print(f"worker {a.worker}: STOP ({e.code}): {e}")
        return e.code


if __name__ == "__main__":
    sys.exit(main())
