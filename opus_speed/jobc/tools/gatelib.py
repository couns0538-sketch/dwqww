#!/usr/bin/env python3
"""gatelib.py - shared parsing and statistics for the Job C gate tools (standard library only).

Formulas (pentanomial Elo / nElo, the exact fastchess 1.8.2 GSPRT LLR with the reference MLE iteration) are
reused from opus_r15/tools/gate_summary.py (branch opus-r15-20261103), where they were checked against the
printed blocks of 62 gates. Everything else is new: a strict PGN reader that refuses truncated, corrupt or
unpaired files, a fastchess log reader (completion order of the game pairs), RUN_INFO / config / RESULT.md
readers, and the pairing rules of a fastchess "-games 2 -repeat" match.

Privacy of outputs: the PGN tags EngineWhiteAuthor / EngineBlackAuthor and any UCI "id author" line are dropped
at parse time and never reach a report.
"""
import datetime
import json
import math
import os
import re

NT = 800.0 / math.log(10.0)          # nElo per t unit
SC = (0.0, 0.25, 0.5, 0.75, 1.0)     # pair scores of the pentanomial cells
Z95 = 1.959963984540054
RESULT_TOKENS = ('1-0', '0-1', '1/2-1/2', '*')
DROP_TAGS = ('EngineWhiteAuthor', 'EngineBlackAuthor')


class GateError(Exception):
    """Invalid input (truncated / corrupt / unpaired PGN, unreadable gate): callers print NO verdict."""


# ----------------------------------------------------------------------------------------------- statistics
def elo_of_score(s):
    s = min(max(s, 1e-12), 1.0 - 1e-12)
    return -400.0 * math.log10(1.0 / s - 1.0)


def ptnml_stats(pt):
    """Pair score, Elo +/- (95 %), nElo +/- from a pentanomial [0, 0.5, 1, 1.5, 2] count list."""
    n = float(sum(pt))
    if n == 0:
        return None
    p = [c / n for c in pt]
    a = sum(pi * si for pi, si in zip(p, SC))
    var = sum(pi * si * si for pi, si in zip(p, SC)) - a * a
    if var <= 0:
        return None
    se = math.sqrt(var / n)
    elo = elo_of_score(a)
    err = (elo_of_score(a + Z95 * se) - elo_of_score(a - Z95 * se)) / 2.0
    nelo = (a - 0.5) / math.sqrt(2.0 * var) * NT
    nelo_err = Z95 * se / math.sqrt(2.0 * var) * NT
    return {'score': a, 'var': var, 'elo': elo, 'elo_err': err, 'nelo': nelo, 'nelo_err': nelo_err}


def _secular(phat, a):
    """Root x of sum_i p_i a_i / (1 + x a_i) = 0 over the occupied cells (bisection-safeguarded Newton)."""
    cells = [(p, ai) for p, ai in zip(phat, a) if p > 0]
    amax = max(ai for _, ai in cells)
    amin = min(ai for _, ai in cells)
    if not (amax > 0 > amin):
        return None
    lo, hi = -1.0 / amax, -1.0 / amin
    x = 0.0
    for _ in range(200):
        f = sum(p * ai / (1.0 + x * ai) for p, ai in cells)
        fp = -sum(p * ai * ai / (1.0 + x * ai) ** 2 for p, ai in cells)
        if f > 0:
            lo = x
        else:
            hi = x
        xn = x - f / fp if fp != 0 else 0.5 * (lo + hi)
        if not (lo < xn < hi):
            xn = 0.5 * (lo + hi)
        if abs(xn - x) <= 1e-15 * (1.0 + abs(x)):
            return xn
        x = xn
    return x


def _mle_tvalue(phat, s):
    """Cell probabilities of maximum likelihood under (mu - 0.5) / sigma = s: start from the uniform pdf, at most
    10 fixed-point steps, stop when no cell moves by 1e-9 (the reference SPRT iteration that fastchess follows)."""
    pdf = [1.0 / len(phat)] * len(phat)
    for _ in range(10):
        mu = sum(p * si for p, si in zip(pdf, SC))
        var = max(sum(p * si * si for p, si in zip(pdf, SC)) - mu * mu, 1e-300)
        sigma = math.sqrt(var)
        a = [si - 0.5 - s * sigma * (1.0 + ((mu - si) / sigma) ** 2) / 2.0 for si in SC]
        x = _secular(phat, a)
        if x is None:
            return None
        new = [p / (1.0 + x * ai) for p, ai in zip(phat, a)]
        done = max(abs(u - v) for u, v in zip(new, pdf)) < 1e-9
        pdf = new
        if done:
            break
    return pdf


