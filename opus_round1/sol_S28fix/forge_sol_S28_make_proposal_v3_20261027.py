"""Write the S28-1 v3 pin proposal for AL1 s198 as a patch (PROPOSAL ONLY; nothing is applied anywhere).

usage: python -I -B forge_sol_S28_make_proposal_v3_20261027.py <AL1L tree> <observation.json> <out.patch>
<AL1L tree> = AL1 source + the lock archive's forge_lockderived_jobC_S01_tests_tools_vs_AL1.patch (read only).
Edits are made in memory from the observed values; every replaced line must occur exactly once. Only tests/tests.cpp,
tools/rerecord_pins.py, README.md and IDEA_SOURCE.md change; engine code, CMake, the 6.4.24 TacticalCase expectations
and the KNOWN_FAILURE output text are untouched.
"""
import difflib
import json
import sys
from pathlib import Path

tree, obs_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
obs = {c['case']: c for c in json.loads(obs_path.read_text(encoding='utf-8'))['cases']}
w, pw, pb = obs['WAC001'], obs['promotion_white'], obs['promotion_black']
assert w['score_kind'] == 'cp' and w['depth'] == 12 and w['pv0'] == w['bestmove']
assert all(p['score_kind'] == 'cp' and p['score'] > 100 and p['depth'] == 1 and p['pv0'] == p['bestmove'] for p in (pw, pb))
NOTE = 'net md5 22b4b9e2, re-recorded 2026-10-27, PROPOSED'


def edit(text, pairs, name):
    for old, new in pairs:
        if text.count(old) != 1:
            raise SystemExit('%s: pattern must occur once: %r' % (name, old[:80]))
        text = text.replace(old, new)
    return text


EDITS = {
    'tests/tests.cpp': [
        ('// These are explicit observations of the locked h256_e12 horizon, not replacement\n'
         '// expectations. Unexpected moves, scores, depths and PVs remain ordinary failures.\n',
         '// These are explicit observations of the locked AL1 s198 horizon (%s),\n'
         '// not replacement expectations. Unexpected moves, scores, depths and PVs remain ordinary failures.\n'
         '// Previous lock h256_e12 (net md5 6d22f612) pins are kept on record next to each pin below. The\n'
         '// KNOWN_FAILURE output text below still says h256_e12 on purpose (byte-stable for existing allowlists).\n' % NOTE),
        ('    // returns f6h5, 661cp at d12, and discovers the mate at a greater depth.\n',
         '    // returns %s, %dcp at d12, and discovers the mate at a greater depth.\n'
         '    // Previous lock h256_e12 (net 6d22f612) pin, kept on record: f6h5/661/d12.\n' % (w['bestmove'], w['score'])),
        ('    constexpr std::string_view documented_wac_move = "f6h5";\n',
         '    constexpr std::string_view documented_wac_move = "%s";\n' % w['bestmove']),
        ('    constexpr int documented_wac_score = 661;\n',
         '    constexpr int documented_wac_score = %d;\n' % w['score']),
        ('        const std::string_view documented_king_text = mirrored ? "c3d2" : "c6d7";\n',
         '        // AL1 s198 at d1: %s / %s (%d cp); previous lock h256_e12: c6d7 / c3d2 (642 cp).\n'
         '        const std::string_view documented_king_text = mirrored ? "%s" : "%s";\n'
         % (pw['bestmove'], pb['bestmove'], pw['score'], pb['bestmove'], pw['bestmove'])),
    ],
    'tools/rerecord_pins.py': [
        ("CASES=[\n ('WAC001','2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1',12,8,'f6h5',661),\n"
         " ('promotion_white','8/k1P5/2K5/8/8/8/8/8 w - - 0 1',1,1,'c6d7',None),\n"
         " ('promotion_black','8/8/8/8/8/2k5/K1p5/8 b - - 0 1',1,1,'c3d2',None),\n",
         "# Documented lock pins: AL1 s198 re-record 2026-10-27 (PROPOSED): WAC001 %s/%d/d12, promotions %s / %s at d1.\n"
         "# Kept on record: h256_e12 (net 6d22f612) WAC001 f6h5/661/d12, promotions c6d7 / c3d2; 6.4.24 g3g6 >= 31997.\n"
         "CASES=[\n ('WAC001','2rr3k/pp3pp1/1nnqbN1p/3pN3/2pP4/2P3Q1/PPB4P/R4RK1 w - - 0 1',12,8,'%s',%d),\n"
         " ('promotion_white','8/k1P5/2K5/8/8/8/8/8 w - - 0 1',1,1,'%s',None),\n"
         " ('promotion_black','8/8/8/8/8/2k5/K1p5/8 b - - 0 1',1,1,'%s',None),\n"
         % (w['bestmove'], w['score'], pw['bestmove'], pb['bestmove'], w['bestmove'], w['score'], pw['bestmove'], pb['bestmove'])),
    ],
    'README.md': [
        ('3. Compare WAC move/score/depth/PV with the exact `f6h5/661/d12` pin, and compare\n'
         '   promotion king moves/PV/depth with `c6d7` and `c3d2` at depth1 (score>100).\n',
         '3. Compare WAC move/score/depth/PV with the exact `%s/%d/d12` pin (AL1 s198, PROPOSED 2026-10-27;\n'
         '   h256_e12 was `f6h5/661/d12`), and compare promotion king moves/PV/depth with `%s` and `%s`\n'
         '   at depth1 (score>100; h256_e12 was `c6d7`/`c3d2`).\n' % (w['bestmove'], w['score'], pw['bestmove'], pb['bestmove'])),
        ('   Never replace exact661 with a score floor. Re-run mutation controls.\n',
         '   Never replace exact%d with a score floor. Re-run mutation controls.\n' % w['score']),
    ],
    'IDEA_SOURCE.md': [
        ('with --observe-only. Original tooling, no engine change.\n',
         'with --observe-only. Original tooling, no engine change.\n'
         '\n'
         'S28 v3 AL1 s198 pin proposal (2026-10-27, PROPOSED, not applied): idea source = QA fix-up S28-1 (redo the\n'
         'pin proposal on the actual lock AL1 s198 instead of e48f006) and the observed AL1 s198 outcomes\n'
         'WAC001 %s/%d/d12 and promotions %s / %s at d1. Test/helper/doc text only; the h256_e12 and 6.4.24\n'
         'values stay on record; no engine, CMake or expectation-logic change; adopting it is a separate reviewed change.\n'
         % (w['bestmove'], w['score'], pw['bestmove'], pb['bestmove'])),
    ],
}

parts = []
for rel in ('IDEA_SOURCE.md', 'README.md', 'tests/tests.cpp', 'tools/rerecord_pins.py'):
    old = (tree / rel).read_text(encoding='utf-8')
    new = edit(old, EDITS[rel], rel)
    parts.append('diff --git a/%s b/%s\n' % (rel, rel))
    parts += difflib.unified_diff(old.splitlines(True), new.splitlines(True), 'a/' + rel, 'b/' + rel)
out.write_text(''.join(parts), encoding='utf-8', newline='\n')
print('written', out)
