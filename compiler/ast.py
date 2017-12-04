class IdentifierNode:
    def __init__(self, pos, text):
        self.text = text
        self.pos = pos

    def __repr__(self):
        return self.text


class NumericNode:
    def __init__(self, pos, value):
        self.value = value
        self.pos = pos

    def __repr__(self):
        return self.value


class ArrayNode:
    def __init__(self, pos, values):
        self.values = values
        self.pos = pos

    def __repr__(self):
        vs = ", ".join(repr(v) for v in self.values)
        return f"[{vs}]"


class StringNode:
    def __init__(self, pos, values):
        self.values = values
        self.pos = pos

    def __repr__(self):
        vs = "".join(self.values)
        return repr(vs)


class LetNode:
    def __init__(self, pos, storage, name, rvalue):
        self.storage = storage
        self.name = name
        self.rvalue = rvalue
        self.pos = pos

    def __repr__(self):
        if self.storage is not None:
            return f"let {self.storage} {self.name} = {self.rvalue}"
        return f"let {self.name} = {self.rvalue}"


class UseNode:
    def __init__(self, pos, unit):
        self.unit = unit
        self.pos = pos

    def __repr__(self):
        return f"use {self.unit}"


class ParamListNode:
    def __init__(self, pos, param_list):
        self.param_list = param_list
        self.pos = pos

    def __repr__(self):
        return ", ".join(repr(p) for p in param_list)


class FunNode:
    def __init__(self, pos, name, param_list, stmt_list):
        self.name = name
        self.param_list = param_list
        self.stmt_list = stmt_list
        self.pos

    def __repr__(self):
        r = []
        r.append(f"fun {self.name}({repr(self.param_list)})")
        for stmt in self.stmt_list:
            r.append(repr(stmt))
        r.append("endfun")
        return "\n".join(r)
