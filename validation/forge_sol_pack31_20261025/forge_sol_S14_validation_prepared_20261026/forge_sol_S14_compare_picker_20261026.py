"""Compare S14 diagnostic streams structurally, without authenticating native runs.

The input can be a synthetic fixture. A PASS here is never evidence that a
compiler/engine ran, that C-family allocations were absent, or that speed grew.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re

MAX_BYTES = 1 << 20
CONTROLS = ("new", "new_array", "new_aligned", "new_array_aligned", "new_nothrow",
            "new_array_nothrow", "new_aligned_nothrow", "new_array_aligned_nothrow")


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def integer(value):
    require(re.fullmatch(r"[0-9]+", value) is not None, "invalid unsigned integer")
    number = int(value)
    require(number <= (1 << 64) - 1, "integer too large")
    return number


def parse_stream(raw, expected):
    require(isinstance(raw, bytes) and 0 < len(raw) <= MAX_BYTES, "stream byte bound")
    require(raw.endswith(b"\n") and b"\r" not in raw and b"\0" not in raw,
            "complete LF stream with final newline required")
    try:
        lines = raw.decode("ascii").splitlines()
    except UnicodeError as error:
        raise ValueError("stream must be ASCII") from error
    cases, modes = expected["workload"], expected["modes"]
    require(len(cases) == 20 and len(modes) == 6 and len(set(modes)) == 6,
            "binding must define20 cases and6 distinct modes")
    count = len(cases) * len(modes)
    require(len(lines) == 1 + len(CONTROLS) + count + 1, "exact line count/complete EOF required")
    header = lines[0].split("\t")
    require(len(header) == 10 and header[0] == "FORGE_S14_PICKER_V1", "stream header")
    role = header[1]
    require(role in expected["bases"], "unknown source role")
    base = expected["bases"][role]
    require(header[2] == base["source_inventory"]["src/search.cpp"]["sha256"], "source hash mismatch")
    require(header[3] == base["core_sha256"], "core hash mismatch")
    require(header[4] == expected["workload_tsv_sha256"], "workload hash mismatch")
    require(header[5] == expected["allocation_coverage"], "allocation coverage declaration mismatch")
    require(header[6:9] == ["20", "6", "64"], "stream dimensions mismatch")
    require(header[9] == "NORMAL", "negative diagnostic mode cannot pass")
    for line, name in zip(lines[1:9], CONTROLS):
        require(line.split("\t") == ["CONTROL", name, "1", "32", "1"],
                "allocation positive control failed: " + name)
    records = []
    mailbox = 20
    windows = count
    for i, line in enumerate(lines[9:-1]):
        fields = line.split("\t")
        require(len(fields) == 14 and fields[0] == "PICK", "picker record fields")
        case_id, mode_id = divmod(i, len(modes))
        case = cases[case_id]
        require(fields[1:5] == [str(case_id), case["id"], modes[mode_id], case["fen"]],
                "case/mode/FEN order differs from binding")
        total, legal_total, ended, ctor, nxt, ctor_bytes, next_bytes = map(integer, fields[7:14])
        require(total <= 256 and legal_total <= total and ended == 1, "picker count/terminator")
        moves = fields[5].split(",") if fields[5] else []
        require(len(moves) == min(total, 64) and len(fields[6]) == len(moves), "prefix length mismatch")
        require(all(re.fullmatch(r"[a-h][1-8][a-h][1-8][qrbn]?", move) and move[:2] != move[2:4]
                    for move in moves), "invalid move spelling")
        require(len(set(moves)) == len(moves), "duplicate prefix move")
        require(all(c in "LI" for c in fields[6]), "invalid legality marker")
        prefix_legal = fields[6].count("L")
        require(prefix_legal <= legal_total <= prefix_legal + total - len(moves), "legal prefix accounting")
        require((ctor, nxt, ctor_bytes, next_bytes) == (0, 0, 0, 0),
                "observed C++ allocation entry in picker window")
        mailbox += 2 * legal_total
        windows += total + 1
        records.append(fields[1:])
    done = lines[-1].split("\t")
    require(len(done) == 5 and done[:3] == ["DONE", "20", "120"], "final summary")
    require(integer(done[3]) == mailbox, "mailbox accounting mismatch")
    require(integer(done[4]) == windows, "allocation window accounting mismatch")
    return {"role": role, "records": records, "mailbox_checks": mailbox,
            "allocation_windows": windows, "sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw)}


def compare_streams(left, right, expected):
    a, b = parse_stream(left, expected), parse_stream(right, expected)
    require(a["role"] != b["role"] and {a["role"], b["role"]} == {"Lprime", "B"},
            "comparison requires distinct existing Lprime and B baselines")
    require(a["records"] == b["records"], "picker prefix/count/legality records differ")
    return {"status": "PASS_STRUCTURAL_BASELINE_COMPARISON", "record_pairs": len(a["records"]),
            "positions": 20, "modes": 6, "maximum_prefix_picks": 64,
            "comparison_kind": "EXISTING_LPRIME_VS_B_BASELINES; NO_ENGINE_CANDIDATE",
            "reported_cpp_allocation_entry_calls_in_windows": 0,
            "allocation_coverage": expected["allocation_coverage"],
            "native_producer_authentication": "NOT_CHECKED",
            "speed_strength": "UNVERIFIED; NOT_MEASURED_BY_THIS_TOOL",
            "left": {k: v for k, v in a.items() if k != "records"},
            "right": {k: v for k, v in b.items() if k != "records"}}


def read_bounded(path):
    path = Path(path)
    require(path.is_file() and not path.is_symlink() and path.stat().st_size <= MAX_BYTES,
            "regular bounded stream file required")
    with path.open("rb") as stream:
        raw = stream.read(MAX_BYTES + 1)
    require(len(raw) <= MAX_BYTES, "stream grew beyond byte bound")
    return raw


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--left", type=Path, required=True)
    ap.add_argument("--right", type=Path, required=True)
    ap.add_argument("--bindings", type=Path, default=Path(__file__).with_name("forge_sol_S14_source_bindings_20261026.json"))
    ap.add_argument("--new-out", type=Path, required=True)
    args = ap.parse_args()
    try:
        require(not args.new_out.exists(), "refuse existing output directory")
        expected = json.loads(args.bindings.read_text())
        result = compare_streams(read_bounded(args.left), read_bounded(args.right), expected)
        result["bindings_sha256"] = hashlib.sha256(args.bindings.read_bytes()).hexdigest()
        args.new_out.mkdir(parents=True, exist_ok=False)
        target = args.new_out / "forge_sol_S14_structural_comparison_20261026.json"
        with target.open("x") as f:
            json.dump(result, f, indent=2); f.write("\n")
        print("PASS structural comparison only; native producer authentication NOT_CHECKED")
        return 0
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        ap.exit(1, "S14 compare: " + str(error) + "\n")


if __name__ == "__main__":
    raise SystemExit(main())
