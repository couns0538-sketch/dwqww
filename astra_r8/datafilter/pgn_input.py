"""Original streaming PGN input checks around the installed parser API.

This recognizes input structure only. The installed chess library still parses
SAN, checks move legality and constructs games. No library parser is vendored.
"""
import re


HEADER = re.compile(r'\[[A-Za-z0-9_]+\s+"(?:[^"\\]|\\.)*"\]\s*')
MOVE_NUMBER = re.compile(r'\d+\.(?:\.\.)?')
NAG = re.compile(r'\$\d+')
SAN = re.compile(r'(?:[KQRBN][a-h]?[1-8]?x?[a-h][1-8]|'
                 r'[a-h](?:x[a-h])?[1-8](?:=?[QRBN])?|'
                 r'[a-h][1-8][a-h][1-8](?:=?[QRBN])?|'
                 r'[O0]-[O0](?:-[O0])?)[+#]?')
RESULTS = {'1-0', '0-1', '1/2-1/2', '*'}


class CheckedPGNInput:
    """Check each consumed line, preserving the caller's stream and bytes."""
    def __init__(self, stream):
        self.stream = stream
        self.line = 0
        self.headers = True
        self.comment = False
        self.variations = 0
        self.terminated = False

    def fail(self, reason):
        name = getattr(self.stream, 'name', '<PGN stream>')
        raise ValueError(f'{name}: PGN line {self.line}: {reason}')

    def readline(self, *args):
        line = self.stream.readline(*args)
        if line:
            self.line += 1
            self.check(line.lstrip('\ufeff') if self.line == 1 else line)
        return line

    def check(self, line):
        if not self.comment and (line.startswith(('%', ';')) or not line.strip()):
            return
        if self.headers and line.startswith('['):
            if not HEADER.fullmatch(line):
                self.fail('malformed header')
            return
        self.headers = False
        index = 0
        while index < len(line):
            if self.comment:
                end = line.find('}', index)
                if end < 0:
                    return
                self.comment = False
                index = end + 1
                continue
            char = line[index]
            if char.isspace():
                index += 1
                continue
            if char == ';':
                return
            if char == '{':
                self.comment = True
                index += 1
                continue
            if self.terminated:
                self.fail('movetext after game termination')
            if char == '(':
                self.variations += 1
                index += 1
                continue
            if char == ')':
                if self.variations == 0:
                    self.fail('unmatched closing variation')
                self.variations -= 1
                index += 1
                continue
            if char in '!?':
                index += 1
                continue
            if char == '$':
                match = NAG.match(line, index)
                if not match:
                    self.fail('malformed annotation')
                index = match.end()
                continue
            match = MOVE_NUMBER.match(line, index)
            if match:
                index = match.end()
                continue
            end = index
            while end < len(line) and not line[end].isspace() and line[end] not in '{}();!?$':
                end += 1
            token = line[index:end]
            if token in RESULTS:
                if self.variations:
                    self.fail('game termination inside variation')
                self.terminated = True
            elif not SAN.fullmatch(token):
                self.fail(f'unrecognized movetext token {token!r}')
            index = end

    def finish(self, has_game):
        if self.comment:
            self.fail('unterminated comment')
        if self.variations:
            self.fail('unterminated variation')
        if has_game and not self.terminated:
            self.fail('missing game termination marker')
