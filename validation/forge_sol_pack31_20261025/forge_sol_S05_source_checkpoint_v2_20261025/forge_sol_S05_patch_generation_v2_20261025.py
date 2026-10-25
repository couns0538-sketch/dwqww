#!/usr/bin/env python3
"""Create and check the bounded S05v2 validation patch in private minimal trees."""
from pathlib import Path
import base64, difflib, hashlib, json, shutil, subprocess

P = Path(__file__).resolve().parent
ROOT = P / 'forge_sol_S05_patchwork_v2_20261025'
PACK = P.parent / 'new_handoff_1435/selected/forge_handoff_full_20261025_1435/files'
BASES = {
    'L': PACK / '01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src',
    'Lp': PACK / '01c_lockderived_jobC_S01/forge_h256_e12_lockderived_jobC_S01_src',
    'B': PACK / '01b_base_h256_e12_buffix/forge_h256_e12_buffix_jobC_S01_src',
}
OLD = Path('/workspace/dwqww/releases/forge_sol_pack31_20261025/S05/forge_sol_S05_ctestwire_20261025.patch')
WORK = P / 'forge_sol_S05_checker_work_v2_20261025'
NEW_TOOLS = ['forge_sol_S05_fmacheck_v3_20261025.py', 'forge_sol_S05_fmacheck_tests_20261025.py']
TARGETS = ['CMakeLists.txt', 'IDEA_SOURCE.md',
           'tests/forge_sol_S05_float_parity_20261025.cpp',
           'tests/forge_sol_S05_float_threads_20261025.cpp',
           'tools/forge_sol_S05_float_uci_20261025.py',
           *['tools/' + name for name in NEW_TOOLS]]
UNCHANGED = ['CMakeLists.txt', 'tests/forge_sol_S05_float_parity_20261025.cpp',
             'tests/forge_sol_S05_float_threads_20261025.cpp', 'tools/forge_sol_S05_float_uci_20261025.py']
PATCH = ROOT / 'forge_sol_S05_ctestwire_v2_20261025.patch'
RECEIPT = ROOT / 'forge_sol_S05_patch_generation_receipt_v2_20261025.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'encoding': 'base64', 'data': base64.b64encode(data).decode()}


def minimal(base, name):
    path = ROOT / name
    path.mkdir()
    for file in ['CMakeLists.txt', 'IDEA_SOURCE.md']:
        shutil.copy2(BASES[base] / file, path / file)
    (path / 'tools').mkdir()
    (path / 'tests').mkdir()
    return path


