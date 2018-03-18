# jeff65 linker symbol data structures
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

import pickle


class Archive:
    """An archive is a collection of compiled symbols.

    The compiler produces an archive for each unit, then the linker combines
    archives into a program image.
    """
    def __init__(self, fileobj=None):
        self.constants = {}
        self.symbols = {}
        if fileobj:
            self.load(fileobj)

    def update(self, archive):
        """Updates this archive with contents of another archive.

        Items already present in this archive are retained, and items present
        in both archives are replaced with the item from the other archive.
        """
        self.constants.update(archive.constants)
        self.symbols.update(archive.symbols)

    def load(self, fileobj):
        self.update(pickle.load(fileobj))

    def dump(self, fileobj):
        pickle.dump(self, fileobj)

    def dumpf(self, path):
        with open(path, 'wb') as f:
            self.dump(f)

    def loadf(self, path):
        with open(path, 'rb') as f:
            self.load(f)

    def find_section(self, section):
        return [(name, sym)
                for name, sym in self.symbols.items()
                if sym.section == section]

    def relocations(self):
        for name, sym in self.symbols.items():
            for offset, reloc in sym.relocations:
                yield (name, offset, reloc)


class Symbol:
    def __init__(self, section, data, relocations=None, attrs=None):
        self.section = section
        self.data = data
        self.relocations = relocations or []
        self.attrs = attrs or {}


class Constant:
    def __init__(self, reloc, width):
        self.reloc = reloc
        self.width = width
