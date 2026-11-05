"""Write sep/PROD_SEPARATION.json from the two final scan REPORTs and the settled triage (numbers read, never typed).
The base record (reasons, writer facts) is Astra's last version as found on the PC (Step 0 md5 04ffdceb...),
read from commit aa78a56, so the tool can be re-run; only updated_vienna changes between runs.

  opus_prod_separation.py [--out PATH] [--replace-committed] [--test-hold-seconds S]
Output follows the mode-x pattern of the other tools: the record is written to PATH.part (opened with mode 'x',
flushed and fsynced) and then renamed to PATH; an existing PATH or PATH.part is refused before anything is written.
--replace-committed allows PATH to be replaced only when git tracks it unchanged since HEAD (the old content stays
in the history); it is meant for regenerating the committed production record and is stated in the report.
--test-hold-seconds S is a test hook: wait S seconds between writing the .part file and publishing it, so a
mid-write interruption can be exercised (the interrupted run leaves PATH.part, never PATH).
BOARDSTM_TRIAGE.json (status COMPLETE for 7,610 / 7,700 / 7,612) is mandatory: the raw 4-field "0 shared keys" is
an en-passant artifact and is labelled as such; the EP-normalised recount (4,088 keys) is the four-field verdict."""
import argparse
import datetime
import hashlib
import json
import os
import subprocess
import time

A14 = 'D:/a14/'
BASE_COMMIT = 'aa78a56'
BASE_MD5 = '04ffdcebf3cb1aee4005b76f60187458'
OV = A14 + 'sep/overlap-production03/REPORT.json'
SG = A14 + 'sep/segments-production02/REPORT.json'
SEAL = A14 + 'sep/segments-production02/MAPS_SEAL.json'
OUT = A14 + 'sep/PROD_SEPARATION.json'
TRIAGE = A14 + 'sep/BOARDSTM_TRIAGE.json'


def md5(p):
    return hashlib.md5(open(p, 'rb').read()).hexdigest()


def need(ok, why):
    # explicit checks, not assert: they must hold even under python -O (review finding F-013)
    if not ok:
        raise SystemExit(f'refusing to write PROD_SEPARATION.json: {why}')


ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
ap.add_argument('--out', default=OUT, help='output path (default: the production record); refused if it exists')
ap.add_argument('--replace-committed', action='store_true',
                help='allow replacing --out when git tracks it unchanged since HEAD (old content stays in the history)')
ap.add_argument('--test-hold-seconds', type=float, default=0.0,
                help='test hook: wait this long after writing the .part file before publishing it')
args = ap.parse_args()
OUT = args.out.replace('\\', '/')
PART = OUT + '.part'
if os.path.exists(PART):
    raise SystemExit(f'refusing: {PART} exists (an earlier run was interrupted or is still running)')
if os.path.exists(OUT):
    if not args.replace_committed:
        raise SystemExit(f'refusing: {OUT} exists (pick a new --out; --replace-committed is only for the tracked record)')
    try:
        rel = os.path.relpath(OUT, A14).replace('\\', '/')
    except ValueError:  # another drive: relpath has no answer on Windows (owner's fix list 2, item 6)
        need(False, f'refusing: {OUT} not under {A14}')
    tracked = subprocess.run(['git', '-C', A14, 'ls-files', '--error-unmatch', '--', rel], capture_output=True)
    same = subprocess.run(['git', '-C', A14, 'diff', '--quiet', 'HEAD', '--', rel])
    if rel.startswith('..') or tracked.returncode != 0 or same.returncode != 0:
        raise SystemExit(f'refusing: {OUT} is not a git-tracked file unchanged since HEAD; --replace-committed does not apply')


ov = json.load(open(OV, encoding='utf-8'))
sg = json.load(open(SG, encoding='utf-8'))
base = subprocess.run(['git', '-C', A14, 'show', BASE_COMMIT + ':sep/PROD_SEPARATION.json'],
                      capture_output=True, check=True).stdout
need(hashlib.md5(base).hexdigest() == BASE_MD5, 'base record is not the Step 0 version')
old = json.loads(base.decode('utf-8'))
need(md5(OV) == '1607d19e2b66dbe3512d0997942523c4' and md5(SG) == 'fcb488f8c726326e013f648e1d202760',
     'a scan report changed (md5)')
need(ov['complete'] is True and sg['complete'] is True, 'a scan report is not complete')
bs, ff = ov['keys']['board_stm'], ov['keys']['four_field']
need((bs['status'], bs['shared_exact_keys'], bs['train_overlap_rows'], bs['holdout_overlap_rows']) == ('FAIL', 7610, 7700, 7612),
     'board+stm counts differ from 7,610 / 7,700 / 7,612')
