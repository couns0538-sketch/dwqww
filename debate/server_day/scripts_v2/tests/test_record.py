"""Fable 2026-11-23, server-day plan: the test of run/record.py (FORMATS.md section 0.1, binding 2).

    test_record.py <folder holding record.py> <games.txt> <record_v2_vectors.json>

games.txt is Astra's published native fixture (debate/server_day/ref/astra/fixtures/games.txt: 13 records of
this morning's binding, 1,139 rows); the vectors file is hers too (debate/server_day/cases/astra/
record_v2_vectors.json: for each of the 13 the binding 2, the record's length and hash, its rows and rows digest;
ten negatives, each an exact edit of a positive with its length, its hash and the check that must refuse it).
Both are DATA here: nothing of hers is run. Every byte stream is rebuilt by her stated construction and compared
with HER length and hash BEFORE the module under test sees it; then the module's own verdict is demanded.

The folder is an argument, so that another record.py (the stand-in the worker was first tested with, this
morning's) is tested the same way. No engine, no file written, a second.

 R1  the inputs are the published ones (hashes), the fixture splits into 13 records, each with her original hash
 R2  her 13 positives: rebuilt, equal to her length and hash; parse() gives one record with her id, bind and row
     count; rows_digest() gives her digest (None for the five without rows); bind() gives her bind; text() gives
     the stream back byte for byte; faults() finds nothing; all 13 in a row parse as 13 with the right offsets
 R3  her 10 negatives: rebuilt, equal to her length and hash; parse() refuses each, by the check she names
 R4  the run enters the binding: a positive is refused under another run's fingerprint; "old-binding" IS the
     fixture's original record (this morning's binding), byte for byte
 R5  FORMATS 0.1's sentence: changing only the id or the opening changes the binding and leaves the rows digest;
     changing a score or the result changes both
 R6  bytes and structure, cases of the PC's own: each must be refused by the named check
 R7  the writer cannot write what a reader refuses: text() and bind() refuse each bad part
 R8  faults(): a sent line that is not the opening's position line, an opening that is not the reserved one,
     an opening end with rows, a wrong opening length: each named; the clean record: nothing
 R9  the shapes agree with the driver's table: every row and engine end line of the fixture passes both
"""
import hashlib
import json
import sys
from pathlib import Path

if len(sys.argv) != 4:
    sys.exit(__doc__)
FOLDER, GAMES, VECTORS = (Path(a).resolve() for a in sys.argv[1:4])
sys.path.insert(0, str(FOLDER))
import record  # noqa: E402

if (FOLDER / "engine_lines.py").exists():
    import engine_lines  # noqa: E402
else:
    sys.path.insert(1, str(Path(__file__).resolve().parents[1] / "run"))
    import engine_lines  # noqa: E402

results = []
ERR = getattr(record, "RecordError", ValueError)
FP = "a" * 64


def check(name: str, ok, detail: object = "") -> bool:
    results.append((name, bool(ok)))
    print(("ok   " if ok else "FAIL ") + name + ("" if ok else f": {str(detail)[:400]}"))
    return bool(ok)


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def tried(fn):
    """('returned', value) or (the check's name of a RecordError, its text) or ('another error', its text)."""
    try:
        return "returned", fn()
    except ERR as e:
        return getattr(e, "check", "RecordError without a check name"), str(e)
    except Exception as e:  # noqa: BLE001
        return f"another error: {type(e).__name__}", str(e)


# ---------------------------------------------------------------- R1: the inputs
games = GAMES.read_bytes()
vec_bytes = VECTORS.read_bytes()
vec = json.loads(vec_bytes)
check("R1 the vectors file is the published one (11,361 bytes, 4fb382d0...) and names this fixture and the run of 64 `a`",
      len(vec_bytes) == 11361 and sha(vec_bytes) == "4fb382d0c350b0b20aa7d5184f5f55427669ff82ffc1b8963366c552a235032c"
      and sha(games) == vec["source_sha256"] and vec["run_fingerprint"] == FP, (len(vec_bytes), sha(vec_bytes)[:12], sha(games)[:12]))
