#!/usr/bin/env python3
"""opus_guardband_record.py - write D:/a14/sep/GUARDBAND_SEPARATION.json from SPLIT.json + PROOF.json (no typed numbers).

The verdict follows the repository's own rule (r14_scan.final_verdict): overlaps 0 and complete, but authentic game
IDs are missing -> UNVERIFIED. The scoped guard-band checks are reported as PASS / FAIL each; the export is NOT built
(Job 3 step 6 needs a PASS proof); the staged candidate and the one promotion command are listed for the owner.
"""
import datetime
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from r14_scan import final_verdict  # noqa: E402

SPLIT = Path('D:/a14/sep/guardband01/SPLIT.json')
PROOF = Path('D:/a14/sep/guardband01/PROOF.json')
OUT = Path('D:/a14/sep/GUARDBAND_SEPARATION.json')


def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()


def main():
    split = json.load(open(SPLIT, encoding='utf-8'))
    proof = json.load(open(PROOF, encoding='utf-8'))
    c = proof['checks']
    overlaps = sum(v['exact_overlap_rows'] for per in c['holdout']['keys'].values() for v in per.values())
    overlaps += sum(c['train_val']['shared_train_rows'].values()) + int(c['audit']['counters']['position_overlap_rows'] or 0)
    complete = proof['scoped_checks'] == 'PASS' and not proof['problems']
    verdict = final_verdict(authenticated=False, complete=complete, overlaps=overlaps, unknowns=0)
    staged = {f'{s}.{k}': dict(path=v['path'], md5=v['md5'], bytes=v['bytes'])
              for s in ('train', 'val') for k, v in split['staged'][s].items()}
    rec = dict(
        schema=1, status=verdict, scoped_checks=proof['scoped_checks'], authentic_game_ids='UNVERIFIED',
        why_not_pass=('The npt-data-holdout-check audit returns UNVERIFIED when game_id is null, and every one of its '
                      f"{c['audit']['counters']['unknown_game_id_rows']:,} rows has none (no authentic game IDs exist). "
                      'r14_scan.final_verdict(authenticated=False, complete, overlaps=0) is UNVERIFIED too.'),
        checks={
            'position_overlap_vs_013_014': dict(status=c['holdout']['status'], keys=c['holdout']['keys'],
                                                key_fill_rate=c['holdout']['key_fill_rate']),
            'train_val_overlap': dict(status=c['train_val']['status'], rows=c['train_val']['shared_train_rows']),
            'cross_split_chain_links_within_k': dict(status=c['chain']['status'],
                                                     links=c['chain']['cross_split_links_within_k'],
                                                     cut_link=c['chain']['cut_link'], k=split['k'],
                                                     min_retained_ply_distance=c['chain']['min_retained_ply_distance'],
                                                     scope=c['chain']['scope']),
            'row_accounting': c['accounting'], 'payload_and_mate_rows': c['payload'],
            'npt_data_holdout_check_audit': dict(status=c['audit']['status'], exit_code=c['audit']['exit_code'],
                                                 counters=c['audit']['counters'], report=c['audit']['report'],
                                                 tool_md5=c['audit']['tool_md5'])},
        split=dict(cut=split['cut'], retained=split['retained'], dropped_by_reason=split['dropped_by_reason'],
                   dropped_listing=split['dropped_listing'], k=split['k'], val_fraction=split['val_fraction']),
        export=dict(built=False, reason='Job 3 step 6 builds the export only on a PASS proof; the proof is UNVERIFIED. '
                                        'Couns decides whether the guard-band evidence is enough for training.',
                    staged_candidate=staged,
                    promote_command=r'D:\a14\runtime\python\python.exe -I -B D:\a14\tools\opus_promote_export.py '
                                    r'--confirm-owner-decision'),
        evidence=dict(split=dict(path=str(SPLIT), md5=md5(SPLIT)), proof=dict(path=str(PROOF), md5=md5(PROOF)),
                      plan='D:/a14/sep/GUARD_BAND_PLAN.md'),
        written_vienna=datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + ' Vienna')
    with open(OUT, 'x', encoding='utf-8', newline='\n') as stream:
        json.dump(rec, stream, indent=1)
    print(json.dumps(dict(status=verdict, scoped=proof['scoped_checks'], overlaps=overlaps)))
    return 0


if __name__ == '__main__':
    sys.exit(main())
