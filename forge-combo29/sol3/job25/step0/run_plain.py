"""Re-run the pinned plain defaults with a fresh process per command."""
import argparse
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'job22'))
from pins19 import DEFAULT, run_pin

cli = argparse.ArgumentParser(description=__doc__)
cli.add_argument('engine', type=Path)
cli.add_argument('output', type=Path)
args = cli.parse_args()
args.output.mkdir(parents=True, exist_ok=False)
results = [run_pin(args.engine, args.output, 'default', command, pin, None) for command, pin in DEFAULT]
raise SystemExit(int(not all(results)))