source, start, outside = [], None, 0
pos = 0
for raw in games.split(b"\n")[:-1]:
    here, pos = pos, pos + len(raw) + 1
    if raw.startswith(b"game "):
        outside += start is not None
        start = here
    elif start is None:
        outside += 1
    elif raw.startswith(b"bind "):
        source.append(games[start:pos])
        start = None
P = vec["positives"]
check("R1 the fixture is 13 records one after another with nothing outside them, each with the original hash the vectors name",
      len(source) == 13 == len(P) and not outside and start is None and games.endswith(b"\n") and b"".join(source) == games
      and [sha(s) for s in source] == [p["original_record_sha256"] for p in P], (len(source), outside))


def positive(n: int) -> bytes:
    """Her construction: the source record with ONLY the 64 digest characters of its bind line replaced."""
    s = source[n - 1]
    assert s[-70:-65] == b"bind " and s.endswith(b"\n")
    return s[:-65] + P[n - 1]["bind"].encode("ascii") + b"\n"


# ---------------------------------------------------------------- R2: the positives
streams = [positive(p["n"]) for p in P] if len(source) == 13 else []
check("R2 each of the 13 rebuilt records has the length and the hash the vectors name (judged before the module sees them)",
      len(streams) == 13 and all(len(s) == p["bytes"] and sha(s) == p["sha256"] for s, p in zip(streams, P)),
      [(p["n"], len(s), sha(s)[:12]) for s, p in zip(streams, P) if len(s) != p["bytes"] or sha(s) != p["sha256"]])
slips, parsed = [], []
for s, p in zip(streams, P):
    how, got = tried(lambda: record.parse(s, FP))
    if how != "returned" or len(got) != 1:
        slips.append((p["n"], how, str(got)[:100]))
        parsed.append(None)
        continue
    g = got[0]
    parsed.append(g)
    if not (g["id"] == p["id"] and g["bind"] == p["bind"] and len(g["rows"]) == p["rows"] and g.get("first") == 0
            and g["last"] == len(s)):
        slips.append((p["n"], "the parsed record", g["id"], g["bind"][:12], len(g["rows"])))
check("R2 parse() takes each of the 13 as ONE record with the id, the bind and the row count the vectors name",
      streams and not slips, slips)
ok = [g for g in parsed if g]
dig = tried(lambda: [record.rows_digest(g["rows"], g["end"]) for g in ok])
check("R2 rows_digest() gives the vectors' digest for the eight games with rows and None for the five without (1,139 rows in all)",
      len(ok) == 13 and dig[0] == "returned" and dig[1] == [p["rows_digest"] for p in P]
      and sum(len(g["rows"]) for g in ok) == 1139 and sum(d is None for d in dig[1]) == 5, str(dig)[:300])
b = tried(lambda: [record.bind(FP, g["id"], g["opening"], g["sent"], g["rows"], g["end"]) for g in ok])
check("R2 bind() over the parsed parts gives the vectors' bind for all 13", len(ok) == 13 and b == ("returned", [p["bind"] for p in P]),
      str(b)[:300])
t = tried(lambda: [record.text(FP, g["id"], g["opening"], g["sent"], g["rows"], g["end"]).encode("ascii") for g in ok])
check("R2 text() over the parsed parts gives each record back byte for byte", len(ok) == 13 and t == ("returned", streams), str(t)[:200])
f = tried(lambda: [record.faults(g) for g in ok])
check("R2 faults() finds nothing in any of the 13", len(ok) == 13 and f == ("returned", [[]] * 13), str(f)[:300])
allof = tried(lambda: record.parse(b"".join(streams), FP))
ends, at = [], 0
for s in streams:
    at += len(s)
    ends.append(at)
check("R2 the 13 in a row parse as 13 records, each ending at its own byte", allof[0] == "returned" and len(allof[1]) == 13
      and [g["last"] for g in allof[1]] == ends and [g["id"] for g in allof[1]] == [p["id"] for p in P], str(allof)[:200])

