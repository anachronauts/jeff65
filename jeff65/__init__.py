# jeff65 module root
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
import pathlib
import sys
from . import gold
from . import blum


def main():
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers()

    compile_parser = subparsers.add_parser(
        'compile', help="compile one or more files")
    compile_parser.add_argument('file', help="the file to compile",
                                type=pathlib.PurePath)
    compile_parser.add_argument("-v", "--verbose",
                                help="show the output of each pass",
                                dest="verbose", action="store_true",
                                default=False)
    compile_parser.set_defaults(func=cmd_compile)

    objdump_parser = subparsers.add_parser(
        'objdump', help="list symbols of an object")
    objdump_parser.add_argument('file', help="the file to examine",
                                type=pathlib.PurePath)
    objdump_parser.set_defaults(func=cmd_objdump)

    args = parser.parse_args()

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


def cmd_none(args):
    raise NotImplementedError


def cmd_compile(args):
    archive = gold.translate(args.file, args.verbose)
    archive.dumpf(args.file.with_suffix('.blum'))
    blum.link('{}.main'.format(args.file.stem), archive,
              args.file.with_suffix('.prg'))


def cmd_objdump(args):
    archive = blum.Archive()
    archive.loadf(args.file)

    print("Unit: '{}'".format(args.file.stem))

    if len(archive.constants) == 0:
        print("Constants: (none)")
    else:
        print("Constants:")
        for name, constant in archive.constants.items():
            print("    {}: {}".format(name, constant))
    print()

    if len(archive.symbols) == 0:
        print("Symbols: (none)")
    else:
        print("Symbols:")
        for name, symbol in archive.symbols.items():
            print("    {}: size={}, section={}, type={}".format(
                name, len(symbol.data), symbol.section, symbol.type_info))
            for relocation in symbol.relocations:
                print("      {}".format(relocation))
