from . import ast


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
        if c == "+":
            yield ast.OperatorAddNode(position)
        elif c == "-":
            yield ast.OperatorSubtractNode(position)
        elif c == "*":
            yield ast.OperatorMultiplyNode(position)
        elif c == "/":
            yield ast.OperatorDivideNode(position)
        elif c.isspace():
            ws = scan(source, c, lambda v, _: v.isspace())
            yield ast.WhitespaceNode(position, ws)
        elif c.isdigit():
            num = scan(source, c,
                       lambda v, _: not v.isspace() and v not in specials)
            yield ast.NumericNode(position, num)
    yield ast.EofNode()
