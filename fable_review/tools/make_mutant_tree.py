"""Build the 'unfixed' tree: the fable-review-buffix worktree's engine with bad_captures_ back at 64 entries (the AL1
lock's code) and without the static_assert, plus the current tests. Used to show the new fixture overflows the old
buffer (built with -D_GLIBCXX_ASSERTIONS, std::array::operator[] aborts on index >= 64)."""
import shutil, pathlib, sys
W = pathlib.Path('F:/opus_scratch/worktrees/fable_review_buffix')
M = pathlib.Path('F:/opus_scratch/fable_review/buffix64/mutant_src')
if M.exists():
    print('mutant_src exists; refreshing tests/ and src/search.cpp only (no deletes)')
else:
    M.mkdir(parents=True)
    for d in ('src', 'include', 'tests', 'tools', 'bench'):
        shutil.copytree(W / d, M / d)
    shutil.copy2(W / 'CMakeLists.txt', M / 'CMakeLists.txt')
# refresh the test file (the fixture list changes between iterations)
shutil.copy2(W / 'tests' / 'bad_capture_tests.cpp', M / 'tests' / 'bad_capture_tests.cpp')
shutil.copy2(W / 'src' / 'search.cpp', M / 'src' / 'search.cpp')
p = M / 'src' / 'search.cpp'
s = p.read_bytes().decode()
old_decl = 'std::array<Move, MoveList::Capacity> bad_captures_{};'
assert s.count(old_decl) == 1, s.count(old_decl)
s = s.replace(old_decl, 'std::array<Move, 64> bad_captures_{};  // MUTANT: the AL1 lock size', 1)
# drop the static_assert that follows (two lines)
i = s.index('static_assert(decltype(bad_captures_){}.size() >= MoveList::Capacity')
j = s.index(';', i) + 1
line_start = s.rfind('\n', 0, i) + 1
line_end = s.find('\n', j) + 1
s = s[:line_start] + s[line_end:]
assert 'static_assert(decltype(bad_captures_)' not in s
p.write_bytes(s.encode())
print('mutant tree ready:', M, '| bad_captures_ 64, static_assert removed')
