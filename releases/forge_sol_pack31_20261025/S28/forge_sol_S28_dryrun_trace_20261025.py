"""Observe the final shell entry point; trace and classify its file-write attempts."""
from pathlib import Path
import base64, hashlib, json, re, subprocess

root = Path('/workspace/forge-pack24-20261025')
work = root / 'S28'
files = root / 'forge_sol_jobpack_24jobs_20261025/files'
out = work / 'forge_sol_S28_final_dryrun_v2_20261025'
trace = work / 'forge_sol_S28_final_dryrun_v2_trace_20261025.txt'
argv = ['strace', '-f', '-qq', '-e', 'trace=%file', '-s', '4096', '-o', str(trace),
        'bash', str(work / 'forge_sol_S28_lock_transition_kit_20261025/forge_sol_S28_lock_transition_20261025.sh'),
        '--tree', str(files / '01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src'),
        '--net', str(files / '03_nets/resid_h256_e48_f006_b06_ep48.inc'),
        '--out', str(out), '--pin-helper',
        str(root / 'S01/forge_sol_S01_delivery_v2_20261025/forge_sol_S01_rerecord_pins_20261025.py'),
        '--queue', str(work / 'forge_sol_S28_native_queue_20261025.json')]

def raw(data):
    return dict(encoding='base64', bytes=len(data), sha256=hashlib.sha256(data).hexdigest(),
                data=base64.b64encode(data).decode('ascii'))

done = subprocess.run(argv, cwd=work, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
record = dict(status='INCOMPLETE', argv=argv, exit=done.returncode, stdout=raw(done.stdout),
              stderr=raw(done.stderr), trace=raw(trace.read_bytes()),
              scope='Actual final-v3 shell dry-run only; observer owns the separate trace file. No full native syscall-trace claim.')
receipt = work / 'forge_sol_S28_final_dryrun_trace_results_20261025.json'
receipt.write_text(json.dumps(record, indent=2) + '\n')
try:
    assert done.returncode == 0
    summary = json.loads(done.stdout)
    assert summary['status'] == 'DRY_RUN' and summary['stage_summaries'] == []
    mutations, failed = [], []
    for line in trace.read_text().splitlines():
        write_open = re.search(r'\b(?:open|openat)\(', line) and re.search(r'O_(?:WRONLY|RDWR|CREAT|TRUNC)', line)
        other = re.search(r'\b(?:creat|mkdir(?:at)?|unlink(?:at)?|rename(?:at2?)?|rmdir|symlink(?:at)?|link(?:at)?|chmod|fchmodat|truncate|mknod|utimes?|utimensat|setxattr|removexattr)\(', line)
        if not (write_open or other): continue
        returned = re.search(r'\)\s+=\s+(-?\d+)\b', line)
        assert returned, ('unresolved mutating syscall', line)
        if int(returned[1]) < 0:
            failed.append(line)
            continue
        paths = re.findall(r'"([^"\n]*)"', line)
        assert paths and all(Path(path).is_absolute() and Path(path).is_relative_to(out) for path in paths), line
        mutations.append(line)
    assert len(mutations) == 4
    check = subprocess.run(['sha256sum', '-c', 'forge_sol_S28_SHA256SUMS_20261025.txt'],
                           cwd=out, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    assert check.returncode == 0
    record.update(status='PASS', successful_mutating_file_calls=mutations,
                  failed_write_open_or_mutation_calls=failed,
                  successful_traced_write_opens_and_path_mutations_contained=True,
                  inside_output_checksum_exit=check.returncode,
                  inside_output_checksum_stdout=raw(check.stdout))
except Exception as error:
    record.update(status='FAIL', error=repr(error))
finally:
    receipt.write_text(json.dumps(record, indent=2) + '\n')
print(record['status'], 'actual final-v3 default dry-run file-write containment')
raise SystemExit(0 if record['status'] == 'PASS' else 1)
