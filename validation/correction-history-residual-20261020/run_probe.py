#!/usr/bin/env python3
"""Freeze, build and run the single declared arithmetic ablation; no Git writes."""
import datetime
import difflib
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile

REPO = Path('/workspace/dwqww')
EVIDENCE = REPO / 'validation/correction-history-residual-20261020'
WORK = Path('/workspace/.cloud-setup/correction-history-residual-20261020-attempt2')
CMAKE = '/workspace/.cloud-setup/venv/bin/cmake'
REV = '47f0560221d986e41a309853e1295c557fcf5bf6'
OLD = 'entry = std::clamp((entry * (256 - weight) + diff * weight) / 256, -CorrectionLimit, CorrectionLimit);'
NEW = 'entry = std::clamp(entry + diff * weight / 256, -CorrectionLimit, CorrectionLimit);'
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', ASAN_OPTIONS='detect_leaks=1:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1:print_stacktrace=1')
records = []

def sha(data):
    return hashlib.sha256(data).hexdigest()

def manifest(root):
    return {str(p.relative_to(root)): sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file()}

def run(label, command, expected=0, cwd=WORK):
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = subprocess.run(command, cwd=cwd, env=ENV, capture_output=True)
    (EVIDENCE / (label + '.stdout')).write_bytes(result.stdout)
    (EVIDENCE / (label + '.stderr')).write_bytes(result.stderr)
    record = dict(label=label, command=command, cwd=str(cwd), started_utc=started,
                  finished_utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                  returncode=result.returncode, expected_returncode=expected)
    records.append(record)
    (EVIDENCE / 'commands.json').write_text(json.dumps(records, indent=2) + '\n')
    print(json.dumps(record), flush=True)
    if result.returncode != expected:
        raise RuntimeError(f'{label}: exit {result.returncode}, expected {expected}; inspect raw logs')
    return result.stdout

EVIDENCE.mkdir(parents=True, exist_ok=True)
WORK.mkdir(parents=True, exist_ok=True)
archive = subprocess.check_output(['git','archive','--format=tar',REV,'src','include'], cwd=REPO)
(EVIDENCE / 'frozen-core-source.tar').write_bytes(archive)
compiler = run('compiler-version', ['c++','--version']).decode()
history_commands = [
    ['git','log','--all','--format=%H %s','-G',r'entry [+].*diff|entry [+]=.*diff|256 - weight','--','src/search.cpp'],
    ['git','log','--all','--format=%H %s','--grep=correction','-i'],
    ['git','show','524b0ca:src/search.cpp'],
    ['git','show','a7368e2','--','src/search.cpp','include/forge/search.hpp'],
    ['git','show','2281239','--','src/search.cpp','include/forge/search.hpp'],
    ['git','show','d3c9507','--','src/search.cpp'],
]
for i,command in enumerate(history_commands):
    run(f'history-{i}', command, cwd=REPO)
provenance = dict(frozen_revision=REV, archive_sha256=sha(archive), compiler=compiler,
                  driver_sha256=sha((EVIDENCE/'probe.cpp').read_bytes()),
                  cmake_sha256=sha((EVIDENCE/'probe-CMakeLists.txt').read_bytes()),
                  baseline_semantics='EMA toward the remaining corrected-eval residual',
                  counterfactual_semantics='residual increment with same clamps, depth gain, two keys and coefficient',
                  source_methods='actual Worker::corrected_eval and Worker::update_correction; existing SearcherTestProbe friendship')
before = {}
for model in ('ema','increment'):
    project = WORK/model
    source = project/'source'
    if project.exists():
        raise RuntimeError(f'refusing to overwrite existing run directory {project}')
    source.mkdir(parents=True)
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        tar.extractall(source, filter='data')
    original = (source/'src/search.cpp').read_text()
    if original.count(OLD)!=1:
        raise RuntimeError('assignment is not unique in frozen source')
    if model=='increment':
        candidate = original.replace(OLD,NEW)
        (source/'src/search.cpp').write_text(candidate)
        patch = ''.join(difflib.unified_diff(original.splitlines(True),candidate.splitlines(True),
                     fromfile='a/src/search.cpp',tofile='b/src/search.cpp'))
        (EVIDENCE/'candidate.patch').write_text(patch)
    shutil.copyfile(EVIDENCE/'probe.cpp',project/'probe.cpp')
    shutil.copyfile(EVIDENCE/'probe-CMakeLists.txt',project/'CMakeLists.txt')
    before[model] = manifest(source)
(EVIDENCE/'source-before.json').write_text(json.dumps(before,indent=2)+'\n')
provenance['source_manifests_sha256']=sha((EVIDENCE/'source-before.json').read_bytes())
provenance['candidate_patch_sha256']=sha((EVIDENCE/'candidate.patch').read_bytes())
(EVIDENCE/'PROVENANCE.json').write_text(json.dumps(provenance,indent=2)+'\n')

binary_hashes={}
for sanitizers in (False,True):
    flavor='asan-ubsan' if sanitizers else 'release'
    for model in ('ema','increment'):
        project=WORK/model
        build=WORK/(model+'-'+flavor)
        label=model+'-'+flavor
        run(label+'-configure',[CMAKE,'-S',str(project),'-B',str(build),'-DCMAKE_BUILD_TYPE=RelWithDebInfo' if sanitizers else '-DCMAKE_BUILD_TYPE=Release',
            '-DCMAKE_CXX_COMPILER=/usr/bin/g++-14','-DCMAKE_EXPORT_COMPILE_COMMANDS=ON','-DPROBE_SANITIZERS='+('ON' if sanitizers else 'OFF')])
        run(label+'-build',[CMAKE,'--build',str(build),'--target','correction_probe','-j2'])
        executable=build/'correction_probe'
        binary_hashes[label]=sha(executable.read_bytes())
        shutil.copyfile(build/'compile_commands.json',EVIDENCE/(label+'-compile-commands.json'))
        shutil.copyfile(executable,EVIDENCE/(label+'-probe'))
        run(label+'-own-contract',[str(executable),model])
        if not sanitizers and model=='ema':
            run('ema-release-increment-contract-expected-RED',[str(executable),'increment'],expected=1)
after={model:manifest(WORK/model/'source') for model in ('ema','increment')}
(EVIDENCE/'source-after.json').write_text(json.dumps(after,indent=2)+'\n')
if before!=after:
    raise RuntimeError('exported core sources changed during probe')
(EVIDENCE/'binary-sha256.json').write_text(json.dumps(binary_hashes,indent=2)+'\n')
(EVIDENCE/'completion.json').write_text(json.dumps(dict(status='arithmetic-probe-complete', source_unchanged_before_after=True,
    speed_measured=False, search_workloads_run=False, matches_run=False, strength='unmeasured'),indent=2)+'\n')
print('COMPLETE source manifests unchanged; arithmetic only; no strength/speed result', flush=True)
