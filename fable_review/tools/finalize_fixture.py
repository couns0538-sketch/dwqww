"""Final test edit: replace the three review-only candidates with one real fixture that must have more than 64
SEE-losing noisy moves (the old bad_captures_ size), with the engine's own census as the expected numbers.
usage: finalize_fixture.py <fen> <noisy> <promotions> <losing>"""
import sys
fen, noisy, promotions, losing = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
assert losing > 64, losing
p = 'F:/opus_scratch/worktrees/fable_review_buffix/tests/bad_capture_tests.cpp'
raw = open(p, 'rb').read()
crlf = b'\r\n' in raw
s = raw.decode().replace('\r\n', '\n')

def rep(old, new):
    global s
    assert s.count(old) == 1, (s.count(old), old[:70])
    s = s.replace(old, new, 1)

rep('''    std::size_t expected_promotions;
    const char* required_losing_move;
};''', '''    std::size_t expected_promotions;
    const char* required_losing_move;
    // Minimum number of SEE-losing noisy moves (0 = not checked). The fable-review fixture
    // demands more than 64: the AL1 lock's bad_captures_ held 64 entries, so the picker
    // overran it there (shown with -D_GLIBCXX_ASSERTIONS on the unfixed engine).
    std::size_t min_losing;
};''')
rep('''        check(losing > 0 && legal_losing > 0,
              std::string(fixture.name) + " contains actual legal SEE-losing moves");''',
    '''        check(losing > 0 && legal_losing > 0,
              std::string(fixture.name) + " contains actual legal SEE-losing moves");
        check(losing >= fixture.min_losing,
              std::string(fixture.name) + " has at least " + std::to_string(fixture.min_losing) +
                  " SEE-losing noisy moves (more than the lock's 64-entry buffer)");''')
rep('''    // Exactly the two supplied QA inputs and three existing Forge fixtures.
    // No generated positions, parser bypasses or direct private-buffer writes.
    constexpr std::array<Fixture, 8> fixtures{{
        {"cand-a", "6q1/1PbPp2P/1pKQQr2/1Rpn3k/Np1Q2r1/BQpNnQp1/1p1Q1pR1/3bB3 w - - 0 1", true, 0, 0, ""},
        {"cand-b", "2q5/1PpPp2P/R2pQ2b/1NQ2n2/1pr2QrQ/pQpQnKp1/3p2Rb/kNB1B3 w - - 0 1", true, 0, 0, ""},
        {"cand-c", "6q1/P1P1Pr2/3p1Q1p/1p1Q1n1Q/NKbp1Q1n/BRpQ1b2/kpRp1Qp1/1NB2r2 w - - 0 1", true, 0, 0, ""},
        {"qa-1",''', f'''    // The two supplied QA inputs, three existing Forge fixtures and one constructed
    // position (fable-review, 2026-10-28) whose SEE census exceeds the lock's
    // 64-entry deferred-capture buffer. No parser bypasses or private-buffer writes.
    constexpr std::array<Fixture, 6> fixtures{{{{
        {{"many-losing", "{fen}",
         false, {noisy}, {promotions}, "", 65}},
        {{"qa-1",''')
# the five original fixtures get min_losing 0
for name in ('qa-1', 'qa-2'):
    rep(f'''        {{"{name}", ''', f'''        {{"{name}", ''')  # anchor check only
s = s.replace('''         true, 0, 0, ""},''', '''         true, 0, 0, "", 0},''')
s = s.replace('''         false, 1, 0, "d1d5"},''', '''         false, 1, 0, "d1d5", 0},''')
s = s.replace('''         false, 8, 8, ""},''', '''         false, 8, 8, "", 0},''')
assert s.count(', 0},') == 5 and s.count('"", 65}') == 1, (s.count(', 0},'), s.count('"", 65}'))
open(p, 'wb').write(s.replace('\n', '\r\n' if crlf else '\n').encode())
print('fixture finalised:', fen, noisy, promotions, losing)