# ---------------------------------------------------------------- R3: the negatives
WANT = {"reject binding against the expected run": "binding", "reject binding": "binding", "reject superseded binding": "binding",
        "reject truncated final line": "final-lf", "reject extra blank between records": "blank",
        "reject noncanonical bytes": "bytes", "reject run name grammar": "run", "reject counter outside range": "counter",
        "reject slot grammar": "slot"}


def negative(case: dict) -> bytes:
    base = streams[case["base_positive"] - 1]
    out = base
    for op in case["operations"]:
        if op["op"] == "replace_once":
            old, new = op["old"].encode("ascii"), op["new"].encode("ascii")
            assert old in out, f"{case['name']}: {op['old']!r} is not in the record"
            out = out.replace(old, new, 1)
        elif op["op"] == "replace_all":
            out = out.replace(op["old"].encode("ascii"), op["new"].encode("ascii"))
        elif op["op"] == "drop_final_lf":
            assert out.endswith(b"\n")
            out = out[:-1]
        elif op["op"] == "append_lf_and_base":
            out = out + b"\n" + base
        else:
            raise AssertionError(f"{case['name']}: an operation this test does not know: {op['op']}")
    return out


N = vec["negatives"]
neg = tried(lambda: [negative(c) for c in N]) if streams else ("no positives", "")
check("R3 each of the 10 rebuilt negatives has the length and the hash the vectors name (judged before the module sees them)",
      neg[0] == "returned" and len(N) == 10 and all(len(s) == c["bytes"] and sha(s) == c["sha256"] for s, c in zip(neg[1], N)),
      str(neg)[:200] if neg[0] != "returned" else [(c["name"], len(s), sha(s)[:12]) for s, c in zip(neg[1], N)
                                                    if len(s) != c["bytes"] or sha(s) != c["sha256"]])
if neg[0] == "returned":
    for s, c in zip(neg[1], N):
        how, text = tried(lambda: record.parse(s, FP))
        check(f"R3 {c['name']}: refused, by the check `{WANT.get(c['expected'], 'UNKNOWN: ' + c['expected'])}` (hers: {c['expected']})",
              how == WANT.get(c["expected"]), (how, str(text)[:160]))

# ---------------------------------------------------------------- R4: the run, and this morning's binding
one = streams[0] if streams else b""
other = tried(lambda: record.parse(one, "b" * 64))
check("R4 the first positive is refused under another run's fingerprint (64 `b`), by the check `binding`", other[0] == "binding", other)
old = [s for s, c in zip(neg[1], N) if c["name"] == "old-binding"] if neg[0] == "returned" else []
check("R4 `old-binding` is the fixture's original first record byte for byte: a record of this morning's binding does not verify",
      len(old) == 1 and len(source) == 13 and old[0] == source[0], len(old))
badfp = [tried(lambda v=v: record.parse(one, v))[0] for v in ("A" * 64, "a" * 63, "", None, 5)]
check("R4 a run fingerprint that is not 64 lower-case hex digits is refused before anything is read", badfp == ["run-fingerprint"] * 5, badfp)

