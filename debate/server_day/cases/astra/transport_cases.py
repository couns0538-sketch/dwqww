"""Four offline restart cases for Forge's a5c74106 server-day scripts.

Usage: python transport_cases.py --scripts PATH 13  (or 14, 15, 16).
Exit 0: expected outcome. Exit 1: violated invariant. Exit 2: prerequisite or
baseline setup unavailable. Every invocation creates and cleans one temporary
directory. Cases 14–16 require python-chess in the invoking interpreter.
"""

import argparse
import hashlib
import importlib.util
import json
import lzma
import os
import subprocess
import sys
import tempfile
from unittest.mock import patch
from pathlib import Path


# Two legal eight-ply openings; a one-row synthetic score resignation follows.
GAMES = [
    ("e2e4 e7e5 g1f3 b8c6 f1b5 a7a6 b5a4 g8f6",
     "r1bqkb1r/1ppp1ppp/p1n2n2/4p3/B3P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 2 5", "a2a3"),
    ("d2d4 d7d5 c2c4 e7e6 b1c3 g8f6 c1g5 f8e7",
     "rnbqk2r/ppp1bppp/4pn2/3p2B1/2PP4/2N5/PP2PPPP/R2QKBNR w KQkq - 4 5", "a1b1"),
]


class SetupError(Exception):
    pass


def sha(blob):
    return hashlib.sha256(blob).hexdigest()


def dump(path, blob):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(blob)


def ledger(path):
    return [json.loads(s) for s in path.read_text().splitlines()] if path.is_file() else []


def game(n):
    opening, fen, move = GAMES[n - 1]
    gid = f"trial-w001-g{n:08}"
    sent = "position startpos moves " + opening
    row = f"sg 8 2100 {move} {fen}"
    end = f"sgend result 1 reason score plies 9 run 1 searches 1 nodes 2000 moves {move}"
    bind = sha(("\n".join([gid, sent, row, end]) + "\n").encode())
    return f"game {gid} opening {opening}\nsent {sent}\n{row}\n{end}\nbind {bind}\n".encode()


def plain(n):
    _, fen, move = GAMES[n - 1]
    return f"fen {fen}\nmove {move}\nscore 2100\nply 8\nresult 1\ne\n".encode()


def execute(script, *args):
    return subprocess.run([sys.executable, "-B", str(script), *map(str, args)],
                          cwd=script.parent, capture_output=True, text=True, timeout=30)


def baseline(result, label):
    if result.returncode:
        raise SetupError(f"{label}: exit {result.returncode}: {(result.stdout + result.stderr)[-400:]}")


class Trial:
    def __init__(self, scripts, root):
        self.scripts, self.root = scripts, root
        self.inbox, self.state = root / "inbox", root / "state"
        self.converter = root / "unavailable.py"
        self.converter.write_text("import sys\nprint('fixture: converter unavailable')\nsys.exit(69)\n")
        self.openings = root / "openings.txt"
        self.openings.write_text("\n".join(g[0] for g in GAMES) + "\n")

    def seal(self, spool, piece, n):
        raw = game(n)
        target = spool / "w001" / "closed" / (piece + ".raw")
        dump(target, raw)
        dump(target.with_suffix(".sha256"), f"{sha(raw)}  {target.name}\n".encode())

    def pack(self, spool, out):
        return execute(self.scripts / "run/packer.py", "--spool", spool, "--out", out,
                       "--converter", self.converter, "--once")

    def receive(self):
        return execute(self.scripts / "home/receiver.py", "--inbox", self.inbox, "--state", self.state,
                       "--converter", self.converter, "--root-seed", "trial", "--openings", self.openings)

    def initial(self, count):
        spool = self.root / "spool"
        for n in range(1, count + 1):
            self.seal(spool, f"p{n - 1:06}", n)
        baseline(self.pack(spool, self.inbox), "baseline rawxz packing")
        baseline(self.receive(), "baseline receive")
        if len(ledger(self.state / "credited.jsonl")) != count:
            raise SetupError("valid baseline games did not receive one ledger entry each")


