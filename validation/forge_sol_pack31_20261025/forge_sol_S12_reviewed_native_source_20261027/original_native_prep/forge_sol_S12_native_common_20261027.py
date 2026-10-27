"""Pinned S12 adapters over existing S11/S09 infrastructure; no native import work."""
from pathlib import Path
import functools
import hashlib
import importlib.util
import json
import os
import re
import shlex
import sys

sys.dont_write_bytecode = True
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
HERE = Path(__file__).resolve().parent
TMP = Path('/tmp/forge_sol_S12_native_20261027')
DEPENDENCIES = HERE / 'forge_sol_S12_native_dependencies_20261027.json'
DEPENDENCIES_SHA = '684bfbcd2c5916b40a95c2c4ef8d1232dc655e7df77359da0ddfc8148df6a8c9'
INVENTORY = HERE / 'forge_sol_S12_native_source_inventory_20261027.json'
INVENTORY_SHA = 'aff25897dc70d43918a1c3fb83e9715ef4d877deead023f5046dee648b615c88'
PATCH_SHA = '66efe4c94225d95a42e8754e3b11ff363cfb4903a855e60c0bbdfdf8b5a6ee8d'
S11 = Path('/tmp/forge_sol_S11_native_prep_20261026')
RELEASE = Path('/workspace/forge-pack24-20261026/S09_NATIVE_PREP_20261026/forge_sol_S09_build_native_20261026.py')
ASAN = Path('/workspace/forge-pack24-20261026/S09_ASAN_PREP_20261026/forge_sol_S09_build_ASAN_20261026.py')


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1 << 20), b''):
            digest.update(block)
    return digest.hexdigest()


def require(okay, message):
    if not okay:
        raise ValueError(message)


def registry():
    require(sha(DEPENDENCIES) == DEPENDENCIES_SHA, 'S12 dependency registry changed')
    return json.loads(DEPENDENCIES.read_text())


def load_pinned(name, path):
    path = Path(path)
    pins = registry()['files']
    require(str(path) in pins and sha(path) == pins[str(path)], 'dependency path/hash changed: ' + str(path))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def verify_dependencies():
    pins = registry()['files']
    for path, wanted in pins.items():
        require(sha(path) == wanted, 'qualified dependency changed: ' + path)
    return dict(pins)


@functools.cache
def old_builder():
    verify_dependencies()
    return load_pinned('s12_reused_S11_builder', S11 / 'forge_sol_S11_build_native_20261026.py')


@functools.cache
def old_qualifier():
    verify_dependencies()
    return load_pinned('s12_reused_S11_qualifier', S11 / 'forge_sol_S11_qualify_native_20261026.py')


def inventory(root):
    result = {}
    for path in sorted(Path(root).rglob('*')):
        require(not path.is_symlink(), 'source symlink requires explicit review')
        if path.is_file():
            result[path.relative_to(root).as_posix()] = sha(path)
    return result


def frozen():
    require(sha(INVENTORY) == INVENTORY_SHA, 'S12 v2 source inventory changed')
    value = json.loads(INVENTORY.read_text())
    require(value['patch_sha256'] == PATCH_SHA and sha(value['patch']) == PATCH_SHA,
            'single frozen S12 v2 patch changed')
    require(set(value['changed_paths']) == {'CMakeLists.txt', 'include/forge/search.hpp',
            'src/search.cpp', 'src/uci.cpp', 'README.md', 'IDEA_SOURCE.md'}, 'S12 declared diff changed')
    return value


def source_expected(base, role):
    require(base in ('Lprime', 'B') and role in ('baseline', 'candidate'), 'unknown S12 source arm')
    value = frozen()
    baseline = value['original_source_freezes'][base]
    candidate = value['candidate_source_freezes'][base]
    require(set(baseline) == set(candidate) and
            {p for p in baseline if baseline[p] != candidate[p]} == set(value['changed_paths']),
            'candidate differs outside the six S12 paths')
    return baseline if role == 'baseline' else candidate


def verify_originals():
    value = frozen()
    require(all(inventory(Path(root)) == value['original_source_freezes'][base]
                for base, root in value['bases'].items()), 'canonical source changed')


def verify_source(source, base, role):
    expected = source_expected(base, role)
    require(inventory(source) == expected, 'actual S12 source/role differs from frozen v2')
    return expected


def permitted(path):
    p = Path(path)
    return p.is_absolute() and p.resolve() == p and p != TMP and p.is_relative_to(TMP)


def artifact_names(source):
    names = list(old_builder().STDLIB_TARGETS)
    if (Path(source) / 'tests/bad_capture_tests.cpp').exists():
        names.append('forge_bad_capture_tests')
    return names + ['core_archive']


def profile_api(profile):
    require(profile in ('Release', 'ASAN'), 'unknown profile')
    return load_pinned('s12_reused_' + profile + '_recipes', RELEASE if profile == 'Release' else ASAN)


def audit_recipe(source, build, profile, feature):
    require(feature in ('OFF', 'ON'), 'unknown S12 compiled feature setting')
    result = profile_api(profile).audit_recipe(Path(source), Path(build))
    cache = (Path(build) / 'CMakeCache.txt').read_text()
    declares_option = re.search(r'\boption\s*\(\s*FORGE_NNUE_LAZY_ACC\b',
                                (Path(source) / 'CMakeLists.txt').read_text()) is not None
    if declares_option:
        require(re.search(r'^FORGE_NNUE_LAZY_ACC:BOOL=' + feature + '$', cache, re.M) is not None,
                'S12 CMake feature flag differs')
    else:
        require(feature == 'OFF' and not re.search(r'^FORGE_NNUE_LAZY_ACC:', cache, re.M),
                'pristine base cannot have an invented S12 CMake cache entry')
    for row in json.loads((Path(build) / 'compile_commands.json').read_text()):
        argv = row.get('arguments') or shlex.split(row['command'])
        definitions = [x for x in argv if x.startswith(('-DFORGE_', '-UFORGE_'))]
        expected = ['-DFORGE_NNUE_HIDDEN=256'] + (['-DFORGE_NNUE_LAZY_ACC=1'] if feature == 'ON' else [])
        require(sorted(definitions) == sorted(expected), 'source/core/header feature ABI or extra Forge define differs')
    result['S12_feature'] = feature
    return result