need((ff['status'], ff['shared_exact_keys']) == ('PASS', 0), 'four-field counts differ from 0')
for side in ('train', 'holdout'):
    for k in (bs, ff):
        need(k[side]['key_fill_rate'] == 1.0 and k[side]['complete'] is True and k[side]['parse_failures'] == 0,
             f'{side} coverage is not complete with fill rate 1.0')


def key_view(k):
    return {'status': k['status'], 'shared_exact_keys': k['shared_exact_keys'],
            'train_overlap_rows': k['train_overlap_rows'], 'holdout_overlap_rows': k['holdout_overlap_rows'],
            'hash_candidate_rows': k['hash_candidate_rows'], 'hash_collision_rows': k['hash_collision_rows'],
            'train_rows': k['train']['rows'], 'holdout_rows': k['holdout']['rows']}


seams = []
holdout = {13, 14}
for p in sg['cross_file_adjacent_pairs']:
    crosses = (p['left_source'] in holdout) != (p['right_source'] in holdout)
    seams.append({'left': f"forge_selfplay_{p['left_source']:03d}.txt line {p['left_line']}",
                  'right': f"forge_selfplay_{p['right_source']:03d}.txt line {p['right_line']}",
                  'status': p['status'], 'reason': p['reason'], 'crosses_train_holdout': crosses})
cross = [s for s in seams if s['crosses_train_holdout']]
need(len(cross) == 2 and all(s['status'] == 'UNREACHABLE' for s in cross), 'train/holdout seams are not both UNREACHABLE')
pc, rc = sg['pair_counts'], sg['reason_counts']
now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M')

rec = {
    'schema': 2,
    'status': 'FAIL',
    'stage': 'position_and_chain_scans_complete',
    'status_by_check': {
        'position_overlap_board_stm': 'FAIL',
        'position_overlap_four_field': None,  # set from BOARDSTM_TRIAGE.json below (mandatory)
        'chain_segments': sg['status'],
        'authentic_game_ids': 'UNVERIFIED',
    },
    'authentic_game_ids': 'UNVERIFIED',
    'writer_behavior': old['writer_behavior'],
    'historical_launcher_association': old['historical_launcher_association'],
    'segments': {
        'status': sg['status'], 'k': sg['k'], 'node_limit': sg['node_limit'],
        'boundary_node_limit': sg['boundary_node_limit'], 'segment_count': sg['segment_count'],
        'range_count': sg['range_count'], 'adjacent_pair_outcomes': pc, 'reason_counts': rc,
        'scope': sg['boundary_search_scope'],
        'sources': {f"{int(k):03d}": {'scanned_rows': v['scanned_rows'], 'valid_key_rows': v['valid_key_rows']}
                    for k, v in sg['source_counts'].items()},
    },
    'cross_boundary_links': {
        'train_holdout_seams_checked': len(cross),
        'reachable': sum(s['status'] == 'REACHABLE' for s in cross),
        'unknown': sum(s['status'] == 'UNKNOWN' for s in cross),
        'unreachable': sum(s['status'] == 'UNREACHABLE' for s in cross),
        'seams': seams,
        'scope': 'observed adjacent physical rows at the file seams only; no all-pairs cross-window search',
    },
    'position_overlap': {'board_stm': key_view(bs), 'four_field_raw': key_view(ff),
                         'hash_algorithm': ov['hash_algorithm'], 'scope': ov['scope']},
    'key_fill_rate': {'board_stm': {'train': bs['train']['key_fill_rate'], 'holdout': bs['holdout']['key_fill_rate']},
                      'four_field_raw': {'train': ff['train']['key_fill_rate'], 'holdout': ff['holdout']['key_fill_rate']}},
    'reasons': [
        f"Position overlap FAIL on the board+side-to-move key: {bs['shared_exact_keys']:,} shared keys, "
        f"{bs['train_overlap_rows']:,} train rows and {bs['holdout_overlap_rows']:,} holdout rows, "
        f"{bs['hash_collision_rows']} hash collisions, key fill rate 1.0 on {bs['train']['rows']:,} train and "
        f"{bs['holdout']['rows']:,} holdout rows.",
        None,  # set from BOARDSTM_TRIAGE.json below (mandatory)
        old['reasons'][0],
        old['reasons'][1],
        old['reasons'][2],
        old['reasons'][3],
        f"Chain scan (K={sg['k']}, node limit {sg['node_limit']:,}) left {pc['UNKNOWN']:,} adjacent pairs UNKNOWN "
        f"(node_limit {rc['node_limit']:,}, gap_exceeds_k {rc['gap_exceeds_k']:,}) next to {pc['REACHABLE']:,} "
        f"REACHABLE and {pc['UNREACHABLE']:,} UNREACHABLE; unresolved adjacent-pair checks remain.",
        "Both train/holdout file seams are UNREACHABLE (012->013 result_mismatch, 014->015 nonpositive_ply_gap), "
        "but the chain scan checks only observed adjacent physical rows at source seams; it does not search "
        "all pairs across windows, so interleaved or reordered games are not excluded.",
        sg['reasons'][1],
        sg['reasons'][2],
    ],
    'reports': [
        {'path': OV.replace('/', '\\'), 'md5': md5(OV)},
        {'path': SG.replace('/', '\\'), 'md5': md5(SG)},
        {'path': SEAL.replace('/', '\\'), 'md5': md5(SEAL)},
    ],
    'evidence': old['evidence'],
    'updated_vienna': now + ' Vienna',
}
need(old['reasons'][4].startswith('Full production position and chain scans are running'), 'base reasons changed')
# Job 2 settled the 4-field question: the triage is mandatory (COMPLETE only; anything else refuses). The raw
# 4-field "0 shared keys" is an en-passant artifact and is labelled as such; the EP-normalised recount is the verdict.
need(os.path.exists(TRIAGE), 'BOARDSTM_TRIAGE.json is missing; the four-field verdict needs the EP-normalised recount')
tr = json.load(open(TRIAGE, encoding='utf-8'))
if tr.get('status') != 'COMPLETE' or tuple(tr['totals']['expected']) != (7610, 7700, 7612):
    raise SystemExit('BOARDSTM_TRIAGE.json is not COMPLETE for 7,610 / 7,700 / 7,612; refusing to fold it in')
