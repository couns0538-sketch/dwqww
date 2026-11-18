#!/usr/bin/env python3
"""Check Job 36's deterministic pins in one fresh Forge process per command."""

import argparse
from datetime import datetime, timezone
from hashlib import file_digest, sha256
from pathlib import Path
import re
import subprocess
import sys


NET_SHA = 'c3d95131d7c1c89ccb5b000b52c7c37ed8665dbf8bb2a0a7a873809c85b9f7c7'
NET_CHECKSUM = '30ab43b4ba5db5f3'
REFUSAL = re.compile(r'unknown option|invalid value|\bERROR\b', re.I)
ADVERTISED = re.compile(r'option name (.+?) type (\w+)(?: (.*))?')
SETTING = re.compile(r'setoption name (.+?) value (.+)')
PINS = (
    ('default', 'bench 11', 312866),
    ('default', 'bench 13', 862329),
    ('default', 'go perft 5', 4865609),
    ('PC20 + net768', 'bench 11', 882074),
    ('PC20 + net768', 'bench 13', 4275906),
)


def digest(path):
    with path.open('rb') as handle:
        return file_digest(handle, 'sha256').hexdigest()


def utc_now():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def require(condition, detail):
    if not condition:
        raise ValueError(detail)


def check_options(lines, settings):
    options = {}
    for line in lines:
        match = ADVERTISED.fullmatch(line)
        if match:
            name, kind, limits = match.groups()
            require(name not in options, f'duplicate UCI option {name}')
            options[name] = kind, limits or ''
    require(options.get('NNUEArch') == ('check', 'default false'), 'missing default-off NNUEArch option')
    require(options.get('NNUEArchFile') == ('string', 'default <empty>'), 'missing NNUEArchFile option')
    for command in settings:
        match = SETTING.fullmatch(command)
        require(match is not None, f'malformed setting {command}')
        name, value = match.groups()
        require(name in options, f'engine did not advertise {name}')
        kind, limits = options[name]
        if kind == 'check':
            require(value in ('true', 'false'), f'{name} is a check option')
        elif kind == 'spin':
            bounds = re.search(r'\bmin (-?\d+) max (-?\d+)$', limits)
            require(bounds is not None, f'no advertised range for {name}')
            low, high = map(int, bounds.groups())
            require(low <= int(value) <= high, f'{name} value {value} outside [{low}, {high}]')
        else:
            require(kind == 'string' and name == 'NNUEArchFile', f'unexpected UCI option type {kind} for {name}')


def check_net(lines, required):
    for event in ('loaded', 'active'):
        matching = [line for line in lines if line.startswith(f'info string NNUE v3 {event}:')]
        if required:
            require(len(matching) == 1, f'expected one NNUE v3 {event} line, observed {matching}')
            require(re.search(r'\bhidden 768\b', matching[0]), f'incorrect net dimensions in {matching[0]}')
            require(re.search(rf'\bchecksum {NET_CHECKSUM}\b', matching[0]), f'incorrect net checksum in {matching[0]}')
        else:
            require(not matching, f'built-in-evaluation pin unexpectedly has {matching}')


def verify(build, executable, expected_sha, profiles, log, timeout):
    actual_sha = digest(executable)
    require(actual_sha == expected_sha, f'{build} SHA-256 {actual_sha}, expected {expected_sha}')
    print(f'{build} executable SHA-256 {actual_sha}', flush=True)
    with log.open('x') as raw:
        raw.write(f'{build} {executable} SHA-256 {actual_sha}\n')
        for profile, command, expected in PINS:
            settings = profiles[profile]
            commands = ['uci', *settings, 'isready', 'ucinewgame', 'isready']
            if command == 'go perft 5':
                commands.append('position startpos')
            commands.extend((command, 'quit'))
            stdin = '\n'.join(commands) + '\n'
            raw.write(f'\n{utc_now()} {profile} — {command}\nUCI stdin\n{stdin}')
            raw.flush()
            try:
                child = subprocess.run([str(executable)], input=stdin.encode(), capture_output=True,
                                       timeout=timeout, check=False)
            except subprocess.TimeoutExpired as error:
                raw.write(f'Timeout {timeout} seconds\nStdout\n{(error.stdout or b"").decode(errors="replace")}')
                raw.write(f'Stderr\n{(error.stderr or b"").decode(errors="replace")}')
                raise
            stdout, stderr = child.stdout.decode(errors='replace'), child.stderr.decode(errors='replace')
            raw.write(f'Raw stdout\n{stdout}Raw stderr\n{stderr}Exit {child.returncode}\n')
            raw.flush()
            require(child.returncode == 0, f'{build} {profile} {command} exited {child.returncode}')
            require(not REFUSAL.search(stdout + stderr), f'{build} {profile} {command} has a refusal or error')
            lines = stdout.splitlines()
            require(lines.count('uciok') == 1 and lines.count('readyok') == 2, f'{build} UCI handshake failed')
            check_options(lines, settings)
            check_net(lines, profile == 'PC20 + net768')
            if command.startswith('bench '):
                depth = command.split()[1]
                observed = re.findall(rf'^info string bench depth {depth} nodes (\d+)\b', stdout, re.M)
            else:
                observed = re.findall(r'^nodes (\d+)$', stdout, re.M)
            require(observed == [str(expected)], f'{build} {profile} {command} returned {observed}, expected {expected}')
            evaluation = f'net768 checksum {NET_CHECKSUM}' if profile == 'PC20 + net768' else 'embedded evaluation'
            print(f'{build}\t{profile}\t{evaluation}\t{command}\t{observed[0]}\tPASS', flush=True)
        require(digest(executable) == expected_sha, f'{build} executable changed during its pins')


def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument('--r15d', type=Path, required=True)
    cli.add_argument('--r15d-sha', required=True)
    cli.add_argument('--kf', type=Path, required=True)
    cli.add_argument('--kf-sha', required=True)
    cli.add_argument('--net', type=Path, required=True)
    cli.add_argument('--pc20', type=Path, required=True)
    cli.add_argument('--output', type=Path, required=True)
    cli.add_argument('--timeout', type=int, default=90)
    args = cli.parse_args()
    net = args.net.resolve(strict=True)
    require(digest(net) == NET_SHA, 'net768 SHA-256 does not match the pinned synthetic net')
    pc20 = args.pc20.read_bytes()
    settings = pc20.decode().splitlines()
    require(len(settings) == 20 and len(set(settings)) == 20, 'expected 20 distinct PC20 settings')
    profiles = {'default': [], 'PC20': settings,
                'PC20 + net768': [*settings, f'setoption name NNUEArchFile value {net}',
                                  'setoption name NNUEArch value true']}
    args.output.mkdir(parents=True, exist_ok=True)
    print(f'Step 0 at {utc_now()}\nPC20 SHA-256 {sha256(pc20).hexdigest()}\nnet768 SHA-256 {NET_SHA}', flush=True)
    for build, exe, expected_sha in (('r15d', args.r15d, args.r15d_sha), ('kF', args.kf, args.kf_sha)):
        verify(build, exe.resolve(strict=True), expected_sha, profiles, args.output / f'{build}.raw.txt', args.timeout)
    require(digest(net) == NET_SHA, 'net768 changed during the pins')
    print(f'Step 0 PASS 10/10 fresh processes at {utc_now()}', flush=True)


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.SubprocessError) as error:
        print(f'Step 0 STOP at {utc_now()} — {error}', file=sys.stderr, flush=True)
        raise SystemExit(1) from error
