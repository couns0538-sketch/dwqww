#!/usr/bin/env python3
"""o30_tuned_patch.py - Opus 30-h job: add ONE switch for a tuned set to an expose22 tree (own code).

usage: python -I -B o30_tuned_patch.py --tuned <TUNED_OPTIONS.txt> --params <the run's params.csv> --repo <scratch repo>
         [--label <text for the source comment>]

Adds the UCI check option `O30Tuned` (default false) to src/uci.cpp: `setoption name O30Tuned value true` writes every
Name=Value of TUNED_OPTIONS.txt into the engine's tune parameters in one step (clamped to each option's range, then
tune::refresh()), `false` writes back the lock values (the start column of the run's params CSV, which the tuner
started from). It is advertised next to the tunables (development / -Expose builds), so a gate runner can check it.
With the option untouched the exe is the expose22 exe: OFF pins = the lock pins. Bench with O30Tuned=true must equal
bench with the explicit option list (checked by the caller with pin_check -Options).
Three anchored edits in src/uci.cpp; refused when an anchor is missing / not unique, when the tree already has
O30Tuned, when a tuned name is not a tune parameter of this tree or a value lies outside the CSV range.
"""
import argparse
import csv
import re
import sys
from pathlib import Path

ADVERTISE_ANCHOR = '''            for (const forge::tune::Parameter& parameter : forge::tune::parameters()) {
                std::cout << "option name " << parameter.name << " type spin default " << *parameter.value
                          << " min " << parameter.minimum << " max " << parameter.maximum << "\\n";
            }
'''
SET_ANCHOR = '            if (handled_tunable) {\n'
NS_ANCHOR = '\nnamespace {\n'


def read_tuned(path):
    out = []
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        m = re.fullmatch(r'([A-Za-z][A-Za-z0-9]*)=(-?\d+)', line)
        if not m:
            sys.exit(f'bad line in {path}: {line!r}')
        out.append((m.group(1), int(m.group(2))))
    if not out:
        sys.exit(f'{path}: no Name=Value lines')
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tuned', required=True)
    ap.add_argument('--params', required=True)
    ap.add_argument('--repo', required=True)
    ap.add_argument('--label', default='the SPSA session of the Opus 30-h job')
    a = ap.parse_args()
    tuned = read_tuned(a.tuned)
    params = {r['name']: r for r in csv.DictReader(open(a.params, encoding='utf-8'))}
    uci = Path(a.repo) / 'src' / 'uci.cpp'
    search = (Path(a.repo) / 'src' / 'search.cpp').read_text(encoding='utf-8')
    raw = uci.read_bytes().decode('utf-8')
    crlf = '\r\n' in raw
    text = raw.replace('\r\n', '\n')
    if 'O30Tuned' in text:
        sys.exit('refusing: src/uci.cpp already has O30Tuned')
    rows = []
    for name, value in tuned:
        if name not in params:
            sys.exit(f'{name} is not in {a.params}')
        lo, hi, start = int(params[name]['min']), int(params[name]['max']), float(params[name]['start'])
        if not lo <= value <= hi:
            sys.exit(f'{name}={value} outside the CSV range [{lo}, {hi}]')
        if f'"{name}"' not in search:
            sys.exit(f'{name} is not a tune parameter of this tree (no "{name}" in src/search.cpp)')
        if start != int(start):
            sys.exit(f'{name}: start {start} is not an integer lock value')
        rows.append((name, int(start), value))
    for anchor in (NS_ANCHOR, ADVERTISE_ANCHOR, SET_ANCHOR):
        if text.count(anchor) < 1 or (anchor != NS_ANCHOR and text.count(anchor) != 1):
            sys.exit(f'anchor not found exactly once: {anchor.strip()[:60]!r}')
    table = '\n'.join(f'    {{"{n}", {lock}, {val}}},' for n, lock, val in rows)
    decl = (f'\nnamespace {{\n'
            f'// O30Tuned (UCI check, default false): the tuned search constants of {a.label} in one switch.\n'
            f'// true = the tuned values below, false = the lock values (each clamped to its option range).\n'
            f'struct O30TunedValue {{\n    std::string_view name;\n    int lock;\n    int tuned;\n}};\n'
            f'constexpr std::array<O30TunedValue, {len(rows)}> O30TunedSet{{{{\n{table}\n}}}};\n')
    text = text.replace(NS_ANCHOR, decl, 1)
    text = text.replace(ADVERTISE_ANCHOR, ADVERTISE_ANCHOR + '            std::cout << "option name O30Tuned type check default false\\n";\n', 1)
    handler = '''            if (name == "O30Tuned") {
                handled_tunable = true;
                if (value_text == "true" || value_text == "false") {
                    const bool on = value_text == "true";
                    for (const forge::tune::Parameter& parameter : forge::tune::parameters()) {
                        for (const O30TunedValue& entry : O30TunedSet) {
                            if (entry.name == parameter.name) {
                                *parameter.value = std::clamp(on ? entry.tuned : entry.lock, parameter.minimum, parameter.maximum);
                            }
                        }
                    }
                    forge::tune::refresh();
                } else {
                    const std::lock_guard<std::mutex> output_lock(forge::uci_output_mutex());
                    std::cout << "info string invalid value for option O30Tuned" << std::endl;
                }
            }
'''
    text = text.replace(SET_ANCHOR, handler + SET_ANCHOR, 1)
    out = text.replace('\n', '\r\n') if crlf else text
    uci.write_bytes(out.encode('utf-8'))
    print(f'O30Tuned added to {uci} ({len(rows)} values, {"CRLF" if crlf else "LF"}): '
          + ', '.join(f'{n} {lock}->{val}' for n, lock, val in rows))


if __name__ == '__main__':
    main()
