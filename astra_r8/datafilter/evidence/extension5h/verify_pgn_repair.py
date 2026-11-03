"""Bind the PGN-only repair to prior self-play proof and a new CPU handoff."""
import ast
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parents[2]
ROOT = Path('C:/astra8_data/extension5h_20261103')
BASE_SHA = '6e2354dffa7d273eca732bafac8c54c2830fe8d9a677cc217801a8f599c43c00'
RECORDS_SHA = '8fe0e9e529bbd65ef3fcdf764ad96705696f66ec8d52188943676fc0623af406'
TEST_SHA = '9598365da24db670bcc03049a4f295c82ad67ccdc4722ba35426d85747c8bfd1'
sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True
os.environ.update(PYTHONDONTWRITEBYTECODE='1', CUDA_VISIBLE_DEVICES='',
                  HIP_VISIBLE_DEVICES='', ROCR_VISIBLE_DEVICES='',
                  OMP_NUM_THREADS='1', MKL_NUM_THREADS='1', OPENBLAS_NUM_THREADS='1')

from filter_positions import low_priority, sha256
from refresh_handoff import configure_cpu_runtime, current_runtime, refresh
from resource_policy import storage_guard
from seal_admission import BoundInputs
from verify_handoff import verify
from verify_input_repair import native_admission, protected_tree, write


def require(condition, message):
    if not condition:
        raise ValueError(message)


def separate_header_method(blob):
    text = blob.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n')
    tree = ast.parse(text)
    classes = [n for n in tree.body if isinstance(n, ast.ClassDef)
               and n.name == 'ResultGameBuilder']
    require(len(classes) == 1, 'exactly one PGN builder required')
    methods = [n for n in classes[0].body if isinstance(n, ast.FunctionDef)
               and n.name == 'end_headers']
    require(len(methods) == 1 and not methods[0].decorator_list,
            'exactly one undecorated end_headers required')
    node = methods[0]
    lines = text.splitlines(keepends=True)
    start, end = node.lineno - 1, node.end_lineno
    return ''.join(lines[:start] + lines[end:]), ''.join(lines[start:end])


