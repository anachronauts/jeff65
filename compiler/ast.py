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
        self.current = next(self.source)

    def next(self):
        self.current = next(self.source)


def parse_all(stream):
    s = MemIter(stream)
    return parse(s, 0)


def parse(stream, rbp):
    t = stream.current
    stream.next()
    left = t.nud(stream)
    while rbp < stream.current.lbp:
        t = stream.current
        stream.next()
        left = t.led(left, stream)
    return left

class NodeBase:
    def __init__(self, position, value):
        self.position = position
        self.value = value

    def nud(self, right):
        return NotImplemented

    def led(self, left, right):
        return NotImplemented

    def __repr__(self):
        return repr(self.value)


class WhitespaceNode(NodeBase):
    lbp = 1000

    def __init__(self, position, value):
        NodeBase.__init__(self, position, value)

    def nud(self, right):
        return parse(right, 1000)

    def __repr__(self):
        return f"<{repr(self.value)}>"


class EofNode(NodeBase):
    lbp = 0

    def __init__(self):
        NodeBase.__init__(self, None, None)

    def __repr__(self):
        return f"<EOF>"


class NumericNode(NodeBase):
    def __init__(self, position, value):
        NodeBase.__init__(self, position, value)

    def nud(self, right):
        return self


class StringNode(NodeBase):
    def __init__(self, position, value):
        NodeBase.__init__(self, position, value)

    def nud(self, right):
        return self


class OperatorAddNode(NodeBase):
    lbp = 10

    def __init__(self, position):
        NodeBase.__init__(self, position, "+")
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


class OperatorMultiplyNode(NodeBase):
    lbp = 20

    def __init__(self, position):
        NodeBase.__init__(self, position, "*")
        self.first = None
        self.second = None

    def led(self, left, right):
        self.first = left
        self.second = parse(right, 20)
        return self

    def __repr__(self):
        return f"(* {self.first} {self.second})"