# ---------------------------------------------------------------- R5: what each digest covers
g = parsed[0] if parsed and parsed[0] else None
if g:
    row8 = [r for r in g["rows"] if r.startswith("sg 8 21 ")]
    rows2 = [r.replace("sg 8 21 ", "sg 8 22 ", 1) for r in g["rows"]]
    end2 = g["end"].replace("sgend result 0 ", "sgend result 1 ", 1)
    base = tried(lambda: (record.bind(FP, g["id"], g["opening"], g["sent"], g["rows"], g["end"]),
                          record.rows_digest(g["rows"], g["end"])))
    base = base[1] if base[0] == "returned" else (None, None)
    var = tried(lambda: {
        "id": (record.bind(FP, "n12-w001-g00000007", g["opening"], g["sent"], g["rows"], g["end"]), record.rows_digest(g["rows"], g["end"])),
        "opening": (record.bind(FP, g["id"], g["opening"][:-1] + ["a2a3"], g["sent"], g["rows"], g["end"]),
                    record.rows_digest(g["rows"], g["end"])),
        "score": (record.bind(FP, g["id"], g["opening"], g["sent"], rows2, g["end"]), record.rows_digest(rows2, g["end"])),
        "result": (record.bind(FP, g["id"], g["opening"], g["sent"], g["rows"], end2), record.rows_digest(g["rows"], end2))})
    v = var[1] if var[0] == "returned" else {}
    check("R5 another id or another opening: another binding, the SAME rows digest; another score or another result: both change",
          var[0] == "returned" and row8 and rows2 != g["rows"] and end2 != g["end"]
          and v["id"][0] != base[0] and v["id"][1] == base[1] and v["opening"][0] != base[0] and v["opening"][1] == base[1]
          and v["score"][0] != base[0] and v["score"][1] != base[1] and v["result"][0] != base[0] and v["result"][1] != base[1]
          and len({base[0], v["id"][0], v["opening"][0], v["score"][0], v["result"][0]}) == 5, str(var)[:300])
else:
    check("R5 another id or another opening: another binding, the SAME rows digest; another score or another result: both change",
          False, "the first positive did not parse")

# ---------------------------------------------------------------- R6: bytes and structure, the PC's own cases
lines = one.split(b"\n")[:-1] if one else [b""] * 6
game_ln, sent_ln, row1, end_ln, bind_ln = (lines[0], lines[1], lines[2], lines[-2], lines[-1]) if len(lines) > 5 else (b"",) * 5


def rebound(body_lines) -> bytes:
    """A record of these lines with the binding of exactly these bytes: valid by its binding, so that the check
    under test is the one that has to refuse it."""
    REBOUND.append(1)
    body = b"".join(ln + b"\n" for ln in body_lines)
    return body + b"bind " + hashlib.sha256(b"forge-serverday-bind-2\n" + FP.encode() + b"\n" + body).hexdigest().encode() + b"\n"


REBOUND: list = []
mid = lines[1:-1]
OWN = [
    ("a NUL byte inside a row", one.replace(b" ", b"\x00", 1), "bytes"),
    ("a tab in place of a space", one.replace(b" ", b"\t", 1), "bytes"),
    ("a DEL byte", one[:40] + b"\x7f" + one[40:], "bytes"),
    ("a byte above 0x7e", one[:40] + b"\xc3" + one[40:], "bytes"),
    ("an empty line before the record", b"\n" + one, "blank"),
    ("an empty line after the record", one + b"\n", "blank"),
    ("an empty line inside the record, with the binding of those bytes", rebound([game_ln, sent_ln, b""] + lines[2:-1]), "blank"),
    ("the record cut after its end line (no bind line)", b"".join(ln + b"\n" for ln in lines[:-1]), "structure"),
    ("a record that starts with its sent line", b"".join(ln + b"\n" for ln in lines[1:]), "structure"),
    ("two sent lines", rebound([game_ln, sent_ln, sent_ln] + lines[2:-1]), "structure"),
    ("no sent line", rebound([game_ln] + lines[2:-1]), "structure"),
    ("a row after the end line", rebound(lines[:-1] + [row1]), "structure"),
    ("two end lines", rebound(lines[:-1] + [end_ln]), "structure"),
    ("a second game line before the first is closed", rebound([game_ln, sent_ln, game_ln] + lines[2:-1]), "structure"),
    ("a line of no kind", rebound([game_ln, sent_ln, b"info depth 1"] + lines[2:-1]), "structure"),
    ("a bind line of 63 digits", one[:-2] + b"\n", "structure"),
    ("a bind line in upper case", one[:-65] + one[-65:-1].upper() + b"\n", "structure"),
    ("a game line with a space at its end", rebound([game_ln + b" "] + mid), "structure"),
    ("a game line with two spaces", rebound([game_ln.replace(b" opening ", b"  opening ", 1)] + mid), "structure"),
    ("an opening move that is not a move", rebound([game_ln[:-4] + b"e2e9"] + mid), "structure"),
    ("a game line without the word opening", rebound([game_ln.replace(b" opening", b" opened", 1)] + mid), "structure"),
    ("an id of two parts", rebound([game_ln.replace(b"-w001-", b"w001-", 1)] + mid), "id"),
    ("a run name of 33 characters", rebound([game_ln.replace(b"n12-", b"a" * 33 + b"-", 1)] + mid), "run"),
    ("a slot of two digits", rebound([game_ln.replace(b"-w001-", b"-w01-", 1)] + mid), "slot"),
    ("a counter of nine digits", rebound([game_ln.replace(b"-g00000001", b"-g000000001", 1)] + mid), "counter"),
    ("a row cut after its move", rebound([game_ln, sent_ln, b" ".join(row1.split(b" ")[:4])] + lines[3:-1]), "row"),
    ("a row with two spaces", rebound([game_ln, sent_ln, row1.replace(b" ", b"  ", 1)] + lines[3:-1]), "row"),
    ("a row with a space at its end", rebound([game_ln, sent_ln, row1 + b" "] + lines[3:-1]), "row"),
    ("a row whose score is not a number", rebound([game_ln, sent_ln, row1.replace(b" ", b" x", 2).replace(b" x", b" ", 1)] + lines[3:-1]), "row"),
    ("an end line with an unknown reason", rebound(lines[:-2] + [end_ln.replace(b" reason ", b" reason resign", 1)]), "end"),
    ("an end line with result 2", rebound(lines[:-2] + [end_ln.replace(b"sgend result 0", b"sgend result 2", 1)]), "end"),
    ("an end line cut before its moves", rebound(lines[:-2] + [end_ln.split(b" moves")[0]]), "end"),
    ("an opening end with a text behind it", rebound([game_ln, b"sent none", b"openingend plies 8 reason nomoves now"]), "end"),
]
slips = []
for name, data, want in OWN:
    how, text = tried(lambda: record.parse(data, FP))
    if how != want:
        slips.append((name, want, how, str(text)[:80]))
