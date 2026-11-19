"""Audit exact fastchess argv and replay its seeded opening choice per PGN pair."""
import argparse
import csv
from hashlib import sha256
import json
from pathlib import Path
import re
import sys


FIXED_HASH = "2c4785517c8eb7a47ac39d282bc3917f77a5d0264c18b7898036e4abbefe6d5f"
BOOK_HASH = "889e8db12ee327cae68b29ada3458a2fb957cf8f5563d29a7fd13d850ff3f638"
PAIR_HASH = "93c3d57cc82bdcb218b29d379fd4a448e5b4c034e06bee62cb02729806d87c3e"
BINARY_HASHES = {
    "r15d": "9068653cd638639a602b7c72dafe741e395598d0178f14fa31d530767f982671",
    "kF": "c9ab02f9e15cc0a293b849116aa56d45ca3c521fa1209ed27386734dbb62d0eb",
    "fastchess": "091bf93dcf08e15d14b77bc2374d0a423982b32200e8add69f17bace3a34b31f",
    "net": "c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7",
}
MASK = (1 << 64) - 1
STARTPOS = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1"


def require(ok, msg):
    if not ok:
        raise ValueError(msg)


def digest(path):
    return sha256(path.read_bytes()).hexdigest()


def tsv(path):
    with path.open(newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def openings(seed, size):
    # ISO C++ mt19937_64, the first eight draws; a forward Fisher–Yates
    # shuffle never changes an element after passing its index.
    state = [seed]
    for i in range(1, 312):
        prev = state[-1]
        state.append((6364136223846793005 * (prev ^ (prev >> 62)) + i) & MASK)
    shuffled = list(range(size))
    for i in range(8):
        low = (1 << 31) - 1
        joined = (state[i] & (MASK ^ low)) | (state[i + 1] & low)
        value = state[i + 156] ^ (joined >> 1) ^ (0xb5026f5aa96619e9 if joined & 1 else 0)
        value ^= (value >> 29) & 0x5555555555555555
        value ^= (value << 17) & 0x71d67fffeda60000
        value ^= (value << 37) & 0xfff7eee000000000
        value ^= value >> 43
        j = i + value % (size - i)
        shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
    return shuffled[:8]


def argv_check(args, inputs, stage, row, j, fixed, pgn):
    expect = [inputs["fastchess"]["path"]]
    fixed_opts = [f"option.{name}={val}" for name, val in fixed if name not in ("Threads", "Hash")]
    fixed_opts += [f"option.NNUEArchFile={inputs['net']['path']}", "option.NNUEArch=true"]
    for side in ["plus", "minus"]:
        prefix = side + "_"
        expect += ["-engine", "cmd=" + inputs["engine"]["path"], "name=" + side, *fixed_opts]
        expect += [f"option.{key[len(prefix):]}={value}" for key,value in row.items() if key.startswith(prefix)]
        if stage == "C24" and side == "plus":
            expect += ["option.LmrQuietBase=60"]
    expect += ["-each","proto=uci","nodes=20000","option.Threads=1","option.Hash=16","option.OwnBook=false",
               "-openings","file=" + inputs["book"]["path"],"format=epd","order=random","-srand",str(2400000+j),
               "-rounds","8","-games","2","-repeat","-concurrency","8","-force-concurrency","-recover","-pgnout"]
    require(args[:-1] == expect and args[-1].startswith("file=") and
            Path(args[-1][5:]).parts[-2:] == (stage,pgn.name), f"{stage} j{j} argv mismatch")


def pgn_headers(path):
    text = path.read_text()
    for block in re.split(r"(?=^\[Event )", text, flags=re.M):
        if block.strip():
            tags = dict(re.findall(r'^\[([^ ]+) "([^"\r\n]*)"\]\r?$', block, flags=re.M))
            yield tags


def check_stage(directory, fixed_path, pairs_path, book_path, last, partial_last):
    stage = directory.name
    require(stage in ("R1","R2","C24","K1"), "unexpected stage")
    inputs = {x["name"]:x for x in tsv(directory / "inputs.tsv")}
    actual = {"book": digest(book_path), "pairsets": digest(pairs_path), "fixed": digest(fixed_path)}
    require(actual == {"book":BOOK_HASH, "pairsets":PAIR_HASH, "fixed":FIXED_HASH}, "reference input digest mismatch")
    for key, expected in dict(actual, engine=BINARY_HASHES["kF" if stage=="K1" else "r15d"],
                              net=BINARY_HASHES["net"],fastchess=BINARY_HASHES["fastchess"]).items():
        require(inputs[key]["sha256"] == expected, f"{stage} {key} input mismatch")
    fixed = [line.split()[2::2] for line in fixed_path.read_text().splitlines()]
    pairsets = tsv(pairs_path)
    book = [line for line in book_path.read_text().splitlines() if line]
    require(len(book)==234, "book position count mismatch")
    print(f"book_sha256 {actual['book']} book_positions {len(book)}")
    print("stage\tj\tseed\tcommands\tPGN_games\tpaired_rounds\tEPD_line_numbers")
    for j in range(1,last+1):
        base = directory / f"j{j:03d}"
        pgn = base.with_suffix(".pgn")
        argv_check(json.loads(base.with_suffix(".command.json").read_text()), inputs, stage,
                   pairsets[j-1], j, fixed, pgn)
        log = base.with_suffix(".log").read_text()
        require(not re.search(r"failed to set option|unknown (?:uci )?option|invalid value", log, re.I),
                f"{stage} j{j} option warning in fastchess output")
        starts = re.findall(r"^Started game (\d+) of 16 \((plus|minus) vs (minus|plus)\)", log, re.M)
        started_ids = {int(game) for game,_,_ in starts}
        require(all((white,black) == (("plus","minus") if int(game)%2 else ("minus","plus"))
                    for game,white,black in starts), f"{stage} j{j} seat assignment in log")
        if not (partial_last and j == last):
            require(started_ids == set(range(1,17)), f"{stage} j{j} missing game starts in log")
        ids = openings(2400000+j, len(book))
        seen = set()
        for tags in pgn_headers(pgn):
            r = int(tags["Round"])
            require(1 <= r <= 8, f"{stage} j{j} round {r}")
            key = r, tags["White"]
            require(key not in seen and {tags["White"],tags["Black"]}=={"plus","minus"}, f"{stage} j{j} seats {key}")
            seen.add(key)
            expected = book[ids[r-1]].split()
            actual_fen = tags.get("FEN", STARTPOS).split()
            # fastchess may export the EPD directly or append default half/fullmove fields.
            require(expected == actual_fen or len(expected)==4 and actual_fen==expected+["0","1"],
                    f"{stage} j{j} round {r} expected EPD line {ids[r-1]+1} {' '.join(expected)} got {' '.join(actual_fen)}")
            require(tags.get("SetUp")=="1" or actual_fen==STARTPOS.split(), f"{stage} j{j} missing SetUp tag")
        if not (partial_last and j == last):
            require(seen == {(r,c) for r in range(1,9) for c in ("plus","minus")}, f"{stage} j{j} missing legs")
        full_rounds = sum((r,"plus") in seen and (r,"minus") in seen for r in range(1,9))
        print(stage,j,2400000+j,1,len(seen),full_rounds,",".join(str(k+1) for k in ids),sep="\t")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("stage",type=Path)
    p.add_argument("fixed_pc20",type=Path)
    p.add_argument("pairsets",type=Path)
    p.add_argument("book_epd",type=Path)
    p.add_argument("last",type=int,help="last completed pair set, included")
    p.add_argument("--partial-last",action="store_true",help="verify any PGN games present in the last interrupted set")
    a=p.parse_args()
    require(1 <= a.last <= (1 if a.stage.name=="C24" else 80), "invalid last pair set")
    check_stage(a.stage,a.fixed_pc20,a.pairsets,a.book_epd,a.last,a.partial_last)


if __name__ == "__main__":
    try:
        main()
    except (KeyError,OSError,ValueError) as exc:
        sys.exit(str(exc))
