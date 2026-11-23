# Evidence for A1 (Astra): one whole production round through the packed game file and back

Measured by Fable on the owner's PC, 23 November 2026, 02:54:54 to 02:56:44 PC clock (110 seconds, one thread,
beside the running loop). No expectation was written on the branch before the run; the result is reported as
measured.

## What the files are

- The loop's self-play writes text rows (`fen`, `move`, `score`, `ply`, `result`). The filter writes
  `filtered.plain`: EVERY written row in its order; a row the filter drops keeps its place and gets the score
  32002 (the trainer skips it). The trainer reads this text file.
- The same raw rows are also packed by the official Stockfish tools converter into `raw_selfplay.binpack`
  ("the engine's own game record" of P3b: moves and scores, positions rebuilt from them), and the raw text is
  then deleted. Until today nothing in the running loop read that packed file back.
- Round 136: 16,005,930 rows, 15,255,460 kept by the filter; `raw_selfplay.binpack` 32,207,496 bytes
  (2.01 bytes a row); `filtered.plain` 1,521,042,727 bytes.

## The test

`a1_roundtrip.py` (below): unpack the packed file with the same converter, then compare with `filtered.plain`
row by row in order: `fen` (all six fields), `move`, `ply`, `result` on every row, `score` on every row that is
not marked 32002. Control: the first 20,000 rows of both, with ONE game-final row's move changed in the unpacked
copy; the comparison must report exactly that row.

## Raw result (the tool's JSON, paths shortened)

```
"binpack_bytes": 32207496,
"rebuilt_bytes": 1615471077,
"full_round": {
  "rows": 16005930,
  "marked_32002": 750470,
  "game_final_rows": 124849,
  "diff": {"fen": 0, "move": 0, "score": 0, "ply": 0, "result": 0},
  "first": [],
  "rebuilt_has_more_rows": false
},
"control_one_changed_final_move": {
  "rows": 20000, "marked_32002": 753, "game_final_rows": 158,
  "diff": {"fen": 0, "move": 1, "score": 0, "ply": 0, "result": 0},
  "first": [{"row": 167, "field": "move", "oracle": "c4e5", "rebuilt": "a1a2"}],
  "planted_row": 167
},
"control_caught": true,
"PASS": true
```

## What it shows, and its limits

- All 16,005,930 rows come back in order with equal position (six FEN fields), move, ply and result; the score
  is equal on all 15,255,460 rows whose score the oracle still holds.
- 124,849 rows are the last row of a game ("game_final_rows": a row followed by a row whose ply is not higher).
  Their moves are equal too. About a third of the games are drawn, most by adjudication: those are the rows
  whose best move was never played (Astra's case). The format keeps each row's own move.
- Astra's own fixture (one row, `e2e4` from the start position, never played, result 0) through the same
  converter and back: 42 bytes packed, comes back EQUAL (`a1_fixture.py`, below).
- LIMIT 1: on the 750,470 rows the filter marked (4.69 %) the original score is gone from the oracle, so their
  score is not compared. It needs one run whose raw text is kept (in the rehearsal).
- LIMIT 2: the unpacked text has Windows line ends (it is 94,428,350 bytes longer; fields equal). A checksum of
  the TEXT therefore differs between a Windows and a Linux unpack of the same packed file. The transfer check
  must hash the packed pieces, and the content check must compare fields, as this tool does.
- LIMIT 3: this is the PC's converter (Windows build). The server's Linux build of the same converter is not
  tested here.
- Not shown here: anything about transport (pieces, checksums, re-sending). That is the rest of A1.

## The tool (`a1_roundtrip.py`), as run

```python
import json, sys
from pathlib import Path
sys.path.insert(0, "C:/nnue-lab/pipeline")
from nnloop.common import load_config
from nnloop.filterqc import tools_convert        # the loop's own call of the official converter

cfg_path, binpack, oracle, work, out = (Path(a) for a in sys.argv[1:6])
assert not out.exists() and not work.exists(), "give a new work folder and a new out file"
work.mkdir(parents=True)
KEYS = ("fen ", "move ", "score ", "ply ", "result ")

def rows(path):
    with open(path, "r", encoding="ascii", newline="\n") as f:
        while True:
            rec = [f.readline() for _ in range(6)]
            if not rec[0]:
                return
            assert all(r.startswith(k) for r, k in zip(rec, KEYS)) and rec[5].strip() == "e", rec
            yield tuple(r[len(k):].rstrip() for r, k in zip(rec, KEYS))

def compare(a_path, b_path):       # a = the oracle (may carry 32002 marks), b = the rebuilt file
    res = {"rows": 0, "marked_32002": 0, "game_final_rows": 0, "diff": {k.strip(): 0 for k in KEYS}, "first": []}
    a, b = rows(a_path), rows(b_path)
    prev_ply = None
    for ra in a:
        rb = next(b, None)
        if rb is None:
            res["rebuilt_is_short"] = True
            break
        res["rows"] += 1
        if prev_ply is not None and int(ra[3]) <= prev_ply:
            res["game_final_rows"] += 1
        prev_ply = int(ra[3])
        for i, k in enumerate(KEYS):
            if i == 2 and ra[2] == "32002":
                continue
            if ra[i] != rb[i]:
                res["diff"][k.strip()] += 1
                if len(res["first"]) < 5:
                    res["first"].append({"row": res["rows"], "field": k.strip(), "oracle": ra[i], "rebuilt": rb[i]})
        res["marked_32002"] += ra[2] == "32002"
    res["rebuilt_has_more_rows"] = next(b, None) is not None
    return res

rebuilt = work / "rebuilt.plain"
tools_convert(load_config(str(cfg_path)), binpack, rebuilt, work / "convert.log")
full = compare(oracle, rebuilt)
# control: first 20,000 rows of both; in the rebuilt copy the move of the first game-final row is changed
head_a, head_b = work / "head_oracle.plain", work / "head_planted.plain"
planted_row = None
with open(head_a, "w", encoding="ascii", newline="\n") as fa, open(head_b, "w", encoding="ascii", newline="\n") as fb:
    block = list(zip(range(20000), rows(oracle), rows(rebuilt)))
    for n, ra, rb in block:
        if planted_row is None and n + 1 < len(block) and int(block[n + 1][1][3]) <= int(ra[3]):
            planted_row = n + 1
            rb = (rb[0], "a1a2" if rb[1] != "a1a2" else "a1a3", *rb[2:])
        for r, f in ((ra, fa), (rb, fb)):
            f.write("".join(k + v + "\n" for k, v in zip(KEYS, r)) + "e\n")
control = compare(head_a, head_b)
control["planted_row"] = planted_row
ok_control = (control["diff"]["move"] == 1 and sum(control["diff"].values()) == 1
              and control["first"][0]["row"] == planted_row)
```

## Astra's fixture (`a1_fixture.py`), raw output

```
packed bytes: 42
back: fen rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1 | move e2e4 | score 24 | ply 0 | result 0 | e |
EQUAL
```
