#!/usr/bin/env python3
"""Source-only S27 controls; no engine or compiler processes."""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('s27_hygiene', ROOT / 'forge_sol_S27_hygiene_20261026.py')
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


def patch_file(path, before, after):
    import difflib
    return ''.join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                       fromfile='a/' + path, tofile='b/' + path)).encode()


class HygieneTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='forge_sol_S27_test_20261026_')
        self.root = Path(self.temp.name)
        self.base = self.root / 'input_tree'
        (self.base / 'src').mkdir(parents=True)
        (self.base / 'tests').mkdir()
        (self.base / 'src/main.cpp').write_text('int unchanged = 0;\n')
        (self.base / 'CMakeLists.txt').write_text('cmake_minimum_required(VERSION 3.20)\n')
        self.input = self.root / 'forge_sol_S27_fixture_20261026.patch'

    def tearDown(self):
        self.temp.cleanup()

    def check(self, payload, **kw):
        self.input.write_bytes(payload)
        return MOD.check_submission(self.input, {'fixture': self.base}, self.root / 'new_output', **kw)

    def codes(self, result):
        return {f['code'] for f in result['findings']}

    def test_safe_test_change_applies_and_preserves_input(self):
        target = self.base / 'tests/sample.py'
        target.write_text('x = 1\n')
        before = MOD.tree_inventory(self.base)
        result = self.check(patch_file('tests/sample.py', 'x = 1\n', 'x = 2\n'))
        self.assertEqual(result['status'], 'PASS', result)
        self.assertEqual(MOD.tree_inventory(self.base), before)

    def test_default_counter_requires_guard(self):
        result = self.check(patch_file('src/main.cpp', 'int unchanged = 0;\n',
                                       'int unchanged = 0;\n++current_stats.refreshes;\n'))
        self.assertIn('default_instrumentation', self.codes(result))

    def test_path_traversal_rejected_without_external_write(self):
        result = self.check(patch_file('../escaped.cpp', '', 'int bad;\n'))
        self.assertIn('unsafe_path', self.codes(result))
        self.assertFalse((self.root / 'escaped.cpp').exists())

    def test_protected_directory_rejected(self):
        result = self.check(patch_file('baseline/src/main.cpp', '', 'int bad;\n'))
        self.assertIn('protected_path', self.codes(result))

    def test_existing_output_rejected_unchanged(self):
        out = self.root / 'existing'
        out.mkdir()
        (out / 'sentinel').write_bytes(b'keep')
        self.input.write_bytes(patch_file('tests/sample.py', '', 'x=2\n'))
        with self.assertRaises(ValueError):
            MOD.check_submission(self.input, {'fixture': self.base}, out)
        self.assertEqual((out / 'sentinel').read_bytes(), b'keep')

    def test_duplicate_content_rejected_after_rename(self):
        import hashlib
        payload = patch_file('tests/sample.py', '', 'x=2\n')
        result = self.check(payload, history=[hashlib.sha256(payload).hexdigest()])
        self.assertIn('duplicate_submission', self.codes(result))

    def test_hostile_license_zip_generated_at_runtime(self):
        vendor = ''.join(chr(n) for n in [79, 112, 101, 110, 65, 73])
        notice = 'MIT ' + 'License\n' + 'Copy' + 'right (c) 2026 ' + vendor + '\n'
        z = self.root / 'forge_sol_S27_bad_fixture_20261026.zip'
        with zipfile.ZipFile(z, 'w') as archive:
            archive.writestr('LI' + 'CENSE', notice)
        result = MOD.check_submission(z, {'fixture': self.base}, self.root / 'new_output')
        self.assertTrue({'forbidden_license_file', 'forbidden_notice', 'forbidden_vendor'} & self.codes(result))

    def test_zip_symlink_rejected(self):
        z = self.root / 'forge_sol_S27_symlink_20261026.zip'
        with zipfile.ZipFile(z, 'w') as archive:
            entry = zipfile.ZipInfo('src/link.cpp')
            entry.create_system = 3
            entry.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(entry, '../outside')
        result = MOD.check_submission(z, {'fixture': self.base}, self.root / 'new_output')
        self.assertIn('zip_special_file', self.codes(result))

    def test_zip_duplicate_and_case_collision_rejected(self):
        z = self.root / 'forge_sol_S27_duplicate_20261026.zip'
        with zipfile.ZipFile(z, 'w') as archive:
            archive.writestr('tests/a.py', 'x=1\n')
            archive.writestr('tests/A.py', 'x=2\n')
        result = MOD.check_submission(z, {'fixture': self.base}, self.root / 'new_output')
        self.assertIn('zip_duplicate', self.codes(result))

    def test_zip_traversal_rejected(self):
        z = self.root / 'forge_sol_S27_traversal_20261026.zip'
        with zipfile.ZipFile(z, 'w') as archive:
            archive.writestr('../outside.py', 'x=1\n')
        result = MOD.check_submission(z, {'fixture': self.base}, self.root / 'new_output')
        self.assertIn('unsafe_path', self.codes(result))

    def test_input_symlink_rejected(self):
        target = self.root / 'real.patch'
        target.write_bytes(patch_file('tests/sample.py', '', 'x=1\n'))
        self.input.symlink_to(target)
        result = MOD.check_submission(self.input, {'fixture': self.base}, self.root / 'new_output')
        self.assertIn('input_file', self.codes(result))

    def test_output_inside_source_rejected(self):
        self.input.write_bytes(patch_file('tests/sample.py', '', 'x=1\n'))
        with self.assertRaises(ValueError):
            MOD.check_submission(self.input, {'fixture': self.base}, self.base / 'new_output')
        self.assertFalse((self.base / 'new_output').exists())

    def test_baseline_symlink_rejected(self):
        (self.base / 'src/external.cpp').symlink_to('/etc/passwd')
        result = self.check(patch_file('tests/sample.py', '', 'x=1\n'))
        self.assertIn('base_special_file', self.codes(result))

    def test_abbreviated_doc_hash_rejected(self):
        result = self.check(patch_file('tests/NOTES.md', '', 'sha256 abcdef12...01234567\n'))
        self.assertIn('abbreviated_hash', self.codes(result))

    def test_new_setter_without_advertisement_rejected(self):
        (self.base / 'src/uci.cpp').write_text('void options() {}\n')
        result = self.check(patch_file('src/uci.cpp', 'void options() {}\n',
                                       'void options() {}\nif (name == "Ghost") { }\n'))
        self.assertIn('unadvertised_runtime_option', self.codes(result))

    def test_ifdef_off_build_option_is_allowed(self):
        (self.base / 'CMakeLists.txt').write_text('option(EXPERIMENT "experiment" OFF)\n')
        after = 'int unchanged = 0;\n#ifdef EXPERIMENT\n++current_stats.refreshes;\n#endif\n'
        result = self.check(patch_file('src/main.cpp', 'int unchanged = 0;\n', after))
        self.assertEqual(result['status'], 'PASS', result)

    def test_if_not_defined_off_guard_is_default_work(self):
        (self.base / 'CMakeLists.txt').write_text('option(EXPERIMENT "experiment" OFF)\n')
        after = 'int unchanged = 0;\n#ifndef EXPERIMENT\n++current_stats.refreshes;\n#endif\n'
        result = self.check(patch_file('src/main.cpp', 'int unchanged = 0;\n', after))
        self.assertIn('default_instrumentation', self.codes(result))

    def test_unguarded_compile_definition_does_not_hide_work(self):
        old = 'option(EXPERIMENT "experiment" OFF)\n'
        (self.base / 'CMakeLists.txt').write_text(old)
        after = 'int unchanged = 0;\n#ifdef EXPERIMENT\n++current_stats.refreshes;\n#endif\n'
        payload = patch_file('CMakeLists.txt', old, old + 'target_compile_definitions(forge_core PRIVATE EXPERIMENT=1)\n')
        payload += patch_file('src/main.cpp', 'int unchanged = 0;\n', after)
        result = self.check(payload)
        self.assertIn('default_build_configuration', self.codes(result))

    def test_output_path_can_contain_spaces(self):
        self.input.write_bytes(patch_file('tests/sample.py', '', 'x=1\n'))
        result = MOD.check_submission(self.input, {'fixture': self.base}, self.root / 'new output')
        self.assertEqual(result['status'], 'PASS', result)

    def test_overlay_zip_preserves_exact_requested_bytes(self):
        z = self.root / 'forge_sol_S27_overlay_20261026.zip'
        with zipfile.ZipFile(z, 'w') as archive:
            archive.writestr('tests/sample.py', 'x=1\n')
        result = MOD.check_submission(z, {'fixture': self.base}, self.root / 'new_output')
        self.assertEqual(result['status'], 'PASS', result)
        self.assertEqual((self.root / 'new_output/fixture/candidate/tests/sample.py').read_bytes(), b'x=1\n')

    def test_signatures_repeat_with_different_output_directory(self):
        payload = patch_file('tests/sample.py', '', 'x=1\n')
        first = self.check(payload)
        second = MOD.check_submission(self.input, {'fixture': self.base}, self.root / 'second_output')
        self.assertEqual(first['deterministic_signature_sha256'], second['deterministic_signature_sha256'])

    def test_git_pointer_file_patch_rejected(self):
        result = self.check(patch_file('.git', '', 'gitdir: /tmp/elsewhere\n'))
        self.assertIn('protected_path', self.codes(result))

    def test_git_pointer_zip_rejected(self):
        z = self.root / 'forge_sol_S27_gitpointer_20261026.zip'
        with zipfile.ZipFile(z, 'w') as archive:
            archive.writestr('.git', 'gitdir: /tmp/elsewhere\n')
        result = MOD.check_submission(z, {'fixture': self.base}, self.root / 'new_output')
        self.assertIn('protected_path', self.codes(result))

    def test_defined_zero_is_still_defined(self):
        (self.base / 'CMakeLists.txt').write_text('option(FEATURE "feature" OFF)\n')
        before = '#define FEATURE 0\nint unchanged = 0;\n'
        (self.base / 'src/main.cpp').write_text(before)
        after = before + '#if defined(FEATURE)\n++current_stats.refreshes;\n#endif\n'
        result = self.check(patch_file('src/main.cpp', before, after))
        self.assertIn('default_instrumentation', self.codes(result))

    def test_commented_fake_guard_does_not_hide_default_work(self):
        (self.base / 'CMakeLists.txt').write_text('option(FEATURE "feature" OFF)\n')
        after = 'int unchanged = 0;\n/*\n#if FEATURE\n*/\n++current_stats.refreshes;\n/*\n#endif\n*/\n'
        result = self.check(patch_file('src/main.cpp', 'int unchanged = 0;\n', after))
        self.assertIn('default_instrumentation', self.codes(result))

    def test_unsafe_git_header_cannot_hide_behind_safe_unified_headers(self):
        payload = b'diff --git a/../../outside b/../../outside\n' + patch_file('tests/sample.py', '', 'x=1\n')
        result = self.check(payload)
        self.assertIn('unsafe_path', self.codes(result))

    def test_unsafe_Index_header_rejected(self):
        result = self.check(b'Index: ../../outside\n' + patch_file('tests/sample.py', '', 'x=1\n'))
        self.assertIn('unsafe_path', self.codes(result))

    def test_global_compile_flag_change_rejected(self):
        before = (self.base / 'CMakeLists.txt').read_text()
        after = before + 'add_compile_definitions(FEATURE=1)\nset(CMAKE_CXX_FLAGS "-DFEATURE=1")\n'
        result = self.check(patch_file('CMakeLists.txt', before, after))
        self.assertIn('default_build_configuration', self.codes(result))

    def test_mixed_patch_and_source_zip_rejected(self):
        z = self.root / 'forge_sol_S27_mixed_20261026.zip'
        with zipfile.ZipFile(z, 'w') as archive:
            archive.writestr('feature.patch', patch_file('tests/sample.py', '', 'x=1\n'))
            archive.writestr('src/nnue.cpp', '++current_stats.refreshes;\n')
        result = MOD.check_submission(z, {'fixture': self.base}, self.root / 'new_output')
        self.assertIn('zip_mixed_submission', self.codes(result))

    def test_wrapped_reviewed_patch_cannot_evade_history(self):
        payload = patch_file('tests/sample.py', '', 'x=1\n')
        z = self.root / 'forge_sol_S27_wrapped_20261026.zip'
        with zipfile.ZipFile(z, 'w') as archive:
            archive.writestr('renamed.patch', payload)
        result = MOD.check_submission(z, {'fixture': self.base}, self.root / 'new_output', history=[MOD.sha_bytes(payload)])
        self.assertIn('duplicate_submission', self.codes(result))

    def test_option_assignment_cannot_override_OFF_guard(self):
        before = 'option(FEATURE "feature" OFF)\n'
        (self.base / 'CMakeLists.txt').write_text(before)
        after = before + 'set(FEATURE ON CACHE BOOL "forced" FORCE)\nif(FEATURE)\ntarget_compile_definitions(forge_core PRIVATE FEATURE=1)\nendif()\n'
        result = self.check(patch_file('CMakeLists.txt', before, after))
        self.assertIn('default_build_configuration', self.codes(result))

    def test_history_loader_rejects_abbreviated_digest(self):
        p = self.root / 'forge_sol_S27_history_20261026.json'
        p.write_text(json.dumps(['a' * 12]))
        with self.assertRaises(ValueError):
            MOD.load_history(p)

    def test_zip_encrypted_flag_rejected(self):
        z = self.root / 'forge_sol_S27_encrypted_20261026.zip'
        with zipfile.ZipFile(z, 'w') as archive:
            archive.writestr('tests/a.py', 'x=1\n')
        data = bytearray(z.read_bytes())
        for signature, offset in [(b'PK\x03\x04', 6), (b'PK\x01\x02', 8)]:
            pos = data.index(signature) + offset
            data[pos] |= 1
        z.write_bytes(data)
        result = MOD.check_submission(z, {'fixture': self.base}, self.root / 'new_output')
        self.assertIn('zip_encrypted', self.codes(result))

    def test_zip_member_size_limit(self):
        z = self.root / 'forge_sol_S27_member_limit_20261026.zip'
        with zipfile.ZipFile(z, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('tests/large.txt', b'a' * (MOD.MAX_MEMBER + 1))
        result = MOD.check_submission(z, {'fixture': self.base}, self.root / 'new_output')
        self.assertIn('zip_limit', self.codes(result))

    def test_zip_compression_ratio_limit(self):
        z = self.root / 'forge_sol_S27_ratio_limit_20261026.zip'
        with zipfile.ZipFile(z, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('tests/ratio.txt', b'a' * (1024 * 1024 + 1))
        result = MOD.check_submission(z, {'fixture': self.base}, self.root / 'new_output')
        self.assertIn('zip_ratio', self.codes(result))

    def test_zip_entry_count_limit(self):
        z = self.root / 'forge_sol_S27_count_limit_20261026.zip'
        with zipfile.ZipFile(z, 'w') as archive:
            for i in range(MOD.MAX_FILES + 1):
                archive.writestr('tests/f' + str(i) + '.txt', '')
        result = MOD.check_submission(z, {'fixture': self.base}, self.root / 'new_output')
        self.assertIn('zip_limit', self.codes(result))

    def test_gitlink_mode_rejected(self):
        payload = b'diff --git a/tests/a.py b/tests/a.py\nnew file mode 160000\n--- /dev/null\n+++ b/tests/a.py\n@@ -0,0 +1 @@\n+x=1\n'
        result = self.check(payload)
        self.assertIn('patch_special_file', self.codes(result))

    def test_binary_patch_rejected(self):
        result = self.check(b'diff --git a/tests/a.bin b/tests/a.bin\nGIT binary patch\nliteral 2\nxy\n')
        self.assertIn('binary_patch', self.codes(result))

    def test_else_of_disabled_guard_is_default_work(self):
        (self.base / 'CMakeLists.txt').write_text('option(FEATURE "feature" OFF)\n')
        after = 'int unchanged = 0;\n#if FEATURE\nint optional=1;\n#else\n++current_stats.refreshes;\n#endif\n'
        result = self.check(patch_file('src/main.cpp', 'int unchanged = 0;\n', after))
        self.assertIn('default_instrumentation', self.codes(result))

    def test_literal_true_guard_is_default_work(self):
        after = 'int unchanged = 0;\n#if 1\n++current_stats.refreshes;\n#endif\n'
        result = self.check(patch_file('src/main.cpp', 'int unchanged = 0;\n', after))
        self.assertIn('default_instrumentation', self.codes(result))

    def test_zip_original_NUL_name_is_rejected(self):
        z = self.root / 'forge_sol_S27_nul_20261026.zip'
        with zipfile.ZipFile(z, 'w') as archive:
            archive.writestr('tests/a.py', 'x=1\n')
        data = z.read_bytes().replace(b'tests/a.py', b'tests/a\x00py')
        z.write_bytes(data)
        result = MOD.check_submission(z, {'fixture': self.base}, self.root / 'new_output')
        self.assertIn('unsafe_path', self.codes(result))

    def test_bundled_history_is_used_when_history_omitted(self):
        self.input.write_bytes(patch_file('tests/sample.py', '', 'x=1\n'))
        result = MOD.check_submission(self.input, {'fixture': self.base}, self.root / 'new_output')
        self.assertEqual(result['history']['role'], 'bundled_prior_submissions')
        self.assertGreater(len(result['history']['entries']), 0)

    def test_cmake_bracket_comment_cannot_hide_default_configuration(self):
        before = 'option(FEATURE "feature" OFF)\n'
        (self.base / 'CMakeLists.txt').write_text(before)
        after = before + '#[[\nif(FEATURE)\n]]\nadd_compile_definitions(FEATURE=1)\n#[[\nendif()\n]]\n'
        result = self.check(patch_file('CMakeLists.txt', before, after))
        self.assertTrue({'cmake_grammar_unverified', 'default_build_configuration'} & self.codes(result))

    def test_multiline_global_command_argument_change_is_checked(self):
        before = 'add_compile_definitions(\n ORIGINAL=1\n)\n'
        after = 'add_compile_definitions(\n ORIGINAL=1\n FEATURE=1\n)\n'
        (self.base / 'CMakeLists.txt').write_text(before)
        result = self.check(patch_file('CMakeLists.txt', before, after))
        self.assertIn('default_build_configuration', self.codes(result))


PACK = Path('/workspace/forge-pack24-20261025/new_handoff_1435/selected/forge_handoff_full_20261025_1435/files')


@unittest.skipUnless(PACK.is_dir(), 'Supplied exact historical source controls are unavailable')
class SuppliedControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='forge_sol_S27_supplied_20261026_')
        self.root = Path(self.temp.name)
        self.source = PACK / '01_lock_src_h256_e12/forge_h256_e12_1ab50b2d_src'
        self.buffix = PACK / '02_buffix/fc_sol_buffix_h256e12_vs_lock.patch'
        self.review = PACK / '02_buffix/CR_PASS_sol_buffix_h256e12_samediff.txt'
        self.jobC = PACK / '09_sol_returns/sol_return_jobC_20261025/forge_sol_knownfail_h256e12_20261025.patch'
        self.jobA = PACK / '09_sol_returns/sol_return_jobA_20261025/forge_sol_exactint32_h256e12_20261025.patch'

    def tearDown(self):
        self.temp.cleanup()

    def view(self, patch, name):
        # Real, complete bytes of each patch-target file; no engine/build claim.
        dest = self.root / name
        dest.mkdir()
        paths = {c['path'] for c in MOD.parse_patch(patch.read_bytes())} | {'CMakeLists.txt'}
        for rel in paths:
            p = self.source / rel
            if p.exists():
                target = dest / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, target)
        return dest

    def capture(self, label, result, out):
        target = os.environ.get('S27_CONTROL_CAPTURE')
        if target:
            row = {'control': label, 'fixture_scope': 'Exact historical pre-patch target-file view; not full-source build', 'result': result,
                   'raw': [json.loads((out / n).read_text()) for n in result['raw_records']]}
            with Path(target).open('a') as stream:
                stream.write(json.dumps(row, sort_keys=True) + '\n')

    def test_actual_reviewed_buffix_positive_and_history_negative(self):
        base = self.view(self.buffix, 'historical_L')
        out = self.root / 'new_output'
        result = MOD.check_submission(self.buffix, {'historical_L': base}, out,
                                      history=[], control_role='approved_buffix_control', review_record=self.review)
        self.capture('buffix_empty_history_positive', result, out)
        self.assertEqual(result['status'], 'PASS', result)
        again = self.root / 'repeat_output'
        repeated = MOD.check_submission(self.buffix, {'historical_L': base}, again, history=[MOD.sha_file(self.buffix)],
                                        control_role='approved_buffix_control', review_record=self.review)
        self.capture('buffix_repeated_sha_negative', repeated, again)
        self.assertEqual({f['code'] for f in repeated['findings']}, {'duplicate_submission'})

    def test_actual_JobC_on_historical_L_and_preJobC_B(self):
        base = self.view(self.buffix, 'historical_L')
        (base / 'tests').mkdir(exist_ok=True)
        shutil.copy2(self.source / 'tests/tests.cpp', base / 'tests/tests.cpp')
        preB = self.root / 'historical_B_preJobC'
        shutil.copytree(base, preB)
        import subprocess
        applied = subprocess.run(['patch', '--batch', '--forward', '--fuzz=0', '-p1', '-i', str(self.buffix)], cwd=preB, capture_output=True)
        self.assertEqual(applied.returncode, 0, applied.stderr)
        out = self.root / 'new_output'
        result = MOD.check_submission(self.jobC, {'historical_L': base, 'historical_B_preJobC': preB}, out, history=[])
        self.capture('jobC_empty_history_two_historical_positive', result, out)
        self.assertEqual(result['status'], 'PASS', result)

    def test_actual_JobA_default_defects_all_detected(self):
        base = self.view(self.jobA, 'historical_L')
        out = self.root / 'new_output'
        result = MOD.check_submission(self.jobA, {'historical_L': base}, out, history=[])
        self.capture('jobA_default_instrumentation_option_stats_negative', result, out)
        codes = {f['code'] for f in result['findings']}
        self.assertTrue({'default_instrumentation', 'default_runtime_option', 'default_bench_statistics'} <= codes, result)


if __name__ == '__main__':
    unittest.main()