n4, kc = tr['normalised_4field_recount'], tr['keys_per_class']
need(n4['shared_keys'] > 0, 'the EP-normalised recount shows 0 shared keys; this tool expects the settled FAIL figure')
rec['status_by_check']['position_overlap_four_field'] = (
    f"raw PASS (0 keys) is an en-passant artifact; EP-normalised FAIL ({n4['shared_keys']:,} keys)")
rec['position_overlap']['four_field_raw']['status'] = (
    f"PASS on the raw 4-field key only (0 shared raw keys): an en-passant artifact, not a separation PASS; "
    f"EP-normalised FAIL ({n4['shared_keys']:,} keys), see four_field_ep_normalised")
rec['position_overlap']['four_field_ep_normalised'] = dict(
    status='FAIL', shared_exact_keys=n4['shared_keys'],
    train_overlap_rows=n4['train_rows'], holdout_overlap_rows=n4['holdout_rows'], scope=n4['scope'])
rec['triage'] = dict(path=TRIAGE.replace('/', '\\'), md5=md5(TRIAGE), keys_per_class=kc,
                     key_reasons=tr['key_reasons'])
rec['reasons'][1] = (
    f"The raw 4-field key shares 0 keys at fill rate 1.0, but that PASS is an en-passant artifact: with EP "
    f"normalised to legal-capture-only, {n4['shared_keys']:,} keys ({n4['train_rows']:,} train rows, "
    f"{n4['holdout_rows']:,} holdout rows) are the same position. Triage of the 7,610 keys: ep_format_diff "
    f"{kc.get('ep_format_diff', 0):,}, real_ep_diff {kc.get('real_ep_diff', 0):,}, other {kc.get('other', 0):,} "
    f"(castling rights differ or mixed pairs).")
rec['reports'].append(dict(path=TRIAGE.replace('/', '\\'), md5=md5(TRIAGE)))
need(None not in rec['status_by_check'].values() and None not in rec['reasons'], 'a placeholder was left unset')
text = json.dumps(rec, indent=2, ensure_ascii=False) + '\n'
with open(PART, 'xb') as stream:  # mode x: a second writer of the same .part is refused
    stream.write(text.encode('utf-8'))  # LF, like the original record
    stream.flush()
    os.fsync(stream.fileno())
if args.test_hold_seconds > 0:
    print('holding', args.test_hold_seconds, 's before publishing', PART, flush=True)
    time.sleep(args.test_hold_seconds)
if os.path.exists(OUT):
    os.replace(PART, OUT)  # only reachable with --replace-committed (checked above)
else:
    os.rename(PART, OUT)  # fails, leaving the .part, if OUT appeared meanwhile
print('written', OUT, md5(OUT), 'at', now, 'Vienna')
