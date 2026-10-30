"""R10: N fast games of the engine with EvalFileHalfKA on against the same engine with it off (fastchess), then every
termination counted from the PGN: no illegal move, no crash/disconnect may appear. Run under run_pinned.py.
usage: python -I -B fast_games.py <forge.exe> <net.nnue> <out dir> [--games 200] [--tc 2+0.02] [--conc 2]"""
import os
import re
import subprocess
import sys

exe, net, out = sys.argv[1], sys.argv[2], sys.argv[3]


def opt(name, default):
    return sys.argv[sys.argv.index(name) + 1] if name in sys.argv else default


games, tc, conc = int(opt("--games", "200")), opt("--tc", "2+0.02"), opt("--conc", "2")
FC = r"C:\Users\Administrator\grok-pc\tools\fastchess\fastchess.exe"
BOOK = r"C:\Users\Administrator\grok-pc\coder-fuzz\8moves_v3.pgn"
os.makedirs(out, exist_ok=True)
pgn = os.path.join(out, "games.pgn")
cmd = [FC, "-engine", "name=halfka_on", f"cmd={exe}", f"option.EvalFileHalfKA={net}",
       "-engine", "name=halfka_off", f"cmd={exe}",
       "-each", f"tc={tc}", "timemargin=1000", "proto=uci", "option.Threads=1", "option.Hash=16", "option.OwnBook=false",
       "-openings", f"file={BOOK}", "format=pgn", "order=random", "-srand", "20261030",
       "-games", "2", "-repeat", "-rounds", str(games // 2), "-concurrency", conc, "-recover",
       "-pgnout", f"file={pgn}", "-config", f"outname={os.path.join(out, 'fastchess_config.json')}"]
with open(os.path.join(out, "fastchess.out"), "x", encoding="utf-8") as f:
    rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, cwd=out)
text = open(pgn, encoding="utf-8", errors="replace").read()
terms, results, n = {}, {"1-0": 0, "0-1": 0, "1/2-1/2": 0, "*": 0}, 0
on_score = 0.0
for g in text.split("[Event ")[1:]:
    tags = dict(re.findall(r'^\[(\w+) "([^"]*)"\]', g, re.M))
    n += 1
    terms[tags.get("Termination", "?")] = terms.get(tags.get("Termination", "?"), 0) + 1
    r = tags.get("Result", "*")
    results[r] = results.get(r, 0) + 1
    if r == "1/2-1/2":
        on_score += 0.5
    elif r in ("1-0", "0-1") and (r == "1-0") == (tags.get("White") == "halfka_on"):
        on_score += 1
bad = {t: c for t, c in terms.items() if any(k in t.lower() for k in ("illegal", "abandon", "disconnect", "stall", "crash"))}
print(f"fastchess exit {rc}; {n} games; results {results}; terminations {terms}; HalfKA-on score {on_score}/{n} "
      f"(no Elo claim: smoke net vs the lock's eval)")
print("NO ILLEGAL MOVES / CRASHES" if n == games and not bad and rc == 0 else f"PROBLEM: {bad}, games {n}/{games}, rc {rc}")
