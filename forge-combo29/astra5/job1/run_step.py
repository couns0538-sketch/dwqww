"""Run the ordered row sets for one step. Stop as soon as a check fails."""

import argparse
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('step', choices=['1', '2', '3'])
    parser.add_argument('exe', type=Path)
    parser.add_argument('epd_directory', type=Path)
    parser.add_argument('rows_directory', type=Path)
    args = parser.parse_args()
    scripts = Path(__file__).resolve().parent
    rows = args.rows_directory.resolve()
    rows.mkdir(parents=True, exist_ok=True)
    epds = args.epd_directory.resolve()
    exe = args.exe.resolve()
    depth = 14 if args.step == '3' else 12
    suites = ['G', 'O'] if args.step == '3' else ['O', 'G']
    singular_settings = {'1': [False], '2': [True], '3': [False, True]}
    for suite in suites:
        for disable_singular in singular_settings[args.step]:
            prefix = suite + ('_sd20' if disable_singular else '')
            for blend in ['base', 'fhb7']:
                path = rows / f'{prefix}_{blend}_d{depth}.tsv'
                cmd = [sys.executable, scripts/'harness.py', 'run', exe, epds/f'{suite}.epd', str(depth), path]
                if disable_singular:
                    cmd.extend(['--singular-depth', '20'])
                if blend == 'fhb7':
                    cmd.append('--fhb7')
                subprocess.run(cmd, cwd=exe.parent, check=True)
                if depth == 12:
                    subprocess.run([sys.executable, scripts/'analyze.py', 'check', path], check=True)
            if depth == 14:
                cmd = [sys.executable, scripts/'analyze.py', 'pair', rows, suite]
                if disable_singular:
                    cmd.append('--sd20')
                subprocess.run(cmd, check=True)


if __name__ == '__main__':
    main()