def main():
    ROOT.mkdir(exist_ok=False)
    result = {'status': 'INCOMPLETE', 'commands': [], 'old_patch_sha256': sha(OLD),
              'replacement_Python_sha256': {name: sha(WORK / name) for name in NEW_TOOLS},
              'old_controls': {}, 'new_controls': {}, 'native_execution': False}
    assert result['old_patch_sha256'] == '59294fd6e68ad0701d73038f618acd20ec72f9073faa8c1a19baec48618f2974'
    original_tests = {key: sha(path / 'tests/tests.cpp') for key, path in BASES.items()}
    def save():
        RECEIPT.write_text(json.dumps(result, indent=2) + '\n')
    def run(label, argv, cwd, allowed=(0,)):
        child = subprocess.run([str(x) for x in argv], cwd=cwd, capture_output=True)
        result['commands'].append({'label': label, 'argv': [str(x) for x in argv], 'cwd': str(cwd),
            'exit': child.returncode, 'stdout': raw(child.stdout), 'stderr': raw(child.stderr),
            'child_waited': True, 'stream_capture_complete': True})
        save()
        if child.returncode not in allowed:
            raise RuntimeError(label + ': unexpected exit ' + str(child.returncode))
        return child
    try:
        old_roots = {}
        for base in BASES:
            path = minimal(base, 'forge_sol_S05_old_' + base + '_v2_20261025')
            old_roots[base] = path
            git = run(base + '_old_git_check', ['git', '-c', 'gc.auto=0', 'apply', '--check', OLD], path, (0, 1, 128))
            run(base + '_old_GNU_dry', ['patch', '--batch', '--no-backup-if-mismatch', '-p1', '-F0', '--dry-run', '-i', OLD], path)
            run(base + '_old_GNU_apply', ['patch', '--batch', '--no-backup-if-mismatch', '-p1', '-F0', '-i', OLD], path)
            result['old_controls'][base] = {'git_exit': git.returncode,
                                          'old_source': str(path), 'applied_files': {rel: sha(path / rel) for rel in TARGETS}}
        candidate = minimal('L', 'forge_sol_S05_private_git_v2_20261025')
        run('git_init', ['git', '-c', 'gc.auto=0', 'init', '--quiet', '--template='], candidate)
        run('git_index_baseline', ['git', '-c', 'gc.auto=0', 'add', '--', 'CMakeLists.txt', 'IDEA_SOURCE.md'], candidate)
        for rel in TARGETS:
            shutil.copy2(old_roots['L'] / rel, candidate / rel)
        for name in NEW_TOOLS:
            shutil.copy2(WORK / name, candidate / 'tools' / name)
        before = (BASES['L'] / 'IDEA_SOURCE.md').read_text()
        old_added = []
        for tag, a, b, c, d in difflib.SequenceMatcher(None, before.splitlines(True),
                (old_roots['L'] / 'IDEA_SOURCE.md').read_text().splitlines(True), autojunk=False).get_opcodes():
            if tag == 'insert':
                old_added.extend((old_roots['L'] / 'IDEA_SOURCE.md').read_text().splitlines(True)[c:d])
            elif tag != 'equal':
                raise ValueError('old IDEA patch is not additive')
        first, rest = before.split('\n', 1)
        new_note = ('\n## S05 v2 copied-zero recognition and fixture cleanup (20261025)\n\n'
                    'Idea sources: the observed Windows PC lock clamp disassembly and the existing S05 fixture harness. '
                    'Recognize only unmasked YMM register copies of an already proven zero, retaining the existing '
                    'clobber and control-flow checks. Memory, masked and narrower copies remain unsupported. '
                    'CTest fixture directories are temporary on success and failure; explicit output remains persistent. '
                    'The validation switch remains OFF by default. C++/CMake and engine arithmetic are unchanged.\n\n')
        (candidate / 'IDEA_SOURCE.md').write_text(first + '\n' + ''.join(old_added) + new_note + rest)
        run('git_new_intent', ['git', '-c', 'gc.auto=0', 'add', '-N', '--', *TARGETS[2:]], candidate)
        diff = run('git_diff', ['git', '-c', 'gc.auto=0', 'diff', '--no-ext-diff', '--full-index', '--unified=5', '--', *TARGETS], candidate)
        PATCH.write_bytes(diff.stdout)
        if bytes([79, 112, 101, 110, 65, 73]).lower() in PATCH.read_bytes().lower():
            raise ValueError('forbidden literal in generated patch')
        assert diff.stdout.count(b'new file mode 100644') == 5
        for base in BASES:
            path = minimal(base, 'forge_sol_S05_new_' + base + '_v2_20261025')
            run(base + '_new_git_check', ['git', '-c', 'gc.auto=0', 'apply', '--check', PATCH], path)
            run(base + '_new_GNU_dry', ['patch', '--batch', '--no-backup-if-mismatch', '-p1', '-F0', '--dry-run', '-i', PATCH], path)
            run(base + '_new_GNU_apply', ['patch', '--batch', '--no-backup-if-mismatch', '-p1', '-F0', '-i', PATCH], path)
            for rel in UNCHANGED:
                assert (path / rel).read_bytes() == (old_roots[base] / rel).read_bytes(), (base, rel)
            for name in NEW_TOOLS:
                assert (path / 'tools' / name).read_bytes() == (WORK / name).read_bytes()
            original = (BASES[base] / 'IDEA_SOURCE.md').read_text()
            observed = (path / 'IDEA_SOURCE.md').read_text()
            title, suffix = original.split('\n', 1)
            assert observed == title + '\n' + ''.join(old_added) + new_note + suffix
            assert sha(BASES[base] / 'tests/tests.cpp') == original_tests[base]
            result['new_controls'][base] = {'path': str(path), 'applied_files': {rel: sha(path / rel) for rel in TARGETS},
                 'CMake_CXX_UCI_tool_identical_to_v1': True, 'current_tests_tests_cpp_unchanged': original_tests[base],
                 'original_IDEA_notes_preserved': True, 'new_Python_exact_root_frozen_inputs': True}
        assert all(sha(WORK / name) == result['replacement_Python_sha256'][name] for name in NEW_TOOLS)
        result.update(status='PASS_FORMAT_ALL_THREE_BASES_ONLY_TWO_PYTHON_CONTENT_UPDATES', patch=str(PATCH),
            patch_sha256=sha(PATCH), proper_new_file_headers=5, full_context=5,
            scope='Private minimal target files only. CMake/C++/UCI tool bytes exact v1; IDEA additions relocated to common title. No engine or build run.')
    except BaseException as error:
        result.update(status='FAILED_PRESERVED', error=repr(error))
        raise
    finally:
        save()
    print(json.dumps({'status': result['status'], 'patch_sha256': sha(PATCH), 'root': str(ROOT)}, sort_keys=True))


if __name__ == '__main__':
    main()
