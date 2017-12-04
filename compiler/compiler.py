import enum
import io
import sys
import argparse


class EmptyNode:
    def __init__(self):
        pass

    def __repr__(self):
        return "<empty>"


class LetNode:
    def __init__(self, storage, name, rvalue):
        self.storage = storage
        self.name = name
        self.rvalue = rvalue

    def __repr__(self):
        return f"let {self.storage} {self.name} = {self.rvalue}"


class UseNode:
    def __init__(self, unit_name):
        self.unit_name = unit_name

    def __repr__(self):
        return f"use {self.unit_name}"


class ParamListNode:
    def __init__(self, param_list):
        self.param_list = param_list

    def __repr__(self):
        return ", ".join(repr(p) for p in param_list)


class FunNode:
    def __init__(self, name, param_list, stmt_list):
        self.name = name
        self.param_list = param_list
        self.stmt_list = stmt_list

    def __repr__(self):
        r = []
        r.append(f"fun {self.name}({repr(self.param_list)})")
        for stmt in self.stmt_list:
            r.append(repr(stmt))
        r.append("endfun")
        return "\n".join(r)


class Token(enum.Enum):
    unknown = -2
    eof = -1
    whitespace = 0
    word = 1
    numeric = 2
    left_paren = 3
    right_paren = 4
    left_bracket = 5
    right_bracket = 6
    left_brace = 7
    right_brace = 8
    double_quote = 9
    single_quote = 10
    operator = 11
    keyword = 12


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


def readinput(stream):
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


def usage(stream):
    basename = os.path.basename(sys.argv[0])
    print(f"usage: {basename} [optiions] input_file", file=stream)
    print("  -h, --help\t\tPrint this help and exit.", file=stream)


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("input_file", help="the file to compile")
    args = arg_parser.parse_args()
    input_file = open(args.input_file, 'r')
    parser = Parser(readinput(input_file))
    for tok in parser.scanner:
        print(tok)
        if tok[0] == Token.eof:
            break
    # ast = parser.parse()
    # print(repr(ast))
    input_file.close()


if __name__ == "__main__":
    main()
