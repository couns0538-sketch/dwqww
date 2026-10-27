#!/usr/bin/env python3
"""make_s38_fixture.py (S38, opus 2026-10-27): deterministic synthetic fastchess fixture for the S38 audit tool.

No engine is run (the PC is busy with gates; an idle-priority match would still share SMT cores with gate engines).
The files copy the real fastchess 1.8.2 formats seen in the PC gate files (PGN with timeleft comments, stdout log,
`-log engine=true` lines) and the termination strings found in fastchess.exe. Single process = one slot (< 1>).
Writes into --out (default: fixtures/ next to this file):
  s38fx_A.{pgn,log}, s38fx_A_engine_io.log   30 games; cand nps ~4.5% above base; cand has a heavy time tail;
                                             events: cand 2 TL + 1 disconnect, base 1 TL + 1 illegal move;
                                             one 'Warning; Illegal PV move' line in the stdout log
  s38fx_REF.{pgn,log}, s38fx_REF_engine_io.log 12 games; symmetric nps, light tail, no events (the reference gate)
  s38fx_truth.json                           the generator's own counts (TL per engine, games, per-search nps list)
"""
import argparse
import json
import os
import random

BOOK_SAN = 'e4 c6 d4 d5 exd5 cxd5 Bd3 Nc6 c3 g6 Nf3 Bg7 O-O Nf6 Bf4 O-O'.split()
BOOK_UCI = 'e2e4 c7c6 d2d4 d7d5 e4d5 c6d5 f1d3 b8c6 c2c3 g7g6 g1f3 f8g7 e1g1 g8f6 c1f4 e8g8'.split()
CYC_SAN = ['Ng5', 'Ng4', 'Nf3', 'Nf6']
CYC_UCI = ['f3g5', 'f6g4', 'g5f3', 'g4f6']
BASE_MS, INC_MS = 10000, 100
CAND, BASEN = 'cand_s38', 'base_s38'