def exact_llr(pt, e0, e1):
    """fastchess normalized-model pentanomial LLR for bounds [e0, e1] nElo. Empty cells count 1e-3."""
    if sum(pt) == 0:
        return None
    reg = [max(1e-3, float(c)) for c in pt]
    n = sum(reg)
    phat = [c / n for c in reg]
    p0 = _mle_tvalue(phat, e0 / NT * math.sqrt(2.0))
    p1 = _mle_tvalue(phat, e1 / NT * math.sqrt(2.0))
    if p0 is None or p1 is None:
        return None
    return n * sum(p * math.log(q1 / q0) for p, q0, q1 in zip(phat, p0, p1) if p > 0)


def brownian_llr(pt, e0, e1):
    """Closed-form approximation (notes/T12/sprt_model.md): pairs * dt * (t_hat - t_mid)."""
    st = ptnml_stats(pt)
    if not st:
        return None
    k = math.sqrt(2.0) * math.log(10.0) / 800.0
    th = (st['score'] - 0.5) / math.sqrt(st['var'])
    dt = (e1 - e0) * k
    return sum(pt) * dt * (th - (e0 + e1) * k / 2.0)


def sprt_bounds(alpha=0.05, beta=0.05):
    return math.log(beta / (1.0 - alpha)), math.log((1.0 - beta) / alpha)


# ----------------------------------------------------------------------------------------------- gate files
def read_text(path):
    with open(path, encoding='utf-8-sig', errors='replace') as f:
        return f.read()


def load_json_bom(path):
    with open(path, encoding='utf-8-sig') as f:
        return json.load(f)


def find_gate_files(d):
    """(pgn, log, run_info, config, result_md) of a gate folder in the crew's layout; missing ones are None."""
    base = os.path.basename(os.path.normpath(d))
    pgn = os.path.join(d, base + '.pgn')
    log = os.path.join(d, base + '.log')
    if not os.path.exists(pgn):
        c = sorted(p for p in os.listdir(d) if p.endswith('.pgn') and 'engine_io' not in p)
        pgn = os.path.join(d, c[0]) if len(c) == 1 else None
    if not os.path.exists(log):
        c = sorted(p for p in os.listdir(d) if p.endswith('.log') and 'engine_io' not in p and not p.endswith('.log.err'))
        log = os.path.join(d, c[0]) if len(c) == 1 else None
    ri = None
    for n in ('RUN_INFO.json', 'RUN_INFO_QA.json'):
        if os.path.exists(os.path.join(d, n)):
            ri = os.path.join(d, n)
            break
    cfg = os.path.join(d, 'config.json') if os.path.exists(os.path.join(d, 'config.json')) else None
    res = None
    for n in ('RESULT.md', 'QA_RESULT.md'):
        if os.path.exists(os.path.join(d, n)):
            res = os.path.join(d, n)
            break
    return pgn, log, ri, cfg, res


def load_run_info(path):
    if not path:
        return {}
    try:
        return load_json_bom(path)
    except (OSError, ValueError) as e:
        raise GateError(f'RUN_INFO unreadable: {path}: {e}')


def load_config(path):
    if not path:
        return {}
    try:
        return load_json_bom(path)
    except (OSError, ValueError):
        return {}


SPRT_RX = re.compile(r'\[\s*(-?[\d.]+)\s*,\s*(-?[\d.]+)\s*\]')


