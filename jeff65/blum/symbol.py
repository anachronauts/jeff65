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


def make_cc(code):
    cc, = struct.unpack('<H', code.encode('ascii'))
    return cc


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
    discriminator = make_cc('Sy')
    fields = [
        ('_name', 'str', make_cc('nm'), True),
        ('section', 'str', make_cc('sc'), True),
        ('type_info', 'type_info', make_cc('ty'), True),
        ('relocations', 'array relocation', make_cc('re'), True),
        ('data', 'blob', make_cc('da'), True),
    ]

    def __init__(self, section, data, type_info, relocations=None):
        self.section = section
        self.data = data
        self.type_info = type_info
        self.relocations = relocations or []
        self._name = None


class Constant:
    discriminator = make_cc('Cn')
    fields = [
        ('_name', 'str', make_cc('nm'), True),
        ('type_info', 'type_info', make_cc('ty'), True),
        ('value_bin', '8b', make_cc('vl'), True),
    ]

    def __init__(self, value, type_info):
        self.value = value
        self.type_info = type_info
        self._name = None

    @property
    def value_bin(self):
        return self.type_info.encode(self.value)


class Relocation:
    full = ord('w')
    hi = ord('h')
    lo = ord('l')

    fields = [
        ('symbol', 'str', make_cc('sy'), True),
        ('increment', 'u16', make_cc('ic'), True),
        ('byte', 'u8', make_cc('by'), True),
    ]

    def __init__(self, symbol, increment=0, byte=None):
        self.symbol = symbol
        self.increment = increment
        self.byte = byte or self.full

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


class ArchiveWriter:
    def __init__(self):
        self.handlers = {
            'str': self.dump_string,
            'u16': self.dump_fmt('<H'),
            'u8': self.dump_fmt('<B'),
            '?': self.dump_fmt('<?'),
            'relocation': self.dump_struct,
            'constant': self.dump_struct,
            'type_info': self.dump_union,
            'array': self.dump_array,
            '8b': self.dump_8b,
            'blob': self.dump_blob,
        }
        self.offsets = []

    def dump(self, archive, fileobj):
        fileobj.write(b'\x93Blm\x0d\x0a\x1a\x0a')
        entries = len(archive.constants) + len(archive.symbols)
        fileobj.write(struct.pack('<L', entries))
        for name, constant in archive.constants.items():
            self.dump_constant(fileobj, name, constant)
        for name, symbol in archive.symbols.items():
            self.dump_symbol(fileobj, name, symbol)
        fills = []
        for offset, data in self.offsets:
            fills.append((offset, fileobj.tell()))
            assert len(data) == fileobj.write(data)
        for offset, value in fills:
            fileobj.seek(offset)
            assert 4 == fileobj.write(struct.pack('<L', value))

    def dump_constant(self, fileobj, name, obj):
        obj._name = name
        self.dump_union(fileobj, obj)

    def dump_symbol(self, fileobj, name, obj):
        obj._name = name
        self.dump_union(fileobj, obj)

    def dump_by_type(self, t, fileobj, obj):
        ts = t.split()
        return self.handlers[ts[0]](*ts[1:], fileobj, obj)

    def dump_8b(self, fileobj, bs):
        assert len(bs) == 8
        assert len(bs) == fileobj.write(bs)
        return len(bs)

    def dump_string(self, fileobj, data: str) -> int:
        bin = data.encode('utf8')
        sz = struct.pack('<L', len(bin))
        count = len(sz) + len(bin)
        assert count == fileobj.write(sz + bin)
        return count

    def dump_fmt(self, fmt):
        def dump(fileobj, data):
            val = struct.pack(fmt, data)
            assert len(val) == fileobj.write(val)
            return len(val)
        return dump

    def dump_struct(self, fileobj, obj):
        field_count = len([None for _, _, _, pack in obj.fields if pack])
        assert 2 == fileobj.write(struct.pack('<H', field_count))
        count = 2
        for field, t, n, pack in obj.fields:
            if not pack:
                continue
            assert 2 == fileobj.write(struct.pack('<H', n))
            count += 2
            count += self.dump_by_type(t, fileobj, getattr(obj, field))
        return count

    def dump_union(self, fileobj, obj):
        assert 2 == fileobj.write(struct.pack('<H', obj.discriminator))
        count = self.dump_struct(fileobj, obj)
        return 2 + count

    def dump_array(self, t, fileobj, objs):
        assert 4 == fileobj.write(struct.pack('<L', len(objs)))
        count = 4
        for obj in objs:
            count += self.dump_by_type(t, fileobj, obj)
        return count

    def dump_blob(self, fileobj, obj):
        offset = fileobj.tell()
        assert 6 == fileobj.write(struct.pack('<LH', 0xdeadbeef, len(obj)))
        self.offsets.append((offset, obj))
        return 6
