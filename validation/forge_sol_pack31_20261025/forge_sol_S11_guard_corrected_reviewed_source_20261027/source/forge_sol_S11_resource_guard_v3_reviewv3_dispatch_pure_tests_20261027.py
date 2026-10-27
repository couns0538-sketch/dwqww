#!/usr/bin/env python3
"""Source pins/AST and read-only actual bindings only; no native main run."""
from pathlib import Path
import ast
import hashlib
import importlib.util
import json
import tempfile
import types
import unittest

HERE=Path(__file__).resolve().parent
NEW=HERE/'forge_sol_S11_scalar_parity_resource_guard_v3_reviewv3_run_20261027.py'
OLD=Path('/tmp/forge_sol_S11_scalar_observer_v2_prep_20261026/forge_sol_S11_scalar_parity_observer_v2_run_20261026.py')


def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module


class Dispatch(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old=load('S11_PURE_v2_dispatch',OLD);cls.new=load('S11_PURE_v3_dispatch',NEW);cls.text=NEW.read_text()

    def test_all_four_actual_arm_bindings_equal_v2(self):
        prereg=json.loads(Path('/tmp/forge_sol_S11_scalar_observer_v2_prep_20261026/forge_sol_S11_scalar_observer_v2_preregister_20261026.json').read_text())
        for row in prereg['commands']:
            argv=row['argv_template'];commit=argv[argv.index('--s10-published-commit')+1]
            for role in ['baseline','candidate']:
                receipt=Path(argv[argv.index('--'+role+'-build')+1]);first=Path(argv[argv.index('--'+role+'-first')+1])
                a=self.old.bind_arm(receipt,first,role,commit);b=self.new.bind_arm(receipt,first,role,commit)
                with self.subTest(base=row['base'],role=role):self.assertEqual(self.old.binding_identity(a),self.new.binding_identity(b))

    def test_changed_resource_source_pin_refuses_import(self):
        with tempfile.TemporaryDirectory(prefix='S11_PURE_RESOURCE_PIN_') as folder:
            root=Path(folder);fake=root/'changed_resource.py';fake.write_bytes(self.new.RESOURCE_PATH.read_bytes()+b'\n# PURE mutation\n')
            consumer=root/'mutated_dispatch.py';consumer.write_text(self.text.replace(str(self.new.RESOURCE_PATH),str(fake)))
            with self.assertRaisesRegex(ValueError,'versioned resource observer source changed'):load('PURE_bad_resource',consumer)

    def test_changed_capture_timeout_pin_refuses_import(self):
        with tempfile.TemporaryDirectory(prefix='S11_PURE_TIMEOUT_PIN_') as folder:
            root=Path(folder);fake=root/'changed_TIMEOUT.json';fake.write_bytes(self.new.TIMEOUT_FAIL_PATH.read_bytes()+b'\n')
            consumer=root/'mutated_dispatch.py';consumer.write_text(self.text.replace(str(self.new.TIMEOUT_FAIL_PATH),str(fake)))
            with self.assertRaisesRegex(ValueError,'original capture timeout receipt changed'):load('PURE_bad_timeout',consumer)

    def test_resource_postflight_checks_both_pins(self):
        nodes=[n for n in ast.walk(ast.parse(self.text)) if isinstance(n,ast.If) and any(isinstance(x,ast.Constant) and x.value=='resource observer or original capture timeout changed during successor parity' for x in ast.walk(n))]
        self.assertEqual(len(nodes),1);code=compile(ast.fix_missing_locations(ast.Module(body=nodes,type_ignores=[])),'PURE_POSTFLIGHT','exec')
        for changed in [None,self.new.RESOURCE_PATH,self.new.TIMEOUT_FAIL_PATH]:
            def sha(path):return 'WRONG_PURE' if path==changed else self.new.RESOURCE_SHA if path==self.new.RESOURCE_PATH else self.new.TIMEOUT_FAIL_SHA
            context={'proof':types.SimpleNamespace(sha=sha),'RESOURCE_PATH':self.new.RESOURCE_PATH,'RESOURCE_SHA':self.new.RESOURCE_SHA,'TIMEOUT_FAIL_PATH':self.new.TIMEOUT_FAIL_PATH,'TIMEOUT_FAIL_SHA':self.new.TIMEOUT_FAIL_SHA}
            if changed is None:exec(code,context)
            else:
                with self.assertRaisesRegex(ValueError,'changed during successor parity'):exec(code,context)

    def test_both_failures_stay_fail_numerical_proof_and_limits_unchanged(self):
        for path,digest in [(self.new.FAILED_PARITY_PATH,self.new.FAILED_PARITY_SHA),(self.new.TIMEOUT_FAIL_PATH,self.new.TIMEOUT_FAIL_SHA)]:
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),digest);self.assertEqual(json.loads(path.read_text())['status'],'FAIL')
        self.assertEqual(self.new.OBSERVER_SHA,self.old.OBSERVER_SHA)
        self.assertEqual(self.new.proof.SCALAR_FLAGS,self.old.proof.SCALAR_FLAGS)
        for literal in ['default=1800','default=500','default=180',"'records_per_chunk':10000","'gzip_level':1"]:self.assertIn(literal,self.text)

    def test_no_existing_top_level_helper_changed(self):
        old={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(OLD.read_text()).body if isinstance(n,ast.FunctionDef)}
        new={n.name:ast.dump(n,include_attributes=False) for n in ast.parse(self.text).body if isinstance(n,ast.FunctionDef)}
        self.assertEqual(old.keys(),new.keys());self.assertEqual({name for name in old if old[name]!=new[name]},{'main'})


if __name__=='__main__':unittest.main(verbosity=2)
