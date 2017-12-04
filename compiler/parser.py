from .token import Token


def production(node, n):
    def decorate(f):
        def fun(*args, **kwargs):
            ns = tuple(f(*args, **kwargs))
            if len(ns) == 0:
                raise StopIteration
            if len(ns) < n:
                return ns[-1]
            return node(*ns)
        return fun
    return decorate


class ParseError(Exception):
    def __init__(self, message, pos):
        super().__init__(message)
        self.position = pos

    def __str__(self):
        msg = super().__str__()
        return f"{msg} (at {self.position})"


class Parser:
    operators = [
        '->', '<-', '=', '+=', '-=',
        '+', '-', '*', '/', '|', '&', '^', '>>', '<<',
        '!=', '==', '<=', '>=', '<', '>',
        '/*', '*/' ]
    keywords = [
        'byte', 'do', 'dword', 'else', 'end', 'endfun', 'endisr', 'for', 'if',
        'in', 'isr', 'let', 'mut', 'qword', 'return', 'stash', 'then', 'to',
        'use', 'while', 'word' ]

    def __init__(self, source):
        self.source = Redo(source)
        self.scanner = Redo(self.scan())

    def startsoperator(self, v):
        return any(op for op in Parser.operators if op.startswith(v))

    def scanrun(self, c, cond):
        run = [c]
        while True:
            try:
                c, _ = next(self.source)
            except StopIteration:
                break
            run.append(c)
            if not cond(c, "".join(run)):
                self.source.redo()
                run.pop()
                break
        return "".join(run)

    def scan(self):
        while True:
            try:
                c, position = next(self.source)
            except StopIteration:
                break
            if self.startsoperator(c):
                op = self.scanrun(c, lambda _, v: self.startsoperator(v))
                # did we actually form an operator or just a prefix?
                if op in Parser.operators:
                    yield (Token.operator, op, position)
                else:
                    yield (Token.unknown, op, position)
            elif c == "'":
                yield (Token.single_quote, c, position)
            elif c == '"':
                yield (Token.double_quote, c, position)
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
                ws = self.scanrun(c, lambda v, _: v.isspace())
                yield (Token.whitespace, ws, position)
            elif c.isdigit():
                num = self.scanrun(c, lambda v, _: not v.isspace() and v not in "()[]{}")
                yield (Token.numeric, num, position)
            elif c.isalpha():
                word = self.scanrun(c, lambda v, _: not v.isspace() and v not in "()[]{}")
                if word in Parser.keywords:
                    yield (Token.keyword, word, position)
                else:
                    yield (Token.word, word, position)
            else:
                yield (Token.unknown, c, position)
        while True:
            # fuse the scanner
            yield (Token.eof, None, None)

    def matchtok(self, *toks):
        return self.matchcond(lambda t, *_: t in toks)

    def unmatchtok(self, *toks):
        return self.matchcond(lambda t, *_: t not in toks)

    def match(self, tok, val):
        return self.matchcond(lambda t, v, _: t is tok and v == val)

    def matchcond(self, cond):
        if cond(*next(self.scanner)):
            return True
        self.scanner.redo()
        return False

    def parse(self):
        while True:
            yield self.statement()
            if self.matchtok(Token.eof):
                break

    def anyof(self, *productions):
        for p in productions:
            try:
                return p()
            except StopIteration:
                pass
        raise StopIteration

    def maybe(self, p):
        try:
            return p()
        except StopIteration:
            return None


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