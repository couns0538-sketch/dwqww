#!/usr/bin/env python3
"""Generate only the requested S03 replacement patch above frozen S02 v2."""
from pathlib import Path
import argparse
import base64
import hashlib
import json
import shutil
import subprocess

PREREQUISITE = 'cc1d5823edbf285aab5311f40b22cd515e42d6f9872e24002a3cd237d5f217d9'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def raw(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'encoding': 'base64', 'data': base64.b64encode(data).decode('ascii')}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--s02-tree', type=Path, required=True)
    parser.add_argument('--s02-patch', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    assert sha(args.s02_patch) == PREREQUISITE, 'unexpected S02 prerequisite'
    here = Path(__file__).resolve().parent
    args.out.mkdir(parents=False, exist_ok=False)
    scratch = args.out / 'forge_sol_S03_git_index_20261025'
    scratch.mkdir()
    for name in ('CMakeLists.txt', 'IDEA_SOURCE.md'):
        shutil.copyfile(args.s02_tree / name, scratch / name)
        (scratch / name).chmod(0o644)
    commands = []
    def git(*parts):
        argv = ['git', '-c', 'core.autocrlf=false', '-c', 'core.hooksPath=/dev/null', *parts]
        child = subprocess.run(argv, cwd=scratch, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, check=False)
        commands.append({'argv': argv, 'cwd': str(scratch), 'exit': child.returncode,
                         'stdout': raw(child.stdout), 'stderr': raw(child.stderr)})
        if child.returncode:
            raise RuntimeError('private git patch command failed')
        return child.stdout
    git('init', '--quiet', '--template=')
    git('add', 'CMakeLists.txt', 'IDEA_SOURCE.md')
    path = scratch / 'CMakeLists.txt'
    source = path.read_text()
    anchor = 'option(FORGE_WARN_UNKNOWN_OPTIONS "Report unknown UCI option names (experiment)" OFF)\n'
    assert source.count(anchor) == 1 and 'FORGE_FIXED_REFERENCES' not in source
    addition = '''
# Optional fixed external oracles; no engine code or default test changes.
option(FORGE_FIXED_REFERENCES "Register fixed perft, mate and bench references" OFF)
if(FORGE_FIXED_REFERENCES)
    find_package(Python3 3.10 REQUIRED COMPONENTS Interpreter)
    enable_testing()
    add_test(NAME forge_fixed_references
        COMMAND ${Python3_EXECUTABLE} -B
            ${CMAKE_CURRENT_SOURCE_DIR}/tests/forge_sol_S03_fixedrefs_20261025.py
            $<TARGET_FILE:forge>
            --out-root ${CMAKE_CURRENT_BINARY_DIR}/forge_sol_S03_runs_20261025)
    set_tests_properties(forge_fixed_references PROPERTIES RUN_SERIAL TRUE LABELS "fixed-reference")
endif()
'''
    path.write_text(source.replace(anchor, anchor + addition, 1))
    path = scratch / 'IDEA_SOURCE.md'
    source = path.read_text()
    anchor = 'Forge 6.4.24 (1ab50b2d), same source as the locked ep10 tree'
    assert source.count(anchor) == 1 and '## S03 fixed external' not in source
    addition = '''## S03 fixed external references, v2 (20261025)

Idea sources: the user's S03 review, the published perft benchmark data at
https://www.chessprogramming.org/Perft_Results and the original Forge tactical
fixtures. Preserve the original oracle, mate/PV checks and float engine. This
test-only patch stacks on the frozen S02 v2 diagnostic patch. Existing output
collisions now produce one error line and exit 1; all expected chess values
remain unchanged. The fixed-reference CMake switch remains OFF by default.

'''
    path.write_text(source.replace(anchor, addition + anchor, 1))
    (scratch / 'tests').mkdir()
    added = []
    for name in ('forge_sol_S03_fixedrefs_20261025.sh',
                 'forge_sol_S03_fixedrefs_20261025.py', 'forge_sol_S03_oracle_20261025.json'):
        target = scratch / 'tests' / name
        shutil.copyfile(here / name, target)
        target.chmod(0o644)
        added.append('tests/' + name)
    git('add', '--intent-to-add', *added)
    git('diff', '--check')
    patch = git('diff', '--binary', '--full-index', '--no-ext-diff', '--unified=5')
    assert patch.count(b'new file mode 100644\n') == 3
    target = args.out / 'forge_sol_S03_fixedrefs_v2_20261025.patch'
    with target.open('xb') as output:
        output.write(patch)
    target.chmod(0o644)
    result = {'status': 'PASS_PATCH_GENERATED_NATIVE_UNVERIFIED',
              'prerequisite_S02_v2_sha256': PREREQUISITE,
              'patch_sha256': sha(target), 'patch': str(target),
              'private_index': str(scratch), 'commands': commands,
              'scope': 'Private index only; no commit, remote, source input edit or engine invocation.'}
    (args.out / 'forge_sol_S03_patch_generation_20261025.json').write_text(
        json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('status', 'patch_sha256', 'patch')}))

if __name__ == '__main__':
    main()
