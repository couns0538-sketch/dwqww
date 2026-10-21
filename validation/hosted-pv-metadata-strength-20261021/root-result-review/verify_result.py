#!/usr/bin/env python3
"""Root data-only byte/source/decision check; no engines or match execution."""
import hashlib
import io
import json
import math
from pathlib import Path, PurePosixPath
import subprocess
import tarfile
from datetime import datetime, timezone

REPO = Path('/workspace/dwqww')
HERE = Path(__file__).resolve().parent
AUDIT = HERE.parent / 'final-audit'
FILES = Path('/workspace/.cloud-setup/pv-metadata-result-39528641493/extracted/files')
REV = 'fd20551497f670aa11133ce4727ee0a1c5a1ba56'
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
def read(path):
    return json.loads(path.read_text())

sealed = 0
for line in (AUDIT / 'SHA256SUMS').read_text().splitlines():
    expected, name = line.split('  ', 1)
    assert sha(AUDIT / name) == expected, name
    sealed += 1
a = read(AUDIT / 'AUDIT.json')
assert a['status'] == 'PASS_VALID_COMPLETED_CAP_INCONCLUSIVE_NO_ACCEPTED_GAIN'
assert a['result_commit'] == REV
manifest = read(AUDIT / 'ORIGINAL-ARCHIVE-MANIFEST.json')
raw = subprocess.check_output(['git', 'show', REV + ':archived-results/pv-metadata-strength-39528641493-1.manifest.json'], cwd=REPO)
assert raw == (AUDIT / 'ORIGINAL-ARCHIVE-MANIFEST.json').read_bytes()
for row in manifest['files']:
    path = PurePosixPath(row['path'])
    assert not path.is_absolute() and '..' not in path.parts
    file = FILES / row['path']
    assert file.is_file() and not file.is_symlink()
    assert file.stat().st_size == row['size'] and sha(file) == row['sha256']
assert len(manifest['files']) == 618
for row in a['final_input_records']:
    assert sha(FILES / row['archived']) == row['sha256']
assert len(a['final_input_records']) == 1012
cfg = read(FILES / 'package/protocol.json')
for name, value in cfg['correctness_evidence_sha256'].items():
    assert sha(FILES / 'proofs' / name) == value
assert len(cfg['correctness_evidence_sha256']) == 449
git_blobs = 0
for label, ref, repo in [('baseline', cfg['baseline_sha'], REPO), ('candidate', cfg['candidate_sha'], REPO), ('fastchess', cfg['fastchess_sha'], Path('/workspace/.cloud-setup/fastchess'))]:
    with tarfile.open(FILES / 'source' / (label + '.tar')) as tar:
        members = {m.name: tar.extractfile(m).read() for m in tar if m.isfile()}
    result = subprocess.run(['git', 'cat-file', '--batch'], cwd=repo, input=''.join(ref + ':' + n + '\n' for n in members).encode(), stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
    assert not result.stderr
    stream = io.BytesIO(result.stdout)
    for name, expected in members.items():
        header = stream.readline().decode().split()
        assert len(header) == 3 and header[1] == 'blob'
        assert stream.read(int(header[2])) == expected and stream.read(1) == b'\n'
        git_blobs += 1
    assert stream.read() == b''
assert git_blobs == 525
# Independently compare all package, workflow, validator and consumed proof bytes
# against the actual immutable public trigger commit, not merely the raw archive.
objects = {n: FILES / 'proofs' / n for n in cfg['correctness_evidence_sha256']}
for p in (FILES / 'package').rglob('*'):
    if p.is_file():
        objects['.github/hosted-pv-metadata-strength/' + p.relative_to(FILES / 'package').as_posix()] = p
objects['.github/workflows/forge-hosted-pv-metadata-strength.yml'] = FILES / 'workflow.yml'
objects['tools/match/windows_validate.py'] = FILES / 'windows_validate.py'
payload = '452a4a9ca96afd7356c8dadc2203efd41c162e47'
result = subprocess.run(['git', 'cat-file', '--batch'], cwd=REPO,
    input=''.join(payload + ':' + n + '\n' for n in objects).encode(),
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
assert not result.stderr
stream = io.BytesIO(result.stdout)
for name, path in objects.items():
    header = stream.readline().decode().split()
    assert len(header) == 3 and header[1] == 'blob', name
    assert stream.read(int(header[2])) == path.read_bytes() and stream.read(1) == b'\n', name
assert stream.read() == b'' and len(objects) == 475
s = a['phase_results']['sprt']
assert s['statistics']['candidate_wins_draws_losses'] == [221, 573, 230]
assert s['statistics']['pairs'] == 512 and s['statistics']['games'] == 1024
counts = s['statistics']['pentanomial_0_half_1_1half_2']
assert counts == [27, 120, 220, 125, 20]
def likelihood(elo):
    mean = 1 / (1 + 10 ** (-elo / 400))
    delta = [i / 4 - mean for i in range(5)]
    p = [c / sum(counts) for c in counts]
    low, high = -1 / max(delta) + 1e-12, -1 / min(delta) - 1e-12
    for _ in range(120):
        mid = (low + high) / 2
        value = sum(pi * d / (1 + mid * d) for pi, d in zip(p, delta))
        if value > 0:
            low = mid
        else:
            high = mid
    lam = (low + high) / 2
    return sum(c * math.log(pi / (1 + lam * d)) for c, pi, d in zip(counts, p, delta))
llr = likelihood(10) - likelihood(0)
assert abs(llr - s['likelihood']['independent_llr']) < 1e-8
assert abs(llr - (-1.62)) <= 0.005000001 and abs(llr) < math.log(19)
assert s['decision'] == 'inconclusive_at_pair_cap' and a['natural_cap'] is True
assert a['phase_results']['aa']['statistics']['games'] == 8
assert a['phase_results']['aa']['decision'] == 'aa_timed_operational_readiness_only'
assert a['no_trim_pool_reset_resume'] is True
out = {'status': 'PASS_ROOT_REHASH_VALID_CAP_NO_ACCEPTED_GAIN', 'utc': datetime.now(timezone.utc).isoformat(),
       'result_commit': REV, 'audit_records_rehashed': sealed, 'raw_payloads_rehashed': 618,
       'frozen_inputs_rehashed': 1012, 'proofs_rehashed': 449, 'actual_git_blobs_verified': git_blobs, 'actual_payload_git_blobs_verified': len(objects),
       'baseline_source_commit': cfg['baseline_sha'], 'candidate_source_commit': cfg['candidate_sha'],
       'games': 1024, 'pairs': 512, 'wins': 221, 'draws': 573, 'losses': 230,
       'root_independent_llr': llr, 'native_llr': -1.62, 'decision': 'INCONCLUSIVE_AT_NATURAL_CAP',
       'native_descriptive_elo': '-3.05 +/-13.84', 'accepted_elo_gain': None,
       'aa_mode': 'separate equal1+0.01, four timed operational pairs',
       'archive_permission_limitation': a['archive_mode_limitation'],
       'legality_source': 'Independent audit replayed all1032 games/137807plies; this root check rehashes their exact original PGNs and source evidence.',
       'native_audit_sha256': sha(AUDIT / 'AUDIT.json'), 'verifier_sha256': sha(Path(__file__)),
       'engine_build_match_execution': False}
with (HERE / 'ROOT.json').open('x') as f:
    json.dump(out, f, indent=2)
    f.write('\n')
print(json.dumps(out))
