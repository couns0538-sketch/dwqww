import importlib.util
from pathlib import Path
import tempfile
import unittest

spec=importlib.util.spec_from_file_location('build_native',Path(__file__).with_name('build_native.py'))
builder=importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class BuildReceiptTests(unittest.TestCase):
    def stage(self,root):
        (root/'src').mkdir()
        (root/'include').mkdir()
        (root/'tests').mkdir()
        for name in ('bitboard','board','book','eval','eval_params','nnue','search','uci'):
            (root/'src'/f'{name}.cpp').write_text('// fixture\n')
        (root/'tests/tmfit_tests.cpp').write_text('// fixture\n')
        (root/'change.patch').write_text('patch fixture\n')

    def test_actual_lock_without_datagen_builds_only_present_units(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.stage(root)
            units=builder.source_units(root,'engine',Path(__file__))
            self.assertEqual(len(units),8)
            self.assertNotIn('datagen.cpp',[p.name for p in units])
            self.assertEqual(builder.source_units(root,'numeric',Path(__file__)),[root/'tests/tmfit_tests.cpp'])

    def test_ungitted_stage_never_inherits_ancestor_git_head(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.stage(root)
            with self.assertRaises(ValueError):builder.source_identity(root,None,None)
            receipt=builder.source_identity(root,'2'*40,root/'change.patch')
            self.assertIsNone(receipt['source_commit'])
            self.assertIsNone(receipt['source_git_head'])
            self.assertEqual(receipt['base_commit_declared'],'2'*40)
            self.assertIn('src/search.cpp',receipt['source_sha256'])
            before=receipt['source_tree_sha256']
            (root/'include/change.hpp').write_text('changed\n')
            self.assertNotEqual(builder.source_identity(root,'2'*40,root/'change.patch')['source_tree_sha256'],before)

    def test_numeric_commands_compile_then_link_without_executing_target(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.stage(root)
            units=builder.source_units(root,'numeric',Path(__file__))
            commands,binary=builder.build_commands('g++',root,root/'out',units,'numeric',expose=True)
            self.assertEqual(len(commands),2)
            self.assertIn('-c',commands[0])
            self.assertIn('-I'+str(root/'src'),commands[0])
            self.assertIn('-DFORGE_EXPOSE_TUNABLES=1',commands[0])
            self.assertEqual(binary.name,'tmfit_numeric_tests.exe')
            self.assertTrue(all(command[0]=='g++' for command in commands))

    def test_referee_uses_board_from_declared_stage(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.stage(root)
            units=builder.source_units(root,'referee',Path(__file__))
            self.assertEqual(units[1:],[root/'src/board.cpp',root/'src/bitboard.cpp'])
            self.assertEqual(len(units),3)

    def test_all_imported_harness_sources_are_bound_and_changes_fail(self):
        self.assertEqual(set(builder.harness_dependencies()),
                         {'builder_snapshot.py','runner_snapshot.py','resource_governor_snapshot.py'})
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp)
            sources=root/'sources';sources.mkdir()
            out=root/'out';out.mkdir()
            dependencies={name:sources/name for name in builder.harness_dependencies()}
            for source in dependencies.values():source.write_text('original\n')
            receipt=builder.snapshot_harness(out,dependencies)
            builder.verify_harness(receipt)
            for name,source in dependencies.items():
                with self.subTest(name=name):
                    self.assertEqual((out/name).read_bytes(),source.read_bytes())
                    source.write_text('changed\n')
                    with self.assertRaises(RuntimeError):builder.verify_harness(receipt)
                    source.write_text('original\n')


if __name__=='__main__':unittest.main()