def gate_bounds(info, cfg, block):
    """(elo0, elo1, alpha, beta, source). Order: config.json sprt -> RUN_INFO sprt -> the log's printed block."""
    sp = cfg.get('sprt') if isinstance(cfg, dict) else None
    if isinstance(sp, dict) and sp.get('elo0') is not None and sp.get('elo1') is not None:
        return float(sp['elo0']), float(sp['elo1']), float(sp.get('alpha', 0.05)), float(sp.get('beta', 0.05)), 'config.json'
    s = info.get('sprt') if isinstance(info, dict) else None
    if isinstance(s, str):
        m = SPRT_RX.search(s)
        if m:
            a = re.search(r'a(?:lpha)?\s*=\s*([\d.]+)', s)
            b = re.search(r'b(?:eta)?\s*=\s*([\d.]+)', s)
            return float(m.group(1)), float(m.group(2)), float(a.group(1)) if a else 0.05, float(b.group(1)) if b else 0.05, 'RUN_INFO'
    if block and block.get('elo0') is not None:
        return block['elo0'], block['elo1'], 0.05, 0.05, 'log block'
    return None


def candidate_name(info, block, games):
    if isinstance(info, dict) and isinstance(info.get('candidate'), dict) and info['candidate'].get('name'):
        return info['candidate']['name']
    if isinstance(info, dict) and isinstance(info.get('cand'), dict) and info['cand'].get('name'):
        return info['cand']['name']
    if block and block.get('a'):
        return block['a']
    return games[0]['tags'].get('White') if games else None


VERDICT_RX = re.compile(r'\*\*Verdict:\s*(.+?)\*\*')


def classify_verdict(text):
    """H1 / H0 / H0-early / CAP / UNKNOWN from a RESULT.md or FORGE_RESULTS.csv verdict string."""
    t = (text or '').strip()
    if not t:
        return 'UNKNOWN'
    if 'H0-early' in t:
        return 'H0-early'
    if t.startswith('H1') or 'H1 accepted' in t or 'H1 NON-REGRESSION' in t:
        return 'H1'
    if t.startswith('H0') or 'H0 accepted' in t:
        return 'H0'
    if 'Cap with no decision' in t or 'no decision' in t:
        return 'CAP'
    return 'UNKNOWN'


def parse_result_md(path):
    """Recorded numbers of RESULT.md: verdict text + class, games, W/L/D, Ptnml, Elo, nElo, LLR, CLEAN flag."""
    if not path:
        return {}
    t = read_text(path)
    out = {'path': path}
    m = VERDICT_RX.search(t)
    out['verdict_text'] = m.group(1) if m else ''
    out['verdict'] = classify_verdict(out['verdict_text'])
    m = re.search(r'Games:\s*(\d+)\s+W/L/D[^:]*:\s*(\d+)\s*/\s*(\d+)\s*/\s*(\d+)', t)
    if m:
        out['games'], out['w'], out['l'], out['d'] = (int(x) for x in m.groups())
    m = re.search(r'Ptnml\(0-2\):\s*\[([\d, ]+)\]', t)
    if m:
        out['ptnml'] = [int(x) for x in m.group(1).split(',')]
    m = re.search(r'Elo:\s*(-?[\d.]+)\s*\+/-\s*([\d.]+)\s+nElo:\s*(-?[\d.]+)\s*\+/-\s*([\d.]+)', t)
    if m:
        out['elo'], out['elo_err'], out['nelo'], out['nelo_err'] = (float(x) for x in m.groups())
    m = re.search(r'LLR:\s*(-?[\d.]+)\s+bounds\s*\((-?[\d.]+),\s*(-?[\d.]+)\)\s*\[elo0=(-?[\d.]+),\s*elo1=(-?[\d.]+)', t)
    if m:
        out['llr'], out['llr_lo'], out['llr_hi'], out['elo0'], out['elo1'] = (float(x) for x in m.groups())
    out['clean'] = 'NOT CLEAN' not in t and ': CLEAN' in t
    return out


# ----------------------------------------------------------------------------------------------- log
FIN_RX = re.compile(r'^Finished game (\d+) \((.+?) vs (.+?)\): (1-0|0-1|1/2-1/2|\*) \{([^}]*)\}')
START_RX = re.compile(r'^Started game (\d+) of (\d+) \((.+?) vs (.+?)\)')


