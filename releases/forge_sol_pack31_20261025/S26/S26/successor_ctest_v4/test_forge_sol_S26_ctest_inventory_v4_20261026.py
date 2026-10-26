"""CTest inventory regression fixtures; parser-only, no native program launch."""
import hashlib
import json
from pathlib import Path
import tempfile
from types import ModuleType
import unittest
import xml.etree.ElementTree as ET

HERE=Path(__file__).resolve().parent
TOOL=HERE/'forge_sol_S26_netbatch_v4_20261026.py'
CORE=['forge_tests','forge_correction_history_tests','forge_runtime_psqt_tests',
      'forge_pawn_span_tests','forge_nearest_pawn_tests','forge_pv_metadata_tests',
      'forge_tt_tests','forge_rule50_tests','forge_legal_witness_tests',
      'match_tool_tests','windows_validation_tests','uci_regression',
      'ponder_regression','ownbook_regression']

class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='ctest_inventory_',dir=HERE);self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name);self.source=self.root/'source';self.build=self.root/'build'
        self.source.mkdir();self.build.mkdir()
        (self.source/'CMakeLists.txt').write_text('enable_testing()\n')
        (self.build/'CMakeCache.txt').write_text('CMAKE_BUILD_TYPE:STRING=Release\n')
        self.mod=ModuleType('inventory_subject');self.mod.__file__=str(TOOL)
        exec(compile(TOOL.read_bytes(),str(TOOL),'exec'),self.mod.__dict__)
        self.allow={'allowed_test_failure':'forge_tests','rules':[]}
    def discovery(self,names=CORE):
        return {'kind':'ctestInfo','version':{'major':1,'minor':0},'tests':[{'name':name,'command':['/synthetic/program']} for name in names]}
    def configured(self,names=CORE):
        (self.build/'CTestTestfile.cmake').write_text(''.join('add_test('+n+' "/synthetic/program")\n' for n in names))
    def inventory(self,data,names=CORE):
        self.configured(names);p=self.root/'discovery.json';p.write_text(json.dumps(data))
        return self.mod.load_ctest_inventory(p,self.source,self.build)
    def junit(self,names=CORE):
        root=ET.Element('testsuite')
        for name in names:ET.SubElement(root,'testcase',name=name)
        p=self.root/'ctest.xml';ET.ElementTree(root).write(p);return p
    def test_L14_and_B15_require_exact_full_inventory(self):
        for names in (CORE,CORE+['forge_bad_capture_tests']):
            with self.subTest(names=len(names)):
                inventory=self.inventory(self.discovery(names),names)
                self.assertEqual(inventory['expected_names'],sorted(names))
                self.assertEqual(self.mod.check_ctest(self.junit(names),0,self.allow,expected_names=inventory['expected_names'])['status'],'PASS')
    def test_one_case_JUnit_does_not_pass(self):
        with self.assertRaises(ValueError):self.mod.check_ctest(self.junit(['forge_tests']),0,self.allow,expected_names=CORE)
    def test_expected_names_cannot_itself_reduce_canonical_core(self):
        with self.assertRaises(ValueError):self.mod.check_ctest(self.junit(['forge_tests']),0,self.allow,expected_names=['forge_tests'])
    def test_missing_duplicate_unexpected_and_skipped_JUnit_cases_fail(self):
        for names in (CORE[:-1],CORE+[CORE[0]],CORE+['unexpected_case']):
            with self.subTest(names=names),self.assertRaises(ValueError):
                self.mod.check_ctest(self.junit(names),0,self.allow,expected_names=CORE)
        p=self.junit();tree=ET.parse(p);ET.SubElement(tree.getroot()[0],'skipped');tree.write(p)
        with self.assertRaises(ValueError):self.mod.check_ctest(p,0,self.allow,expected_names=CORE)
    def test_nonrun_status_without_skipped_element_fails(self):
        for status in ('notrun','disabled','skipped','unknown'):
            p=self.junit();tree=ET.parse(p);tree.getroot()[0].set('status',status);tree.write(p)
            with self.subTest(status=status),self.assertRaises(ValueError):self.mod.check_ctest(p,0,self.allow,expected_names=CORE)
    def test_discovery_rejects_missing_core_and_omitted_configured_B_case(self):
        for data,names in [(self.discovery(['forge_tests']),CORE),(self.discovery(CORE[:-1]),CORE),(self.discovery(),CORE+['forge_bad_capture_tests'])]:
            with self.subTest(data=data),self.assertRaises(ValueError):self.inventory(data,names)
    def test_discovery_rejects_wrong_element_types_and_duplicates(self):
        variants=[None,[],{'tests':[]},self.discovery(),self.discovery(),self.discovery(),self.discovery(),self.discovery()]
        variants[3]['tests']='forge_tests';variants[4]['tests'][0]=1
        variants[5]['tests'][0]['name']=False;variants[6]['tests'][0]['command']='not-an-argv'
        variants[7]['tests'].append(variants[7]['tests'][0].copy())
        for data in variants:
            with self.subTest(data=data),self.assertRaises(ValueError):self.inventory(data)
    def test_generated_quoted_and_bracketed_static_names_are_complete(self):
        p=self.root/'discovery.json';p.write_text(json.dumps(self.discovery()))
        (self.build/'CTestTestfile.cmake').write_text(''.join('add_test('+('"'+name+'"' if index%2 else '[=['+name+']=]')+' "/synthetic/program")\n' for index,name in enumerate(CORE)))
        self.assertEqual(self.mod.load_ctest_inventory(p,self.source,self.build)['expected_names'],sorted(CORE))
    def test_discovery_rejects_unexpected_case_not_declared_in_build(self):
        with self.assertRaises(ValueError):self.inventory(self.discovery(CORE+['invented_case']))
    def test_binding_changes_when_source_or_generated_inventory_changes(self):
        inventory=self.inventory(self.discovery());before=inventory['binding']
        self.assertEqual(self.mod.ctest_inventory_binding(self.source,self.build),before)
        (self.source/'CMakeLists.txt').write_text('enable_testing()\n# changed\n')
        self.assertNotEqual(self.mod.ctest_inventory_binding(self.source,self.build),before)
    def test_missing_generated_testfile_and_unparseable_declaration_fail_closed(self):
        p=self.root/'discovery.json';p.write_text(json.dumps(self.discovery()))
        with self.assertRaises(ValueError):self.mod.load_ctest_inventory(p,self.source,self.build)
        (self.build/'CTestTestfile.cmake').write_text('add_test(${DYNAMIC_NAME} /synthetic/program)\n')
        with self.assertRaises(ValueError):self.mod.load_ctest_inventory(p,self.source,self.build)
    def test_original_failure_guards_still_reject_with_full_suite(self):
        for child,message in [('error','crash'),('failure','Segmentation fault')]:
            p=self.junit();tree=ET.parse(p);ET.SubElement(tree.getroot()[0],child,message=message);tree.write(p)
            with self.assertRaises(ValueError):self.mod.check_ctest(p,8,self.allow,expected_names=CORE)
    def test_real_saved_B_JUnit_parser_replay_without_engine(self):
        root=HERE.parent
        junit=root/'forge_sol_S26_NATIVE_B_lock_control_20261026/00_74c4009d86b7/ctest.xml'
        allow=self.mod.read_json(root/'forge_sol_S26_allowlist_20261026.json')
        bound=self.mod.bind_allowlist(allow,'55334ba94fd508d5f8e8e0e715c86a6996eddc69b20b1c110110a96e46deaa2c','74c4009d86b7d3a5ae9e6119d0890e5b923508f4063161bb4bc1539aab275b1b')
        self.assertEqual(self.mod.check_ctest(junit,0,bound,expected_names=CORE+['forge_bad_capture_tests'])['status'],'PASS')

    def test_crash_guards_are_exercised_with_complete_inventory(self):
        allow={'allowed_test_failure':'forge_tests','rules':[{'pattern':'FAIL: known horizon','max_count':1}]}
        for message in ('Failed','Segmentation fault','Timeout','Subprocess aborted'):
            p=self.junit();tree=ET.parse(p);case=tree.getroot()[0]
            ET.SubElement(case,'failure',message=message)
            ET.SubElement(case,'system-out').text='FAIL: known horizon';tree.write(p)
            if message=='Failed':
                self.assertEqual(self.mod.check_ctest(p,8,allow,expected_names=CORE)['status'],'PASS')
            else:
                with self.subTest(message=message),self.assertRaisesRegex(ValueError,'abnormal CTest termination|unrecognized CTest failure status'):
                    self.mod.check_ctest(p,8,allow,expected_names=CORE)
    def test_unrelated_diagnostic_guard_is_exercised_with_complete_inventory(self):
        allow={'allowed_test_failure':'forge_tests','rules':[{'pattern':'FAIL: known horizon','max_count':1}]}
        p=self.junit();tree=ET.parse(p)
        ET.SubElement(tree.getroot()[1],'system-out').text='FAIL: known horizon';tree.write(p)
        with self.assertRaisesRegex(ValueError,'known diagnostic from unexpected test'):
            self.mod.check_ctest(p,0,allow,expected_names=CORE)
    def test_duplicate_guard_is_exercised_with_complete_inventory(self):
        p=self.junit();tree=ET.parse(p);ET.SubElement(tree.getroot(),'testcase',name=CORE[0]);tree.write(p)
        with self.assertRaisesRegex(ValueError,'empty or duplicate CTest case name'):
            self.mod.check_ctest(p,0,self.allow,expected_names=CORE)

if __name__=='__main__':unittest.main()
