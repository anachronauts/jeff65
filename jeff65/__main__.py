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
import pathlib
import sys
from . import gold
from . import blum

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("input_file", help="the file to compile")
args = arg_parser.parse_args()

input_file = pathlib.PurePath(args.input_file)

obj = gold.translate(input_file)
gold.dump_unit(obj, input_file.with_suffix('.blum'))
blum.link(input_file.stem, obj, input_file.with_suffix('.prg'))
blum.dump_symbols(obj, sys.stdout)
