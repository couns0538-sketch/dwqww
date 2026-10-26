"""Original, bounded Fastchess observation reader. No native acceptance authority.

Supports Results/Games/Ptnml/LLR summaries and Finished-game/Player fault lines.
Snapshots are cumulative and are never summed. Fault events and reported final
totals are separate observations, not additive or verified unique counts.
"""
from __future__ import annotations
import math
import re


def penta_matches_wdl(p, wdl):
    """Five bins leave WL vs DD ambiguous; check existence, never invent it."""
    if p is None or wdl is None:
        return None
    w, d, l = wdl
    wl = w - 2*p[4] - p[3]
    return (0 <= wl <= p[2] and l - 2*p[0] - p[1] == wl
            and d == p[1]+p[3]+2*(p[2]-wl))


def mine_log(text, candidate, baseline):
    if not isinstance(text, str) or not candidate or not baseline or candidate == baseline:
        raise ValueError('text and two distinct nonempty player names are required')
    issues, snapshots, events, acceptances, llr_lines = [], [], [], [], []
    finished, duplicates, player_totals, headers, unparsed = {}, [], {}, [], []
    player, current, terminal_matches = None, None, 0
    for lineno, original in enumerate(text.lstrip('\ufeff').splitlines(), 1):
        line = original.split('fastchess ---', 1)[-1].strip()
        header = re.fullmatch(r'Results of (.+) vs (.+?) \((.*)\):', line)
        if header:
            a, b, description = header.groups()
            if headers and headers[-1]['description'] != description:
                issues.append(f'line {lineno}: changed resource/opening description; separate matches cannot be pooled')
            if terminal_matches:
                issues.append(f'line {lineno}: summary after Finished match; separate experiment')
            headers.append({'line': lineno, 'candidate': a, 'baseline': b, 'description': description})
            if (a, b) != (candidate, baseline):
                issues.append(f'line {lineno}: different or reversed match header')
            current = {'line': lineno, 'games': None, 'wdl': None, 'pentabins': None, 'llr': None}
            snapshots.append(current)
        elif line.startswith('Results of '):
            unparsed.append({'line': lineno, 'text': line})
            issues.append(f'line {lineno}: unsupported Results header')
        if line == 'Finished match':
            terminal_matches += 1
            if terminal_matches > 1:
                issues.append('multiple Finished match terminals; separate experiments cannot be pooled')
        if line.startswith('Games:'):
            m = re.match(r'^Games: (\d+), Wins: (\d+), Losses: (\d+), Draws: (\d+)(?:,|$)', line)
            if not m or current is None:
                issues.append(f'line {lineno}: unsupported or unbound Games summary')
            else:
                n, w, l, d = map(int, m.groups())
                current.update(games=n, wdl=[w, d, l])
                if n != w+d+l:
                    issues.append(f'line {lineno}: W/D/L sum differs from games')
        if line.startswith('Ptnml'):
            m = re.match(r'^Ptnml\(0-2\):\s*\[\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\]', line)
            if not m or current is None:
                issues.append(f'line {lineno}: unsupported or unbound Ptnml summary')
            else:
                current['pentabins'] = list(map(int, m.groups()))
        if 'LLR:' in line:
            token = line.split('LLR:', 1)[1].split()
            token = token[0] if token else ''
            try:
                value = float(token)
            except ValueError:
                value = None
            if value is None or not math.isfinite(value):
                issues.append(f'line {lineno}: invalid final-or-intermediate LLR token {token!r}')
                value = None
            entry = {'line': lineno, 'token': token, 'value': value, 'text': line}
            llr_lines.append(entry)
            if current is not None:
                current['llr'] = entry
        terminal = re.search(r'SPRT.*completed\s*-\s*(H[01]) was accepted', line)
        if terminal:
            acceptances.append({'line': lineno, 'hypothesis': terminal[1], 'text': line})
        game = re.match(r'^Finished game (\d+) \((.+) vs (.+)\): (1-0|0-1|1/2-1/2|\*)(?:\s|$)', line)
        if game:
            gid, white, black, result = game.groups()
            score = {'1-0': 2, '0-1': 0, '1/2-1/2': 1, '*': None}[result]
            if {white, black} != {candidate, baseline} or white == black:
                issues.append(f'line {lineno}: unexpected finished-game players')
                score = None
            elif black == candidate and score is not None:
                score = 2-score
            if gid in finished:
                duplicates.append(gid)
                issues.append(f'line {lineno}: duplicate finished game {gid}')
            else:
                finished[gid] = {'line': lineno, 'white': white, 'black': black, 'result': result, 'score': score}
        elif line.startswith('Finished game'):
            unparsed.append({'line': lineno, 'text': line})
            issues.append(f'line {lineno}: malformed Finished game record retained')
        pm = re.match(r'^Player:\s*(.+)$', line)
        if pm:
            player = pm[1]
            if player not in (candidate, baseline):
                issues.append(f'line {lineno}: unexpected fault-summary player')
            player_totals.setdefault(player, {})
        fm = re.match(r'^(Timeouts|Crashed):\s*(\d+)\s*$', line)
        if fm and player is not None:
            kind = {'Timeouts': 'time_loss', 'Crashed': 'crash'}[fm[1]]
            count = int(fm[2])
            if count < player_totals[player].get(kind, 0):
                issues.append(f'line {lineno}: decreasing fault total; possible restart')
            player_totals[player][kind] = count
        elif line.startswith(('Timeouts:', 'Crashed:')):
            unparsed.append({'line': lineno, 'text': line})
            issues.append(f'line {lineno}: malformed or unbound fault total retained')
        kind = None
        if re.search(r'(?:loses|wins) on time|forfeits? on time|time forfeit', line, re.I):
            kind = 'time_loss'
        elif re.search(r'\bcrash(?:ed)?\b|segmentation fault|exited (?:unexpectedly|with (?:status|code) [-+]?[1-9])', line, re.I) and not re.match(r'^Crashed:', line):
            kind = 'crash'
        elif re.search(r'\billegal move\b', line, re.I):
            kind = 'illegal'
        if kind:
            events.append({'line': lineno, 'kind': kind, 'text': line})
        if re.search(r'Tournament was interrupted', line, re.I):
            issues.append(f'line {lineno}: interrupted tournament')
    if len(acceptances) > 1:
        issues.append('duplicate or conflicting native acceptance messages')
    for s in snapshots:
        if s['pentabins'] is not None and s['games'] is not None:
            if 2*sum(s['pentabins']) != s['games']:
                issues.append(f"line {s['line']}: paired games differ from summary games")
            if penta_matches_wdl(s['pentabins'], s['wdl']) is False:
                issues.append(f"line {s['line']}: impossible W/D/L and pentanomial combination")
    for previous, later in zip(snapshots, snapshots[1:]):
        for field in ('games', 'wdl', 'pentabins'):
            a, b = previous[field], later[field]
            if a is not None and b is not None:
                decreasing = b < a if field == 'games' else any(y < x for x,y in zip(a,b))
                if decreasing:
                    issues.append(f"line {later['line']}: decreasing cumulative {field}; possible restart")
    reported = dict(snapshots[-1]) if snapshots else {'games': None, 'wdl': None, 'pentabins': None, 'llr': None}
    # The final LLR observation is authoritative as an observation, even if invalid;
    # never fall back to a finite value from a previous snapshot.
    reported['llr'] = llr_lines[-1] if llr_lines else None
    reported['acceptances'] = acceptances
    wdl = [0, 0, 0]
    for g in finished.values():
        if g['score'] is not None:
            wdl[2-g['score']] += 1
    if finished and reported['games'] is not None:
        if len(finished) != reported['games'] or wdl != reported['wdl']:
            issues.append('final summary differs from retained finished-game lines')
    if events or any(v for t in player_totals.values() for v in t.values()):
        issues.append('fault observations present; no strength acceptance')
    status = 'BLOCKED' if issues else ('PARSED' if snapshots or finished or llr_lines else 'UNVERIFIED')
    return {'schema': 'forge_sol_S06_fastchess_log_v1', 'status': status,
            'candidate': candidate, 'baseline': baseline, 'headers': headers,
            'reported': reported, 'snapshots': snapshots, 'llr_observations': llr_lines,
            'unparsed_records': unparsed, 'finished_match_terminals': terminal_matches,
            'finished': {'games': len(finished), 'wdl': wdl, 'unknown': sum(g['score'] is None for g in finished.values()),
                         'duplicates': duplicates, 'records': finished},
            'faults': {'events': events, 'reported_player_totals': player_totals,
                       'verified_unique_total': None, 'clean_proven': False},
            'issues': issues, 'acceptance_authorized': False,
            'scope': 'Text observations only; grammar, source/build, legality and frozen protocol not authenticated.'}
