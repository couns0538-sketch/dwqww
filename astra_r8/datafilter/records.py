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
        if self.original_headers.get('SetUp') == '1' and 'FEN' not in self.original_headers:
            raise ValueError('original PGN FEN required when SetUp is 1')
        if 'FEN' in self.original_headers:
            board_from_fen(self.original_headers['FEN'])
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


def board_from_fen(fen):
    """Accept full standard FEN text understood by the locked Forge UCI parser."""
    if (not isinstance(fen, str) or not fen.isascii()
            or any(ord(char) < 32 and char != '\t' for char in fen)):
        raise ValueError('original single-line ASCII full FEN required')
    fields = fen.split()
    if (len(fields) != 6
            or not re.fullmatch(r'[pnbrqkPNBRQK1-8/]+', fields[0])
            or fields[2] != '-' and not re.fullmatch(r'[KQkq]+', fields[2])
            or len(set(fields[2])) != len(fields[2])
            or any(not re.fullmatch(r'\+?[0-9]+', value) for value in fields[4:])
            or not 0 <= int(fields[4]) <= 2**63 - 1
            or not 1 <= int(fields[5]) <= 2**63 - 1):
        raise ValueError('original standard full FEN with signed-64-bit clocks required')
    board = chess.Board(fen)
    if not board.is_valid():
        raise ValueError('invalid board')
    # Every extra non-pawn needs a promotion, which consumes an absent pawn.
    # Python's basic status checks do not enforce this necessary inventory bound.
    for color in chess.COLORS:
        missing_pawns = 8 - len(board.pieces(chess.PAWN, color))
        promoted = sum(max(0, len(board.pieces(piece, color)) - original)
                       for piece, original in ((chess.QUEEN, 1), (chess.ROOK, 2),
                                               (chess.BISHOP, 2), (chess.KNIGHT, 2)))
        if promoted > missing_pawns:
            raise ValueError('impossible promoted material inventory')
    return board


def record(fen, score, score_type, result_white, source, source_row,
           source_kind, best_move=None, raw_score=None, depth=None):
    board = board_from_fen(fen)
    if source_kind not in ('selfplay', 'pgn', 'lichess'):
        raise ValueError('unsupported source kind')
    if not isinstance(source, str) or not source.strip() or isinstance(source_row, bool) or not isinstance(source_row, (str, int)):
        raise ValueError('invalid source provenance')
    if type(source_row) is int and source_row < 1:
        raise ValueError('source row must be positive')
    if isinstance(source_row, str) and (not re.fullmatch(r'[0-9]+(?::[0-9]+)?', source_row) or int(source_row.split(':')[0]) < 1):
        raise ValueError('source row must identify a positive line or game:ply')
    if score_type not in ('cp', 'mate') or type(score) is not int:
        raise ValueError('invalid score/type')
    if result_white is not None and (type(result_white) is not int or result_white not in (-1, 0, 1)):
        raise ValueError('invalid result')
    if source_kind == 'lichess' and result_white is not None:
        raise ValueError('Lichess eval positions have no game result')
    if depth is not None and (type(depth) is not int or depth < 0):
        raise ValueError('invalid search depth')
    if raw_score is not None and (type(raw_score) not in (int, str) or isinstance(raw_score, str) and not raw_score.strip()):
        raise ValueError('invalid raw score metadata')
    if best_move is not None and not isinstance(best_move, str):
        raise ValueError('invalid stored best move')
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

def _lichess_move(board, raw_move):
    if raw_move is None:
        return None
    if not isinstance(raw_move, str):
        raise ValueError('invalid Lichess best move')
    move = board.parse_uci(raw_move)
    if not move:
        raise ValueError('null Lichess best move is not a legal stored move')
    return move.uci()


def lichess_record(obj, source, row):
    if not isinstance(obj, dict) or not isinstance(obj.get('fen'), str):
        raise ValueError('Lichess object with original FEN required')
    fen = obj['fen']
    if len(fen.split()) == 4:
        raise ValueError('Lichess FEN is missing move counters; genuinely known full state required')
    board = board_from_fen(fen)
    evaluations = obj.get('evals')
    if not isinstance(evaluations, list) or not evaluations:
        raise ValueError('nonempty Lichess evaluation list required')
    selected, deepest = 0, -2
    for index, evaluation in enumerate(evaluations):
        if not isinstance(evaluation, dict):
            raise ValueError('invalid Lichess evaluation')
        depth = evaluation.get('depth')
        if depth is not None and (type(depth) is not int or depth < 0):
            raise ValueError('invalid Lichess depth')
        if not isinstance(evaluation.get('pvs'), list) or not evaluation['pvs']:
            raise ValueError('nonempty Lichess PV list required')
        rank = -1 if depth is None else depth
        if rank > deepest:
            selected, deepest = index, rank
    evaluation = evaluations[selected]
    pv = evaluation['pvs'][0]
    if not isinstance(pv, dict):
        raise ValueError('invalid selected Lichess PV')
    kinds = [kind for kind in ('cp', 'mate') if kind in pv]
    if len(kinds) != 1 or type(pv[kinds[0]]) is not int:
        raise ValueError('exactly one integer Lichess cp or mate score required')
    kind = kinds[0]
    white_score = pv[kind]
    line = pv.get('line', '')
    if not isinstance(line, str):
        raise ValueError('invalid Lichess PV move text')
    moves = line.split()
    raw_move = moves[0] if moves else None
    result = record(fen, white_score * (1 if board.turn else -1), kind, None,
                    source, row, 'lichess', _lichess_move(board, raw_move),
                    white_score, evaluation.get('depth'))
    result.update(lichess_eval_index=selected, lichess_raw_best_move=raw_move,
                  lichess_move_format='uci_chess960')
    return result

def validate_record(r):
    if not isinstance(r, dict):
        raise ValueError('normalized record must be a JSON object')
    if r['raw_score'] is None:
        raise ValueError('raw score metadata is required')
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
    provenance = ('lichess_eval_index', 'lichess_raw_best_move', 'lichess_move_format')
    if any(key in r for key in provenance):
        if not all(key in r for key in provenance) or r['source_kind'] != 'lichess':
            raise ValueError('incomplete or misplaced Lichess provenance')
        if (type(r['lichess_eval_index']) is not int or r['lichess_eval_index'] < 0
                or r['lichess_move_format'] != 'uci_chess960'):
            raise ValueError('invalid Lichess selection/notation provenance')
        if _lichess_move(chess.Board(r['fen']), r['lichess_raw_best_move']) != r['best_move']:
            raise ValueError('Lichess raw and normalized best moves differ')
    return r

def read_records(path, kind='normalized'):
    if kind not in ('normalized', 'selfplay', 'lichess', 'pgn'):
        raise ValueError('unsupported input kind')
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
