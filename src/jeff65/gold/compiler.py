# jeff65 gold-syntax compiler sequence
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

import logging
import sys
from . import grammar
from .. import ast, blum, parsing
from .passes import asm, binding, lower, resolve, simplify, typepasses

logger = logging.getLogger(__name__)


passes = [
    resolve.ResolveUnits,
    binding.ShadowNames,
    typepasses.ConstructTypes,
    binding.BindNamesToTypes,
    resolve.ResolveMembers,
    typepasses.PropagateTypes,
    binding.EvaluateConstants,
    binding.ResolveConstants,
    resolve.ResolveStorage,
    lower.LowerAssignment,
    lower.LowerFunctions,
    asm.AssembleWithRelocations,
    asm.FlattenSymbol,
]


def open_unit(unit):
    if str(unit) == "-":
        return sys.stdin
    return open(unit, "r")


def parse(fileobj, name):
    with parsing.ReStream(fileobj) as stream:
        tree = grammar.parse(
            stream,
            grammar.lex,
            lambda t, s, c, m: ast.AstNode(
                t, span=s, attrs={f"{k:02}": v for k, v in enumerate(c)}
            ),
        )
    return tree.transform(simplify.Simplify())


def translate(unit):
    # parse will close the file for us
    obj = parse(open_unit(unit), name=unit.name)
    for p in passes:
        obj = obj.transform(p())
        logger.debug(__("Pass {}:\n{:p}", p.__name__, obj))

    archive = blum.Archive()
    for node in obj.select("toplevels", "stmt"):
        if node.t == "fun_symbol":
            sym_name = "{}.{}".format(unit.stem, node.attrs["name"])
            sym = blum.Symbol(
                section="text", data=node.attrs["text"], type_info=node.attrs["type"]
            )
            archive.symbols[sym_name] = sym

    return archive
