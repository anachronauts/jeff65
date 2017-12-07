# jeff65 main entry point
# Copyright (C) 2017  jeff65 maintainers
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

import argparse
import sys

from .gold import lexer, ast, ast2

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("input_file", help="the file to compile")
args = arg_parser.parse_args()


def open_input(name):
    if name == "-":
        return sys.stdin
    return open(name, 'r')


with open_input(args.input_file) as input_file:
    lex = list(lexer.lex(input_file))
    print(lex)
    tree = ast.parse_all(lex)
    print(tree)
    tree2 = ast2.transform2(tree)
    print(tree2)
