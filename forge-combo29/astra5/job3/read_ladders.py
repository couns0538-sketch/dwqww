"""Reconstruct ladder results from saved UCI traffic, check TSV/meta, and print report tables."""
import argparse
import csv
from pathlib import Path
import sys


FEN = "2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1"
KNOWN = {
    "PC20": {1: ("f6h5", "cp", 78, 262), 7: ("f6h5", "cp", 465, 2358),
             11: ("f6h5", "cp", 653, 25366), 16: ("f6h5", "cp", 736, 182707)},
    "S14": {12: ("f6h5", "cp", 634, 39758), 15: ("f6h5", "cp", 721, 147253),
            16: ("g3g6", "mate", 2, 240516)},
}


def transcript(path):
    records, settings = [], []
    requested = None
    info = None
    newgame = ready_request = ready = positioned = False
    for line in path.read_text().splitlines():
        if line.startswith("> setoption "):
            settings.append(line[2:])
        elif line == "> ucinewgame":
            newgame, ready_request, ready, positioned = True, False, False, False
        elif line == "> isready" and newgame:
            ready_request = True
        elif line == "< readyok" and ready_request:
            ready = True
        elif line == "> position fen " + FEN and ready:
            positioned = True
        elif line.startswith("> go depth "):
            if not positioned or requested is not None:
                raise ValueError(f"{path.name}: unexpected search sequence: {line}")
            requested, info = int(line.split()[-1]), None
            newgame = ready_request = ready = positioned = False
        elif requested is not None and line.startswith("< info "):
            tokens = line[2:].split()
            if "depth" in tokens and "nodes" in tokens:
                info = line[2:]
        elif line.startswith("< bestmove "):
            if requested is None or info is None:
                raise ValueError(f"{path.name}: bestmove before go depth and last info")
            tokens = info.split()
            depth = int(tokens[tokens.index("depth") + 1])
            nodes = int(tokens[tokens.index("nodes") + 1])
            score_type, value = tokens[tokens.index("score") + 1:tokens.index("score") + 3]
            move = line.split()[2]
            mate = (move == "g3g6" and score_type == "mate" and int(value) > 0)
            records.append((requested, depth, move, score_type, int(value), nodes, int(mate), info))
            requested, info = None, None
    return records, settings


def audit(directory, label, max_depth, two=False):
    prefix = directory / label
    data, settings = transcript(prefix.with_suffix(".raw.txt"))
    meta = prefix.with_suffix(".meta").read_text().splitlines()
    if settings != [s for s in meta if s.startswith("setoption ")]:
        raise ValueError(f"{prefix}: settings transcript differs from metadata")
    with prefix.with_suffix(".tsv").open(newline="") as stream:
        tsv = list(csv.reader(stream, delimiter="\t"))
    if tsv[0] != ["requested_depth", "info_depth", "bestmove", "score_type", "score", "nodes", "mate_found", "info"]:
        raise ValueError(f"{prefix}: unexpected TSV header")
    if tsv[1:] != [[str(x) for x in row] for row in data]:
        raise ValueError(f"{prefix}: raw records differ from TSV")
    if f"completed_rows {len(data)}" not in meta or [r[0] for r in data] != list(range(1,len(data)+1)):
        raise ValueError(f"{prefix}: row count or depth sequence mismatch")
    hits = [r for r in data if r[6]]
    repeated = next((r[0] for p, r in zip(data, data[1:]) if p[6] and r[6]), None)
    complete = len(data) == max_depth or (two and repeated is not None and repeated == len(data))
    if not complete:
        raise ValueError(f"{prefix}: incomplete ladder through {len(data)}")
    return data, hits, repeated, settings


def baseline(root):
    audited = {s: audit(root / "step1", s, 20)[0] for s in ("PC20", "S14")}
    failures = []
    for label, known in KNOWN.items():
        for d, expected in known.items():
            raw = audited[label][d-1]
            observed = raw[2:6]
            if observed != expected:
                failures.append((label, d, expected, observed, raw[-1]))
    for label, d, expected, observed, line in failures:
        print(f"{label} d{d} reference {expected}, measured {observed}\n{line}")
    print(f"Step 1 known rows: {7-len(failures)}/7 equal. Both raw transcripts and metadata checked.\n")
    print("| Depth | PC20 move | PC20 score | PC20 nodes | S14 move | S14 score | S14 nodes |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for a,b in zip(audited["PC20"], audited["S14"]):
        print(f"| {a[0]} | {a[2]} | {a[3]} {a[4]} | {a[5]} | {b[2]} | {b[3]} {b[4]} | {b[5]} |")


def report_switches(root, manifest):
    with manifest.open() as stream:
        settings = {}
        for row in csv.DictReader(stream, delimiter="\t"):
            settings.setdefault(row["label"], []).append((row["name"], row["value"]))
    settings.update({"RfpTtGuard": [("RfpTtGuard", "1")], "RfpNoTtPv": [("RfpNoTtPv", "1")]})
    baseline_options = audit(root / "step1", "PC20", 20)[-1]
    results = []
    print("| Build | Switch | Value(s) after PC20 | First mate depth | Score | Nodes there | "
          "First consecutive pair | Depths read |")
    print("| --- | --- | --- | --- | --- | --- | --- | --- |")
    for label, overrides in settings.items():
        rows,hits,repeated,options = audit(root / "step3", label, 16, two=True)
        expected = baseline_options + [f"setoption name {n} value {v}" for n,v in overrides]
        if options != expected:
            raise ValueError(f"{label}: settings differ from expected switch override(s)")
        first = hits[0] if hits else None
        build = "PCA" if label in ("RfpTtGuard", "RfpNoTtPv") else "PC"
        settings_text = ", ".join(f"{n} {v}" for n,v in overrides)
        streak = f"{repeated-1}, {repeated}" if repeated is not None else "—"
        depth, score, nodes = (first[0], f"{first[3]} {first[4]}", first[5]) if first else ("not by 16", "—", "—")
        print(f"| {build} | {label} | {settings_text} | {depth} | {score} | {nodes} | {streak} | {len(rows)} |")
        if first:
            results.append((first[0], build, label))
    if results:
        earliest=min(x[0] for x in results)
        names = [f"{b} {s}" for d,b,s in results if d==earliest]
        print(f"\nEarliest confirmed positive mate score with g3g6 at D{earliest}: {', '.join(names)}.")
    else:
        print("\nNo switch produced a positive g3g6 mate score through D16.")


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["baseline","control","switches"])
    parser.add_argument("root", type=Path, help="directory containing step1/, control/ and step3/")
    parser.add_argument("manifest", type=Path, nargs="?", help="switch manifest for switches mode")
    args=parser.parse_args()
    if args.mode == "baseline":
        baseline(args.root)
    elif args.mode == "control":
        rows,hits,repeated,_ = audit(args.root / "control","all",20)
        print("| Depth | Best move | Score | Nodes |")
        print("| --- | --- | --- | --- |")
        for d,_,move,kind,value,nodes,_,_ in rows:
            print(f"| {d} | {move} | {kind} {value} | {nodes} |")
        print(f"\nFirst positive mate score with g3g6: {hits[0][0] if hits else 'not by 20'}. "
              f"First consecutive pair: {f'{repeated-1}, {repeated}' if repeated is not None else 'none'}.")
    elif args.manifest:
        report_switches(args.root,args.manifest)
    else:
        parser.error("switches requires the switch manifest")


if __name__ == "__main__":
    try:
        main()
    except (OSError,ValueError,IndexError) as exc:
        sys.exit(str(exc))
