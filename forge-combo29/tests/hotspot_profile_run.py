#!/usr/bin/env python3
"""Bounded gprof audit of immutable lock; not candidate timing or acceptance."""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import re
import subprocess


def sha(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=pathlib.Path, required=True)
    parser.add_argument('--baseline', type=pathlib.Path, required=True)
    args = parser.parse_args()
    repo = pathlib.Path(subprocess.check_output(['git', 'rev-parse', '--show-toplevel'], text=True).strip())
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)
    baseline = args.baseline.resolve()
    baseline_hash = '1371770e2ad61aa2fe3c038acc7da3912da5d64c9cb1dcc5e4668221fb3226f6'
    if sha(baseline) != baseline_hash:
        raise RuntimeError('Reference executable must match byte-verified immutable lock')
    commit = subprocess.check_output(['git', 'rev-parse', '16833ec'], text=True).strip()
    source_allowlist = ['forge-combo29/src', 'forge-combo29/include']
    archive = subprocess.check_output(['git', 'archive', commit, '--', *source_allowlist])
    source = out / 'source'
    source.mkdir(exist_ok=True)
    subprocess.run(['tar', '-x', '-C', str(source)], input=archive, check=True)
    cwd = source / 'forge-combo29'
    source_verification = []
    for line in subprocess.check_output(['git', 'ls-tree', '-r', commit, '--', *source_allowlist], text=True).splitlines():
        metadata, path = line.split('\t', 1)
        expected = metadata.split()[2]
        actual = subprocess.check_output(['git', 'hash-object', str(source / path)], text=True).strip()
        if expected != actual:
            raise RuntimeError('Source blob mismatch: ' + path)
        source_verification.append({'path': path, 'expected_git_blob': expected, 'actual_git_blob': actual, 'matched': True})
    flags = ['-std=c++20', '-O3', '-DNDEBUG', '-DFORGE_NNUE_HIDDEN=256', '-DFORGE_EXPOSE_TUNABLES=1',
             '-DFORGE_SPD_TT_NOTLS=1', '-DFORGE_SPD_NO_ZERO_MOVELISTS=2', '-DFORGE_SEARCH_SPEED2=1',
             '-DFORGE_SPD_PREFETCH_EARLY=1', '-DFORGE_SPD_SLIDER_PEXT=1', '-DFORGE_SPD_NNUE_ZMM=1',
             '-ffp-contract=off', '-fno-fast-math', '-march=x86-64-v4', '-pthread', '-Iinclude',
             '-pg', '-g', '-fno-omit-frame-pointer']
    command = ['/usr/bin/g++-14', *flags, *[str(p.relative_to(cwd)) for p in sorted((cwd / 'src').glob('*.cpp'))],
               '-o', str(out / 'forge-gprof')]
    subprocess.run(command, cwd=cwd, check=True)
    report = {'source_commit': commit, 'source_archive_allowlist': source_allowlist, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'profiler': subprocess.check_output(['gprof', '--version'], text=True).splitlines()[0],
              'compiler': subprocess.check_output(['/usr/bin/g++-14', '--version'], text=True).splitlines()[0],
              'compile_command': command, 'compile_cwd': str(cwd),
              'compiled_source_verification': source_verification,
              'profile_binary_sha256': sha(out / 'forge-gprof'), 'reference_binary_sha256': baseline_hash,
              'cpu_affinity': sorted(os.sched_getaffinity(0)),
              'scope': 'Instrumented immutable lock, not candidate comparison or accepted performance evidence',
              'runs': []}
    def save():
        (out / 'hotspot_profile_results.json').write_text(json.dumps(report, indent=2) + '\n')
    save()
    for nnue in [True, False]:
        for depth in [16, 18]:
            label = f"nnue_{'on' if nnue else 'off'}_depth{depth}"
            run_dir = out / label
            run_dir.mkdir(exist_ok=True)
            commands = f'setoption name UseNNUE value {str(nnue).lower()}\nbench {depth}\nquit\n'
            entry = {'id': label, 'nnue': nnue, 'depth': depth, 'stdin': commands,
                     'load_before': os.getloadavg()}
            results = {}
            for variant, exe in [('reference', baseline), ('profile', out / 'forge-gprof')]:
                env = os.environ.copy()
                env.pop('GMON_OUT_PREFIX', None)
                proc = subprocess.run([str(exe)], input=commands, text=True, cwd=run_dir,
                                      capture_output=True, timeout=180, env=env)
                (run_dir / f'{variant}.stdout.txt').write_text(proc.stdout)
                (run_dir / f'{variant}.stderr.txt').write_text(proc.stderr)
                if proc.returncode:
                    raise RuntimeError(f'{label} {variant} exited {proc.returncode}')
                nodes = re.findall(r'info string bench depth (\d+) nodes (\d+) time (\d+) nps (\d+)', proc.stdout)
                if len(nodes) != 1 or int(nodes[0][0]) != depth:
                    raise RuntimeError('Missing bench node signature')
                results[variant] = int(nodes[0][1])
            entry['nodes'] = results
            if results['reference'] != results['profile']:
                raise RuntimeError('Instrumentation changed node signature')
            gmon = run_dir / 'gmon.out'
            if not gmon.exists():
                raise RuntimeError('gprof runtime did not write gmon.out')
            entry['gmon_sha256'] = sha(gmon)
            entry['load_after'] = os.getloadavg()
            for kind, switch in [('flat', '-p'), ('callgraph', '-q')]:
                prof = subprocess.run(['gprof', '-b', '-C', switch, str(out / 'forge-gprof'), str(gmon)],
                                      text=True, capture_output=True, check=True)
                (run_dir / (kind + '.txt')).write_text(prof.stdout)
                (run_dir / (kind + '.stderr.txt')).write_text(prof.stderr)
            subprocess.run(['python3', str(repo / 'forge-combo29/tests/hotspot_profile_decode.py'),
                            str(out / 'forge-gprof'), str(gmon), str(run_dir / 'decoded.json')], check=True)
            report['runs'].append(entry)
            save()
            print(f'PASS {label}: identical nodes={results["reference"]}; profile collected', flush=True)
    report['reference_hash_unchanged'] = sha(baseline) == baseline_hash
    report['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    save()


if __name__ == '__main__':
    main()