def inventory(t):
    spool = t.root / "spool"
    index = t.inbox / "PIECES.txt"
    t.seal(spool, "p000000", 1)
    baseline(t.pack(spool, t.inbox), "first inventory entry")
    first = index.read_bytes()
    t.seal(spool, "p000001", 2)
    baseline(t.pack(spool, t.inbox), "second seal")
    # Exact on-disk image after the second .packed rename, before its index append.
    index.write_bytes(first)
    status = [t.pack(spool, t.inbox).returncode for _ in range(2)]
    keys = [ln.split()[0] for ln in index.read_text().splitlines() if ln.strip()]
    physical = sorted(p.parent.name + "/" + p.stem for p in t.inbox.glob("w*/p*.packed"))
    expected = ["w001/p000000", "w001/p000001"]
    return (status == [0, 0] and physical == expected and sorted(keys) == expected,
            {"restart_exits": status, "physical_seals": physical, "listed": keys},
            "Both seals remain, and after two successful restarts each is indexed exactly once.")


def retained(state, raw):
    for p in state.rglob("*"):
        if not p.is_file():
            continue
        blob = p.read_bytes()
        if blob == raw or (blob.startswith(b"\xfd7zXZ\x00") and lzma.decompress(blob) == raw):
            return True
    return False


def missing_before_ack(t):
    t.initial(1)
    raw = t.state / "raw/w001/p000000.raw"
    ack = t.state / "confirmed/w001/p000000.confirmed"
    # Lose the retained raw and ACK on restart; the exact incoming offer is still present.
    raw.rename(t.root / "offline-original")
    ack.unlink()
    retry = t.receive()
    custody = retained(t.state, game(1))
    asked = (t.state / "ask_again/w001/p000000.txt").exists()
    receipt = ack.read_text().split()[0] if ack.is_file() else None
    entries = ledger(t.state / "credited.jsonl")
    safe = ((receipt == sha(game(1)) and custody) if receipt else (asked or retry.returncode != 0))
    return (safe and len(entries) == 1,
            {"retry_exit": retry.returncode, "ack_digest": receipt, "matching_retained_bytes": custody,
             "asked_again": asked, "credited_entries": len(entries)},
            "Reissue an ACK only with durable matching bytes, or withhold it and request recovery. Credit stays at one.")


def changed_slot(t):
    t.initial(1)
    old = sha(game(1))
    other_spool, other_offer = t.root / "other-spool", t.root / "other-offer"
    t.seal(other_spool, "p000000", 2)
    baseline(t.pack(other_spool, other_offer), "independent alternate sealed offering")
    # A restored sender offers its other finished copy under the same slot/index.
    t.inbox.rename(t.root / "first-offer")
    other_offer.rename(t.inbox)
    retry = t.receive()
    entries = ledger(t.state / "credited.jsonl")
    receipts = ledger(t.state / "pieces.jsonl")
    hashes = sorted({p["raw_sha256"] for p in receipts if p["piece"] == "w001/p000000"})
    ack = t.state / "confirmed/w001/p000000.confirmed"
    ack_digest = ack.read_text().split()[0] if ack.is_file() else None
    reported = retry.returncode != 0 or any((t.state / p).exists() for p in
               ("ask_again/w001/p000000.txt", "quarantine", "quarantined.jsonl", "conflicts.jsonl"))
    original = retained(t.state, game(1))
    ok = reported and original and hashes == [old] and ack_digest in (old, None) and len(entries) == 1
    return (ok, {"retry_exit": retry.returncode, "conflict_reported": reported, "ack_digest": ack_digest,
                 "prior_custody": original, "accepted_seal_digests": hashes, "credited_entries": len(entries)},
            "Signal the changed sealed index, preserve its first object and accepted digest, and add no credit.")


