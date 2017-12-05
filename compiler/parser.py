from . import ast
from .token import Token
from .lexer import Redo


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
    def __init__(self, what, t, v, p, soft=False):
        message = f"expected {what}, got {t}={repr(v)}"
        super().__init__(message)
        self.what = what
        self.token = t
        self.value = v
        self.position = p
        self.soft = soft

    def __str__(self):
        msg = super().__str__()
        return f"{msg} (at {self.position})"


class Parser:
    def __init__(self, tokens):
        self.tokens = Redo(tokens)

    def parse(self):
        """Begin the parse operation on this token stream.
        """
        self.maybe(self.whitespace)
        while True:
            yield self.stmt_toplevel()
            if self.maybe(self.eof) is not None:
                break

    def match(self, what, cond, soft=False):
        """Consume something specific from the token stream based on a condition. If that condition
        is not met, this function does not consume anything and will (by default) raise ParseError.

        Keyword arguments:
        what -- A human-readable description of what is being consumed (for ParseError messages).
        cond -- The condition for consumption.
        soft -- Set this to True if a ParseError should not be thrown when the condition is unmet.
        """
        t, v, p = next(self.tokens)
        if cond(t, v):
            return v
        self.tokens.redo()
        raise ParseError(what, t, v, p, soft)

    def maybe(self, parse, *args, **kwargs):
        try:
            return parse(*args, soft=True, **kwargs)
        except ParseError as e:
            if not e.soft:
                raise
            return None

    def oneof(self, *parses, soft=False):
        last_e = None
        whats = []
        for parse in parses:
            what, fun, *args = parse
            whats.append(what)
            try:
                return fun(*args, soft=True)
            except ParseError as e:
                if not e.soft:
                    raise
                last_e = e
        raise ParseError(", ".join(whats), last_e.token, last_e.value, last_e.position, soft)

    def make_node(self, node, *args, **kwargs):
        return node(self.tokens.current[2], *args, **kwargs)

    def anything(self, soft=False):
        return self.match("!!! PARSER BUG !!!", lambda t, v: True, soft)

    def token(self, what, token, soft=False):
        return self.match(what, lambda t, v: t == token, soft)

    def whitespace(self, soft=False):
        """Consume a whitespace token from the token stream. If the next token is not whitespace,
        this function does not consume anything and will (by default) raise ParseError.

        Keyword arguments:
        soft -- Set this to True if a ParseError should not be thrown if the next token is not
                whitespace.
        """
        return self.token("whitespace", Token.whitespace, soft)

    def eof(self, soft=False):
        """Consume an end-of-file token from the token stream. If the next token is not an
        end-of-file, this function does not consume anything and will (by default) raise ParseError.

        Keyword arguments:
        soft -- Set this to True if a ParseError should not be thrown if the next token is not
                end-of-file.
        """
        return self.token("end-of-file", Token.eof, soft)

    def keyword(self, kws, soft=False):
        """Consume a specific keyword token from the token stream. If that keyword is not the next
        token, this function does not consume anything and will (by default) raise ParseError.

        Keyword arguments:
        kws -- The keyword string.
        soft -- Set this to True if a ParseError should not be thrown if the next token is not the
                specified keyword.
        """
        fkws = "' or '".join(kws)
        return self.match(
            f"keyword '{fkws}'",
            lambda t, v: t == Token.keyword and v in kws,
            soft)

    def identifier(self, soft=False):
        text = self.match(
            "identifier",
            lambda t, v: t == Token.word,
            soft)
        return self.make_node(ast.IdentifierNode, text)

    def operator(self, ops, soft=False):
        fops = "' or '".join(ops)
        return self.match(
            f"operator '{fops}'",
            lambda t, v: t == Token.operator and v in ops,
            soft)

    def numeric(self, soft=False):
        num = self.match(
            "numeric",
            lambda t, v: t == Token.numeric,
            soft)
        return self.make_node(ast.NumericNode, num)

    def expression(self, soft=False):
        # TODO handle expressions
        val = self.numeric(soft)
        self.maybe(self.whitespace)
        return val

    def comment_init(self, soft=False):
        vals = []
        self.token("/*", Token.operator, soft)
        while self.maybe(self.token, "*/", Token.operator) is None:
            vals.append(self.anything())
        self.whitespace()
        return self.make_node(ast.CommentNode, vals)

    def array_init(self, soft=False):
        vals = []
        self.token("[", Token.left_bracket, soft)
        self.maybe(self.whitespace)
        while self.maybe(self.token, "]", Token.right_bracket) is None:
            vals.append(self.expression())
            sep = self.oneof(
                ("separator", self.operator, [',']),
                ("end of list", self.token, "]", Token.right_bracket))
            self.maybe(self.whitespace)
            if sep == "]":
                break
        return self.make_node(ast.ArrayNode, vals)

    def string_init(self, soft=False):
        vals = []
        self.token("\"", Token.double_quote, soft)
        while self.maybe(self.token, "\"", Token.double_quote) is None:
            vals.append(self.anything())
            if vals[-1] == "\\":
                vals[-1] = self.anything()
        self.whitespace()
        return self.make_node(ast.StringNode, vals)

    def stmt_use(self, soft=False):
        self.keyword(["use"], soft)
        self.whitespace()
        unit = self.identifier()
        self.whitespace()
        return self.make_node(ast.UseNode, unit)

    def stmt_let(self, soft=False):
        self.keyword(["let"], soft)
        self.whitespace()
        storage = self.maybe(self.keyword, ["mut", "stash"])
        if storage:
            self.whitespace()
        name = self.identifier()
        self.whitespace()
        self.operator(['='])
        self.whitespace()
        rvalue = self.oneof(
            ("expression", self.expression),
            ("array initializer", self.array_init),
            ("string initializer", self.string_init))
        return self.make_node(ast.LetNode, storage, name, rvalue)

    def stmt_if(self, soft=False):
        self.keyword(["if"], soft)
        self.whitespace()
        condition = None
        while self.maybe(self.keyword, "then") is None:
            # TODO: parse the condition rather than just eating it
            self.anything()
        self.whitespace()
        stmt_list = []
        # TODO: support else and elif
        while True:
            ctrl = self.oneof(
                ("'else' statement", self.keyword, "else"),
                ("'elif' statement", self.keyword, "elif"),
                ("'end' statement", self.keyword, "end"),
                soft=True)
            if ctrl == "elif":
                while self.maybe(self.keyword, "then") is None:
                    # TODO: parse the condition rather than just eating it
                    self.anything()
                self.whitespace()
            elif ctrl == "end":
                break
            # TODO: parse the body rather than just eating it
            self.anything()
        self.whitespace()
        return self.make_node(ast.IfNode, condition, stmt_list)

    def stmt_while(self, soft=False):
        self.keyword(["while"], soft)
        self.whitespace()
        condition = None
        while self.maybe(self.keyword, "do") is None:
            # TODO: parse the condition rather than just eating it
            self.anything()
        self.whitespace()
        stmt_list = []
        while self.maybe(self.keyword, "end") is None:
            stmt_list.append(self.stmt())
        self.whitespace()
        return self.make_node(ast.WhileNode, condition, stmt_list)

    def stmt_isr(self, soft=False):
        self.keyword(["isr"], soft)
        self.whitespace()
        name = self.identifier()
        self.whitespace()
        stmt_list = []
        while self.maybe(self.keyword, "endisr") is None:
            stmt_list.append(self.stmt())
        self.whitespace()
        return self.make_node(ast.IsrNode, name, stmt_list)

    def stmt(self):
        return self.oneof(
            ("comment", self.comment_init),
            ("'let' statement", self.stmt_let),
            ("'if' statement", self.stmt_if),
            ("'while' statement", self.stmt_while),
            soft=True)

    def stmt_toplevel(self):
        return self.oneof(
            ("comment", self.comment_init),
            ("'use' statement", self.stmt_use),
            ("'let' statement", self.stmt_let),
            ("'isr' statement", self.stmt_isr),
            soft=True)


def parse(tokens):
    """Parse a token stream into an Abstract Syntax Tree.

    Keyword arguments:
    tokens -- A generator of tokens annotated with file position information.
              Such a generator can be acquired from `Lexer.lex()`.
    """
    return Parser(tokens).parse()
