#!/usr/bin/env python3
"""opus_boardstm_triage.py - classify every train/holdout board+stm overlap (R14 finish Job 2; own code).

Input: the full shared-key listing from r14_overlap (--report, keys.board_stm.shared_keys) and/or from
opus_boardstm_probe (--probe PROBE.json, its SHARED.jsonl). With both, the two listings must be identical (same
keys, same train and holdout rows with path, line and FEN) or the triage is UNVERIFIED.

Per train/holdout row pair of a shared key (same board, same side to move):
  other (castling_diff)      castling rights differ
  other (identical_4field)   rights and raw EP equal: a 4-field overlap the scan said does not exist (fail closed)
  ep_format_diff             raw EP fields differ, but both become the same field under legal-capture-only EP
                             (opus_ep): the same chess position written two ways
  real_ep_diff               the normalised EP fields still differ: one row allows a legal en-passant capture
  other (invalid_ep)         an EP field that does not fit the board (fail closed)
A key takes its pairs' class when they all agree, otherwise other (mixed).
Recount (Job 2c): 4-field keys with EP normalised; a normalised 4-field match needs the same board+stm, so the
recount over the complete board+stm listing is the recount over all rows.

  opus_boardstm_triage.py --report R.json --probe P.json --expect 7610,7700,7612 --out sep/BOARDSTM_TRIAGE.json
      [--rows sep/BOARDSTM_TRIAGE_ROWS.tsv]
Status COMPLETE only if: listing complete, totals equal --expect, listings agree (when both given), no invalid EP,
no identical 4-field pair. Otherwise UNVERIFIED with the reasons. Exit 0 = COMPLETE, 2 = UNVERIFIED.
"""
import argparse
import collections
import datetime
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from opus_ep import ep_status  # noqa: E402

EXPAND = str.maketrans({str(n): '.' * n for n in range(1, 9)})


def md5(path):
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def expanded_key(fen):
    f = fen.split()
    return ''.join(rank.translate(EXPAND) for rank in f[0].split('/')) + ' ' + f[1]


def norm_rows(rows):
    return [(r['path'].casefold(), int(r['line']), ' '.join(r['fen'].split())) for r in rows]


def from_report(path):
    rep = json.load(open(path, encoding='utf-8'))
    k = rep['keys']['board_stm']
    if not k.get('listing_complete') or k.get('shared_keys') is None:
        raise ValueError('report listing incomplete or missing')
    listing = {}
    for item in k['shared_keys']:
        listing[item['key']] = dict(train=norm_rows(item['train']), holdout=norm_rows(item['holdout']))
    meta = dict(path=str(path), md5=md5(path), status=rep.get('status'), complete=rep.get('complete'),
                shared_exact_keys=k['shared_exact_keys'], train_overlap_rows=k['train_overlap_rows'],
                holdout_overlap_rows=k['holdout_overlap_rows'], hash_collision_rows=k['hash_collision_rows'],
                fill=dict(train=k['train']['key_fill_rate'], holdout=k['holdout']['key_fill_rate']))
    return listing, meta


def from_probe(path):
    rec = json.load(open(path, encoding='utf-8'))
    shared = Path(rec['shared_listing']['path'])
    if md5(shared) != rec['shared_listing']['md5']:
        raise ValueError('probe SHARED.jsonl md5 differs from PROBE.json')
    listing = {}
    with open(shared, encoding='utf-8') as stream:
        for line in stream:
            item = json.loads(line)
            train, holdout = norm_rows(item['train']), norm_rows(item['holdout'])
            listing[expanded_key(item['train'][0]['fen'])] = dict(train=train, holdout=holdout)
    meta = dict(path=str(path), md5=md5(path), shared_path=str(shared), shared_md5=md5(shared),
                status=rec.get('status'), shared_exact_keys=rec.get('shared_exact_keys'),
                train_overlap_rows=rec.get('train_overlap_rows'), holdout_overlap_rows=rec.get('holdout_overlap_rows'),
                hash_collision_train_rows=rec.get('hash_collision_train_rows'))
    return listing, meta


