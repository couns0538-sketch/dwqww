"""Fable 2026-11-23, W5 with A14 of FINAL_PLAN_2311.md: the test of home/to_round.py.

    test_to_round.py <engine exe> <net file> <converter exe> <serverday folder> <the loop's config>
                     <folder that holds nnloop> <NEW work folder>

The ORACLE is the loop's own driver function `play_game_sg` (pipeline/nnloop/datagen_uci.py): it is fed, for
every game, the very lines the engine printed for the server-day worker (a stand-in engine that hands them out
one by one, a stand-in random source that picks the game's own opening moves), and the text it returns is what
the loop would have written for that game. to_round.py must write exactly that text for every credited game.
36 real games: N12's six and 30 with openings by seed, through worker, packer and receiver.

 R1 the whole chain ends with 0; every credited game goes in
 R2 the text is, byte for byte, the loop's own text of the same games in the same order
 R3 the loop's driver, fed these games, sends the position line that the worker wrote and the manifest's frozen
    game line (so the frozen game line IS today's config)
 R4 the report's counts fit (rows in and out, the endings, the left-out games)
 R5 a config whose tables do not open: exit code 4, no text written
 R6 a manifest with another game line (`writeminply 9`): exit code 2
 R7 a credited game missing from state/raw: exit code 3
Not shown here: a game whose result the tables correct (none among these 36: about 1 game in 130 in the loop's
rounds); the oracle and the tool share the after-game function itself, so R2 tests what is handed to it.
"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

if len(sys.argv) != 8:
    print(__doc__)
    sys.exit(2)
EXE, NET, CONV, SD, CONFIG, PIPE, WORK = (Path(x).resolve() for x in sys.argv[1:8])
if WORK.exists():
    print(f"STOP: {WORK} exists already (a NEW work folder)")
    sys.exit(2)
WORK.mkdir(parents=True)
sys.path.insert(0, str(SD / "run"))
sys.path.insert(0, str(PIPE))
import record  # noqa: E402
import chess  # noqa: E402
from nnloop import datagen_uci  # noqa: E402
from nnloop.common import load_config  # noqa: E402

MAN, KNOWN = SD / "workloads" / "MANIFEST.json", SD / "known" / "startup.json"
results = []


def check(name: str, ok, detail="") -> bool:
    results.append((name, bool(ok)))
    print(f"{'ok  ' if ok else 'FAIL'} {name}" + (f": {str(detail)[:400]}" if detail != "" and not ok else ""), flush=True)
    return bool(ok)


def run(cmd):
    p = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, timeout=1800)
    return p.returncode, (p.stdout + p.stderr).strip()


def to_round(state, out, manifest=MAN, config=CONFIG):
    return run([sys.executable, "-I", "-B", SD / "home" / "to_round.py", "--state", state, "--manifest", manifest,
                "--config", config, "--pipeline", PIPE, "--out", out])


class LinesEngine:
    """Stands in for the loop's engine object: hands out one game's lines as the engine printed them."""

    def __init__(self, rec):
        self.lines, self.sent = list(rec["rows"]) + [rec["end"]], []

    def new_game(self):
        self.sent.append("<new game>")

    def send(self, line):
        self.sent.append(line)

    def _get(self, _deadline):
        return self.lines.pop(0)


class OpeningRng:
    """Stands in for the loop's random source: the random plies are plies 0 to k - 1, each choice is the game's
    own next opening move."""

    def __init__(self, opening):
        self.opening = list(opening)

    def sample(self, population, k):
        return list(population)[:k]

    def choice(self, moves):
        want = self.opening.pop(0)
        return next(m for m in moves if m.uci() == want)


N12 = [ln.split()[3:] for ln in (SD / "workloads" / "n12_batch.uci").read_text(encoding="ascii").splitlines()
       if ln.startswith("position startpos moves ")]
OPENINGS = WORK / "n12_openings.txt"
OPENINGS.write_text("".join(" ".join(o) + "\n" for o in N12), encoding="ascii")
steps = []
for name, worker, games, piece_games, run_id, openings in (("n12", 1, 6, 4, "n12", OPENINGS), ("rnd", 2, 30, 7, "rnd", None)):
    spool, outp, state = WORK / f"spool_{name}", WORK / f"out_{name}", WORK / "state"
    steps.append(run([sys.executable, "-I", "-B", SD / "run" / "worker.py", "--exe", EXE, "--net", NET, "--manifest", MAN,
                      "--known-startup", KNOWN, "--spool", spool, "--run-id", run_id, "--worker", worker, "--root-seed", "seedA",
                      "--piece-games", piece_games, "--games", games] + (["--openings", openings] if openings else [])))
    steps.append(run([sys.executable, "-I", "-B", SD / "run" / "packer.py", "--spool", spool, "--out", outp, "--converter", CONV, "--once"]))
    steps.append(run([sys.executable, "-I", "-B", SD / "home" / "receiver.py", "--inbox", outp, "--state", state, "--converter", CONV,
                      "--root-seed", "seedA"] + (["--openings", openings] if openings else [])))
STATE = WORK / "state"
credited = [json.loads(x) for x in (STATE / "credited.jsonl").read_text(encoding="ascii").splitlines()]
rc, out = to_round(STATE, WORK / "round")
check("R1 worker, packer and receiver for both runs, then to_round: all end with 0", all(s[0] == 0 for s in steps) and rc == 0,
      [s for s in steps if s[0] != 0] + [out])
rep = json.loads((WORK / "round" / "report.json").read_text(encoding="ascii")) if rc == 0 else {}
check("R1 every credited game goes in (35: the game without rows of N12 is not credited)", len(credited) == 35 and rep.get("games_in") == 35, rep)

cfg = load_config(CONFIG)
g = cfg["datagen"]
check("R3 control: the loop's config allows its own game-in-the-engine path", datagen_uci.selfgame_ok(cfg) == "", datagen_uci.selfgame_ok(cfg))
frozen = json.loads(MAN.read_text(encoding="ascii"))["selfgame_line"]
oracle, sent_ok, n_rows, left_out = [], True, 0, 0
by_id = {}
for piece in sorted({c["piece"] for c in credited}):
    for rec in record.parse((STATE / "raw" / (piece + ".raw")).read_bytes()):
        by_id[rec["id"]] = rec
order = [rec for piece in sorted({c["piece"] for c in credited}) for rec in record.parse((STATE / "raw" / (piece + ".raw")).read_bytes())
         if rec["id"] in {c["id"] for c in credited}]
for rec in order:
    eng = LinesEngine(rec)
    text, n, _res, _plies = datagen_uci.play_game_sg(eng, OpeningRng(rec["opening"]), g, None)
    oracle.append(text)
    n_rows += n
    left_out += datagen_uci.LAST_SKIP is not None
    sent_ok = sent_ok and eng.sent == ["<new game>", rec["sent"], frozen] and not eng.lines
got = (WORK / "round" / "games.plain").read_bytes() if rc == 0 else b""
check(f"R2 the text of {len(order)} games is the loop's own text, byte for byte ({n_rows} rows)",
      len(order) == 35 and got == "".join(oracle).encode("ascii") and n_rows > 3000,
      (len(got), len("".join(oracle))))
check("R3 the loop's driver sends, for every game, the position line the worker wrote and the manifest's frozen game line", sent_ok)
rows_in = sum(len(r["rows"]) for r in order)
check("R4 the report: rows in, rows written, games by ending and left-out games fit the oracle",
      rep.get("rows_in") == rows_in and rep.get("rows_written") == n_rows and sum(rep.get("by_ending", {}).values()) == 35
      and rep.get("left_out_by_ply_limit_rule") == left_out and rep.get("games_written") == sum(1 for t in oracle if t), rep)
check("R4 the text holds six lines a row", got.count(b"\n") == 6 * n_rows and got.count(b"\ne\n") == n_rows)

text = CONFIG.read_text(encoding="utf-8")
old = 'tablebase_path = "C:/nnue-lab/tablebases/syzygy345"'
if text.count(old) != 1 or not g.get("adjudicate_tablebase", False):
    check("R5 a config whose tables do not open (NOT RUN: the config has no such line, or the tables are switched off)", False)
else:
    empty = WORK / "no_tables"
    empty.mkdir()
    cfg2 = WORK / "config_no_tables.toml"
    cfg2.write_text(text.replace(old, f'tablebase_path = "{empty.as_posix()}"'), encoding="utf-8")
    rc5, out5 = to_round(STATE, WORK / "round_no_tables", config=cfg2)
    check("R5 the tables do not open: exit code 4, said so, no text written",
          rc5 == 4 and "tables did not open" in out5 and not (WORK / "round_no_tables" / "games.plain").exists(), (rc5, out5))
man = json.loads(MAN.read_text(encoding="ascii"))
man9 = WORK / "manifest_wmp9.json"
man9.write_text(json.dumps(dict(man, selfgame_line=man["selfgame_line"].replace("writeminply 8", "writeminply 9"))), encoding="ascii")
rc6, out6 = to_round(STATE, WORK / "round_wmp9", manifest=man9)
check("R6 a manifest with another game line: exit code 2, both lines named, nothing written",
      rc6 == 2 and "writeminply 9" in out6 and "writeminply 8" in out6 and not (WORK / "round_wmp9").exists(), (rc6, out6))
state7 = WORK / "state_missing"
shutil.copytree(STATE, state7)
gone = sorted((state7 / "raw").rglob("*.raw"))[-1]
gone.unlink()
rc7, out7 = to_round(state7, WORK / "round_missing")
check("R7 a credited game's piece missing from state/raw: exit code 3, the piece named", rc7 == 3 and gone.name in out7, (rc7, out7))

bad = [n for n, ok in results if not ok]
print(f"{'ALL ' + str(len(results)) + ' CHECKS PASS' if not bad else 'FAILED ' + str(len(bad)) + ' of ' + str(len(results))}")
sys.exit(1 if bad or not results else 0)
