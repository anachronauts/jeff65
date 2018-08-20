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
import logging
import pathlib
import sys


class BraceMessage:
    def __init__(self, fmt, *args, **kwargs):
        self.fmt = fmt
        self.args = args
        self.kwargs = kwargs

    def __str__(self):
        return self.fmt.format(*self.args, **self.kwargs)

    @classmethod
    def install(cls):
        """Add to builtins as __.

        Hacking builtins is generally a bad idea, but this is similar to _ in
        gettext, which is part of the standard library, so...
        """
        import builtins
        builtins.__ = cls


BraceMessage.install()


def main(argv=None):
    parser = argparse.ArgumentParser()

    parser.add_argument("--debug",
                        help="run in debug mode",
                        dest="debug", action="store_true",
                        default=False)
    parser.add_argument("-v", "--verbose",
                        help="show additional information during operation",
                        dest="verbose", action="store_true",
                        default=False)

    subparsers = parser.add_subparsers()
    compile_parser = subparsers.add_parser(
        'compile', help="compile one or more files")
    compile_parser.add_argument("-o", help="place the output into OUTPUT",
                                dest="output", type=pathlib.PurePath)
    compile_parser.add_argument('file', help="the file to compile",
                                type=pathlib.PurePath)
    compile_parser.set_defaults(func=cmd_compile)

    objdump_parser = subparsers.add_parser(
        'objdump', help="list symbols of an object")
    objdump_parser.add_argument('file', help="the file to examine",
                                type=pathlib.PurePath)
    objdump_parser.set_defaults(func=cmd_objdump)

    args = parser.parse_args(argv)
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    elif args.verbose:
        logging.basicConfig(level=logging.INFO)

    if hasattr(args, 'func'):
        args.func(args)
    else:
        parser.print_help()
        sys.exit(1)


def cmd_none(args):
    raise NotImplementedError


def cmd_compile(args):
    from . import gold
    from . import blum

    archive = gold.translate(args.file)
    # archive.dumpf(args.file.with_suffix('.blum'))
    blum.link('{}.main'.format(args.file.stem), archive,
              args.output or args.file.with_suffix(".prg"))


def cmd_objdump(args):
    from . import blum

    archive = blum.Archive()
    archive.loadf(args.file)

    print("Unit: '{}'".format(args.file.stem))

    if len(archive.symbols) == 0:
        print("Symbols: (none)")
    else:
        print("Symbols:")
        for name, symbol in archive.symbols.items():
            print("    {}: size={}, section={}, type={}".format(
                name, len(symbol.data), symbol.section, symbol.type_info))
            for relocation in symbol.relocations:
                print("      {}".format(relocation))
