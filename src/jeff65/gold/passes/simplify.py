# jeff64 gold-syntax CST -> AST simplification
# Copyright (C) 2018  jeff65 maintainers
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

from ..grammar import T
from ... import ast, parsing, pattern
from ...pattern import Predicate as P


def require_token(t):
    return P.require(lambda n, c: n.t == t)


def token(t, key=None):
    return P(key, lambda n, c: n.t == t)


def unop(operator, sym, a_rhs):
    @pattern.match(
        ast.AstNode('expr', {
            "exhaustive!": True,
            "00": token(operator),
            "01": P('rhs'),
        }))
    def name_unop(self, rhs):
        return ast.AstNode(sym, {a_rhs: rhs})

    return name_unop


def binop(operator, sym):
    @pattern.match(
        ast.AstNode('expr', {
            "exhaustive!": True,
            "00": P("lhs"),
            "01": token(operator),
            "02": P("rhs"),
        }))
    def name_binop(self, lhs, rhs):
        return ast.AstNode(sym, {
            "lhs": lhs,
            "rhs": rhs,
        })

    return name_binop


def to_list(sym, t_node, a_element):
    @pattern.match(
        ast.AstNode(sym, {
            "exhaustive!": True,
            "00": P("car"),
            "01": P("cdr"),
        }))
    def name_right_recursion(self, car, cdr):
        return ast.AstNode(sym, {
            a_element: car,
            "next": cdr,
        })

    @pattern.match(ast.AstNode(sym, {"exhaustive!": True}))
    def name_right_recursion_final(self):
        return None

    return name_right_recursion, name_right_recursion_final


def drop_if_one_child(sym):
    @pattern.match(
        ast.AstNode(sym, {
            "exhaustive!": True,
            "00": P.any_node("inner"),
        }))
    def remove_outer(self, inner):
        return inner

    return remove_outer