check(f"R6 each of {len(OWN)} damaged byte streams is refused, by the check named for it ({len(REBOUND)} of them carry the "
      "binding of their own bytes, so the binding cannot be what refuses them)", one and not slips, slips[:5])
empty = tried(lambda: record.parse(b"", FP))
check("R6 no bytes at all are no records (an empty list), not an error", empty == ("returned", []), empty)

# ---------------------------------------------------------------- R7: the writer cannot write what a reader refuses
if g:
    a = (g["id"], g["opening"], g["sent"], g["rows"], g["end"])
    BADPARTS = [
        ("an id in upper case", ("N12-w001-g00000001",) + a[1:], "run"), ("a counter of 0", ("n12-w001-g00000000",) + a[1:], "counter"),
        ("a slot of four digits", ("n12-w0001-g00000001",) + a[1:], "slot"), ("an id that is a number", (17,) + a[1:], "id"),
        ("an opening move with a line break", (a[0], a[1][:-1] + ["e2e4\n"]) + a[2:], "structure"),
        ("an opening that is one text", (a[0], "e2e4 e7e5") + a[2:], "structure"),
        ("an empty sent line", a[:2] + ("",) + a[3:], "structure"), ("a sent line with a line break", a[:2] + (a[2] + "\nsg",) + a[3:], "structure"),
        ("a sent line with a character outside ASCII", a[:2] + (a[2] + "é",) + a[3:], "structure"),
        ("a row with a line break and a second row inside", a[:3] + ([a[3][0] + "\n" + a[3][1]] + a[3][2:],) + a[4:], "row"),
        ("a row that is cut", a[:3] + ([a[3][0][:20]] + a[3][1:],) + a[4:], "row"),
        ("an end line with a line break", a[:4] + (a[4] + "\n",), "end"), ("an end line of no kind", a[:4] + ("sgerror noscore",), "end"),
    ]
    slips = []
    for name, parts, want in BADPARTS:
        for fn in (record.text, record.bind):
            how, text = tried(lambda: fn(FP, *parts))
            if how != want:
                slips.append((name, fn.__name__, want, how, str(text)[:60]))
    how = [tried(lambda v=v: record.text(v, *a))[0] for v in ("A" * 64, "a" * 65, None)]
    check(f"R7 text() and bind() refuse each of {len(BADPARTS)} bad parts by the check named for it, and a bad run fingerprint",
          not slips and how == ["run-fingerprint"] * 3, (slips[:4], how))