def interrupted_round(t):
    t.initial(2)
    pipeline = t.root / "fixture-pipeline"
    pkg = pipeline / "nnloop"
    dump(pkg / "__init__.py", b"")
    # Test-only adapters return fixed options and format rows. Real to_round.py
    # owns the actual open/write/error/restart path; no PC filtering is tested.
    dump(pkg / "common.py", b"import json\ndef load_config(path):\n    return json.loads(path.read_text())\n")
    dump(pkg / "datagen_uci.py", (
        'LAST_ADJ = LAST_SKIP = None\n'
        'def _after_game(board, recs, result, by_limit, draw_adj, plies, settings):\n'
        '    text = "".join(f"fen {fen}\\nmove {move}\\nscore {score}\\nply {ply}\\nresult {result}\\ne\\n"\n'
        '                   for fen, move, score, ply, white in recs)\n'
        '    return text, len(recs), result, plies\n').encode())
    cfg = t.root / "fixture-settings.json"
    cfg.write_text(json.dumps({"datagen":{"soft_nodes":2000, "eval_limit":2000, "max_ply":300, "write_min_ply":8,
                                         "draw_adj_ply":80, "draw_adj_score":5, "draw_adj_count":8}}))
    out = t.root / "published"
    def publish(destination):
        return execute(t.scripts / "home/to_round.py", "--state", t.state, "--manifest",
                       t.scripts / "workloads/MANIFEST.json", "--config", cfg, "--pipeline", pipeline, "--out", destination)
    second = t.state / "raw/w001/p000001.raw"
    parked = t.root / "offline-second"
    clean = t.root / "clean-control"
    baseline(publish(clean), "clean round publication with both sources")
    if ((clean / "games.plain").read_bytes() != plain(1) + plain(2)
            or json.loads((clean / "report.json").read_text()).get("rows_written") != 2):
        raise SetupError("clean test-adapter publication did not reconstruct both known rows")
    second.rename(parked)
    interrupted = publish(out)
    output = out / "games.plain"
    visible = output.stat().st_size if output.is_file() else None
    partial = out.exists()
    parked.rename(second)
    restarted = publish(out)
    content = output.read_bytes() if output.is_file() else b""
    report = json.loads((out / "report.json").read_text()) if (out / "report.json").is_file() else {}
    ok = (interrupted.returncode != 0 and not partial and restarted.returncode == 0
          and content == plain(1) + plain(2) and report.get("rows_written") == 2)
    return (ok, {"adapter": "test-only fixed config / two synthetic rows; no PC filtering",
                 "clean_control_rows": 2, "interrupted_exit": interrupted.returncode, "published_path_after_failure": partial,
                 "interrupted_visible_bytes": visible, "same_destination_restart_exit": restarted.returncode,
                 "final_rows_reported": report.get("rows_written"), "final_bytes": len(content)},
            "A missing second source exposes no partial final destination; after restoration, retry publishes the two rows once.")


def main():
    args = argparse.ArgumentParser(description=__doc__)
    args.add_argument("--scripts", type=Path, required=True)
    args.add_argument("--work-dir", type=Path, help="parent directory for the private case folder")
    args.add_argument("case", type=int, choices=(13, 14, 15, 16))
    a = args.parse_args()
    scripts = a.scripts.resolve()
    required = ["run/packer.py", "run/record.py"]
    if a.case >= 14:
        required += ["home/receiver.py"]
        if importlib.util.find_spec("chess") is None:
            print("PREREQUISITE: python-chess in this interpreter")
            return 2
    if a.case == 16:
        required += ["home/to_round.py", "workloads/MANIFEST.json"]
    for path in required:
        if not (scripts / path).is_file():
            print("PREREQUISITE: missing", path)
            return 2
    cases = {13:inventory, 14:missing_before_ack, 15:changed_slot, 16:interrupted_round}
    try:
        if a.work_dir is not None:
            a.work_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=f"forge-case-{a.case}-", dir=a.work_dir) as tmp:
            child_tmp = str(Path(tmp).resolve())
            with patch.dict(os.environ, {"TMP": child_tmp, "TEMP": child_tmp, "TMPDIR": child_tmp}):
                ok, actual, expected = cases[a.case](Trial(scripts, Path(child_tmp)))
    except (SetupError, OSError, ValueError, subprocess.TimeoutExpired) as e:
        print("PREREQUISITE or fixture setup failed:", e)
        return 2
    print("EXPECTED", expected)
    print("ACTUAL", json.dumps(actual, sort_keys=True))
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
