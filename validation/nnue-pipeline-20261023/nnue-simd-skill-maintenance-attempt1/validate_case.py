"""Bounded reference/structure checks for repo-local NNUE handoff guidance."""
from pathlib import Path
import hashlib
import json
import re
import sys

import numpy as np

OUT = Path(__file__).resolve().parent
ROOT = Path('/workspace/dwqww')
HANDOFF = OUT.parent
SKILL = ROOT / '.agents/skills/validating-chess-simd/SKILL.md'
sys.path.insert(0, str(ROOT / 'tools/nnue'))
from include_parser import load_include


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    original = (OUT / 'SKILL.before.md').read_text()
    current = SKILL.read_text()
    heading = '## Trained residual networks and handoffs\n'
    start, end = current.index(heading), current.index('## Windows and match evidence\n')
    assert current[:start] + current[end:] == original, 'Unrelated skill bytes changed'
    front = current.split('---', 2)[1]
    assert front == original.split('---', 2)[1]
    name = re.search(r'^name: (.+)$', front, re.M).group(1)
    description = re.search(r'^description: (.+)$', front, re.M).group(1)
    assert re.fullmatch('[a-z0-9-]+', name) and description.startswith('Use when') and len(description) < 1024
    links = []
    for target in re.findall(r'\[[^\]]+\]\(([^)]+)\)', current):
        if '://' in target or target.startswith('#'):
            continue
        actual = (SKILL.parent / target.split('#', 1)[0]).resolve()
        assert actual.is_file(), str(actual)
        links.append({'target': target, 'resolved_path': str(actual), 'sha256': sha(actual)})

    manifest_path = HANDOFF / 'prepared-fresh-only-attempt1/manifest.json'
    recipe = HANDOFF / 'prepared-fresh-only-attempt1/train-provenance.jsonl'
    manifest = json.loads(manifest_path.read_text())
    with recipe.open() as stream:
        rows = [json.loads(line) for line in stream]
    partition = set(manifest['split']['train_game_ids'])
    retained = {row['game_id'] for row in rows}
    assert len(partition) == 200 and len(retained) == 196 and len(rows) == 14895
    assert retained < partition
    closure = json.loads((HANDOFF / 'FULL-PREP-CLOSED-v2.json').read_text())
    zeros = closure['zero_retained_training_partition_games']
    assert {row['game_id'] for row in zeros} == partition - retained
    assert all(row['reason'] and (row['original_quiet_rows'] == 0 or row['minimum_abs_score_cp'] > 1000) for row in zeros)
    assert len(retained) == closure['actual_retained_fresh_training_games']
    old_closure = json.loads((HANDOFF / 'FULL-PREP-CLOSED.json').read_text())
    assert old_closure['actual_tool_exit_code'] == 0 and old_closure['status'] == 'FAILED'
    assert json.loads((OUT / 'bad-200-equality.receipt.json').read_text())['returncode'] == 1

    baseline = json.loads((HANDOFF / 'baseline-shipped-fresh4149-attempt1/summary.json').read_text())
    metrics = baseline['initial']
    assert metrics['count'] == 4149 and metrics['teacher_mse_combined'] < metrics['teacher_mse_hce'] < metrics['teacher_mse_net_only']
    contract_path = ROOT / 'tools/nnue/engine_contract.json'
    contract = json.loads(contract_path.read_text())
    assert contract['default_accumulator_width'] == 128 and contract['residual'] is True
    assert contract['network_centipawn_limit'] == 30000 and contract['combined_centipawn_limit'] == 31871
    legacy = json.loads((HANDOFF / 'prepared-all13m-reservoir-attempt1/manifest.json').read_text())
    assert legacy['split']['legacy_training_game_ids_unknown'] is True

    original_inc = ROOT / 'src/nnue_weights.inc'
    header = OUT / 'header-only-control.inc'
    with header.open('xb') as stream:
        stream.write(b'// Evidence-only header change; unchanged integer parameters.\n' + original_inc.read_bytes())
    old_net = load_include(original_inc, expected_hidden=128)
    same_net = load_include(header, expected_hidden=128)
    pilot_inc = HANDOFF / 'pilot-fresh14895-zero20-attempt1/exports/epoch-0001.inc'
    pilot_net = load_include(pilot_inc, expected_hidden=128)
    def parameters(net):
        return np.concatenate([np.asarray(net[key]).reshape(-1) for key in ('w1', 'b1', 'w2', 'b2')]) * 4096
    old_p, same_p, pilot_p = (parameters(net) for net in (old_net, same_net, pilot_net))
    assert old_net['sha256'] != same_net['sha256'] and np.array_equal(old_p, same_p)
    changed = int(np.count_nonzero(pilot_p - old_p))
    assert changed > 0 and len(old_p) == 98689
    identities = {str(path): sha(path) for path in (SKILL, Path(__file__), manifest_path, recipe,
        contract_path, original_inc, header, pilot_inc,
        HANDOFF / 'baseline-shipped-fresh4149-attempt1/summary.json',
        HANDOFF / 'FULL-PREP-CLOSED.json', HANDOFF / 'FULL-PREP-CLOSED-v2.json',
        HANDOFF / 'prepared-all13m-reservoir-attempt1/manifest.json')}
    result = {'status': 'PASS_BOUNDED_SKILL_STRUCTURE_AND_ACTUAL_CASE_APPLICATION',
        'before_sha256': sha(OUT / 'SKILL.before.md'), 'after_sha256': sha(SKILL),
        'existing_frontmatter_preserved': True, 'all_preexisting_skill_bytes_preserved': True,
        'local_links_verified': links, 'new_section_words': len(current[start:end].split()),
        'bad200equality_actual_expected_failure_rc': 1,
        'correct_actual_fresh_subset': {'assigned': len(partition), 'retained': len(retained), 'rows': len(rows), 'zero_retained_games': zeros},
        'actual_deployed_hybrid_vs_residual_diagnostic': {key: metrics[key] for key in ('count', 'teacher_mse_hce', 'teacher_mse_combined', 'teacher_mse_net_only')},
        'header_only_control': {'file_sha_changed': True, 'numeric_quantized_changes': 0},
        'existing_pilot_numeric_change_example': {'include_sha256': sha(pilot_inc), 'changed_quantized_parameters': changed, 'parameter_count': len(old_p), 'scope': 'Previously tested pilot is an example, not a full-data candidate selection'},
        'source_sha256': identities, 'deployment': 'Repo-local existing skill only; no skill-creator/global installation claim',
        'limits': 'Reference/structure and real-case checks, not a repeated agent behavior study, engine validation, training, independent-audit model evaluation or Elo evidence'}
    (OUT / 'ACTUAL-CASE-VALIDATION.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: result[key] for key in ('status', 'before_sha256', 'after_sha256', 'new_section_words', 'header_only_control', 'existing_pilot_numeric_change_example')}, indent=2))


if __name__ == '__main__':
    main()
