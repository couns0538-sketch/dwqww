#!/usr/bin/env python3
"""make_net_index.py - Opus 30-h job: D:\\o30\\nets\\INDEX.md from every packed net (D:\\o30\\nets\\<name>\\RESULT.json, plus
FINAL_CHECKS.json and TRAINING.json when present). Read-only on the net folders; writes INDEX.md.new and renames it
over INDEX.md (the index is a generated file; the evidence stays in the per-net folders).
usage: python -I -B make_net_index.py [--root D:\\o30\\nets] [--skip-prefix test_]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import combine_sanity  # noqa: E402  (own module next to this file: pooled pentanomial)

LOCK = {'s16': 0.014310027, 'jobA': 0.013272058}


def fmt_z(z):
    return 'n/a' if z is None else f'{z:+.2f}'


def match_log(d, sub):
    """The fastchess log of the sanity_match.py run in <net>/<sub>: sanity_match.py names it after the folder
    (<sub>/<sub>.log; bug hunt 2026-11-04: <sub>/sanity.log only exists for the folder 'sanity')."""
    for name in (sub + '.log', 'sanity.log'):
        p = os.path.join(d, sub, name)
        if os.path.isfile(p):
            return p
    return None


def sanity_from_log(d):
    """Every sanity_match.py run of a net in <net>/sanity, sanity2, sanity3 (GPU nets have no FINAL_CHECKS.json):
    'Games: N, Wins ..., Points ... (x %)' + 'Elo: ...' + the candidate exe and the opening seed from RUN_INFO.json; a
    match below its planned games is marked RUNNING. A folder without a log or without a summary (a placeholder) is
    skipped. With two or more matches the game pairs are also POOLED (combine_sanity.py; window 3 played extra games of
    a net on other openings) - review W2-10's "newest log wins" is replaced by listing every match."""
    texts, logs, seeds = [], [], []
    for sub in ('sanity', 'sanity2', 'sanity3'):
        p = match_log(d, sub)
        if p is None:
            continue
        games = elo = ''
        for line in open(p, encoding='utf-8', errors='replace'):
            if line.startswith('Games:'):
                games = line.strip()
            elif line.startswith('Elo:'):
                elo = line.strip().split(', nElo')[0]
        if not games:
            continue
        out = f'{games}; {elo}' if elo else games
        seed = '?'
        ri = os.path.join(d, sub, 'RUN_INFO.json')
        if os.path.isfile(ri):
            info = json.load(open(ri, encoding='utf-8-sig'))
            planned = info.get('games')
            played = int(games.split(',')[0].split(':')[1])
            state = 'RUNNING, ' if isinstance(planned, int) and played < planned else ''
            cmd = info.get('cmd', [])
            seed = cmd[cmd.index('-srand') + 1] if '-srand' in cmd and cmd.index('-srand') + 1 < len(cmd) else '?'
            out = (f"{state}{out}; exe {info['candidate']['sha256'][:8]}; planned {planned if planned else '?'} games, "
                   f"opening seed {seed} ({sub})")
        texts.append(out)
        logs.append(p)
        seeds.append(seed)
    if not texts:
        return '-'
    if len(texts) == 1:
        return texts[0]
    pairs = [0] * 5
    for p in logs:
        pairs = [a + b for a, b in zip(pairs, combine_sanity.ptnml(p))]
    n, mean, e, pm = combine_sanity.summary(pairs)
    same = ' - SAME openings, the pool repeats them' if len(set(seeds)) < len(seeds) else ''
    return ' / '.join(texts) + f' / POOLED {2 * n} games {mean * 100:.2f} %, Elo {e:+.2f} +/- {pm:.2f}{same}'


