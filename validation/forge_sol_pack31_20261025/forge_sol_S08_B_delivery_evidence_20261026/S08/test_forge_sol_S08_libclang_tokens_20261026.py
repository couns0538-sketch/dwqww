import importlib.util,pathlib,unittest
P=pathlib.Path(__file__).with_name('forge_sol_S08_libclang_token_hash_20261026.py')
spec=importlib.util.spec_from_file_location('off_clang_tokens',P);api=importlib.util.module_from_spec(spec);spec.loader.exec_module(api)
class TokenControls(unittest.TestCase):
    def digest(self,text):return api.token_hash(text)['sha256']
    def test_outside_whitespace_has_equal_tokens(self):
        self.assertEqual(self.digest(b'int value=1;const char*s="a b";'),self.digest(b'int\n value = 1 ; const char * s = "a b" ;\n'))
    def test_string_whitespace_mutation_changes_tokens(self):
        self.assertNotEqual(self.digest(b'const char*s="a b";'),self.digest(b'const char*s="ab";'))
    def test_identifier_join_changes_tokens(self):
        self.assertNotEqual(self.digest(b'foo bar;'),self.digest(b'foobar;'))
    def test_operator_join_changes_tokens(self):
        self.assertNotEqual(self.digest(b'void f(){x + + y;}'),self.digest(b'void f(){x ++ y;}'))
    def test_raw_string_newline_preserved(self):
        self.assertNotEqual(self.digest(b'const char*s=R"(a\n b)";'),self.digest(b'const char*s=R"(a b)";'))
if __name__=='__main__':unittest.main(verbosity=2)
