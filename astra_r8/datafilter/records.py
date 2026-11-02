"""Original full-state normalization. No filtering, clipping or deduplication."""
import json
import math
import re
import chess
import chess.pgn
from pgn_input import CheckedPGNInput

EV = re.compile(r'^\s*([+-]?)(M?)(\d+(?:\.\d+)?)/(\d+)')

class ResultGameBuilder(chess.pgn.GameBuilder):
    """Reject conflicting result tokens instead of silently preferring headers."""
    def begin_game(self):
        self.original_headers = {}
        return super().begin_game()

    def visit_header(self, tagname, tagvalue):
        if tagname in ('Result', 'Variant', 'FEN', 'SetUp'):
            previous = self.original_headers.get(tagname)
            if previous is not None and previous != tagvalue:
                raise ValueError(f'conflicting PGN header: {tagname}')
            self.original_headers[tagname] = tagvalue
        if tagname == 'Result' and tagvalue not in ('1-0', '0-1', '1/2-1/2', '*'):
            raise ValueError('invalid PGN result: ' + tagvalue)
        return super().visit_header(tagname, tagvalue)

    def end_headers(self):
        board = self.game.headers.board()
        if type(board) is not chess.Board or board.chess960:
            raise ValueError('PGN must describe standard chess')
        return super().end_headers()

    def visit_result(self, result):
        header = self.game.headers.get('Result', '*')
        if header != '*' and result != header:
            raise ValueError(f'conflicting PGN result: header {header}, movetext {result}')
        return super().visit_result(result)


def read_pgn_game(fh):
    checked = CheckedPGNInput(fh)
    game = chess.pgn.read_game(checked, Visitor=ResultGameBuilder)
    checked.finish(game is not None)
    if game is not None and game.errors:
        raise ValueError('malformed PGN')
    return game


def record(fen, score, score_type, result_white, source, source_row,
           source_kind, best_move=None, raw_score=None, depth=None):
    if len(fen.split()) != 6 or int(fen.split()[5]) < 1:
        raise ValueError('original full FEN required')
    board = chess.Board(fen)
    if not board.is_valid():
        raise ValueError('invalid board')
    if source_kind not in ('selfplay', 'pgn', 'lichess'):
        raise ValueError('unsupported source kind')
    if not isinstance(source, str) or not source or isinstance(source_row, bool) or not isinstance(source_row, (str, int)) or not str(source_row):
        raise ValueError('invalid source provenance')
    if type(source_row) is int and source_row < 1:
        raise ValueError('source row must be positive')
    if score_type not in ('cp', 'mate') or type(score) is not int:
        raise ValueError('invalid score/type')
    if result_white is not None and (type(result_white) is not int or result_white not in (-1, 0, 1)):
        raise ValueError('invalid result')
    if best_move is not None and chess.Move.from_uci(best_move) not in board.legal_moves:
        raise ValueError('illegal stored best move')
    return dict(fen=fen, score_stm=score, score_type=score_type,
                raw_score=score if raw_score is None else raw_score,
                result_white=result_white, result_stm=None if result_white is None else result_white * (1 if board.turn else -1),
                has_result=result_white is not None, source=source, source_row=source_row,
                source_kind=source_kind, best_move=best_move, depth=depth,
                ply=2*(board.fullmove_number-1)+(not board.turn))

def selfplay_record(line, source, row):
    fields = [x.strip() for x in line.split('|')]
    if len(fields) != 3:
        raise ValueError('expected FEN | STM score | White result')
    fen, score, result = fields
    outcomes = {'0': -1, '0.0': -1, '0.5': 0, '1': 1, '1.0': 1, '?': None, '*': None, '': None}
    if result not in outcomes:
        raise ValueError('invalid result: ' + result)
    return record(fen, int(score), 'cp', outcomes[result], source, row, 'selfplay', raw_score=score)

def lichess_record(obj, source, row):
    pv = obj['evals'][0]['pvs'][0]
    kind = 'mate' if 'mate' in pv else 'cp'
    white_score = pv[kind]
    if type(white_score) is not int:
        raise ValueError('invalid Lichess score type')
    board = chess.Board(obj['fen'])
    move = pv.get('line', '').split()
    return record(obj['fen'], white_score * (1 if board.turn else -1), kind, None,
                  source, row, 'lichess', move[0] if move else None, white_score,
                  obj['evals'][0].get('depth'))

def validate_record(r):
    if type(r['has_result']) is not bool or type(r['ply']) is not int:
        raise ValueError('invalid derived metadata type')
    if r['result_stm'] is not None and type(r['result_stm']) is not int:
        raise ValueError('invalid result_stm type')
    rebuilt = record(r['fen'], r['score_stm'], r['score_type'], r['result_white'],
                     r['source'], r['source_row'], r['source_kind'], r['best_move'],
                     r['raw_score'], r.get('depth'))
    for key in ('has_result', 'result_stm', 'ply'):
        if r[key] != rebuilt[key]:
            raise ValueError('inconsistent ' + key)
    return r

def read_records(path, kind='normalized'):
    with open(path, encoding='utf-8-sig') as fh:
        if kind == 'pgn':
            game_index = 0
            while (game := read_pgn_game(fh)) is not None:
                game_index += 1
                if game.errors:
                    raise ValueError(f'{path}: game {game_index}: malformed PGN')
                token = game.headers.get('Result', '*')
                outcomes = {'1-0': 1, '0-1': -1, '1/2-1/2': 0, '*': None}
                if token not in outcomes:
                    raise ValueError(f'{path}: game {game_index}: invalid result {token}')
                result = outcomes[token]
                board = game.board()
                for ply, node in enumerate(game.mainline()):
                    m = EV.match(node.comment or '')
                    if m:
                        score = round(float(m[3]) * (1 if m[2] else 100)) * (-1 if m[1] == '-' else 1)
                        yield record(board.fen(en_passant='fen'), score, 'mate' if m[2] else 'cp', result,
                                     str(path), f'{game_index}:{ply}', 'pgn', node.move.uci(), node.comment, int(m[4]))
                    board.push(node.move)
            return
        for row, line in enumerate(fh, 1):
            if not line.strip() or line.lstrip().startswith('#'):
                continue
            try:
                if kind == 'selfplay':
                    yield selfplay_record(line, str(path), row)
                elif kind == 'lichess':
                    yield lichess_record(json.loads(line), str(path), row)
                else:
                    yield validate_record(json.loads(line))
            except (ValueError, KeyError, TypeError, IndexError) as exc:
                raise ValueError(f'{path}:{row}: {exc}') from exc

def dumps(r):
    return json.dumps(r, sort_keys=True, separators=(',', ':'), allow_nan=False)
