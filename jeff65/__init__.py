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
from . import gold
from . import blum


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("input_file", help="the file to compile")
    arg_parser.add_argument("-v", "--verbose",
                            help="show the output of each pass",
                            dest="verbose", action="store_true", default=False)
    args = arg_parser.parse_args()

    input_file = pathlib.PurePath(args.input_file)

    archive = gold.translate(input_file, args.verbose)
    archive.dumpf(input_file.with_suffix('.blum'))
    blum.link('{}.main'.format(input_file.stem), archive,
              input_file.with_suffix('.prg'))
