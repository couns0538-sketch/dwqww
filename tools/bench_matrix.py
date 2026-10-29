#!/usr/bin/env python3
"""Fresh-process Forge bench matrix, with fixed OFF pins and original byte logs.

JSON --sets: [{"name":"B1","options":[["BundlePreset","B1"]]}]. Options are
ordered pairs; presets precede individual overrides. An OFF row is always added.
Threads=1, Hash=16 and OwnBook=false are controlled and cannot be overridden.
Reported NPS is observational; this runner does not establish a speed/Elo gain.
IDEA_SOURCE: user's B6 specification, Forge's UCI protocol, and same-repo A3 parser.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
import queue
import re
import subprocess
import sys
import threading
import time
from pathlib import Path
from check_bundle_opts import INTEGER, OPTION, parse_options, positive_timeout, unique_json_object, valid_name

PINS = {11: 312866, 13: 862329, 16: 3024920, 20: 12389307, 22: 34048354}
CONTROLS = [["Threads", "1"], ["Hash", "16"], ["OwnBook", "false"]]
BENCH = re.compile(r"info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)")
ERROR = re.compile(r"unknown option|invalid value|\brefused\b|\bERROR\b", re.I)
MAX_CAPTURE = 8 * 1024 * 1024  # per stream; exceeding this is an explicit failure


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_sets(path):
    data = [] if path is None else json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=unique_json_object)
    if not isinstance(data, list):
        raise ValueError("--sets requires a JSON array")
    result = [{"name": "OFF", "options": []}]
    names = {"off"}
    for entry in data:
        if not isinstance(entry, dict) or set(entry) != {"name", "options"}:
            raise ValueError("each set requires only name and options")
        name = entry["name"]
        if not valid_name(name) or len(name) > 80 or any(ord(c) < 32 or c == '|' for c in name):
            raise ValueError("invalid matrix row name")
        if name.casefold() in names:
            raise ValueError("OFF is reserved; other set names must be unique")
        names.add(name.casefold())
        if not isinstance(entry["options"], list):
            raise ValueError("options must be an ordered array of [name, value] pairs")
        options = []
        for pair in entry["options"]:
            if not isinstance(pair, list) or len(pair) != 2 or not valid_name(pair[0]):
                raise ValueError("invalid option pair")
            option, value = pair
            if option.casefold() in {p[0].casefold() for p in CONTROLS}:
                raise ValueError(f"{option} is controlled by this runner")
            if type(value) not in (str, int, bool, type(None)):
                raise ValueError(f"{option}: unsupported JSON value")
            if isinstance(value, str) and any(ord(c) < 32 for c in value):
                raise ValueError(f"{option}: control characters are forbidden")
            text = str(value).lower() if type(value) is bool else str(value) if type(value) is int else value
            options.append([option, text])
        result.append({"name": name, "options": options})
    return result


def validate_value(name, value, advertised, combo_values):
    if name not in advertised:
        raise ValueError(f"unadvertised option {name}")
    option = advertised[name]
    kind = option["type"]
    if kind == "button":
        if value is not None:
            raise ValueError(f"{name}: button requires null")
    elif value is None:
        raise ValueError(f"{name}: value required")
    elif kind == "check" and value not in ("true", "false"):
        raise ValueError(f"{name}: check requires true/false")
    elif kind == "spin":
        if not INTEGER.fullmatch(value) or not option["min"] <= int(value) <= option["max"]:
            raise ValueError(f"{name}: spin value outside advertised range")
    elif kind == "combo" and value not in combo_values[name]:
        raise ValueError(f"{name}: value is not an advertised variant")


class Session:
    """One owned process, bounded by one deadline; captures stdout and stderr separately."""
    def __init__(self, exe, stem, timeout):
        self.deadline = time.monotonic() + timeout
        self.queue = queue.Queue()
        self.capture_error = None
        self.stdin_log = stem.with_suffix('.stdin').open('xb')
        self.process = subprocess.Popen([str(exe)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                        stderr=subprocess.PIPE, shell=False)
        self.write_queue = queue.Queue()
        self.threads = [threading.Thread(target=self.write_commands, daemon=True)]
        self.threads[0].start()
        for stream, suffix, stdout in ((self.process.stdout, '.stdout', True), (self.process.stderr, '.stderr', False)):
            t = threading.Thread(target=self.capture, args=(stream, stem.with_suffix(suffix), stdout), daemon=True)
            t.start(); self.threads.append(t)

    def capture(self, stream, path, stdout):
        count = 0
        try:
            with path.open('xb') as log:
                while True:
                    line = stream.readline(MAX_CAPTURE + 1)
                    if not line:
                        break
                    count += len(line)
                    if count > MAX_CAPTURE:
                        self.capture_error = "capture limit exceeded; stream truncated"
                        self.queue.put(None)
                        break
                    log.write(line)
                    if stdout:
                        self.queue.put(line.decode('utf-8', 'replace').strip())
        except OSError as error:
            self.capture_error = f"capture failed: {error}"
            self.queue.put(None)
        finally:
            stream.close()
            if stdout:
                self.queue.put(None)

    def remaining(self):
        left = self.deadline - time.monotonic()
        if left <= 0:
            raise TimeoutError("cell deadline exceeded")
        return left

    def write_commands(self):
        try:
            while True:
                data = self.write_queue.get()
                if data is None:
                    return
                self.stdin_log.write(data); self.stdin_log.flush()
                self.process.stdin.write(data); self.process.stdin.flush()
        except OSError as error:
            self.capture_error = f"stdin write failed: {error}"
            self.queue.put(None)

    def send(self, command):
        self.remaining()
        self.write_queue.put((command + '\n').encode('utf-8'))

    def until(self, predicate):
        lines = []
        while True:
            try:
                line = self.queue.get(timeout=self.remaining())
            except queue.Empty as error:
                raise TimeoutError("cell response deadline exceeded") from error
            if self.capture_error:
                raise ValueError(self.capture_error)
            if line is None:
                raise ValueError("engine exited before required response")
            lines.append(line)
            if ERROR.search(line):
                raise ValueError(f"engine diagnostic: {line}")
            if predicate(line):
                return lines

    def finish(self, clean):
        try:
            if clean:
                self.send('quit')
                self.process.wait(timeout=self.remaining())
                if self.process.returncode != 0:
                    raise ValueError(f"engine exited {self.process.returncode}")
        finally:
            if self.process.poll() is None:
                self.process.kill()  # only this runner's child
            self.process.wait(timeout=5)
            self.write_queue.put(None)
            for thread in self.threads:
                thread.join(timeout=5)
            if any(t.is_alive() for t in self.threads):
                raise ValueError("I/O thread did not finish")
            self.process.stdin.close()
            self.stdin_log.close()
            if self.capture_error:
                raise ValueError(self.capture_error)


def cell(exe, out, index, config, depth, timeout):
    stem = out / f"cell_{index:03d}"
    result = {"set": config["name"], "depth": depth, "stem": stem.name, "status": "FAIL"}
    session = None
    clean = False
    error = None
    try:
        session = Session(exe, stem, timeout)
        session.send('uci')
        advertisement = session.until(lambda line: line == 'uciok')
        actual = parse_options(advertisement)
        for name, kind in (("Threads", "spin"), ("Hash", "spin"), ("OwnBook", "check")):
            if name not in actual or actual[name]["type"] != kind:
                raise ValueError(f"{name}: controlled option must be advertised as {kind}")
        if "BundlePreset" in actual and actual["BundlePreset"]["type"] != "combo":
            raise ValueError("BundlePreset must be advertised as combo")
        combos = {}
        for line in advertisement:
            match = OPTION.fullmatch(line)
            if match and match[2] == 'combo':
                combos[match[1]] = re.split(r'\s+var\s+', re.sub(r'^default\s+', '', match[3]))[1:]
        options = list(CONTROLS)
        if "BundlePreset" in actual:
            options.append(["BundlePreset", "OFF"])
        options += config["options"]
        for name, value in options:
            validate_value(name, value, actual, combos)
        for name, value in options:
            session.send(f'setoption name {name}' + ('' if value is None else f' value {value}'))
        session.send('isready')
        session.until(lambda line: line == 'readyok')
        session.send(f'bench {depth}')
        session.until(lambda line: line.startswith('info string bench'))
        clean = True
    except (OSError, ValueError, TimeoutError) as exc:
        error = f'{type(exc).__name__}: {exc}'
    finally:
        if session is not None:
            try:
                session.finish(clean)
            except (OSError, ValueError, TimeoutError, subprocess.TimeoutExpired) as exc:
                error = error or f'{type(exc).__name__}: {exc}'
            result['returncode'] = session.process.returncode
    try:
        stdout = stem.with_suffix('.stdout').read_bytes()
        stderr = stem.with_suffix('.stderr').read_bytes()
        text = stdout.decode('utf-8', 'replace')
        diagnostics = [line for line in (text + '\n' + stderr.decode('utf-8', 'replace')).splitlines() if ERROR.search(line)]
        if diagnostics:
            raise ValueError(f'engine diagnostic: {diagnostics[0]}')
        candidates = [line.strip() for line in text.splitlines() if line.strip().startswith('info string bench')]
        if len(candidates) != 1 or not BENCH.fullmatch(candidates[0]):
            raise ValueError('expected exactly one well-formed bench result')
        got_depth, nodes, elapsed, nps = map(int, BENCH.fullmatch(candidates[0]).groups())
        result.update(nodes=nodes, elapsed_ms=elapsed, nps=nps)
        if got_depth != depth or nodes <= 0:
            raise ValueError('wrong bench depth or nonpositive nodes')
        if config['name'] == 'OFF' and nodes != PINS[depth]:
            raise ValueError(f'OFF mismatch: expected {PINS[depth]}, got {nodes}')
    except (OSError, ValueError) as exc:
        error = error or f'{type(exc).__name__}: {exc}'
    result['status'] = 'PASS' if error is None else 'FAIL'
    result['error'] = error
    result['log_sha256'] = {p.name: sha256(p) for p in (stem.with_suffix(s) for s in ('.stdin', '.stdout', '.stderr')) if p.exists()}
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('exe', type=Path)
    parser.add_argument('--sets', type=Path, help='JSON array of named ordered option pairs')
    parser.add_argument('--out-dir', type=Path, required=True, help='must not already exist')
    parser.add_argument('--timeout', type=positive_timeout, default=180.0, help='complete deadline per cell, seconds')
    args = parser.parse_args(argv)
    doc = None
    try:
        configs = load_sets(args.sets)
        exe = args.exe.resolve(strict=True)
        before = sha256(exe)
        out = args.out_dir.resolve()
        out.mkdir(parents=True, exist_ok=False)
        source = Path(__file__).resolve()
        doc = {'status': 'RUNNING', 'binary': str(exe), 'binary_sha256_before': before,
               'source_sha256': {str(p): sha256(p) for p in (source, source.with_name('check_bundle_opts.py'))},
               'sets_source_sha256': sha256(args.sets) if args.sets else None, 'sets': configs,
               'pins': PINS, 'timeout_seconds': args.timeout, 'command': sys.argv, 'cells': []}
        def save():
            pending = out / 'results.pending.json'
            pending.write_text(json.dumps(doc, indent=2) + '\n', encoding='utf-8')
            os.replace(pending, out / 'results.json')
        save()
        for config in configs:
            for depth in PINS:
                row = cell(exe, out, len(doc['cells']), config, depth, args.timeout)
                doc['cells'].append(row); save()
                if row['status'] != 'PASS':
                    raise ValueError(f"{config['name']} d{depth}: {row['error']}")
        doc['binary_sha256_after'] = sha256(exe)
        if before != doc['binary_sha256_after']:
            raise ValueError('engine binary changed during matrix')
        doc['status'] = 'PASS'; save()
        print('Set | ' + ' | '.join(f'd{d} nodes / NPS' for d in PINS) + ' | Status')
        for config in configs:
            rows = [r for r in doc['cells'] if r['set'] == config['name']]
            print(config['name'] + ' | ' + ' | '.join(f"{r['nodes']} / {r['nps']}" for r in rows) + ' | PASS')
        print('NPS is observational; no speed or Elo conclusion.')
        return 0
    except (OSError, ValueError) as exc:
        if doc is not None:
            doc['status'] = 'FAIL'; doc['error'] = str(exc)
            try:
                doc['binary_sha256_after'] = sha256(args.exe.resolve())
            except OSError:
                doc['binary_sha256_after'] = None
            save()
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
