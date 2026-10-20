"""Future-only isolated helper; not imported by any launched workflow."""
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import time

def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as source:
        for block in iter(lambda: source.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')

def stop_group(process):
    # A leader exit does not establish that its descendants have exited.
    try:
        os.killpg(process.pid, signal.SIGINT)
    except ProcessLookupError:
        pass
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.wait(timeout=5)

def verify_candidate_bench_signature(stdout, stderr, returncode, expected_nodes):
    matches = re.findall(r'\Ainfo string bench depth 11 nodes ([0-9]+) time ([0-9]+) nps ([0-9]+)(?:\r?\n)?\Z', stdout)
    if (type(expected_nodes) is not int or expected_nodes != 385781 or returncode != 0 or
            stderr or len(matches) != 1 or int(matches[0][0]) != expected_nodes or
            re.search(r'^\s*(?:warning|error|fatal)\b|\[(?:WARN(?:ING)?|ERR(?:OR)?|FATAL)\s*\]', stdout, re.I | re.M)):
        raise ValueError('Candidate bench signature/exit/warning failure')
    return {'engine_nodes': int(matches[0][0]), 'engine_ms': int(matches[0][1]),
            'engine_nps': int(matches[0][2]), 'scope': 'Signature readiness only; no speed comparison'}


def _owned_group_empty(process):
    try:
        os.killpg(process.pid, 0)
    except ProcessLookupError:
        return True
    return False


def candidate_bench_readiness(engine, out, expected_nodes):
    stdout_path, stderr_path = out / 'candidate-bench11.stdout', out / 'candidate-bench11.stderr'
    command = {'command': [str(engine)], 'stdin': 'bench 11\nquit\n', 'expected_nodes': expected_nodes,
               'guard_seconds': 10, 'scope': 'Signature readiness only; no timing ratio'}
    save(out / 'candidate-bench11-command.json', command)
    facts = {**command, 'verdict': 'pending', 'cleanup_attempted': False,
             'returncode_before_verdict': None, 'owned_group_empty_before_verdict': None,
             'stdout_sha256_before_verdict': None, 'stderr_sha256_before_verdict': None}
    process = None
    started = time.monotonic()
    with stdout_path.open('x') as stdout, stderr_path.open('x') as stderr:
        try:
            process = subprocess.Popen(command['command'], stdin=subprocess.PIPE, stdout=stdout,
                                       stderr=stderr, text=True, start_new_session=True)
            facts['pid'] = process.pid
            try:
                process.communicate(input=command['stdin'], timeout=max(.001, 10 - (time.monotonic() - started)))
            finally:
                stdout.flush()
                stderr.flush()
                facts.update(returncode_before_verdict=process.returncode,
                             owned_group_empty_before_verdict=_owned_group_empty(process),
                             stdout_sha256_before_verdict=sha(stdout_path),
                             stderr_sha256_before_verdict=sha(stderr_path))
                # Persist observations before any parser or process-group assertion can fail.
                save(out / 'candidate-bench11-process.json', facts)
            result = verify_candidate_bench_signature(stdout_path.read_text(), stderr_path.read_text(),
                                                     process.returncode, expected_nodes)
            if not facts['owned_group_empty_before_verdict']:
                raise ValueError('Owned candidate bench descendant survived leader exit')
            result.update(command=command['command'], stdin=command['stdin'], guard_seconds=10,
                          elapsed_seconds=time.monotonic() - started,
                          owned_process_group_empty=True, stdout_sha256=sha(stdout_path),
                          stderr_sha256=sha(stderr_path))
            save(out / 'candidate-bench11.json', result)
            facts['verdict'] = 'passed'
            return result
        except BaseException as error:
            facts.update(verdict='failed', error=repr(error))
            if process is not None:
                facts['cleanup_attempted'] = True
                try:
                    stop_group(process)
                except BaseException as cleanup_error:
                    facts['cleanup_error'] = repr(cleanup_error)
            raise
        finally:
            stdout.flush()
            stderr.flush()
            facts.update(returncode_after_cleanup=process.returncode if process is not None else None,
                         owned_group_empty_after_cleanup=_owned_group_empty(process) if process is not None else None,
                         stdout_sha256_after_cleanup=sha(stdout_path), stderr_sha256_after_cleanup=sha(stderr_path),
                         stdout_sha256=sha(stdout_path), stderr_sha256=sha(stderr_path),
                         elapsed_seconds=time.monotonic() - started)
            save(out / 'candidate-bench11-process.json', facts)
