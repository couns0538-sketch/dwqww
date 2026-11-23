"""Review-only regression test. Run with -I -B and a new --work-dir."""
import argparse
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import rules_replay as rr

# Independent input copied from the pinned workload manifest, separate from the implementation.
POLICY = "selfgame softnodes 2000 evallimit 2000 maxply 300 writeminply 8 drawply 80 drawscore 5 drawcount 8"


def require(condition, name):
    if not condition:
        raise AssertionError(name)
    print("PASS", name)


def rejected(game, reservation, name):
    try:
        rr.check_game(game, reservation, game_line=POLICY)
    except rr.ReplayError:
        print("PASS", name)
        return
    raise AssertionError(name + " was accepted")


def run(work):
    cases = json.loads((HERE / "fixtures/cases.json").read_text(encoding="ascii"))
    with (HERE / "fixtures/games.txt").open("rb") as source:
        games = list(rr.read_games(source))
    require(len(games) == len(cases) and len(games) >= 11, "all frozen records present")
    results = []
    for g, case in zip(games, cases):
        require(g["id"] == case["id"], "frozen case identity " + case["id"])
        reservation = rr.reserve(g["id"], seed=case.get("seed"), fixed=case.get("opening"))
        result = rr.check_game(g, reservation, game_line=POLICY)
        want = case["expected"]
        require(all(result[key] == want[key] for key in ("reason", "rows", "moves", "searches")),
                "native independent counts " + case["id"] + " " + want["reason"])
        results.append(result)
        if result["reason"] != "nomoves":
            moves = result["moves"]
            score_end = result["reason"] in ("matescore", "evallimit")
            adjudicated = result["reason"] == "drawadj"
            require(result["searches"] == moves + int(score_end or adjudicated)
                    and result["rows"] == moves + int(adjudicated),
                    "PC ending table " + case["id"])
    require(set(r["reason"] for r in results) == set(rr.ENDINGS) | {"nomoves"}, "all ending paths")
    require([r["rows"] for r in results[:6]] == [86, 101, 0, 127, 81, 67], "six frozen N12 row counts")
    first = games[0]
    reservation = rr.reserve(first["id"], fixed=cases[0]["opening"])
    rejected(first, rr.reserve("another-w001-g00000001", fixed=cases[0]["opening"]), "reservation belongs to another logical id")
    wrong = copy.deepcopy(first)
    tokens = wrong["rows"][0].split()
    tokens[-2] = str(int(tokens[-2]) + 1)
    wrong["rows"][0] = " ".join(tokens)
    rejected(wrong, reservation, "one wrong row halfmove clock")
    for score in (2000, -2000):
        wrong = copy.deepcopy(first)
        tokens = wrong["rows"][0].split()
        tokens[2] = str(score)
        wrong["rows"][0] = " ".join(tokens)
        rejected(wrong, reservation, "evaluation limit cannot emit row at " + str(score))
    wrong = copy.deepcopy(first)
    wrong["end"] = wrong["end"].replace("nodes 302461 ", "nodes 85 ")
    rejected(wrong, reservation, "fewer visited nodes than successful searches")
    wrong = copy.deepcopy(first)
    wrong["rows"] = wrong["rows"][:-1]
    rejected(wrong, reservation, "missing unplayed draw decision")
    wrong = copy.deepcopy(first)
    wrong["end"] += " " + first["rows"][-1].split()[3]
    rejected(wrong, reservation, "adjudication move wrongly appended as played")
    wrong = copy.deepcopy(first)
    wrong["end"] = wrong["end"].replace("searches 86 ", "searches 85 ")
    rejected(wrong, reservation, "decision missing from search count")
    wrong = copy.deepcopy(first)
    wrong["end"] = wrong["end"].replace("reason drawadj", "reason rule")
    rejected(wrong, reservation, "false rules ending")
    wrong = copy.deepcopy(first)
    wrong["rows"][0] = wrong["rows"][0].replace(" b1c3 ", " a1a8 ", 1)
    rejected(wrong, reservation, "illegal move or mismatched played move")
    for standard, alternate in (("e1g1","e1h1"), ("e8g8","e8h8")):
        wrong = copy.deepcopy(first)
        wrong["rows"] = [r.replace(" " + standard + " ", " " + alternate + " ") for r in wrong["rows"]]
        prefix, suffix = wrong["end"].split(" moves ", 1)
        wrong["end"] = prefix + " moves " + " ".join(alternate if m == standard else m for m in suffix.split())
        rejected(wrong, reservation, "noncanonical standard-chess castling " + alternate)
    wrong = copy.deepcopy(first)
    wrong["sent"] = "none"
    wrong["rows"] = []
    wrong["end"] = "openingend plies 8 reason nomoves"
    rejected(wrong, reservation, "claim no moves with 27 legal")
    rejected(first, rr.reserve(first["id"], fixed=cases[1]["opening"]), "swapped reserved opening")
    wrong = copy.deepcopy(games[2])
    wrong["opening"] = list(cases[3]["opening"])
    wrong["sent"] = "position startpos moves " + " ".join(wrong["opening"])
    rejected(wrong, rr.reserve(wrong["id"], fixed=cases[3]["opening"]), "same FEN, different repetition history")
    seed_case = next(c for c in cases if c.get("seed") == "edge2715")
    index = cases.index(seed_case)
    raw = games[index]
    selected = HERE / "fixtures/games.txt"
    # CLI receives independent immutable input and writes only inside the provided new folder.
    fixed_file = work / "one-opening.txt"
    fixed_file.write_text(" ".join(cases[0]["opening"]) + "\n", encoding="ascii")
    one = work / "one.raw"
    with selected.open("rb") as src:
        lines = []
        for line in src:
            lines.append(line)
            if line.startswith(b"bind "):
                break
    one.write_bytes(b"".join(lines))
    manifest = work / "input policy.json"
    manifest.write_text(json.dumps({"selfgame_line": POLICY}), encoding="ascii")
    pin = hashlib.sha256(manifest.read_bytes()).hexdigest()
    cmd = [sys.executable, "-I", "-B", str(HERE / "rules_replay.py"), "--raw", str(one),
           "--manifest", str(manifest), "--manifest-sha256", pin,
           "--fixed-openings", str(fixed_file), "--work-dir", str(work / "first pass")]
    observed = subprocess.run(cmd, capture_output=True, text=True)
    require(observed.returncode == 0, "normal CLI publishes one rules report")
    report = work / "first pass" / "rules.jsonl"
    require(json.loads(report.read_text(encoding="ascii"))["rows"] == 86, "correct CLI row count")
    require(subprocess.run(cmd, capture_output=True).returncode != 0, "existing work folder refused")
    cmd[-1] = str(work / "wrong policy hash")
    cmd[cmd.index(pin)] = "0" * 64
    require(subprocess.run(cmd, capture_output=True).returncode != 0 and
            not (work / "wrong policy hash/rules.jsonl").exists(), "wrong producing manifest hash refused")
    modified = work / "different producing policy.json"
    modified.write_text(json.dumps({"selfgame_line": POLICY.replace("writeminply 8", "writeminply 9")}), encoding="ascii")
    cmd[cmd.index("0" * 64)] = hashlib.sha256(modified.read_bytes()).hexdigest()
    cmd[cmd.index(str(manifest))] = str(modified)
    cmd[-1] = str(work / "different policy")
    require(subprocess.run(cmd, capture_output=True).returncode != 0 and
            not (work / "different policy/rules.jsonl").exists(), "different pinned game policy refused")
    duplicate = work / "ambiguous producing policy.json"
    duplicate.write_text('{"selfgame_line":"other","selfgame_line":' + json.dumps(POLICY) + '}', encoding="ascii")
    cmd[cmd.index(str(modified))] = str(duplicate)
    old_pin = hashlib.sha256(modified.read_bytes()).hexdigest()
    cmd[cmd.index(old_pin)] = hashlib.sha256(duplicate.read_bytes()).hexdigest()
    cmd[-1] = str(work / "duplicate policy")
    require(subprocess.run(cmd, capture_output=True).returncode != 0 and
            not (work / "duplicate policy/rules.jsonl").exists(), "duplicate producing policy key refused")
    cmd[cmd.index(str(duplicate))] = str(manifest)
    cmd[cmd.index(hashlib.sha256(duplicate.read_bytes()).hexdigest())] = pin
    interrupted = work / "cut.raw"
    interrupted.write_bytes(one.read_bytes() + b"game interrupted")
    cmd[cmd.index(str(one))] = str(interrupted)
    cmd[-1] = str(work / "cut pass")
    require(subprocess.run(cmd, capture_output=True).returncode != 0 and
            not (work / "cut pass/rules.jsonl").exists(), "no published verdict on a torn input")
    require(raw["sent"] != "none" and results[index]["reason"] == "mate", "eighth-ply mate stays a completed game")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--work-dir", type=Path, required=True)
    work = parser.parse_args().work_dir
    work.mkdir(exist_ok=False)
    run(work)
