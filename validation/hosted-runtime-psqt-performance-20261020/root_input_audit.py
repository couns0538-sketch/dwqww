"""Verify original hosted bytes against actual frozen Git objects, without engines."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import subprocess
import tarfile

repo = Path(__file__).resolve().parents[2]
out = Path(__file__).resolve().parent
original = Path('/workspace/.cloud-setup/runtime-psqt-hosted-result-39510219605')
payload = '5e50d99a93a381a881b4f1813dce462a3e4106bf'
prefix = '/home/runner/work/dwqww/dwqww/'
digest = lambda b: hashlib.sha256(b).hexdigest()
summary = json.loads((original / 'performance/summary.json').read_text())
frozen = summary['frozen_inputs']
assert len(frozen) == 160
assert summary['final_rehash']['status'] == 'passed'
assert not summary['final_rehash']['mismatches']
assert summary['final_rehash']['observed'] == frozen
expected = {}
repo_count = result_count = 0
for path, record in frozen.items():
    assert path.startswith(prefix)
    relative = path[len(prefix):]
    if relative.startswith('hosted-performance-results/'):
        source = original / relative.removeprefix('hosted-performance-results/')
        assert digest(source.read_bytes()) == record['sha256']
        result_count += 1
    else:
        expected[payload + ':' + relative] = record['sha256']
        repo_count += 1
        if relative.startswith('.github/hosted-runtime-psqt-performance/'):
            source = original / 'package' / relative.removeprefix('.github/hosted-runtime-psqt-performance/')
        elif relative.startswith('.github/workflows/'):
            source = original / 'workflow.yml'
        else:
            source = original / 'proofs' / relative
        assert digest(source.read_bytes()) == record['sha256']
source_counts = {}
for label, commit in [('baseline', 'fc51e43c26f735cbc1ffabf0fcf64f48a4592c0b'),
                      ('candidate', '61f598056572dfade6994af8ad2e38817cd28aa3')]:
    provenance = json.loads((original / (label + '-build-provenance.json')).read_text())
    assert provenance['source_commit'] == commit
    raw = (original / 'source' / (label + '.tar')).read_bytes()
    assert digest(raw) == provenance['source_tar_sha256']
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:') as archive:
        assert archive.pax_headers['comment'] == commit
        members = [m for m in archive.getmembers() if m.isfile()]
        inventory = {m.name: digest(archive.extractfile(m).read()) for m in members}
        assert len(inventory) == len(members)
    assert inventory == provenance['exported_source_sha256']
    names = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', commit,
                                    '--', 'CMakeLists.txt', 'LICENSE', 'src', 'include',
                                    'tests', 'bench', 'tools'], cwd=repo, text=True).splitlines()
    assert set(names) == set(inventory)
    for name, sha in inventory.items():
        expected[commit + ':' + name] = sha
    for name in ['forge', 'libforge_core.a']:
        assert digest((original / 'artifacts' / label / name).read_bytes()) == provenance['built_artifacts_sha256'][name]
    source_counts[label] = len(inventory)
specs = sorted(expected)
raw = subprocess.check_output(['git', 'cat-file', '--batch'], cwd=repo,
                              input=('\n'.join(specs) + '\n').encode())
stream = io.BytesIO(raw)
for spec in specs:
    header = stream.readline().decode().split()
    assert len(header) == 3 and header[1] == 'blob', (spec, header)
    data = stream.read(int(header[2]))
    assert stream.read(1) == b'\n' and digest(data) == expected[spec], spec
assert stream.read() == b''
objects = {}
for label in ['baseline', 'candidate']:
    data = subprocess.check_output(['ar', 'p', str(original / 'artifacts' / label / 'libforge_core.a'),
                                    'nnue.cpp.o'])
    assert data
    objects[label] = digest(data)
result = {
    'status': 'PASS_ROOT_ACTUAL_GIT_SOURCE_AND_ALL_HOSTED_INPUT_BYTES',
    'utc': datetime.now(timezone.utc).isoformat(), 'payload_commit': payload,
    'frozen_inputs': len(frozen), 'frozen_repo_inputs': repo_count,
    'frozen_result_inputs': result_count, 'source_file_counts': source_counts,
    'git_blobs_independently_rehashed': len(specs),
    'original_host_final_byte_and_mode_observations_equal_initial': True,
    'hosted_nnue_object_sha256': objects,
    'hosted_nnue_objects_byte_identical': len(set(objects.values())) == 1,
    'extraction_permission_qualification': 'Read-only extraction modes are not the recorded original hosted modes; no executable or actual-mode restoration claim.',
    'engine_compile_benchmark_match_or_network_execution': False,
    'statistics': 'Separate independent final-audit script recomputes all samples/calibration/bootstrap.',
}
(out / 'ROOT-INPUT-AUDIT.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
