from .token import Token

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
