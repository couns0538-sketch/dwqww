#!/usr/bin/env python3
"""Deterministic, score-bounded Forge self-play openings.

R8 v5 --openings consumes ONLY UCI moves from standard startpos. The optional
Chess960-style mode exports FENs with NO castling rights; it is neither true
Chess960 nor compatible with unchanged R8. Existing outputs are never replaced.
IDEA_SOURCE: user Astra A1 data request; same-repository R8 commit
5dd3a57d6f286f09b8881671ba8a368f6d34f717 and Forge Board/probe interfaces.
"""
from __future__ import annotations
import argparse
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path
import random
import re
import sys

STANDARD_FEN = 'rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1'
R8_SOURCE = '5dd3a57d6f286f09b8881671ba8a368f6d34f717'

@dataclass(frozen=True)
class Config:
    out: Path
    count: int = 100
    seed: int = 1
    nodes: int = 5000
    hash_mb: int = 1
    min_plies: int = 6
    max_plies: int = 16
    max_abs_cp: int = 150
    min_abs_cp: int = 0
    max_attempts: int | None = None
    final_only: bool = False
    format: str = 'r8'
    chess960_style: bool = False

    def validate(self):
        if not 1 <= self.count <= 100000: raise ValueError('count must be 1..100000')
        if not 0 <= self.seed < 2**64: raise ValueError('seed must be an unsigned 64-bit integer')
        if not 1 <= self.nodes <= 2**63-1 or not 1 <= self.hash_mb <= 1024: raise ValueError('invalid node/hash budget')
        if not 0 <= self.min_plies <= self.max_plies <= 64: raise ValueError('plies must satisfy 0 <= min <= max <= 64')
        if self.format not in ('r8', 'fen'): raise ValueError('format must be r8 or fen')
        if self.chess960_style and self.format == 'r8':
            raise ValueError('Chess960-style FENs are not supported by unchanged R8; use --format fen (no castling)')
        if self.format == 'r8' and self.min_plies == 0: raise ValueError('R8 books may not contain blank zero-ply lines')
        if not 0 <= self.min_abs_cp <= self.max_abs_cp <= 10000: raise ValueError('invalid cp band')
        if self.max_attempts is not None and not self.count <= self.max_attempts <= 10000000:
            raise ValueError('max-attempts must be between count and 10000000')

    @property
    def attempt_limit(self): return self.max_attempts if self.max_attempts is not None else self.count * 100


def json_line(value): return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n'

