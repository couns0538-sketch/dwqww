#!/usr/bin/env python3
"""Repair S25 Git formatting in minimal private copies without changing test behavior."""
from pathlib import Path
import base64, difflib, hashlib, json, re, shutil, subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE / 'forge_sol_S25_patchwork_v2_20261025'
AUDIT = HERE.parent / 'S25_v2_audit/forge_sol_S25_v2_resume_audit_20261025.json'
PUBLISHED = Path('/workspace/dwqww/releases/forge_sol_pack31_20261025/S25')
PATCH = ROOT / 'forge_sol_S25_outcontract_v2_20261025.patch'
RECEIPT = ROOT / 'forge_sol_S25_patch_generation_receipt_v2_20261025.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def raw(data):
    return {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
            'encoding': 'base64', 'data': base64.b64encode(data).decode()}


def main():
    assert sha(AUDIT) == 'b14028e6886b637c33b2c60a7fcfcd20c6f34600b321b3bbbd16a1959cd780f5'
    audit = json.loads(AUDIT.read_text())
    old_patch = Path(audit['original_patch']['path'])
    assert sha(old_patch) == 'a8317834664d249f4d549c29d5bd30975c0fe8058d713c466f4a23aee6a3e5b2'
    targets = re.findall(r'^\+\+\+ b/(.+)$', old_patch.read_text(), re.M)
    assert set(targets) == {'CMakeLists.txt', 'IDEA_SOURCE.md',
        'tests/forge_sol_S25_outcontract_20261025.py',
        'tests/forge_sol_S25_options_20261025.json',
        'tests/forge_sol_S25_parser_tests_20261025.py'}
    bases = {row['base']: Path(row['source']) for row in audit['source_probes']}
    old_applied = {row['base']: Path(row['mini_applied']) for row in audit['source_probes']}
    ROOT.mkdir(exist_ok=False)
    result = {'status': 'INCOMPLETE', 'commands': [], 'prior_audit_sha256': sha(AUDIT),
              'old_patch_sha256': sha(old_patch), 'source_checks': {}, 'native_execution': False,
              'prior_Git_failures': 'Actual three dev/null errors per base in the existing audit; not rerun here'}
    def save():
        RECEIPT.write_text(json.dumps(result, indent=2) + '\n')
    def run(label, argv, cwd):
        child = subprocess.run([str(x) for x in argv], cwd=cwd, capture_output=True)
        result['commands'].append({'label': label, 'argv': [str(x) for x in argv],
            'cwd': str(cwd), 'exit': child.returncode, 'stdout': raw(child.stdout),
            'stderr': raw(child.stderr), 'child_waited': True, 'stream_capture_complete': True})
        save()
        if child.returncode:
            raise RuntimeError(label + ': exit ' + str(child.returncode))
        return child
    def minimal(base, name):
        path = ROOT / name
        path.mkdir()
        for rel in ['CMakeLists.txt', 'IDEA_SOURCE.md']:
            shutil.copy2(bases[base] / rel, path / rel)
        (path / 'tests').mkdir()
        return path
    try:
        source_before = {base: {str(f.relative_to(tree)): sha(f)
            for folder in ['src', 'include', 'tests'] for f in (tree / folder).rglob('*') if f.is_file()}
            for base, tree in bases.items()}
        candidate = minimal('L', 'forge_sol_S25_private_git_v2_20261025')
        run('private_git_init', ['git', '-c', 'gc.auto=0', 'init', '--quiet', '--template='], candidate)
        run('private_git_index', ['git', '-c', 'gc.auto=0', 'add', '--', 'CMakeLists.txt', 'IDEA_SOURCE.md'], candidate)
        for rel in targets:
            shutil.copy2(old_applied['L'] / rel, candidate / rel)
        before_lines = (bases['L'] / 'IDEA_SOURCE.md').read_text().splitlines(True)
        old_lines = (old_applied['L'] / 'IDEA_SOURCE.md').read_text().splitlines(True)
        addition = []
        for tag, a, b, c, d in difflib.SequenceMatcher(None, before_lines, old_lines, autojunk=False).get_opcodes():
            if tag == 'insert':
                addition.extend(old_lines[c:d])
            elif tag != 'equal':
                raise ValueError('original S25 IDEA change is not purely additive')
        block = ''.join(addition)
        first, suffix = ''.join(before_lines).split('\n', 1)
        (candidate / 'IDEA_SOURCE.md').write_text(first + '\n' + block + suffix)
        new_files = [rel for rel in targets if rel.startswith('tests/')]
        run('private_git_intent_new', ['git', '-c', 'gc.auto=0', 'add', '-N', '--', *new_files], candidate)
        diff = run('private_git_diff_U5', ['git', '-c', 'gc.auto=0', 'diff', '--no-ext-diff', '--full-index', '--unified=5', '--', *targets], candidate)
        PATCH.write_bytes(diff.stdout)
        assert diff.stdout.count(b'new file mode 100644') == 3
        assert bytes([79, 112, 101, 110, 65, 73]).lower() not in diff.stdout.lower()
        for base, tree in bases.items():
            path = minimal(base, 'forge_sol_S25_new_' + base + '_v2_20261025')
            for label, argv in [('Git_check', ['git', '-c', 'gc.auto=0', 'apply', '--check', PATCH]),
                    ('GNU_F0_dry', ['patch', '--batch', '--no-backup-if-mismatch', '-p1', '-F0', '--dry-run', '-i', PATCH]),
                    ('GNU_F0_apply', ['patch', '--batch', '--no-backup-if-mismatch', '-p1', '-F0', '-i', PATCH])]:
                run(base + '_' + label, argv, path)
            identical = {}
            for rel in ['CMakeLists.txt', *new_files]:
                assert (path / rel).read_bytes() == (old_applied[base] / rel).read_bytes()
                identical[rel] = sha(path / rel)
            for rel in new_files:
                assert (path / rel).read_bytes() == (PUBLISHED / Path(rel).name).read_bytes()
            title, tail = (tree / 'IDEA_SOURCE.md').read_text().split('\n', 1)
            assert (path / 'IDEA_SOURCE.md').read_text() == title + '\n' + block + tail
            after = {str(f.relative_to(tree)): sha(f)
                for folder in ['src', 'include', 'tests'] for f in (tree / folder).rglob('*') if f.is_file()}
            assert source_before[base] == after
            result['source_checks'][base] = {'path': str(path), 'byte_identical_v1_files': identical,
                'original_src_include_tests_unchanged': True, 'production_files': len([x for x in after if x.startswith(('src/', 'include/'))]),
                'current_tests_cpp_sha256': sha(tree / 'tests/tests.cpp'), 'original_IDEA_title_and_suffix_unchanged': True,
                'feature_default_OFF': 'option(FORGE_OUTPUT_CONTRACT "Register normal UCI and bench output-contract tests" OFF)' in (path / 'CMakeLists.txt').read_text()}
        result.update(status='PASS_FORMAT_ONLY_ALL_THREE_BASES', patch=str(PATCH), patch_sha256=sha(PATCH),
            IDEA_addition_nonblank_unchanged=True, proper_new_file_headers=3, full_context=5,
            scope='Exact existing CMake/checker/allowlist/parser bytes; only Git format and identical IDEA paragraph placement differ. No new behavior, engine or compiler execution.')
    except BaseException as error:
        result.update(status='FAILED_PRESERVED', error=repr(error))
        raise
    finally:
        save()
    print(json.dumps({'status': result['status'], 'patch_sha256': sha(PATCH), 'root': str(ROOT)}, sort_keys=True))


if __name__ == '__main__':
    main()
