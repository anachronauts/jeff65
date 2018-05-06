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
import struct


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
    def __init__(self, value, width):
        self.value = value
        self.width = width


class Relocation:
    hi = b'h'
    lo = b'l'

    def __init__(self, symbol, increment=0, byte=None):
        self.symbol = symbol
        self.increment = increment
        self.byte = byte

    def bind(self, symbol):
        if self.symbol is None:
            return Relocation(symbol, self.increment, self.byte)
        return self

    def compute_offset(self, base, offsets):
        return base + offsets[self.symbol] + self.increment

    def compute_value(self, base, offsets):
        offset = self.compute_offset(base, offsets)
        if self.byte == self.lo:
            return offset & 0x00ff
        elif self.byte == self.hi:
            return offset >> 8
        return offset

    def compute_bin(self, base, offsets):
        offset = self.compute_offset(base, offsets)
        bin = struct.pack('<H', offset)
        if self.byte == self.lo:
            return bin[0:1]
        elif self.byte == self.hi:
            return bin[1:2]
        return bin


class ArchiveWriterContext:
    def __init__(self, archive, fileobj):
        self.fileobj = fileobj