def write_new_json(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream: stream.write(json_line(value))

def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()

def settings(config):
    data = asdict(config); data.pop('out')
    data['max_attempts'] = config.attempt_limit
    data.update(r8_source_commit=R8_SOURCE, score_perspective='side to move; White conversion also recorded',
                uniqueness='piece placement plus side to move; ignore clocks, castling and EP for diversity',
                score_every_selected_position=not config.final_only,
                chess960_castling='DISABLED; not true Chess960' if config.chess960_style else 'orthodox')
    return data

def prepare_output(config):
    config.validate()
    Path(config.out).mkdir(parents=True, exist_ok=False)
    write_new_json(Path(config.out)/'settings.json', settings(config))

def chess960_style_fen(rng):
    """Original combinatorial arrangement: bishops opposite colours; king between rooks."""
    row = [''] * 8
    row[rng.choice((0, 2, 4, 6))] = 'B'
    row[rng.choice((1, 3, 5, 7))] = 'B'
    empty = [i for i, piece in enumerate(row) if not piece]
    row[rng.choice(empty)] = 'Q'
    empty = [i for i, piece in enumerate(row) if not piece]
    for i in rng.sample(empty, 2): row[i] = 'N'
    for i, piece in zip([i for i, piece in enumerate(row) if not piece], 'RKR'): row[i] = piece
    back = ''.join(row)
    return back.lower() + '/pppppppp/8/8/8/8/PPPPPPPP/' + back + ' w - - 0 1'

def check_fen_frame(fen):
    if not isinstance(fen, str) or len(fen.split()) != 6 or any(c in fen for c in '\r\n\t'):
        raise ValueError('probe supplied invalid FEN framing')
    if fen.split()[1] not in ('w', 'b'): raise ValueError('invalid side to move')
    return fen

def inspect(probe, fen):
    value = probe.query(fen, op='inspect')
    if value.get('operation') != 'inspect': raise ValueError('unexpected inspection response operation')
    if type(value.get('terminal')) is not bool or type(value.get('in_check')) is not bool:
        raise ValueError('inspection requires boolean terminal/in_check')
    moves = value.get('moves')
    if not isinstance(moves, list): raise ValueError('inspection requires legal move list')
    seen = set()
    for move in moves:
        if not isinstance(move, dict) or not re.fullmatch(r'[a-h][1-8][a-h][1-8][qrbn]?', move.get('uci', '')):
            raise ValueError('invalid legal move token')
        if move['uci'] in seen: raise ValueError('duplicate legal move token')
        seen.add(move['uci']); check_fen_frame(move.get('fen'))
    if not moves and not value['terminal']: raise ValueError('nonterminal position has no legal moves')
    return value

def analyze(probe, fen, ply):
    value = probe.query(fen, op='analyze')
    if value.get('operation') != 'analyze': raise ValueError('unexpected analysis response operation')
    for field in ('score', 'depth', 'nodes'):
        if type(value.get(field)) is not int: raise ValueError('analysis requires integer ' + field)
    if value['depth'] < 0 or value['nodes'] < 0: raise ValueError('negative search accounting')
    kind = value.get('score_type', 'cp')
    if kind != 'cp' or value.get('lowerbound', False) or value.get('upperbound', False):
        raise ValueError('exact cp analysis required, not mate/bound')
    cp = value['score']
    return {'ply': ply, 'fen': fen, 'score_stm_cp': cp,
            'score_white_cp': cp if fen.split()[1] == 'w' else -cp,
            'depth': value['depth'], 'reported_nodes': value['nodes']}

def generate(config, probe, *, prepared=False):
    """Write candidate outputs using an injected probe; caller seals after clean probe shutdown.

    Direct callers get a new directory by default. CLI reserves its directory
    first so original native IPC can live inside it, then uses prepared=True.
    """
    config.validate(); out = Path(config.out)
    if not prepared: prepare_output(config)
    elif not (out/'settings.json').is_file(): raise ValueError('prepared output reservation is missing')
    elif json.loads((out/'settings.json').read_text()) != settings(config): raise ValueError('prepared settings differ from requested configuration')
    rng = random.Random(config.seed)
    filename = 'openings.moves' if config.format == 'r8' else 'openings.fen'
    counters = dict(attempts=0, accepted=0, rejected_terminal=0, rejected_check=0,
                    rejected_band=0, rejected_minimum=0, rejected_duplicate=0,
                    inspect_queries=0, analysis_queries=0)
    seen = set(); white_scores = []; max_selected_abs = 0
    with (out/filename).open('x', encoding='ascii', newline='\n') as book, \
         (out/'metadata.jsonl').open('x', encoding='utf-8', newline='\n') as metadata:
        for attempt in range(1, config.attempt_limit + 1):
            counters['attempts'] = attempt
            start = chess960_style_fen(rng) if config.chess960_style else STANDARD_FEN
            fen = start; moves = []; checks = []; rejected = False
            length = rng.randint(config.min_plies, config.max_plies)
            state = inspect(probe, fen); counters['inspect_queries'] += 1
            if state['terminal']:
                counters['rejected_terminal'] += 1; continue
            if not config.final_only:
                item = analyze(probe, fen, 0); counters['analysis_queries'] += 1; checks.append(item)
                if abs(item['score_stm_cp']) > config.max_abs_cp:
                    counters['rejected_band'] += 1; continue
            for ply in range(1, length + 1):
                choice = rng.choice(sorted(state['moves'], key=lambda x: x['uci']))
                fen = choice['fen']; moves.append(choice['uci'])
                state = inspect(probe, fen); counters['inspect_queries'] += 1
                if state['terminal']:
                    counters['rejected_terminal'] += 1; rejected = True; break
                if not config.final_only:
                    item = analyze(probe, fen, ply); counters['analysis_queries'] += 1; checks.append(item)
                    if abs(item['score_stm_cp']) > config.max_abs_cp:
                        counters['rejected_band'] += 1; rejected = True; break
            if rejected: continue
            if state['in_check']: counters['rejected_check'] += 1; continue
            if config.final_only:
                item = analyze(probe, fen, length); counters['analysis_queries'] += 1; checks.append(item)
            final = checks[-1]; cp = final['score_stm_cp']
            if abs(cp) > config.max_abs_cp: counters['rejected_band'] += 1; continue
            if abs(cp) < config.min_abs_cp: counters['rejected_minimum'] += 1; continue
            key = ' '.join(fen.split()[:2])
            if key in seen: counters['rejected_duplicate'] += 1; continue
            seen.add(key); counters['accepted'] += 1
            white_scores.append(final['score_white_cp'])
            max_selected_abs = max(max_selected_abs, *(abs(x['score_stm_cp']) for x in checks))
            record = dict(index=counters['accepted'], attempt=attempt, start_fen=start, fen=fen,
                          moves=moves, plies=length, checks=checks,
                          probe_binary_sha256=getattr(probe, 'binary_sha256', None), **{k: final[k] for k in ('score_stm_cp', 'score_white_cp', 'depth', 'reported_nodes')})
            book.write((' '.join(moves) if config.format == 'r8' else fen) + '\n')
            metadata.write(json_line(record)); book.flush(); metadata.flush()
            if counters['accepted'] == config.count: break
    complete = counters['accepted'] == config.count
    report = dict(status='GENERATED_NOT_SEALED' if complete else 'INCOMPLETE_ATTEMPT_LIMIT', **counters,
                  requested=config.count, output_format=config.format,
                  r8_compatible=config.format == 'r8' and not config.chess960_style,
                  chess960_style_no_castling=config.chess960_style,
                  score_checks='every selected position including initial' if not config.final_only else 'final position only',
                  max_abs_selected_cp=max_selected_abs if white_scores else None,
                  white_advantage=sum(x > 0 for x in white_scores), black_advantage=sum(x < 0 for x in white_scores),
                  equal_score=sum(x == 0 for x in white_scores),
                  min_white_cp=min(white_scores) if white_scores else None,
                  max_white_cp=max(white_scores) if white_scores else None,
                  mean_abs_cp=sum(abs(x) for x in white_scores)/len(white_scores) if white_scores else None,
                  strength_claim='NONE')
    write_new_json(out/'generation.json', report)
    return report

def seal(config, report):
    if report['status'] != 'GENERATED_NOT_SEALED' or report['accepted'] != config.count:
        raise ValueError('cannot seal incomplete generation')
    out = Path(config.out)
    files = {str(p.relative_to(out)): digest(p) for p in sorted(out.rglob('*')) if p.is_file()}
    write_new_json(out/'MANIFEST.sha256.json', files)
    write_new_json(out/'SUCCESS.json', {'status':'PASS', 'count':report['accepted'], 'manifest_sha256':digest(out/'MANIFEST.sha256.json'),
                                     'native_legal_replay':'NOT_RUN_BY_THIS_SEAL', 'strength_claim':'NONE'})

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--probe', required=True, type=Path); parser.add_argument('--out', required=True, type=Path)
    for name, default in [('count',100),('seed',1),('nodes',5000),('hash-mb',1),('min-plies',6),('max-plies',16),('max-abs-cp',150),('min-abs-cp',0)]:
        parser.add_argument('--'+name, type=int, default=default)
    parser.add_argument('--max-attempts', type=int); parser.add_argument('--final-only', action='store_true')
    parser.add_argument('--format', choices=['r8','fen'], default='r8'); parser.add_argument('--chess960-style', action='store_true')
    args = parser.parse_args(argv); fields = vars(args).copy(); exe = fields.pop('probe'); config = Config(**fields)
    prepared = False
    try:
        config.validate()
        from forge_probe import ProbeClient
        prepare_output(config); prepared = True
        with ProbeClient(exe, config.nodes, config.hash_mb, workdir=config.out/'probe') as probe:
            report = generate(config, probe, prepared=True)
        if report['status'] != 'GENERATED_NOT_SEALED':
            print(json.dumps(report, sort_keys=True)); return 2
        seal(config, report); print(json.dumps(report, sort_keys=True)); return 0
    except Exception as error:
        if prepared: write_new_json(config.out/'FAILED.json', {'status':'FAIL','error_type':type(error).__name__,'error':str(error)})
        print(str(error), file=sys.stderr); return 2

if __name__ == '__main__': raise SystemExit(main())