@pattern.transform(pattern.Order.Ascending)
class Simplify:

    remove_outer_expr = drop_if_one_child('expr')
    remove_outer_alist = drop_if_one_child('alist')

    list_toplevel, list_toplevel_f = to_list("toplevel", "toplevel", "stmt")
    list_block, list_block_f = to_list("block", "block", "stmt")

    @pattern.match(
        ast.AstNode("unit", {
            "exhaustive!": True,
            "00": P("toplevels"),
        }))
    def name_unit(self, toplevels):
        return ast.AstNode("unit", {
            "toplevels": toplevels,
        })

    @pattern.match(ast.AstNode("alist", {"exhaustive!": True}))
    def remove_empty_alist(self):
        return None

    @pattern.match(
        ast.AstNode("alist_inner", {
            "exhaustive!": True,
            "00": P("arg"),
        }))
    def collapse_alist_final(self, arg):
        return ast.AstNode("alist", {
            "arg": arg,
            "next": None,
        })

    @pattern.match(
        ast.AstNode("alist_inner", {
            "exhaustive!": True,
            "00": P("arg"),
            "01": require_token(T.PUNCT_COMMA),
            "02": P("cdr"),
        }))
    def collapse_alist(self, arg, cdr):
        return ast.AstNode("alist", {
            "arg": arg,
            "next": cdr,
        })

    @pattern.match(
        ast.AstNode('stmt_use', {
            "exhaustive!": True,
            "00": require_token(T.STMT_USE),
            "01": P('unit_name'),
        }))
    def collapse_stmt_use(self, unit_name):
        return ast.AstNode('use', attrs={
            'name': unit_name.text,
        })

    @pattern.match(
        ast.AstNode('stmt_constant', {
            "exhaustive!": True,
            "00": require_token(T.STMT_CONSTANT),
            "01": ast.AstNode('declaration', {
                "exhaustive!": True,
                "00": P('name'),
                "01": require_token(T.PUNCT_COLON),
                "02": P('ty'),
            }),
            "02": require_token(T.OPERATOR_ASSIGN),
            "03": P('rhs'),
        }))
    def collapse_stmt_constant(self, name, ty, rhs):
        return ast.AstNode('constant', attrs={
            'name': name.text,
            'type': ty,
            'value': rhs,
        })

    @pattern.match(
        ast.AstNode("storage", {
            "exhaustive!": True,
        }))
    def storage_default(self):
        return None

    @pattern.match(
        ast.AstNode("storage", {
            "exhaustive!": True,
            "00": token(T.STORAGE_MUT),
        }))
    def storage_mut(self):
        return "mut"

    @pattern.match(
        ast.AstNode("storage", {
            "exhaustive!": True,
            "00": token(T.STORAGE_STASH),
        }))
    def storage_stash(self):
        return "stash"

    @pattern.match(
        ast.AstNode("stmt_let", {
            "exhaustive!": True,
            "00": require_token(T.STMT_LET),
            "01": P("storage"),
            "02": ast.AstNode("declaration", {
                "00": P("name"),
                "01": require_token(T.PUNCT_COLON),
                "02": P("ty"),
            }),
            "03": require_token(T.OPERATOR_ASSIGN),
            "04": P("value"),
        }))
    def collapse_stmt_let(self, storage, name, ty, value):
        return ast.AstNode("let", {
            "name": name.text,
            "type": ty,
            "storage": storage,
            "value": value,
        })

    @pattern.match(
        ast.AstNode('stmt_assign', {
            "exhaustive!": True,
            "00": P('lhs'),
            "01": require_token(T.OPERATOR_ASSIGN),
            "02": P('rhs'),
        }))
    def collapse_stmt_assign(self, lhs, rhs):
        return ast.AstNode('set', {
            "lvalue": lhs,
            "rvalue": rhs,
        })

    # # TODO: handle arguments, return values
    @pattern.match(
        ast.AstNode('stmt_fun', {
            "exhaustive!": True,
            "00": require_token(T.STMT_FUN),
            "01": P('name'),
            "02": require_token(T.PAREN_OPEN),
            "03": P.any(),  # plist
            "04": require_token(T.PAREN_CLOSE),
            "05": P("body"),
            "06": require_token(T.PUNCT_ENDFUN),
        }))
    def collapse_stmt_fun(self, name, body):
        return ast.AstNode('fun', {
            'name': name.text,
            'return': None,
            'args': None,
            'body': body,
        })

    @pattern.match(
        ast.AstNode('type_id', {
            "exhaustive!": True,
            "00": P('ty'),
        }))
    def simple_type(self, ty):
        return ty.text

    @pattern.match(
        ast.AstNode('type_id', {
            "exhaustive!": True,
            "00": token(T.OPERATOR_REF),
            "01": P("storage"),  # TODO figure out how to handle this properly
            "02": P('ty'),
        }))
    def ref_type(self, storage, ty):
        return ast.AstNode('type_ref', {
            'type': ty,
            # **{'storage': s.text for s in storage},
            'storage': storage,
        })

    @pattern.match(
        ast.AstNode('expr', {
            "exhaustive!": True,
            "00": token(T.NUMERIC, 'n'),
        }))
    def numeric(self, n):
        try:
            if n.text.startswith('0x'):
                value = int(n.text[2:], 16)
            elif n.text.startswith('0o'):
                value = int(n.text[2:], 8)
            elif n.text.startswith('0b'):
                value = int(n.text[2:], 2)
            else:
                value = int(n.text)
        except ValueError as e:
            raise parsing.ParseError(str(e))

        return ast.AstNode('numeric', {'value': value})

    @pattern.match(
        ast.AstNode('expr', {
            "exhaustive!": True,
            "00": token(T.IDENTIFIER, 'id'),
        }))
    def identifier(self, id):
        return ast.AstNode('identifier', {
            'name': id.text,
        })

    @pattern.match(
        ast.AstNode('expr', {
            "exhaustive!": True,
            "00": token(T.PAREN_OPEN),
            "01": P('inner'),
            "02": token(T.PAREN_CLOSE),
        }))
    def drop_expr_parens(self, inner):
        return inner

    name_negate = unop(T.OPERATOR_MINUS, 'negate', 'value')
    name_deref = unop(T.OPERATOR_DEREF, 'deref', 'address')
    name_add = binop(T.OPERATOR_PLUS, 'add')
    name_sub = binop(T.OPERATOR_MINUS, 'sub')
    name_mul = binop(T.OPERATOR_TIMES, 'mul')
    name_div = binop(T.OPERATOR_DIVIDE, 'div')

    @pattern.match(
        ast.AstNode('expr', {
            "exhaustive!": True,
            "00": P('namespace'),
            "01": token(T.OPERATOR_DOT),
            "02": ast.AstNode('member', {
                "exhaustive!": True,
                "00": P('member'),
            }),
        }))
    def name_member_access(self, namespace, member):
        return ast.AstNode('member_access', attrs={
            'namespace': namespace,
            'member': member.text,
        })

    @pattern.match(
        ast.AstNode('stmt_call', {
            "exhaustive!": True,
            "00": P('function'),
            "01": token(T.PAREN_OPEN),
            "02": P('alist'),  # TODO handle this properly
            "03": token(T.PAREN_CLOSE),
        }))
    def name_call(self, function, alist):
        return ast.AstNode('call', attrs={
            'target': function,
            'args': alist,
        })

    # Collapse left-recursion on strings.
    @pattern.match(ast.AstNode('string_inner', {"exhaustive!": True}))
    def string_inner_empty(self):
        return []

    @pattern.match(
        ast.AstNode('string_inner', {
            "00": P('string0'),
            "01": token(T.STRING, 'string1'),
        }))
    def string_inner_segment(self, string0, string1):
        string0.append(string1.text)
        return string0

    @pattern.match(
        ast.AstNode('string_inner', {
            "00": P('string0'),
            "01": token(T.STRING_ESCAPE, 'string1'),
        }))
    def string_inner_escape(self, string0, string1):
        string0.append(string1.text[1])
        return string0

    @pattern.match(
        ast.AstNode('string', {
            "00": require_token(T.STRING_DELIM),
            "01": P('value'),
            "02": require_token(T.STRING_DELIM),
        }))
    def collapse_string(self, value):
        return ast.AstNode('string', attrs={'value': "".join(value)})
