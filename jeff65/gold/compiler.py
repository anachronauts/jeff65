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

import sys
import antlr4
from .lexer import Lexer
from .grammar import Parser
from . import asm, ast, binding, lower, storage, typepasses, units


passes = [
    # binding.ExplicitScopes,
    units.ResolveUnits,
    binding.ShadowNames,
    typepasses.ConstructTypes,
    binding.BindNamesToTypes,
    units.ResolveMembers,
    typepasses.PropagateTypes,
    binding.EvaluateConstants,
    binding.ResolveConstants,
    storage.ResolveStorage,
    lower.LowerAssignment,
    lower.LowerFunctions,
    asm.AssembleWithRelocations,
    asm.FlattenSymbol,
]


def open_unit(unit):
    if unit == "-":
        return sys.stdin
    return open(unit, 'r')


def translate(unit):
    with open_unit(unit) as input_file:
        lexer = Lexer(input_file, name=unit)
        tokens = antlr4.CommonTokenStream(lexer)
        parser = Parser(tokens)
        tree = parser.unit()
        builder = ast.AstBuilder()
        antlr4.ParseTreeWalker.DEFAULT.walk(builder, tree)
        unit = builder.ast

        for p in passes:
            unit = unit.transform(p())

        print(unit.pretty())
