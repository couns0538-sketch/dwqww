"""Root-only source/data precheck and exact authorization; launches nothing."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path, PurePosixPath

REPO = Path('/workspace/dwqww')
HERE = Path(__file__).resolve().parent
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def safe(p):
    assert p.is_file() and all(not x.is_symlink() for x in [p, *p.parents]), str(p)
    return p

manifest = HERE / 'SUPPORT-SHA256SUMS'
assert digest(safe(manifest)) == 'f7ced33d5de6896083a8c072cdb5d561dcdf5f73f0b80051027d926edb5e3a14'
seen = set()
for line in manifest.read_text().splitlines():
    wanted, name = line.split('  ', 1)
    rel = PurePosixPath(name)
    assert not rel.is_absolute() and '..' not in rel.parts and rel.as_posix() == name and name not in seen
    p = REPO / name
    assert p.is_relative_to(HERE) and digest(safe(p)) == wanted, name
    seen.add(name)
assert len(seen) == 21

preauth_path = HERE / 'PREAUTH-INPUTS.json'
assert digest(safe(preauth_path)) == 'e0120d2ec3be5d4d3d0c859d1cf4e8e8e0a13a07d0040a7323484e071f601b10'
pre = json.loads(preauth_path.read_text())
assert pre['input_count'] == len(pre['input_sha256']) == len(pre['input_bytes_modes']) == 362
assert set(pre['input_sha256']) == set(pre['input_bytes_modes'])
for name, wanted in pre['input_sha256'].items():
    p = safe(Path(name))
    assert p.is_absolute() and digest(p) == wanted, name
    facts = pre['input_bytes_modes'][name]
    assert set(facts) == {'sha256', 'mode'} and facts['sha256'] == wanted
    assert type(facts['mode']) is int and (p.stat().st_mode & 0o7777) == facts['mode'], name

driver = HERE / 'capture_actual_five.py'
assert digest(driver) == pre['driver_sha256'] == '2c13f469263921fbfba0c6cddccc43ec315394fc894afb734ecf599cd1a83f6b'
assert digest(HERE / 'owned_process.frozen.py') == pre['helper_sha256'] == '461a65d2fecdf208994749cb0d44c56bf2f8524610f211a4bf76bd019c25704d'
assert digest(REPO / 'validation/see-proof-reuse-candidate-20261021/root-verification/NATIVE.json') == pre['root_proof_sha256'] == '92cd28951c1a6f9fc81eebb568a6173dcee5c2f0255f0ab3722e3b0114a12193'
out = HERE / 'ROOT-CAPTURE-AUTHORIZATION.json'
assert not out.exists() and not (HERE / 'actual-five-captures').exists()
auth = json.loads((HERE / 'ROOT-CAPTURE-AUTHORIZATION.example.json').read_text())
auth.update(authorized=True, status='ROOT_AUTHORIZED_ONE_ACTUAL24_FIVE_COMMAND_CAPTURE',
            authorized_by='/root', utc=datetime.now(timezone.utc).isoformat(),
            driver_sha256=pre['driver_sha256'], input_sha256=pre['input_sha256'],
            preauth_sha256=digest(preauth_path), root_native_sha256=pre['root_proof_sha256'],
            root_checker_sha256=digest(Path(__file__)))
with out.open('x') as stream:
    stream.write(json.dumps(auth, indent=2) + '\n')
print(json.dumps({'status': 'ROOT_PRECHECK_PASS_ONE_CAPTURE_AUTHORIZED_NOT_EXECUTED',
                  'support_records': len(seen), 'inputs': 362, 'authorization_sha256': digest(out),
                  'engine_or_compiler_processes': 0}))
