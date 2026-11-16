import re, sys, math

# Merge fastchess stdout game lines with PGN FEN headers by round number.
# Output line: round|white|black|result|how it ended|opening FEN

def parse_stdout(path):
    games = {}
    pat = re.compile(r"^Finished game (\d+) \((.+?) vs (.+?)\): (\S+)\s*\{(.+?)\}")
    for line in open(path):
        m = pat.match(line.strip())
        if m:
            n = int(m.group(1))
            games[n] = (m.group(2), m.group(3), m.group(4), m.group(5))
    return games

def parse_pgn(path):
    out = {}
    headers = {}
    round_no = None
    def flush():
        nonlocal headers, round_no
        if round_no is not None:
            out[round_no] = (headers.get("FEN", "?"), headers.get("Result", "?"))
        headers, round_no = {}, None
    for line in open(path):
        line = line.rstrip("\n")
        if line.startswith("["):
            m = re.match(r'\[(\w+)\s+"(.*)"\]', line)
            if m:
                headers[m.group(1)] = m.group(2)
                if m.group(1) == "Round":
                    flush()
                    round_no = int(m.group(2))
        elif line.strip() == "" and headers:
            pass
    flush()
    return out

stdout_path, pgn_path, out_path = sys.argv[1], sys.argv[2], sys.argv[3]
games = parse_stdout(stdout_path)
fens = parse_pgn(pgn_path)
missing_fen = 0
with open(out_path, "w") as f:
    for n in sorted(games):
        w, b, r, how = games[n]
        pair = (n + 1) // 2  # fastchess numbers rounds per opening pair
        fen, pres = fens.get(pair, ("?", "?"))
        if fen == "?":
            missing_fen += 1
        f.write(f"{n}|{w}|{b}|{r}|{how}|{fen}\n")
print(f"{out_path}: {len(games)} games, missing FEN: {missing_fen}")