def last_block(log_text):
    """The last fastchess result block of the log (same fields as gate_summary.py), or None."""
    i = log_text.rfind('Results of ')
    if i < 0:
        return None
    t = log_text[i:i + 2000]
    b = {'pos': i}
    m = re.match(r'Results of (.+?) vs (.+?) \(([^)]*)\):', t)
    if m:
        b['a'], b['b'], b['settings'] = m.group(1), m.group(2), m.group(3)
    m = re.search(r'Elo: (-?[\d.]+|inf|-inf|nan) \+/- ([\d.]+|nan|inf), nElo: (-?[\d.]+|nan|inf) \+/- ([\d.]+|nan|inf)', t)
    if m:
        b['elo'], b['elo_err'], b['nelo'], b['nelo_err'] = (float(x) for x in m.groups())
    m = re.search(r'Games: (\d+), Wins: (\d+), Losses: (\d+), Draws: (\d+)', t)
    if m:
        b['games'], b['w'], b['l'], b['d'] = (int(x) for x in m.groups())
    m = re.search(r'Ptnml\(0-2\): \[([\d, ]+)\]', t)
    if m:
        b['ptnml'] = [int(x) for x in m.group(1).split(',')]
    m = re.search(r'LLR: (-?[\d.]+) \([^)]*\) \((-?[\d.]+), (-?[\d.]+)\) \[(-?[\d.]+), (-?[\d.]+)\]', t)
    if m:
        b['llr'], b['llr_lo'], b['llr_hi'], b['elo0'], b['elo1'] = (float(x) for x in m.groups())
    b['finished'] = 'Finished match' in log_text[i:]
    m = re.search(r'SPRT \(\[[^\]]*\]\) completed - (H[01]) was accepted', log_text[i:])
    b['sprt_completed'] = m.group(1) if m else None
    m = re.search(r'Total Time: (\d+):(\d+):(\d+)', log_text[i:])
    if m:
        b['total_time_s'] = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + int(m.group(3))
    return b


def parse_log(path):
    """Game bookkeeping of a fastchess stdout log: started numbers, finished games in completion order
    (game_no, white, black, result, reason, before_last_block), the printed last block, the time stamps if the
    log carries them (older runner: 'YYYY-MM-DD HH:MM:SS | text')."""
    text = read_text(path)
    cut = text.rfind('Results of ')
    started, finished = {}, []
    first_ts = last_ts = None
    ts_rx = re.compile(r'^(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d) \| ?(.*)$')
    pos = 0
    for raw in text.splitlines(keepends=True):
        line_pos = pos
        pos += len(raw)
        line = raw.rstrip('\r\n')
        m = ts_rx.match(line)
        if m:
            ts = m.group(1)
            first_ts = first_ts or ts
            last_ts = ts
            line = m.group(2)
        m = START_RX.match(line)
        if m:
            started[int(m.group(1))] = (m.group(3), m.group(4), int(m.group(2)))
            continue
        m = FIN_RX.match(line)
        if m:
            finished.append({'no': int(m.group(1)), 'white': m.group(2), 'black': m.group(3), 'result': m.group(4),
                             'reason': m.group(5), 'before_block': cut < 0 or line_pos < cut})
    return {'path': path, 'started': started, 'finished': finished, 'block': last_block(text) if cut >= 0 else None,
            'first_ts': first_ts, 'last_ts': last_ts, 'rounds_total': max((v[2] for v in started.values()), default=None),
            'indexing': text.lstrip('\ufeff').startswith('Indexing opening suite') or 'Indexing opening suite' in text[:400]}


# ----------------------------------------------------------------------------------------------- PGN
TAG_RX = re.compile(r'^\[([A-Za-z0-9_]+)\s+"((?:[^"\\]|\\.)*)"\]\s*$')
TOKEN_RX = re.compile(r'\{[^}]*\}|\([^)]*\)|;[^\n]*|\S+')
MOVENO_RX = re.compile(r'^(\d+)\.(\.\.)?$')
GLUED_RX = re.compile(r'^(\d+)\.+(\S+)$')
COMMENT_RX = re.compile(r'^([+-]?)(M?)(\d+(?:\.\d+)?)/(\d+)\s+([\d.]+)s(?:,\s*tl=([\d.]+)s)?')
MOVE_CHARS_RX = re.compile(r'^[KQRBNP]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QRBN])?[+#]?$|^O-O(?:-O)?[+#]?$|^[a-h][1-8]=?[QRBN]?[+#]?$')


