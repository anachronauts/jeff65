from .token import Token


operators = [
    '->', '<-', '=', '+=', '-=',
    '+', '-', '*', '/', '|', '&', '^', '>>', '<<',
    '!=', '==', '<=', '>=', '<', '>',
    '/*', '*/', ','
]

specials = "()[]{},\"\\"

keywords = [
    'byte', 'do', 'dword', 'else', 'end', 'endfun', 'endisr', 'for', 'if',
    'in', 'isr', 'let', 'mut', 'qword', 'return', 'stash', 'then', 'to',
    'use', 'while', 'word'
]


class Redo:
    def __init__(self, source):
        self.source = source
        self.current = None
        self.last = None

    def __iter__(self):
        return self

    def __next__(self):
        if self.last is None:
            self.current = next(self.source)
        else:
            self.current = self.last
            self.last = None
        return self.current

    def redo(self):
        self.last = self.current

    def peek(self):
        if self.last is None:
            next(self)
            self.redo()
        return self.last


def annotate_chars(stream):
    line = 1
    column = 0
    while True:
        c = stream.read(1)
        if len(c) == 0:
            break
        yield (c, (line, column))
        if c == '\n':
            line += 1
            column = 0
        else:
            column += 1


def is_operator_prefix(prefix):
    return any(op for op in operators if op.startswith(prefix))


def scan(source, c, cond):
    run = [c]
    while True:
        try:
            c, _ = next(source)
        except StopIteration:
            break
        run.append(c)
        if not cond(c, "".join(run)):
            source.redo()
            run.pop()
            break
    return "".join(run)


def lex(stream):
    source = Redo(annotate_chars(stream))
    while True:
        try:
            c, position = next(source)
        except StopIteration:
            break
        if is_operator_prefix(c):
            op = scan(source, c, lambda _, v: is_operator_prefix(v))
            # did we actually form an operator or just a prefix?
            if op in operators:
                yield (Token.operator, op, position)
            else:
                yield (Token.unknown, op, position)
        elif c == "'":
            yield (Token.single_quote, c, position)
        elif c == '"':
            yield (Token.double_quote, c, position)
        elif c == '\\':
            yield (Token.backslash, c, position)
        elif c == '(':
            yield (Token.left_paren, c, position)
        elif c == ')':
            yield (Token.right_paren, c, position)
        elif c == '[':
            yield (Token.left_bracket, c, position)
        elif c == ']':
            yield (Token.right_bracket, c, position)
        elif c == '{':
            yield (Token.left_brace, c, position)
        elif c == '}':
            yield (Token.right_brace, c, position)
        elif c.isspace():
            ws = scan(source, c, lambda v, _: v.isspace())
            yield (Token.whitespace, ws, position)
        elif c.isdigit():
            num = scan(source, c,
                       lambda v, _: not v.isspace() and v not in specials)
            yield (Token.numeric, num, position)
        elif c.isalpha():
            word = scan(source, c,
                        lambda v, _: not v.isspace() and v not in specials)
            if word in keywords:
                yield (Token.keyword, word, position)
            else:
                yield (Token.word, word, position)
        else:
            yield (Token.unknown, c, position)
    while True:
        # fuse the scanner
        yield (Token.eof, "<EOF>", None)