def limits(rem, inc):
    avail = max(1, rem - 10)
    soft = avail // 22 + inc * 75 // 100
    hard = min(avail * 60 // 100, soft * 5)
    return max(1, min(soft, avail)), max(1, min(hard, avail))


def fmt_s(ms):
    return f'{ms / 1000:.3f}s'


class Clock:
    def __init__(self):
        self.t = 3 * 3600 * 1_000_000  # microseconds since midnight, 03:00:00

    def adv(self, ms):
        self.t += int(ms * 1000)

    def stamp(self):
        us = self.t
        h, us = divmod(us, 3600 * 10**6)
        m, us = divmod(us, 60 * 10**6)
        s, us = divmod(us, 10**6)
        return f'{h:02d}:{m:02d}:{s:02d}.{us:06d}'


def gen(name, games, rng, profile, events, warn_after):
    clock = Clock()
    pgn, log, eio = [], ['Indexing opening suite...'], []
    truth = {'games': games, 'tl': {CAND: 0, BASEN: 0}, 'illegal': {CAND: 0, BASEN: 0}, 'crash': {CAND: 0, BASEN: 0},
             'nps': {CAND: [], BASEN: []}, 'engine_moves': {CAND: 0, BASEN: 0}}
    score = {'w': 0, 'l': 0, 'd': 0}

    def E(slot, who, arrow, text):
        eio.append(f'[Engine] [{clock.stamp()}] <{slot:>3}>  {who} {arrow} {text}')

    for g in range(1, games + 1):
        white, black = (CAND, BASEN) if g % 2 else (BASEN, CAND)
        log.append(f'Started game {g} of {games} ({white} vs {black})')
        for who in (white, black):
            E(1, who, '<---', 'ucinewgame')
        ev = events.get(g)           # (kind, loser) or None
        n_engine = rng.randint(24, 50)
        if ev is not None:   # the losing engine must be the side to move when the game ends
            loser_col = 'w' if ev[1] == white else 'b'
            if ('w' if (len(BOOK_SAN) + n_engine) % 2 == 0 else 'b') != loser_col:
                n_engine += 1
        rem = {'w': BASE_MS + INC_MS, 'b': BASE_MS + INC_MS}
        san, uci, cmts = list(BOOK_SAN), list(BOOK_UCI), ['book'] * len(BOOK_SAN)
        for i in range(n_engine):
            ply = len(BOOK_SAN) + i
            col = 'w' if ply % 2 == 0 else 'b'
            who = white if col == 'w' else black
            p = profile[who]
            soft, hard = limits(rem[col], INC_MS)
            f = rng.uniform(1.6, 2.6) if rng.random() < p['tail'] else rng.uniform(0.45, 1.25)
            used = max(5, min(int(soft * f), hard, rem[col] - 5))
            depth = p['depth0'] + ply // 20 + rng.randint(-2, 2)
            phase_k = 1.0 + 0.05 * min(2, ply // 40)
            fin_t = max(1, used - rng.randint(1, 4))
            nps = int(p['nps'] * phase_k * rng.uniform(0.97, 1.03))
            E(1, who, '<---', 'position startpos moves ' + ' '.join(uci))
            E(1, who, '<---', f'go wtime {rem["w"]} btime {rem["b"]} winc {INC_MS} binc {INC_MS}')
            for k, (frac, ramp) in enumerate(((0.1, 0.85), (0.35, 0.95), (1.0, 1.0))):   # nps rises during a search
                tt = max(1, int(fin_t * frac)) if frac < 1.0 else fin_t
                nk = int(nps * ramp)
                clock.adv(tt * 0.3)
                E(1, who, '--->', f'info depth {max(1, depth - 2 + k)} seldepth {depth + 6} score cp {rng.randint(-40, 40)} '
                                  f'nodes {nk * tt // 1000} nps {nk} hashfull {min(999, tt)} time {tt} pv {CYC_UCI[i % 4]}')
            clock.adv(used * 0.1)
            if fin_t >= 100:
                truth['nps'][who].append(nps)
            truth['engine_moves'][who] += 1
            E(1, who, '--->', f'bestmove {CYC_UCI[i % 4]}')
            rem[col] = rem[col] - used + INC_MS
            ev_s = f'{"+" if rng.random() < 0.5 else "-"}{rng.randint(0, 60) / 100:.2f}'.replace('+0.00', '0.00').replace('-0.00', '0.00')
            san.append(CYC_SAN[i % 4]); uci.append(CYC_UCI[i % 4])
            cmts.append(f'{ev_s}/{depth} {fmt_s(used)}, tl={fmt_s(rem[col])}')
        if ev is None:
            r = rng.random()
            if r < 0.30:
                res, reason, term = '1-0', 'White mates', 'normal'
            elif r < 0.55:
                res, reason, term = '0-1', 'Black mates', 'normal'
            else:
                res, reason, term = '1/2-1/2', 'Draw by 3-fold repetition', 'normal'
        else:
            kind, loser = ev
            side = 'White' if loser == white else 'Black'
            res = '0-1' if side == 'White' else '1-0'
            if kind == 'tl':
                reason, term = f'{side} loses on time', 'time forfeit'
                who, col = loser, ('w' if side == 'White' else 'b')
                E(1, who, '<---', 'position startpos moves ' + ' '.join(uci))
                E(1, who, '<---', f'go wtime {rem["w"]} btime {rem["b"]} winc {INC_MS} binc {INC_MS}')
                E(1, who, '--->', f'info depth 9 seldepth 14 score cp 3 nodes 900000 nps 1500000 hashfull 20 time 600 pv {CYC_UCI[0]}')
            elif kind == 'illegal':
                reason, term = f'{side} makes an illegal move', 'illegal move'
            else:
                reason, term = f'{side} disconnects', 'abandoned'
            truth[kind][loser] += 1
        cmts[-1] = cmts[-1] + ', ' + reason
        cand_pts = {'1-0': 1.0, '0-1': 0.0}.get(res, 0.5) if white == CAND else {'1-0': 0.0, '0-1': 1.0}.get(res, 0.5)
        score['w' if cand_pts == 1.0 else 'l' if cand_pts == 0.0 else 'd'] += 1
        log.append(f'Finished game {g} ({white} vs {black}): {res} {{{reason}}}')
        if g == warn_after:
            log.append(f'Warning; Illegal PV move - move e2e5 from {BASEN}')
        plies = len(san)
        hdr = [('Event', f'forge_{name}'), ('Site', '?'), ('Date', '2026.10.27'), ('Round', str((g + 1) // 2)),
               ('White', white), ('Black', black), ('Result', res), ('GameDuration', '00:00:20'),
               ('PlyCount', str(plies)), ('Termination', term), ('TimeControl', '10+0.1')]
        pgn.extend(f'[{k} "{v}"]' for k, v in hdr)
        pgn.append('')
        toks = []
        for i, (s, c) in enumerate(zip(san, cmts)):
            mv = f'{i // 2 + 1}. {s}' if i % 2 == 0 else s
            toks.append(f'{mv} {{{c}}}')
        toks.append(res)
        line = ''
        for t in toks:
            if len(line) + len(t) + 1 > 80 and line:
                pgn.append(line)
                line = t
            else:
                line = f'{line} {t}' if line else t
        pgn.append(line)
        pgn.append('')
    pts = score['w'] + 0.5 * score['d']
    log += ['-' * 50, f'Results of {CAND} vs {BASEN} (10+0.1, 1t, 16MB, s38fx_book.pgn):',
            f'Games: {games}, Wins: {score["w"]}, Losses: {score["l"]}, Draws: {score["d"]}, Points: {pts:.1f} ({100 * pts / games:.2f} %)',
            '(synthetic fixture: the Elo / LOS / Ptnml / LLR lines of a real block are omitted)', '-' * 50, 'Finished match']
    return pgn, log, eio, truth


def write(path, lines, crlf):
    with open(path, 'w', encoding='utf-8', newline='\r\n' if crlf else '\n') as f:
        f.write('\n'.join(lines) + '\n')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures'))
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    truth = {}
    prof_a = {CAND: {'nps': 1_620_000, 'tail': 0.10, 'depth0': 17}, BASEN: {'nps': 1_550_000, 'tail': 0.0, 'depth0': 17}}
    ev_a = {7: ('tl', CAND), 18: ('tl', CAND), 25: ('tl', BASEN), 27: ('illegal', BASEN), 29: ('disconnect', CAND)}
    prof_r = {CAND: {'nps': 1_550_000, 'tail': 0.0, 'depth0': 17}, BASEN: {'nps': 1_550_000, 'tail': 0.0, 'depth0': 17}}
    for nm, games, prof, ev, warn, seed in (('s38fx_A', 30, prof_a, ev_a, 5, 38001), ('s38fx_REF', 12, prof_r, {}, 0, 38002)):
        ev = {k: (('crash' if v[0] == 'disconnect' else v[0]), v[1]) for k, v in ev.items()}
        pgn, log, eio, t = gen(nm, games, random.Random(seed), prof, ev, warn)
        write(os.path.join(a.out, nm + '.pgn'), pgn, True)
        write(os.path.join(a.out, nm + '.log'), log, True)
        write(os.path.join(a.out, nm + '_engine_io.log'), eio, True)
        truth[nm] = t
    with open(os.path.join(a.out, 's38fx_truth.json'), 'w', encoding='utf-8', newline='\n') as f:
        json.dump(truth, f, indent=1, sort_keys=True)
        f.write('\n')
    print('wrote', ', '.join(sorted(os.listdir(a.out))))


if __name__ == '__main__':
    main()