def parse_comment(c):
    """fastchess move comment '{+0.12/21 0.867s, tl=9.333s[, reason]}' -> dict(cp|mate, depth, sec, tl, reason) or
    {'book': True} for '{book}'. Scores are from the mover's point of view (checked: +M1 at a mate)."""
    s = c[1:-1].strip() if c.startswith('{') else c.strip()
    if s == 'book':
        return {'book': True}
    m = COMMENT_RX.match(s)
    if not m:
        return {'raw': s}
    sign, mate, val, depth, sec, tl = m.groups()
    out = {'depth': int(depth), 'sec': float(sec), 'tl': float(tl) if tl else None}
    v = float(val)
    if mate:
        out['mate'] = int(v) if sign != '-' else -int(v)
    else:
        out['cp'] = int(round(v * 100)) * (-1 if sign == '-' else 1)
    rest = s[m.end():].strip(', ')
    if rest:
        out['reason'] = rest
    return out


def parse_pgn_strict(path, verify_moves=False):
    """All games of a PGN file. Raises GateError on: a malformed tag line, a game without a result token, a result
    token that differs from the Result tag, a Result tag of '*', a PlyCount tag that differs from the counted
    plies, a trailing fragment (file ends inside a game) or, with verify_moves, an illegal move (python-chess).
    Each game: {'tags': {...}, 'plies': [(san, comment_dict_or_None), ...], 'line': first line number}."""
    games = []
    cur = None          # current game dict while reading tags
    body = []           # movetext lines of the current game
    state = 'between'   # between | tags | moves
    line_no = 0
    with open(path, encoding='utf-8', errors='replace') as f:
        for raw in f:
            line_no += 1
            line = raw.rstrip('\r\n')
            if '\x00' in line:
                raise GateError(f'{os.path.basename(path)} line {line_no}: NUL byte (binary garbage)')
            stripped = line.strip()
            if state in ('between', 'tags') and stripped.startswith('['):
                m = TAG_RX.match(stripped)
                if not m:
                    raise GateError(f'{os.path.basename(path)} line {line_no}: malformed tag line {stripped[:60]!r}')
                if state == 'between':
                    cur = {'tags': {}, 'line': line_no}
                    state = 'tags'
                if m.group(1) not in DROP_TAGS:
                    cur['tags'][m.group(1)] = m.group(2)
                continue
            if state == 'tags':
                if not stripped:
                    state = 'moves'
                    continue
                state = 'moves'          # movetext without the blank separator line
            if state == 'moves':
                if stripped.startswith('[') and not body:
                    raise GateError(f'{os.path.basename(path)} line {line_no}: game at line {cur["line"]} has headers but no movetext')
                if stripped.startswith('[') and body:
                    # a new game starts: the previous one must have ended with a result token
                    games.append(_finish_game(cur, body, path, verify_moves))
                    cur, body = {'tags': {}, 'line': line_no}, []
                    m = TAG_RX.match(stripped)
                    if not m:
                        raise GateError(f'{os.path.basename(path)} line {line_no}: malformed tag line {stripped[:60]!r}')
                    if m.group(1) not in DROP_TAGS:
                        cur['tags'][m.group(1)] = m.group(2)
                    state = 'tags'
                    continue
                if stripped:
                    body.append(stripped)
                continue
            if state == 'between' and stripped:
                raise GateError(f'{os.path.basename(path)} line {line_no}: text outside a game: {stripped[:60]!r}')
    if state == 'tags':
        raise GateError(f'{os.path.basename(path)}: file ends inside the headers of the game at line {cur["line"]} (truncated)')
    if state == 'moves':
        if not body:
            raise GateError(f'{os.path.basename(path)}: file ends after the headers of the game at line {cur["line"]} (truncated)')
        games.append(_finish_game(cur, body, path, verify_moves))
    if not games:
        raise GateError(f'{os.path.basename(path)}: no game found')
    return games