def rematch_v2p4(d):
    """The rematch on the gate exe v2p4 in <net>/sanity_v2p4 (the CPU nets n2e / n2L were first played on v2p3,
    ff856ba8): latest 'Games: ...' + 'Elo: ...' of its fastchess log + the candidate exe from RUN_INFO.json, or ''."""
    sub = os.path.join(d, 'sanity_v2p4')
    log = os.path.join(sub, 'sanity_v2p4.log')
    if not os.path.isfile(log):
        return ''
    games = elo = ''
    for line in open(log, encoding='utf-8', errors='replace'):
        if line.startswith('Games:'):
            games = line.strip()
        elif line.startswith('Elo:'):
            elo = line.strip().split(', nElo')[0]
    if not games:
        return ''
    out = f'{games}; {elo}' if elo else games
    ri = os.path.join(sub, 'RUN_INFO.json')
    if os.path.isfile(ri):
        info = json.load(open(ri, encoding='utf-8-sig'))
        planned = info.get('games')
        played = int(games.split(',')[0].split(':')[1])
        state = 'RUNNING, ' if isinstance(planned, int) and played < planned else ''
        out = f"{state}{out}; exe {info['candidate']['sha256'][:8]}"
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default=r'D:\o30\nets')
    ap.add_argument('--skip-prefix', default='test_')
    a = ap.parse_args()
    rows = []
    for name in sorted(os.listdir(a.root)):
        d = os.path.join(a.root, name)
        rp = os.path.join(d, 'RESULT.json')
        if name.startswith(a.skip_prefix) or not os.path.isfile(rp):
            continue
        r = json.load(open(rp))
        fc = json.load(open(os.path.join(d, 'FINAL_CHECKS.json'))) if os.path.isfile(os.path.join(d, 'FINAL_CHECKS.json')) else None
        tr = json.load(open(os.path.join(d, 'TRAINING.json'))) if os.path.isfile(os.path.join(d, 'TRAINING.json')) else None
        rows.append((name, r, fc, tr))
    lines = ['# D:\\o30\\nets - v2 nets for the crew gate queue (Opus 30-h job)', '',
             'Generated by `opus_30h/a/make_net_index.py` from the per-net RESULT.json / FINAL_CHECKS.json / TRAINING.json.',
             'Every number is offline or sanity only: NO Elo claim. Gate: the GATE EXE with `EvalFileV2=<net path>` vs the lock',
             'FD3A5190 (UHO [0,5] SPRT first, 8moves_v3 confirm). The exe advertises EvalFileV2; with it empty the exe plays the',
             'lock net with the lock pins.', '',
             '**Gate exe: `D:\\o30\\w\\v2p4_pc1\\src_copy\\forge_ltopgo_v2p4_pc1.exe` sha256',
             'a2a560cb4b6a2c1127a41867fc5287cad0834bcd207f0583571c248d363ee7ca** (kit v2.5, pc1 = pc2; v2port.patch md5 926ada2c with',
             'the root fix of 2026-11-04: without it the v2 path lost ~8 % speed in games). The two CPU-trained nets (n2e,',
             'n2L) were packed on v2p3 (ff856ba8) and bench to the same node counts on v2p4; every GPU net was packed on v2p4',
             '(named per net below). OFF pins, identity, UCI conformance and the loader fuzz pass on v2p4. Use v2p4, not ff856ba8.', '',
             'Offline rule (written before the results, a/RESULTS.md): S31 b0.6 at least 2e-5 below the lock net AND a paired',
             'jobA-val z <= +2. Paired = the same rows scored by both nets (o30_paired.py); z = diff / its measurement error.',
             'READ THE SANITY COLUMN WITH THE CONTROL: the gate exe v2p4 playing the LOCK net (written as KB4 replicas, identical',
             'evaluation and tree) scored 47.0 % = -20.9 +/- 18.5 against the lock exe in the same 400-game setting',
             '(D:\\o30\\control\\lockkb4_v2p4; on the older v2p3 exe -32.2 +/- 18.5, lockkb4_v2exe) - the v2 exe itself costs',
             'Elo. Compare each net with that control, not only with 50 %. More king buckets cost speed on top (identity nets,',
             'same trees, a/logs/checks_gpu_w2, 3-4 runs: KB8 ~0.988x, KB16 ~0.969x, KB32 ~0.942x the nps of KB4). Sanity',
             'matches are not gates.', '',
             '| net | S31 b0.6 vs lock (z) | jobA val vs lock (z) | offline rule | pack checks | sanity match (SANITY ONLY) |',
             '|---|---|---|---|---|---|']
    for name, r, fc, tr in rows:
        rule = r.get('offline_rule')
        sanity = sanity_from_log(os.path.join(a.root, name))
        if fc:
            wdl = next((l.strip() for l in fc['sanity'] if 'W/D/L' in l), '')
            elo = next((l.strip().split('  nElo')[0] for l in fc['sanity'] if l.strip().startswith('Elo ')), '')
            sanity = (wdl.split('  Ptnml')[0] + (f'; {elo}' if elo else '')) or '-'
            ri = os.path.join(a.root, name, 'sanity', 'RUN_INFO.json')
            if sanity != '-' and os.path.isfile(ri):   # which exe played it (a later, faster exe must not be mixed in)
                sanity += f"; exe {json.load(open(ri, encoding='utf-8-sig'))['candidate']['sha256'][:8]}"
        rm = rematch_v2p4(os.path.join(a.root, name))
        if rm:   # bug hunt 2026-11-04: the rematch on the gate exe was missing from the index
            sanity += f'; REMATCH on the gate exe v2p4: {rm}'
        if rule:
            lines.append(f"| {name} | {rule['s16_b06_diff']:+.2e} ({fmt_z(rule['s16_z'])}) | {rule['jobA_b06_diff']:+.2e} "
                         f"({fmt_z(rule['jobA_z'])}) | {'PASS' if rule['pass'] else 'FAIL'} | {r['all_checks_passed']} | {sanity} |")
        else:
            lines.append(f"| {name} | {r['score_s16']['mse_b0.6'] - LOCK['s16']:+.2e} (not paired) | "
                         f"{r['score_jobA_val']['mse_b0.6'] - LOCK['jobA']:+.2e} (not paired) | not recorded | "
                         f"{r['all_checks_passed']} | {sanity} |")
    lines.append('')
    for name, r, fc, tr in rows:
        s16, ja = r['score_s16'], r['score_jobA_val']
        lines += [f'## {name}', '',
                  '| field | value |', '|---|---|',
                  f"| net (full path) | `{r['net']}` |",
                  f"| net sha256 / md5 | {r['sha256']} / {r['md5']} |",
                  f"| exe (gate) | `{r['exe']}` sha256 {r['exe_sha256']} |",
                  f"| gate option | `{r['gate_option']}` |",
                  f"| shape | {r['info'].split(': ', 1)[1].strip() if ': ' in r['info'] else r['info']} |",
                  f"| S31 holdout b0.6 / b1.0 | {s16['mse_b0.6']:.9f} ({s16['mse_b0.6'] - LOCK['s16']:+.2e} vs the lock net) / {s16['mse_b1.0']:.9f} |",
                  f"| jobA val b0.6 (20k-node labels) | {ja['mse_b0.6']:.9f} ({ja['mse_b0.6'] - LOCK['jobA']:+.2e}) |"]
        rule = r.get('offline_rule')
        if rule:
            lines.append(f"| offline rule | {'PASS' if rule['pass'] else 'FAIL'}: S31 paired {rule['s16_b06_diff']:+.2e} "
                         f"(z {fmt_z(rule['s16_z'])}), jobA paired {rule['jobA_b06_diff']:+.2e} (z {fmt_z(rule['jobA_z'])}) |")
        lines += [
                  f"| bench ON d11 / d13 / d16 | {r['bench_on']} |",
                  f"| OFF pins / ON line | {r['pins_off']} / {r['pins_on']} |",
                  f"| parity (AVX2 / SSE / scalar vs own reference, 10,000 FENs) | {sum(' -> PASS' in x for x in r['parity'])} of 3 builds PASS; "
                  f"{'planted bug caught' if any('planted bug caught' in x for x in r['parity']) else 'planted bug NOT caught'}; "
                  f"{'PARITY PASS' if any(x.startswith('PARITY PASS') for x in r['parity']) else 'PARITY FAIL'} |",
                  f"| all pack checks passed | {r['all_checks_passed']} |"]
        if tr:
            lines.append(f"| training | {tr.get('summary', '')} |")
        if not fc and sanity_from_log(os.path.join(a.root, name)) != '-':
            lines.append(f"| sanity match (SANITY ONLY) | {sanity_from_log(os.path.join(a.root, name))} |")
        if fc:
            lines.append(f"| smoke 300 s | {' / '.join(fc['smoke_300s'][-2:])} |")
            lines.append(f"| speed vs lock (advisory, different trees) | {' / '.join(fc['abba_nps'])} |")
            lines.append(f"| sanity match (SANITY ONLY) | {' / '.join(l for l in fc['sanity'] if 'Elo' in l or 'W/D/L' in l or 'Games' in l)[:400]} |")
        rm = rematch_v2p4(os.path.join(a.root, name))
        if rm:
            lines.append(f"| sanity rematch on the gate exe v2p4 (SANITY ONLY; `sanity_v2p4\\`) | {rm} |")
        lines.append('')
    tmp = os.path.join(a.root, 'INDEX.md.new')
    with open(tmp, 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(lines) + '\n')
    os.replace(tmp, os.path.join(a.root, 'INDEX.md'))
    print(f'INDEX.md: {len(rows)} nets')


if __name__ == '__main__':
    main()
