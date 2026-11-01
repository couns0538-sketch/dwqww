"""Check the public option, Expose-only coefficient listing and clock activation."""
import argparse
import json
from pathlib import Path
import re
from run_tmfit import Engine, digest, resource_guard


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plain', type=Path, required=True)
    parser.add_argument('--expose', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    resource_guard(args.out.parent)
    args.out.mkdir(parents=True, exist_ok=False)
    checks = []
    for label, exe in [('plain', args.plain), ('expose', args.expose)]:
        for mode in (0, 1):
            log_path = args.out/f'{label}-{mode}.log'
            with log_path.open('x', encoding='utf-8') as log:
                with Engine(exe, log, mode, {}) as engine:
                    search = engine.search('position startpos',
                        'go wtime 1000 btime 1000 winc 10 binc 10', 5)
            transcript = log_path.read_text(encoding='utf-8')
            coefficient_names = re.findall(r'^< option name (TmFit(?!Model)\w+) type spin', transcript, re.M)
            checks.append(dict(build=label, mode=mode, binary_sha256=digest(exe),
                public_option='< option name TmFitModel type spin default 0 min 0 max 1' in transcript,
                coefficients=coefficient_names, diagnostics=len(search['diagnostics']),
                passed=(len(coefficient_names) == (11 if label == 'expose' else 0)
                        and bool(search['diagnostics']) == bool(mode)
                        and '< option name TmFitModel type spin default 0 min 0 max 1' in transcript)))
    report = dict(strength='UNPROVEN', checks=checks, passed=all(c['passed'] for c in checks))
    (args.out/'summary.json').write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report))
    if not report['passed']:
        raise RuntimeError('UCI surface check failed')


if __name__ == '__main__':
    main()
