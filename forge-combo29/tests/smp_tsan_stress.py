#!/usr/bin/env python3
"""Full-engine UCI lifecycle stress; classify TSan initialization separately."""
import argparse
import hashlib
import json
import os
import pathlib
import queue
import subprocess
import threading
import time


def run(binary, rounds, log_path):
    transcript = []
    lines = queue.Queue()
    completed = 0
    failure = None
    env = dict(os.environ)
    env['TSAN_OPTIONS'] = 'halt_on_error=1:exitcode=66:history_size=4'
    process = subprocess.Popen([str(binary)], stdin=subprocess.PIPE,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, bufsize=1, env=env)
    def read():
        for line in process.stdout:
            line = line.rstrip()
            transcript.append('< ' + line)
            lines.put(line)
        lines.put(None)
    reader = threading.Thread(target=read, daemon=True)
    reader.start()
    def send(command):
        transcript.append('> ' + command)
        process.stdin.write(command + '\n')
        process.stdin.flush()
    def wait(prefix, timeout=45):
        end = time.monotonic() + timeout
        while True:
            line = lines.get(timeout=max(0.001, end - time.monotonic()))
            if line is None:
                raise RuntimeError('Engine exited waiting for ' + prefix)
            if line.startswith(prefix):
                return line
            if time.monotonic() >= end:
                raise TimeoutError('No ' + prefix)
    def search(command, release=None):
        nonlocal completed
        send('position startpos')
        send(command)
        if release:
            wait('info depth 1 ')
            send('isready')
            wait('readyok')
            send(release)
        wait('bestmove ')
        completed += 1
    try:
        send('uci')
        wait('uciok')
        send('setoption name OwnBook value false')
        send('setoption name Ponder value true')
        for index in range(rounds):
            # Options/newgame are changed only after bestmove, never in search.
            send(f'setoption name Threads value {2 if index % 2 == 0 else 4}')
            send(f'setoption name Hash value {[1, 4, 16][index % 3]}')
            send('setoption name UseNNUE value ' + ('true' if (index // 2) % 2 == 0 else 'false'))
            send('ucinewgame')
            send('isready')
            wait('readyok')
            for nodes in (0, 1, 256, 4096):
                search(f'go nodes {nodes}')
            search('go infinite', 'stop')
            search('go ponder movetime 40', 'ponderhit')
            search('go ponder', 'stop')
            search('go movetime 20')
            search('go movetime 0')
            send('setoption name Clear Hash')
            send('isready')
            wait('readyok')
        send('quit')
        process.wait(timeout=15)
    except Exception as error:
        failure = f'{type(error).__name__}: {error}'
        if process.poll() is None:
            process.kill()
        process.wait(timeout=15)
    reader.join(timeout=5)
    log_path.write_text('\n'.join(transcript) + '\n')
    text = '\n'.join(transcript)
    race = 'WARNING: ThreadSanitizer: data race' in text
    sanitizer_warning = 'WARNING: ThreadSanitizer:' in text
    runtime_fatal = 'FATAL: ThreadSanitizer:' in text
    init_failure = runtime_fatal and any(marker in text.lower() for marker in
        ('unexpected memory mapping', 'failed to mmap', 'can not mmap', 'cannot mmap'))
    result = {
        'binary': str(binary), 'sha256': hashlib.sha256(binary.read_bytes()).hexdigest(),
        'rounds_requested': rounds, 'searches_completed': completed,
        'exit_code': process.returncode, 'exception': failure,
        'tsan_options': env['TSAN_OPTIONS'], 'log': log_path.name,
        'classification': ('race_report' if race else 'sanitizer_warning' if sanitizer_warning
                           else 'sanitizer_initialization_failure' if init_failure
                           else 'sanitizer_runtime_failure' if runtime_fatal
                           else 'passed' if failure is None and process.returncode == 0
                           else 'execution_failure'),
    }
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('binary', type=pathlib.Path)
    parser.add_argument('--rounds', type=int, default=8)
    parser.add_argument('--output', type=pathlib.Path, required=True)
    args = parser.parse_args()
    result = run(args.binary.resolve(), args.rounds, args.output.with_suffix('.log'))
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    return 0 if result['classification'] == 'passed' else 1


if __name__ == '__main__':
    raise SystemExit(main())
