#!/usr/bin/env python3
"""Regression: OwnBook=false suppresses a loaded external Polyglot move."""
from pathlib import Path
import hashlib
import json
import sys
import tempfile

ROOT = Path('/workspace/.cloud-setup/forge-windows-nnue-update-source')
sys.path.insert(0, str(ROOT))
from tools.uci_regression import Engine

def run(binary, logfile):
    checks = []
    e = Engine(binary)
    error = None
    try:
        e.send("uci")
        e.until(lambda line: line == "uciok")
        e.ready()
        with tempfile.TemporaryDirectory(prefix="forge-ownbook-") as directory:
            book = Path(directory) / "external book.bin"
            book.write_bytes(bytes.fromhex("463b96181691fc9c031c000100000000"))
            book_sent = "Z:" + str(book).replace("/", "\\")
            e.send("setoption name Book File value " + book_sent)
            loaded = e.until(lambda row: row.startswith("info string loaded book ") or
                             row.startswith("info string cannot load book "))
            assert loaded[-1] == f"info string loaded book {book_sent} with 1 entries", loaded
            e.send("setoption name Book Depth value 30")
            e.send("setoption name Book Variety value 0")
            for setting, expected in ((True, True), (False, False), (True, True), (False, False), (True, True)):
                if len(checks) == 3:
                    e.send("setoption name OwnBook value false")
                    e.send("setoption name Book File value " + book_sent)
                    loaded = e.until(lambda row: row.startswith("info string loaded book ") or
                                     row.startswith("info string cannot load book "))
                    assert loaded[-1] == f"info string loaded book {book_sent} with 1 entries", loaded
                else:
                    e.send("setoption name OwnBook value " + str(setting).lower())
                e.ready()
                e.position()
                best, lines = e.search("go movetime 400")
                book_used = any(row.startswith("info string book move ") for row in lines)
                assert book_used == expected, (setting, best, lines)
                if expected:
                    assert best == "e2e4", (setting, best, lines)
                else:
                    assert best != "0000" and any(row.startswith("info depth ") for row in lines), (setting, best, lines)
                checks.append({"OwnBook": setting, "expected_book": expected, "actual_book": book_used, "PASS": True})
    except Exception as exc:
        error = repr(exc)
    finally:
        try:
            e.close()
        except Exception as exc:
            error = (error or "") + "; close: " + repr(exc)
        output = {"engine": str(binary), "engine_sha256": hashlib.sha256(binary.read_bytes()).hexdigest(),
                  "checks": checks, "error": error, "raw_uci_transcript": e.transcript}
        logfile.parent.mkdir(parents=True, exist_ok=True)
        logfile.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    if error:
        raise RuntimeError(error)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        raise SystemExit("Usage: python test_ownbook_external.py PATH_TO_ENGINE PATH_TO_OUTPUT_JSON")
    run(Path(sys.argv[1]).resolve(), Path(sys.argv[2]))