else:
    check("R7 text() and bind() refuse each bad part", False, "the first positive did not parse")

# ---------------------------------------------------------------- R8: the meaning of one record
if g:
    def made(opening, sent, rows, end):
        return record.parse(record.text(FP, g["id"], opening, sent, rows, end).encode("ascii"), FP)[0]
    swapped = g["opening"][:-1] + ["a2a3"]
    r8 = tried(lambda: {
        "clean": record.faults(made(g["opening"], g["sent"], g["rows"], g["end"])),
        "clean, reserved": record.faults(made(g["opening"], g["sent"], g["rows"], g["end"]), reserved=list(g["opening"])),
        "another opening, the old sent line": record.faults(made(swapped, g["sent"], g["rows"], g["end"])),
        "sent line with two spaces": record.faults(made(g["opening"], g["sent"].replace(" moves ", "  moves ", 1), g["rows"], g["end"])),
        "not the reserved opening": record.faults(made(g["opening"], g["sent"], g["rows"], g["end"]), reserved=swapped),
        "opening end, clean": record.faults(made(g["opening"][:5], "none", [], "openingend plies 5 reason nomoves")),
        "opening end with rows": record.faults(made(g["opening"][:5], "none", g["rows"][:1], "openingend plies 5 reason nomoves")),
        "opening end with a sent line": record.faults(made(g["opening"][:5], g["sent"], [], "openingend plies 5 reason nomoves")),
        "opening end of another length": record.faults(made(g["opening"][:5], "none", [], "openingend plies 7 reason nomoves")),
        "a played game with `sent none`": record.faults(made(g["opening"], "none", g["rows"], g["end"]))})
    v = r8[1] if r8[0] == "returned" else {}
    check("R8 faults(): nothing in the clean record, the clean reserved one and the clean opening end; one or more named faults in "
          "each of the seven others",
          r8[0] == "returned" and v["clean"] == [] and v["clean, reserved"] == [] and v["opening end, clean"] == []
          and all(len(v[k]) >= 1 for k in v if k not in ("clean", "clean, reserved", "opening end, clean")) and len(v) == 10,
          str(r8)[:400])
else:
    check("R8 faults()", False, "the first positive did not parse")

# ---------------------------------------------------------------- R9: one shape in two tables
rows_all = [r for q in ok for r in q["rows"]]
ends_all = [q["end"] for q in ok if q["end"].startswith("sgend ")]
both = tried(lambda: [ln for ln in rows_all + ends_all if engine_lines.why_not(ln)])
ODD = ["sg 8 21 e2e4", "sg 8 21 e2e4 rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0", "sg 8  21 e2e4 8/8/8/8/8/8/8/8 w - - 0 1",
       "sgend result 0 reason rule plies 8 run 0 searches 0 nodes 0 fen 8/8/8/8/8/8/8/8 w - - 0 1", "sgend result 0 reason rule"]
odd = tried(lambda: [ln for ln in ODD if not engine_lines.why_not(ln) or record.ROW.fullmatch(ln) or record.END.fullmatch(ln)])
check("R9 all 1,139 rows and the engine end lines of the fixture pass the driver's table too, and five cut lines are refused by both",
      len(rows_all) == 1139 and len(ends_all) >= 8 and both == ("returned", []) and odd == ("returned", []), (str(both)[:200], str(odd)[:200]))

bad = [n for n, ok_ in results if not ok_]
print(f"\n{len(results) - len(bad)} of {len(results)} checks pass")
if bad:
    print("FAILED: " + "; ".join(n[:90] for n in bad))
    sys.exit(1)
print(f"ALL {len(results)} CHECKS PASS")
