"""Bounded semantic fixtures for the proposed skill, not agent-behavior evidence."""
from pathlib import Path
import re
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fit_model
import run_tmfit


def main():
    root = Path(__file__).resolve().parents[3]
    skill = root / 'skills/validate-chess-engine/SKILL.md'
    text = skill.read_text(encoding='utf-8')
    front = re.fullmatch(r'---\n(.*?)\n---\n(.*)', text, re.DOTALL)
    assert front
    fields = dict(line.split(': ', 1) for line in front[1].splitlines())
    assert set(fields) == {'name', 'description'}
    assert fields['name'] == skill.parent.name
    assert re.fullmatch('[a-z0-9]+(?:-[a-z0-9]+)*', fields['name'])
    assert len(fields['name']) <= 64 and len(fields['description']) <= 1024
    assert fields['description'].startswith('Use when ')
    assert not any(c in fields['description'] for c in '<>')
    assert not re.search(r'^\s*\[TODO:', front[2], re.MULTILINE)
    links = re.findall(r'\]\((references/[^)]+)\)', text)
    assert all((skill.parent / link).is_file() for link in links)
    print(f'PASS: restricted two-scalar frontmatter and {len(links)} reference links')
    print('Scope: stdlib checks only; official quick_validate requires unavailable PyYAML')

    common = dict(game_id='fixture', search_id=0, changed=0, node_fraction=0.5,
                  score_cp=0, score_delta_cp=0, soft_ms=100, complete=True,
                  final_best_move='d2d4', search_iteration_count=2)
    rows = [dict(common, depth=1, best_move='d2d4', elapsed_ms=10, search_iteration_index=0),
            dict(common, depth=2, best_move='e2e4', elapsed_ms=30, search_iteration_index=1)]
    data = fit_model.prepare(rows, require_seals=True)
    assert data.y.tolist() == [1] and data.returned_move_disagreements == 1
    assert data.excluded_incomplete == 0 and data.excluded_final == 1
    print('PASS: interrupted returned-move change retains completed-iteration label=1; mismatch counted')

    # Synthetic arithmetic witness only: discrete soft-stop decisions break
    # the implication from neutral average multiplier to neutral actual time.
    completions = [80, 160, 320]
    baseline = next(t for t in completions if t >= 100)
    mapped = [next(t for t in completions if t >= 100 * m) for m in (0.5, 1.5)]
    ratio = (sum(mapped) / len(mapped)) / baseline
    assert (0.5 + 1.5) / 2 == 1 and ratio == 0.75
    print('PASS: synthetic mean multiplier=1.0, OFF time=160, ON times=[80,160], actual ratio=0.75')
    print('Scope: mathematical counterexample; not measured engine time evidence')

    games = [dict(mode=1, result='ply_cap', moves=50) for _ in range(4)]
    summary = run_tmfit.sanitizer_summary(games, 4)
    assert summary['pass_'] and summary['all_on']
    assert 'ratio_on_off' not in summary
    mixed = [dict(game, mode=i % 2) for i, game in enumerate(games)]
    assert not run_tmfit.sanitizer_summary(mixed, 4)['pass_']
    print('PASS: four-ON sanitizer coverage qualifies independently; alternating OFF/ON fails coverage')
    print('Status: proposed/not installed; no independent fresh-agent behavior test performed')


if __name__ == '__main__':
    main()
