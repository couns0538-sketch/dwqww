"""Source-level OFF/placement contracts only; no compiler/native claims."""
import json
from pathlib import Path
import re
import unittest

BASE=Path(__file__).resolve().parent
TREE=BASE/'Lprime'
ORIGINAL=Path(json.loads((BASE/'forge_sol_S08_original_source_hashes_20261026.json').read_text())['source'])


def off_projection(text):
    stack=[];output=[]
    def enabled():return all(x[1] for x in stack)
    for line in text.splitlines(keepends=True):
        stripped=line.strip()
        if re.match(r'#\s*(if|ifdef|ifndef)\b',stripped):
            known=bool(re.match(r'#\s*(ifdef\s+FORGE_PROF\b|if\s+defined\s*\(\s*FORGE_PROF\s*\))',stripped))
            if not known and enabled():output.append(line)
            stack.append([known,not known])
        elif re.match(r'#\s*else\b',stripped):
            if stack[-1][0]:stack[-1][1]=not stack[-1][1]
            elif enabled():output.append(line)
        elif re.match(r'#\s*endif\b',stripped):
            known=stack[-1][0]
            if not known and enabled():output.append(line)
            stack.pop()
        else:
            if enabled():output.append(line)
    if stack:raise AssertionError('unbalanced preprocessor nesting')
    return ''.join(output)


def tokens(text):
    parts=re.findall(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'|//[^\n]*|/\*[\s\S]*?\*/|[A-Za-z_]\w*|\d+|[^\s]',text)
    return [x for x in parts if not x.startswith('//') and not x.startswith('/*')]


class SourceContracts(unittest.TestCase):
    def test_OFF_source_tokens_are_identical_to_original(self):
        # Catches changed search arithmetic/control or surviving OFF hooks.
        for rel in ('include/forge/search.hpp','src/search.cpp','src/uci.cpp','src/nnue.cpp','src/eval.cpp'):
            with self.subTest(file=rel):
                self.assertEqual(tokens(off_projection((TREE/rel).read_text())),tokens((ORIGINAL/rel).read_text()))

    def test_option_is_off_and_instrumentation_sources_are_conditional(self):
        # Catches linking counter symbols or defining FORGE_PROF in OFF builds.
        cmake=(TREE/'CMakeLists.txt').read_text()
        self.assertRegex(cmake,r'option\(FORGE_PROF\s+"[^"]+"\s+OFF\)')
        block=re.search(r'if\(FORGE_PROF\)([\s\S]*?)endif\(\)',cmake)
        self.assertIsNotNone(block)
        self.assertIn('src/profile.cpp',block.group(1))
        self.assertIn('FORGE_PROF=1',block.group(1))
        self.assertEqual(cmake.count('src/profile.cpp'),1)

    def test_each_real_node_increment_is_followed_by_counter_hooks(self):
        # Catches counting recursive calls or moves rather than actual nodes.
        source=(TREE/'src/search.cpp').read_text()
        locations=[m.end() for m in re.finditer(r'\+\+local_nodes_;',source)]
        self.assertEqual(len(locations),2)
        for location in locations:
            self.assertIn('prof::Counter::Nodes',source[location:location+250])
        self.assertIn('prof::Counter::MainNodes',source)
        self.assertIn('prof::Counter::QsNodes',source)

    def test_TLS_and_controller_scope_are_searcher_local(self):
        # Catches shared global banks, missing nested restore, or reset after spawn.
        header=TREE/'include/forge/profile.hpp'
        self.assertTrue(header.is_file(),'counter API missing')
        h=header.read_text();self.assertIn('thread_local Bank*',h)
        self.assertIn('previous_',h)
        search=(TREE/'src/search.cpp').read_text()
        facade=search[search.index('SearchInfo Searcher::search('):]
        self.assertLess(facade.index('profile.reset_quiescent()'),facade.index('std::vector<std::thread> helpers'))
        worker=search[search.index('SearchInfo Worker::search('):]
        self.assertLess(worker.index('prof::Scope'),worker.index('const auto origin'))

    def test_fired_counters_are_inside_real_taken_branches(self):
        # Catches opportunity-only counters advertised as actual prunes.
        source=(TREE/'src/search.cpp').read_text()
        for branch,event in (('if (razor < alpha)','RazorCutoffs'),('if (value >= probcut_beta) {','ProbCutCutoffs'),('if (singular_score < singular_beta) {','SingularExtensions')):
            with self.subTest(event=event):
                location=source.index(branch)
                self.assertIn('prof::Counter::'+event,source[location:location+240])
        self.assertIn('prof::Counter::QsSeePrunes',source)
        self.assertIn('prof::Counter::HistoryPrunes',source)
        self.assertIn('prof::Counter::IirReductions',source)
        self.assertIn('prof::Counter::LmpActivations',source)

    def test_bench_profiles_precede_final_summary(self):
        # Catches S25 regression: delayed profile output after final bench line.
        source=(TREE/'src/uci.cpp').read_text()
        bench=source[source.index('} else if (command == "bench"'):source.index('} else if (command == "ponderhit"')]
        self.assertIn('bench_prof',bench)
        self.assertLess(bench.index('prof::write_snapshot'),bench.index('"info string bench depth "'))
        self.assertNotIn('prof::write_snapshot',bench[bench.index('"info string bench depth "'):])


if __name__=='__main__':unittest.main(verbosity=2)