def _finish_game(cur, body, path, verify_moves):
    tags = cur['tags']
    name = os.path.basename(path)
    for k in ('Round', 'White', 'Black', 'Result'):
        if k not in tags:
            raise GateError(f'{name}: game at line {cur["line"]} lacks the {k} tag')
    if tags['Result'] not in ('1-0', '0-1', '1/2-1/2'):
        raise GateError(f'{name}: game at line {cur["line"]} has Result {tags["Result"]!r} (unfinished or corrupt)')
    text = ' '.join(body)
    tokens = TOKEN_RX.findall(text)
    plies, result_tok, pending = [], None, None
    for tok in tokens:
        if result_tok is not None:
            raise GateError(f'{name}: game at line {cur["line"]}: text after the result token: {tok[:30]!r}')
        if tok.startswith('{'):
            if not plies:
                continue
            san, _ = plies[-1]
            plies[-1] = (san, parse_comment(tok))
            continue
        if tok.startswith(';') or tok.startswith('(') or tok.startswith('$'):
            continue
        if tok in RESULT_TOKENS:
            result_tok = tok
            continue
        if MOVENO_RX.match(tok):
            continue
        m = GLUED_RX.match(tok)
        if m:
            tok = m.group(2)
        if not MOVE_CHARS_RX.match(tok):
            raise GateError(f'{name}: game at line {cur["line"]}: not a SAN move: {tok[:30]!r} (corrupt movetext)')
        plies.append((tok, None))
    if result_tok is None:
        raise GateError(f'{name}: game at line {cur["line"]} has no result token (truncated)')
    if result_tok != tags['Result']:
        raise GateError(f'{name}: game at line {cur["line"]}: result token {result_tok} differs from the Result tag {tags["Result"]}')
    if 'PlyCount' in tags:
        try:
            pc = int(tags['PlyCount'])
        except ValueError:
            raise GateError(f'{name}: game at line {cur["line"]}: PlyCount {tags["PlyCount"]!r} is not a number')
        if pc != len(plies):
            raise GateError(f'{name}: game at line {cur["line"]}: PlyCount {pc} but {len(plies)} moves in the movetext (truncated or corrupt)')
    try:
        int(tags['Round'])
    except ValueError:
        raise GateError(f'{name}: game at line {cur["line"]}: Round {tags["Round"]!r} is not a number')
    if verify_moves:
        import chess
        b = chess.Board(tags['FEN']) if tags.get('FEN') else chess.Board()
        for i, (san, _) in enumerate(plies):
            try:
                b.push_san(san)
            except ValueError:
                raise GateError(f'{name}: game at line {cur["line"]}: illegal move {san} at ply {i + 1}')
    return {'tags': tags, 'plies': plies, 'line': cur['line']}


def parse_time(s):
    """'2026-10-31T01:23:21 -0700' or '2026-10-31 01:23:21' -> naive datetime (PC wall clock; the zone label is ignored)."""
    if not s:
        return None
    s = s.strip()[:19].replace('T', ' ')
    try:
        return datetime.datetime.strptime(s, '%Y-%m-%d %H:%M:%S')
    except ValueError:
        return None


def game_points(g, cand):
    """Points of `cand` in a game (1, 0.5, 0) or None if cand did not play."""
    t = g['tags']
    if cand not in (t['White'], t['Black']):
        return None
    r = t['Result']
    if r == '1/2-1/2':
        return 0.5
    white_won = r == '1-0'
    return 1.0 if (white_won == (t['White'] == cand)) else 0.0


