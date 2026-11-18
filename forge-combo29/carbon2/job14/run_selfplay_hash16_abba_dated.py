#!/usr/bin/env python3
"""
Wrapper around job8/run_selfplay_hash16_abba.py that ensures every timing raw file
opens with a verbatim `date -u` line and closes with a verbatim `date -u` line
(per FABLE_TO_carbon2_14.md Evidence Rules).
"""
from __future__ import annotations

import pathlib
import subprocess
import sys


def main() -> int:
    # Extract --out argument
    argv = sys.argv[1:]
    out_idx = argv.index("--out") + 1
    out_path = pathlib.Path(argv[out_idx])
    tmp_out = out_path.with_suffix(".body.tmp")
    inner_argv = list(argv)
    inner_argv[out_idx] = str(tmp_out)

    start_utc = subprocess.check_output(["date", "-u"], text=True).strip()
    out_path.write_text(f"START_UTC: {start_utc}\n")
    print(f"START_UTC: {start_utc}", flush=True)

    driver = pathlib.Path(__file__).resolve().parent.parent / "job8/run_selfplay_hash16_abba.py"
    rc = subprocess.call([sys.executable, str(driver)] + inner_argv)
    if rc != 0:
        return rc

    end_utc = subprocess.check_output(["date", "-u"], text=True).strip()
    body = tmp_out.read_text()
    tmp_out.unlink(missing_ok=True)
    out_path.write_text(f"START_UTC: {start_utc}\n{body}END_UTC: {end_utc}\n")
    print(f"END_UTC: {end_utc}", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