def main():
    low_priority()
    output = ROOT/'pgn_fix_validation_v1'
    storage_guard(output, allowance=10_000_000)
    output.mkdir()
    configure_cpu_runtime(output)
    bound = BoundInputs()

    def pin(path, digest):
        path = Path(path).resolve()
        require(sha256(path) == digest, 'linked bytes differ: ' + str(path))
        require(bound.files.get(str(path), digest) == digest, 'conflicting link')
        bound.files[str(path)] = digest

    prior_path = ROOT/'input_repair_validation/COMPLETE.json'
    prior = bound.read(prior_path)
    require(bound.files[str(prior_path.resolve())] == BASE_SHA and prior['status'] == 'PASS',
            'exact preceding input proof required')
    old_path = ROOT/'pgn_raw_fen_review/records_before.py.txt'
    new_path = HERE/'records.py'
    old_blob, new_blob = old_path.read_bytes(), new_path.read_bytes()
    old_digest = hashlib.sha256(old_blob).hexdigest()
    new_digest = hashlib.sha256(new_blob).hexdigest()
    require(old_digest == prior['source_files'][str(new_path)] and new_digest == RECORDS_SHA,
            'reviewed parser identities differ')
    old_rest, old_method = separate_header_method(old_blob)
    new_rest, new_method = separate_header_method(new_blob)
    require(old_rest == new_rest and old_method != new_method,
            'change is not confined to the reviewed PGN header method')
    pin(old_path, old_digest)
    pin(new_path, new_digest)
    files = [*HERE.glob('*.py'), *(HERE/'tests').glob('*.py'),
             HERE/'evidence/extension5h/verify_input_repair.py']
    current = {str(p): sha256(p) for p in files}
    added_test = str(HERE/'tests/test_pgn_original_fen.py')
    require(set(current) == set(prior['source_files']) | {added_test},
            'unexpected source membership change')
    require(current[added_test] == TEST_SHA, 'reviewed regression tests changed')
    changed = {p for p, h in prior['source_files'].items() if current[p] != h}
    require(changed == {str(new_path)}, 'non-PGN implementation changed')
    for p, h in current.items():
        pin(p, h)
    pin(__file__, sha256(__file__))
    inherited = {}
    for name, item in {**prior['receipts'], **prior['stages']}.items():
        path = item.get('path', item.get('receipt'))
        pin(path, item['sha256'])
        inherited[name] = dict(path=path, sha256=item['sha256'])
    runtime = current_runtime()
    previous_runtime = prior['runtime']
    require({k:v for k,v in runtime.items() if k != 'files'} ==
            {k:v for k,v in previous_runtime.items() if k != 'files'}, 'runtime versions changed')
    require(runtime['files'].keys() == previous_runtime['files'].keys(), 'runtime membership changed')
    require({p for p,h in runtime['files'].items() if h != previous_runtime['files'][p]} ==
            {str(new_path)}, 'installed runtime changed')
    protected = protected_tree()
    require(protected == prior['protected_v7'], 'protected v7 changed')
    started = time.perf_counter()
    write(output/'RUN.json', dict(candidate=subprocess.check_output(
        ['git', 'rev-parse', 'HEAD'], cwd=HERE, text=True).strip(),
        source_files=current, driver_sha256=sha256(__file__), strength='UNPROVEN'))
    write(output/'source_lineage.json', dict(status='PASS', base_proof_sha256=BASE_SHA,
        before_records_sha256=old_digest, current_records_sha256=new_digest,
        unchanged_module_rest_sha256=hashlib.sha256(old_rest.encode()).hexdigest(),
        before_header_method=old_method, current_header_method=new_method,
        inherited_receipts=inherited,
        limitation='Prior 100k identity, 1000 result/mirror and filter proofs retain their original module identity. Only the PGN header method changed; these are not fresh reruns.'))
    previous_manifest_path = ROOT/'handoff_v8/manifest.json'
    previous_manifest = bound.read(previous_manifest_path)
    require(bound.files[str(previous_manifest_path.resolve())] == prior['manifest_sha256'],
            'preceding handoff bytes differ')
    write(output/'native_admission.json', native_admission(previous_manifest['train']))
    destination = ROOT/'handoff_v9'
    refresh(destination)
    published = verify(destination/'manifest.json')
    manifest = bound.read(destination/'manifest.json')
    require(bound.files[str((destination/'manifest.json').resolve())] == published['manifest_sha256'],
            'verified manifest bytes differ')
    require(manifest['runtime'] == runtime == current_runtime(), 'runtime changed during proof')
    require(protected_tree() == protected, 'protected v7 changed during proof')
    require({str(p):sha256(p) for p in files} == current, 'source changed during proof')
    require({str(p) for p in [*HERE.glob('*.py'), *(HERE/'tests').glob('*.py'),
                             HERE/'evidence/extension5h/verify_input_repair.py']} == set(current),
            'source membership changed during proof')
    bound.verify()
    write(output/'published_verify.json', published)
    names = ('source_lineage.json', 'native_admission.json', 'published_verify.json')
    write(output/'COMPLETE.json', dict(status='PASS', strength='UNPROVEN',
        source_files=current, driver_sha256=sha256(__file__), runtime=runtime,
        protected_v7=protected, base_proof_sha256=BASE_SHA,
        manifest_sha256=published['manifest_sha256'], seconds=time.perf_counter()-started,
        receipts={name:dict(path=str(output/name),sha256=sha256(output/name)) for name in names},
        bound_inputs=bound.files,
        limitations=['UNPROVEN; no training, GPU use or engine changes.',
                     'Earlier legacy/result/filter measurements retain their original source identities.',
                     'New tests, source lineage, complete native admission and CPU handoff qualify this PGN-only change.']))
    print(json.dumps(dict(status='PASS', manifest_sha256=published['manifest_sha256'])), flush=True)


if __name__ == '__main__':
    main()
