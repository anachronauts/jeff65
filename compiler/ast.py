# see http://effbot.org/zone/simple-top-down-parsing.htm
#
# - "nud" means "null denotation", which defines its behavior at the beginning
#   of a language construct.
# - "led" means "left denotation", which defines its behavior inside a language
#   construct.
# - "lbp" means "left binding power", which controls precedence.


class MemIter:
    def __init__(self, source):
        self.source = iter(source)
        self.current = None

    def next(self):
        self.current = next(self.source)


def parse_all(stream):
    s = MemIter(stream)
    s.next()
    return parse(s, 0)


def parse(stream, rbp):
    t = stream.current
    stream.next()
    left = t.nud(stream)
    print(f"left0={left}")
    while rbp < stream.current.lbp:
        t = stream.current
        stream.next()
        left = t.led(left, stream)
        print(f"left={left}")
    print(f"parse={left}")
    return left


class EofNode:
    lbp = 0

    def __init__(self, text, position):
        self.text = text
        self.position = position

    def __repr__(self):
        return f"<EOF>"


class NumericNode:
    def __init__(self, text, position):
        self.text = text
        self.position = position

    def nud(self, right):
        return self

    def __repr__(self):
        return self.text


class OperatorAddNode:
    lbp = 10

    def __init__(self, text, position):
        self.text = text
        self.position = position
        self.first = None
        self.second = None

    def nud(self, right):
        """ unary plus """
        self.first = parse(right, 100)
        self.second = None
        return self

    def led(self, left, right):
        self.first = left
        self.second = parse(right, 10)
        return self

    def __repr__(self):
        return f"(+ {self.first} {self.second})"


class WhitespaceNode:
    lbp = 1000

    def __init__(self, text, position):
        self.text = text
        self.position = position

    def nud(self, right):
        return parse(right, 1000)

    def __repr__(self):
        return f"<{repr(self.text)}>"


class OperatorMultiplyNode:
    lbp = 20

    def __init__(self, text, position):
        self.text = text
        self.position = position
        self.first = None
        self.second = None

    def led(self, left, right):
        self.first = left
        self.second = parse(right, 20)
        return self

    def __repr__(self):
        return f"(* {self.first} {self.second})"
