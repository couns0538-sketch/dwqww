#!/usr/bin/env python3
"""Pure import/pin/AST/read-only binding tests. Never calls native main/run_owned."""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import tempfile
import types
import unittest

HERE=Path(__file__).resolve().parent
NEW=HERE/'forge_sol_S11_scalar_parity_observer_v2_run_20261026.py'
OLD=Path('/tmp/forge_sol_S11_baseline_reuse_prep_20261026/forge_sol_S11_scalar_parity_reuse_run_20261026.py')


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


class DispatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=load('observer_pure_old_dispatch',OLD)
        cls.new=load('observer_pure_v2_dispatch',NEW)
        cls.text=NEW.read_text()

    def test_actual_non_isa_binding_identity_matches_original(self):
        grant=json.loads(Path('/tmp/forge_sol_S11_operator_recovery_20261026/forge_sol_S11_operator_granted_sequence_20261026.json').read_text())
        for row in grant['steps'][-2:]:
            argv=row['argv']
            for role in ('baseline','candidate'):
                build=Path(argv[argv.index('--'+role+'-build')+1])
                first=Path(argv[argv.index('--'+role+'-first')+1])
                with self.subTest(base=row['base'],role=role):
                    a=self.old.bind_arm(build,first,role,grant['verified_S10_commit'])
                    b=self.new.bind_arm(build,first,role,grant['verified_S10_commit'])
                    self.assertEqual(self.old.binding_identity(a),self.new.binding_identity(b))

    def test_changed_observer_pin_refuses_import(self):
        with tempfile.TemporaryDirectory(prefix='forge_sol_S11_PURE_pin_') as folder:
            root=Path(folder);fake=root/'modified_observer.py'
            fake.write_bytes(self.new.OBSERVER_PATH.read_bytes()+b'\n# PURE negative mutation\n')
            candidate=root/'mutated_dispatch.py'
            candidate.write_text(self.text.replace(str(self.new.OBSERVER_PATH),str(fake)))
            with self.assertRaisesRegex(ValueError,'versioned ISA observer source changed'):
                load('PURE_mutated_observer_pin',candidate)

    def test_changed_original_fail_pin_refuses_import(self):
        with tempfile.TemporaryDirectory(prefix='forge_sol_S11_PURE_failpin_') as folder:
            root=Path(folder);fake=root/'modified_original_FAIL.json'
            fake.write_bytes(self.new.FAILED_PARITY_PATH.read_bytes()+b'\n')
            candidate=root/'mutated_dispatch.py'
            candidate.write_text(self.text.replace(str(self.new.FAILED_PARITY_PATH),str(fake)))
            with self.assertRaisesRegex(ValueError,'original failed parity receipt changed'):
                load('PURE_mutated_failed_receipt_pin',candidate)

    def test_exact_postflight_guard_checks_both_pins(self):
        tree=ast.parse(self.text)
        guards=[node for node in ast.walk(tree) if isinstance(node,ast.If)
                and any(isinstance(x,ast.Constant) and x.value=='ISA observer or original failed attempt changed during successor parity' for x in ast.walk(node))]
        self.assertEqual(len(guards),1)
        code=compile(ast.fix_missing_locations(ast.Module(body=guards,type_ignores=[])),str(NEW),'exec')
        for changed in [None,self.new.OBSERVER_PATH,self.new.FAILED_PARITY_PATH]:
            def sha(path):
                if path==changed:return 'WRONG_PURE_MUTATION'
                return self.new.OBSERVER_SHA if path==self.new.OBSERVER_PATH else self.new.FAILED_PARITY_SHA
            context={'proof':types.SimpleNamespace(sha=sha),'OBSERVER_PATH':self.new.OBSERVER_PATH,
                     'OBSERVER_SHA':self.new.OBSERVER_SHA,'FAILED_PARITY_PATH':self.new.FAILED_PARITY_PATH,
                     'FAILED_PARITY_SHA':self.new.FAILED_PARITY_SHA}
            with self.subTest(changed=str(changed)):
                if changed is None:exec(code,context)
                else:
                    with self.assertRaisesRegex(ValueError,'changed during successor parity'):exec(code,context)

    def test_non_isa_definitions_and_limits_remain_identical(self):
        old={node.name:ast.dump(node,include_attributes=False) for node in ast.parse(OLD.read_text()).body if isinstance(node,ast.FunctionDef)}
        new={node.name:ast.dump(node,include_attributes=False) for node in ast.parse(self.text).body if isinstance(node,ast.FunctionDef)}
        self.assertEqual(set(old),set(new))
        self.assertEqual({name for name in old if old[name]!=new[name]},{'main'})
        for literal in ['default=1800','default=500','default=180',"'records_per_chunk':10000","'gzip_level':1"]:
            self.assertIn(literal,self.text)
        self.assertEqual(self.old.proof.SCALAR_FLAGS,self.new.proof.SCALAR_FLAGS)

    def test_original_fail_remains_fail_and_no_arms(self):
        raw=self.new.FAILED_PARITY_PATH.read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),self.new.FAILED_PARITY_SHA)
        value=json.loads(raw)
        self.assertEqual(value['status'],'FAIL')
        self.assertEqual(value['error'],'ValueError: scalar inference uses unsupported packed width')
        self.assertEqual(value['arms'],{})


if __name__=='__main__':unittest.main(verbosity=2)