def build_pairs(games, cand, log=None, concurrency=None, strict=True):
    """Pairs of a '-games 2 -repeat' match in completion order.
    Returns (pairs, info). Each pair: {'round', 'cell' (0..4), 'order' (completion index), 'before_block'}.
    Rules: a round must hold exactly 2 games with the colours swapped between the same two players. A single
    game in a round is legitimate only when the match stopped by SPRT and the partner game was started but never
    finished in the log (aborted in flight); at most `concurrency` such singles. Anything else raises GateError."""
    rounds = {}
    for g in games:
        rounds.setdefault(int(g['tags']['Round']), []).append(g)
    players = set()
    for g in games:
        players.add(g['tags']['White'])
        players.add(g['tags']['Black'])
    if cand not in players:
        raise GateError(f'candidate {cand!r} does not play in the PGN (players: {sorted(players)})')
    if len(players) != 2:
        raise GateError(f'expected exactly 2 players, found {sorted(players)}')
    fin_pos, fin_by_no = {}, {}
    if log:
        for i, f in enumerate(log['finished']):
            fin_pos[f['no']] = i
            fin_by_no[f['no']] = f
    stopped = bool(log and log['block'] and (log['block'].get('sprt_completed') or
                                             (log['block'].get('finished') and log['rounds_total'] and
                                              log['block'].get('games', 0) < 2 * log['rounds_total'])))
    pairs, singles, info = [], [], {'singles': [], 'order_source': 'log' if log else 'pgn GameEndTime (approximate, 1 s resolution)'}
    for r, gs in sorted(rounds.items()):
        if len(gs) > 2:
            raise GateError(f'round {r} has {len(gs)} games (expected 2): unpaired / duplicated PGN')
        if len(gs) == 1:
            g = gs[0]
            own_no = 2 * r - 1 if g['tags']['White'] == cand else 2 * r
            partner = 2 * r if own_no == 2 * r - 1 else 2 * r - 1
            ok = bool(log) and stopped and partner in log['started'] and partner not in fin_by_no
            if not ok or not strict and False:
                why = ('no log to prove the partner game was aborted in flight' if not log else
                       'the match did not stop by SPRT' if not stopped else
                       f'partner game {partner} finished in the log but is missing from the PGN' if partner in fin_by_no else
                       f'partner game {partner} was never started')
                raise GateError(f'round {r} has a single game: unpaired PGN ({why})')
            singles.append(r)
            info['singles'].append({'round': r, 'game_in_pgn': own_no, 'partner_aborted': partner})
            continue
        a, b = gs
        ta, tb = a['tags'], b['tags']
        if not (ta['White'] == tb['Black'] and ta['Black'] == tb['White']):
            raise GateError(f'round {r}: colours are not swapped between the two games ({ta["White"]} vs {ta["Black"]} / {tb["White"]} vs {tb["Black"]})')
        pa, pb = game_points(a, cand), game_points(b, cand)
        cell = int(round((pa + pb) * 2))
        nos = (2 * r - 1, 2 * r)
        if log:
            if any(n not in fin_by_no for n in nos):
                raise GateError(f'round {r}: game(s) {[n for n in nos if n not in fin_by_no]} are in the PGN but not finished in the log')
            for g in (a, b):
                n = 2 * r - 1 if g['tags']['White'] == cand else 2 * r
                f = fin_by_no[n]
                if f['result'] != g['tags']['Result'] or f['white'] != g['tags']['White']:
                    raise GateError(f'round {r} game {n}: PGN says {g["tags"]["White"]} {g["tags"]["Result"]}, log says {f["white"]} {f["result"]}')
            order = max(fin_pos[n] for n in nos)
            before = all(fin_by_no[n]['before_block'] for n in nos)
        else:
            ends = [parse_time(g['tags'].get('GameEndTime')) for g in gs]
            order = (max(e for e in ends if e) if any(ends) else datetime.datetime.min, r)
            before = True
        pairs.append({'round': r, 'cell': cell, 'order': order, 'before_block': before, 'games': gs})
    if singles and concurrency and len(singles) > concurrency:
        raise GateError(f'{len(singles)} single games but concurrency {concurrency}: unpaired PGN')
    if log:
        n_pgn = len(games)
        n_log = len(log['finished'])
        if n_pgn != n_log:
            raise GateError(f'PGN has {n_pgn} games, the log finished {n_log}: incomplete or foreign PGN')
    pairs.sort(key=lambda p: p['order'])
    for i, p in enumerate(pairs):
        p['k'] = i + 1
    return pairs, info


def ptnml_of(pairs):
    pt = [0, 0, 0, 0, 0]
    for p in pairs:
        pt[p['cell']] += 1
    return pt


def tally_wdl(games, cand):
    w = d = l = 0
    for g in games:
        p = game_points(g, cand)
        if p is None:
            continue
        if p == 1.0:
            w += 1
        elif p == 0.0:
            l += 1
        else:
            d += 1
    return w, d, l


def load_results_csv(path):
    """FORGE_RESULTS.csv rows by tag (UTF-8 BOM tolerant)."""
    import csv
    out = {}
    if not path or not os.path.exists(path):
        return out
    with open(path, encoding='utf-8-sig', newline='') as f:
        for row in csv.DictReader(f):
            out[row.get('tag', '')] = row
    return out
