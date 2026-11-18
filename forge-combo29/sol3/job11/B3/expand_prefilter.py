from pathlib import Path
import sys

tree = Path(sys.argv[1])
path = tree / 'src/search.cpp'
source = path.read_text(encoding='ascii')
for kind in ('search_child', 'qsearch_child', 'search_cuckoo', 'qsearch_cuckoo'):
    start = source.index(f'int Worker::{kind}(')
    end = source.index('\n}\n', start)
    function = source[start:end]
    call = 'may_repeat_checked(board, root_history_index_, ss->ply)'
    assert function.count(call) == 1
    function = function.replace(call, 'repetition_possible')
    constant = ('        ' if kind.endswith('_child') else '    ') + 'constexpr int DrawScore = 0;\n'
    assert function.count(constant) == 1
    indent = constant[:constant.index('constexpr')]
    function = function.replace(constant, constant + indent + 'const bool repetition_possible = ' + call + ';\n')
    source = source[:start] + function + source[end:]
path.write_text(source, encoding='ascii')