def fields(fen):
    f = fen.split()
    rights = ''.join(c for c in 'KQkq' if c in f[2]) or '-'
    return f[0], f[1], rights, f[3]


def pair_class(t, h):
    board, side, rt, et = fields(t)
    _, _, rh, eh = fields(h)
    st, sh = ep_status(board, side, et), ep_status(board, side, eh)
    if 'invalid' in (st, sh):
        return 'other', 'invalid_ep'
    if rt != rh:
        return 'other', 'castling_diff'
    if et == eh:
        return 'other', 'identical_4field'
    nt = et if st == 'legal' else '-'
    nh = eh if sh == 'legal' else '-'
    return ('ep_format_diff', f'{st}/{sh}') if nt == nh else ('real_ep_diff', f'{st}/{sh}')


def norm4(fen):
    board, side, rights, ep = fields(fen)
    st = ep_status(board, side, ep)
    return f"{board} {side} {rights} {ep if st == 'legal' else '-'}"


def pieces(fen):
    return sum(c.isalpha() for c in fen.split()[0])


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--report')
    ap.add_argument('--probe')
    ap.add_argument('--expect', required=True, help='keys,train_rows,holdout_rows')
    ap.add_argument('--out', required=True)
    ap.add_argument('--rows')
    a = ap.parse_args()
    if not a.report and not a.probe:
        sys.exit('need --report and/or --probe')
    expect = tuple(int(x) for x in a.expect.split(','))
    reasons, sources = [], {}
    listings = []
    for kind, path, loader in (('report', a.report, from_report), ('probe', a.probe, from_probe)):
        if path:
            try:
                listing, meta = loader(path)
            except (OSError, ValueError, KeyError) as exc:
                reasons.append(f'{kind} listing unusable: {exc}')
                sources[kind] = dict(path=path, error=str(exc))
                continue
            sources[kind] = meta
            listings.append((kind, listing))
    if len(listings) == 2 and listings[0][1] != listings[1][1]:
        a_keys, b_keys = set(listings[0][1]), set(listings[1][1])
        reasons.append(f'listings differ: {len(a_keys - b_keys)} keys only in report, {len(b_keys - a_keys)} only in '
                       f'probe, {sum(listings[0][1][k] != listings[1][1][k] for k in a_keys & b_keys)} keys with other rows')
    if not listings:
        listing = {}
    else:
        listing = listings[0][1]
    totals = (len(listing), sum(len(v['train']) for v in listing.values()), sum(len(v['holdout']) for v in listing.values()))
    if totals != expect:
        reasons.append(f'totals {totals} differ from the expected {expect}')

    key_class = collections.Counter()
    key_reason = collections.Counter()
    pair_counter = collections.Counter()
    pair_reason = collections.Counter()   # reasons of 'other' pairs (fail-closed checks use these, not key reasons)
    pattern = collections.Counter()
    by_holdout = collections.defaultdict(collections.Counter)
    by_pieces = collections.defaultdict(collections.Counter)
    by_train_file = collections.defaultdict(collections.Counter)
    rows_by_class = collections.defaultdict(lambda: [0, 0])
    norm_shared_keys = norm_train_rows = norm_holdout_rows = 0
    lines = ['key\tclass\treason\tside\tpath\tline\tfen\tep_status\tnormalised_4field']
    for key in sorted(listing):
        item = listing[key]
        classes = set()
        for _, _, tf in item['train']:
            for _, _, hf in item['holdout']:
                cls, why = pair_class(tf, hf)
                classes.add((cls, why if cls == 'other' else cls))
                pair_counter[cls] += 1
                if cls == 'other':
                    pair_reason[why] += 1
                b, s, _, et = fields(tf)
                _, _, _, eh = fields(hf)
                pattern[(cls, 'train ' + ('-' if et == '-' else 'EP ' + ep_status(b, s, et)),
                         'holdout ' + ('-' if eh == '-' else 'EP ' + ep_status(b, s, eh)))] += 1
        names = {c for c, _ in classes}
        if len(classes) == 1:
            cls, why = next(iter(classes))
        elif names == {'other'}:
            cls, why = 'other', '+'.join(sorted(w for _, w in classes))
        else:
            cls, why = 'other', 'mixed'
        key_class[cls] += 1
        key_reason[why] += 1
        n_pieces = pieces(item['train'][0][2])
        by_pieces[n_pieces][cls] += 1
        for path, _, _ in item['holdout']:
            by_holdout[Path(path).name][cls] += 1
        for path, _, _ in item['train']:
            by_train_file[Path(path).name][cls] += 1
        rows_by_class[cls][0] += len(item['train'])
        rows_by_class[cls][1] += len(item['holdout'])
        tn = {norm4(f) for _, _, f in item['train']}
        hn = {norm4(f) for _, _, f in item['holdout']}
        common = tn & hn
        norm_shared_keys += len(common)
        norm_train_rows += sum(norm4(f) in common for _, _, f in item['train'])
        norm_holdout_rows += sum(norm4(f) in common for _, _, f in item['holdout'])
        for side, rows in (('train', item['train']), ('holdout', item['holdout'])):
            for path, line, fen in rows:
                b, s, _, ep = fields(fen)
                lines.append('\t'.join([key, cls, why, side, path, str(line), fen, ep_status(b, s, ep), norm4(fen)]))
    if pair_reason['invalid_ep'] or pair_reason['identical_4field']:
        reasons.append(f"fail-closed pair classes present: invalid_ep pairs {pair_reason['invalid_ep']}, "
                       f"identical_4field pairs {pair_reason['identical_4field']}")
    status = 'UNVERIFIED' if reasons else 'COMPLETE'
    if a.rows:
        Path(a.rows).write_text('\n'.join(lines) + '\n', encoding='utf-8', newline='\n')
    record = dict(
        schema=1, tool='opus_boardstm_triage.py', tool_md5=dict(triage=md5(__file__),
                                                                 ep=md5(Path(__file__).with_name('opus_ep.py'))),
        status=status, reasons=reasons, sources=sources,
        definitions={
            'ep_format_diff': 'raw EP fields differ; equal after legal-capture-only EP normalisation (same position)',
            'real_ep_diff': 'normalised EP fields still differ: a legal en-passant capture exists in one row only',
            'other': 'castling_diff, mixed pair classes, invalid_ep or identical_4field (the last two fail closed)',
            'pair': 'every train row x every holdout row of one shared board+stm key',
            'normalised_4field': 'board, side, castling (KQkq order), EP kept only with a legal capture (opus_ep)'},
        totals=dict(shared_keys=totals[0], train_rows=totals[1], holdout_rows=totals[2], expected=list(expect)),
        keys_per_class=dict(key_class), key_reasons=dict(key_reason), pairs_per_class=dict(pair_counter),
        other_pair_reasons=dict(pair_reason),
        rows_per_class={c: dict(train=v[0], holdout=v[1]) for c, v in rows_by_class.items()},
        raw_ep_patterns=[dict(pair_class=c, train=t, holdout=h, pairs=n) for (c, t, h), n in sorted(pattern.items())],
        per_holdout_file={k: dict(v) for k, v in sorted(by_holdout.items())},
        per_piece_count={str(k): dict(v) for k, v in sorted(by_pieces.items())},
        per_train_file={k: dict(v) for k, v in sorted(by_train_file.items())},
        normalised_4field_recount=dict(
            shared_keys=norm_shared_keys, train_rows=norm_train_rows, holdout_rows=norm_holdout_rows,
            scope='exact over all rows: a normalised 4-field match implies a board+stm match, and the board+stm '
                  'listing is complete'),
        rows_file=dict(path=a.rows, md5=md5(a.rows)) if a.rows else None,
        written_vienna=datetime.datetime.now().strftime('%Y-%m-%d %H:%M') + ' Vienna')
    with open(a.out, 'x', encoding='utf-8', newline='\n') as stream:
        json.dump(record, stream, indent=1)
    print(json.dumps(dict(status=status, reasons=reasons, keys_per_class=record['keys_per_class'],
                          normalised_4field_recount=record['normalised_4field_recount'])))
    return 0 if status == 'COMPLETE' else 2


if __name__ == '__main__':
    sys.exit(main())
