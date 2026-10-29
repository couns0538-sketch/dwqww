#!/usr/bin/env python3
"""Write exact positive/negative Fastchess strict smoke commands; execute nothing.

IDEA_SOURCE: user A1 strict UCI smoke contract and official Fastchess CLI manual.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shlex
import sys


def sha256(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for b in iter(lambda: f.read(1024 * 1024), b''):
            h.update(b)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('engine', type=Path)
    p.add_argument('--fastchess', type=Path, default=Path('/tmp/astra3-tools/fastchess-src/fastchess'))
    p.add_argument('--out-dir', type=Path, required=True, help='new plan/evidence directory')
    args = p.parse_args()
    engine = args.engine.resolve(strict=True)
    runner = args.fastchess.resolve(strict=True)
    out = args.out_dir.resolve()
    out.mkdir(parents=True, exist_ok=False)
    cases = []
    for label, expected in [('positive', 0), ('unknown_option', 1)]:
        directory = out / label
        directory.mkdir()
        command = [str(runner), '-engine', 'cmd=' + str(engine), 'name=integration-A',
                   'option.BundlePreset=N1', 'option.CaptureFutilityBase=0']
        if label == 'unknown_option':
            command.append('option.Astra3UnknownOptionProbe=1')
        command += ['-engine', 'cmd=' + str(engine), 'name=integration-B',
                    'option.BundlePreset=N1', 'option.CaptureFutilityBase=0',
                    '-each', 'proto=uci', 'tc=5+0.05', 'option.Threads=1',
                    'option.Hash=16', 'option.OwnBook=false',
                    '-rounds', '1', '-games', '2', '-repeat', '-concurrency', '1',
                    '-maxmoves', '80', '-strict',
                    '-pgnout', 'file=' + str(directory / 'games.pgn'), 'append=false',
                    '-log', 'file=' + str(directory / 'engine.log'), 'level=trace',
                    'engine=true', 'append=false', 'realtime=true']
        cases.append({'case': label, 'argv': command, 'cwd': str(directory), 'expected_exit': expected,
                      'stdout': str(directory / 'stdout.bin'), 'stderr': str(directory / 'stderr.bin'),
                      'exit_receipt': str(directory / 'exit.json'),
                      'timeout_seconds': 180,
                      'extra_checks': ['exactly two completed PGNs; no illegal/crash/time-forfeit termination']
                          if label == 'positive' else ['diagnostic names Astra3UnknownOptionProbe; no games start']})
        # This is a human-readable command, not an automatically executed shell.
        (directory / 'COMMAND.txt').write_text(shlex.join(command) + '\n')
    doc = {'status': 'COMMANDS_ONLY_NOT_RUN', 'engine': str(engine), 'engine_sha256': sha256(engine),
           'fastchess': str(runner), 'fastchess_sha256': sha256(runner),
           'generator_sha256': sha256(Path(__file__)), 'invocation': sys.argv,
           'cases': cases, 'purpose': 'strict UCI smoke only; no SPRT, no gate seed, no Elo evidence',
           'opening': 'standard starting position, color-reversed pair; no opening file or randomized seed',
           'limits': 'maxmoves 80 bounds this protocol smoke; this is not a playing-strength test'}
    (out / 'commands.json').write_text(json.dumps(doc, indent=2) + '\n')
    print(out / 'commands.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
