#!/usr/bin/env python3
"""Recount Job 30 games with the independent full UCI parser from Job 28."""

import argparse
import json
from pathlib import Path
import sys

here = Path(__file__).resolve().parent.parent
for candidate in (here / 'job28', here / 'sol-job28'):
    if (candidate / 'independent_matches28.py').is_file():
        sys.path.insert(0, str(candidate))
        break
else:
    raise SystemExit('Missing adjacent Job 28 independent parser')

from independent_matches28 import check

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('raw', type=Path)
parser.add_argument('manifest', type=Path)
parser.add_argument('match', choices=('K19', 'M3', 'M4'))
parser.add_argument('--pgn', type=Path)
args = parser.parse_args()
try:
    check(args.raw, json.loads(args.manifest.read_bytes()), args.match, args.pgn)
except (OSError, KeyError, TypeError, ValueError) as error:
    raise SystemExit(str(error)) from error
