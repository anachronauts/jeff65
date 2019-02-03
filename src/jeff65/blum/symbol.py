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

import collections
import collections.abc
import io
import mmap
import struct
import warnings
import zlib
from . import types
from .fmt import Fmt


MAX_STRING_SIZE = (1 << 31) - 1
MAX_BLOB_SIZE = (1 << 31) - 1
ARCHIVE_MAGIC = b'\x93Blm\x0d\x0a\x1a\x0a'


class Archive:
    """An archive is a collection of compiled symbols.

    The compiler produces an archive for each unit, then the linker combines
    archives into a program image.
    """

    def __init__(self, fileobj=None):
        self.symbols = {}
        if fileobj:
            self.load(fileobj)

    def update(self, archive):
        """Updates this archive with contents of another archive.

        Items already present in this archive are retained, and items present
        in both archives are replaced with the item from the other archive.
        """
        self.symbols.update(archive.symbols)

    def load(self, fileobj):
        with ArchiveReader(fileobj, closefd=False) as reader:
            self.update(reader.load())

    def dump(self, fileobj):
        with ArchiveWriter(fileobj, closefd=False) as writer:
            writer.dump(self)

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
            for offset, reloc in sym.relocations.items():
                yield (name, offset, reloc)


class Relocation:
    full = ord('w')
    hi = ord('h')
    lo = ord('l')

    fields = [
        ('symbol', Fmt.str, Fmt.make_cc('sy'), True),
        ('increment', Fmt.i16, Fmt.make_cc('ic'), True),
        ('byte', Fmt.u8, Fmt.make_cc('by'), True),
    ]

    def __init__(self, symbol, increment=0, byte=None):
        self.symbol = symbol
        self.increment = increment
        self.byte = byte or self.full

    def __eq__(self, other):
        return (isinstance(other, Relocation)
                and self.symbol == other.symbol
                and self.increment == other.increment
                and self.byte == other.byte)

    def __repr__(self):
        return 'Relocation({}, increment={}, byte={})'.format(
            self.symbol, self.increment, repr(self.byte))

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

    def validate(self):
        assert isinstance(self.symbol, str)
        assert isinstance(self.increment, int)
        assert self.byte in [self.full, self.hi, self.lo]

    @classmethod
    def _empty(cls):
        return cls(None)


class Symbol:
    discriminator = Fmt.make_cc('Sy')
    _fmt_relocation_table = Fmt.table(Fmt.u16, Fmt.struct(Relocation))
    fields = [
        ('section', Fmt.str, Fmt.make_cc('sc'), True),
        ('type_info', types.fmt_type_info, Fmt.make_cc('ty'), True),
        ('relocations', _fmt_relocation_table, Fmt.make_cc('re'), True),
        ('data', Fmt.blob, Fmt.make_cc('da'), True),
    ]

    def __init__(self, section, data, type_info, relocations=None):
        self.section = section
        self.data = data
        self.type_info = type_info
        if relocations is not None:
            self.relocations = collections.OrderedDict(relocations)
        else:
            self.relocations = collections.OrderedDict()

    def __eq__(self, other):
        return (isinstance(other, Symbol)
                and self.section == other.section
                and self.data == other.data
                and self.type_info == other.type_info
                and self.relocations == other.relocations)

    def validate(self):
        assert isinstance(self.section, str)
        assert isinstance(self.data, bytes)
        assert self.type_info is not None
        assert isinstance(self.relocations, collections.abc.Mapping)

    @classmethod
    def _empty(cls):
        return cls(None, None, None)


class ArchiveError(Exception):
    pass


class ArchiveWriter:
    def __init__(self, fileobj, closefd=True):
        self.fileobj = fileobj
        self.closefd = closefd
        self.handlers = {
            Fmt._bool: self.dump_fmt('?'),
            Fmt._u8: self.dump_fmt('B'),
            Fmt._u16: self.dump_fmt('H'),
            Fmt._u32: self.dump_fmt('L'),
            Fmt._i8: self.dump_fmt('b'),
            Fmt._i16: self.dump_fmt('h'),
            Fmt._i32: self.dump_fmt('l'),
            Fmt._str: self.dump_string,
            Fmt._blob: self.dump_blob,
            Fmt._array: self.dump_array,
            Fmt._table: self.dump_table,
            Fmt._struct: self.dump_struct,
            Fmt._union: self.dump_union,
        }
        self.blob_infos = collections.deque()
        self.crc = 0
        self._depth = 0

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def close(self):
        if self.closefd:
            self.fileobj.close()

    def _write(self, *datas):
        offset = self.fileobj.tell()
        for data in datas:
            assert len(data) == self.fileobj.write(data)
            self.crc = zlib.crc32(data, self.crc)
        return offset

    def dump(self, archive):
        # write out a placeholder header.
        self.fileobj.seek(0)
        self.dump_header(0, 0, 0, placeholder=True)

        entry_offset, entry_len, entry_crc = 0, 0, 0
        for name, symbol in archive.symbols.items():
            # first get the blobs out in traversal order, and write them out.
            # Keep track of the offsets and checksums.
            for blob in Fmt.find_blobs(symbol):
                self.crc = 0
                blob_offset = self._write(blob)
                self.blob_infos.append((blob_offset, len(blob), self.crc))

            # next we emit the structure.
            self.crc = 0
            sym_offset = self.dump_union([Symbol], symbol)
            sym_len = self.fileobj.tell() - sym_offset
            sym_crc = self.crc
            assert len(self.blob_infos) == 0  # should have consumed all blobs

            # finally, the entry
            self.crc = 0
            entry_offset = self.dump_entry(
                sym_offset, sym_len, sym_crc,
                entry_offset, entry_len, entry_crc, name)
            entry_len = self.fileobj.tell() - entry_offset
            entry_crc = self.crc

        # replace the header with the real one
        self.fileobj.seek(0)
        self.dump_header(entry_offset, entry_len, entry_crc)

    def dump_header(self, next_off, next_len, next_crc, placeholder=False):
        if placeholder:
            magic = b'\xff' * len(ARCHIVE_MAGIC)
        else:
            magic = ARCHIVE_MAGIC
        return self._write(struct.pack('<8s3L', magic,
                                       next_off, next_len, next_crc))

    def dump_entry(self,
                   data_off, data_len, data_crc,
                   next_off, next_len, next_crc,
                   name):
        enc_name = name.encode('utf8')
        fixed_part = struct.pack('<6Ll',
                                 data_off, data_len, data_crc,
                                 next_off, next_len, next_crc,
                                 len(enc_name))
        return self._write(fixed_part, enc_name)

    def dump_by_type(self, t, obj):
        return self.handlers[t[0]](*t[1:], obj)

    def dump_string(self, data):
        enc_data = data.encode('utf8')
        sz = struct.pack('<l', len(enc_data))
        return self._write(sz, enc_data)

    def dump_fmt(self, fmt):
        return lambda data: self._write(struct.pack('<' + fmt, data))

    def dump_struct(self, ty, obj):
        assert type(obj) == ty
        field_count = len([None for _, _, _, pack in obj.fields if pack])
        offset = self._write(struct.pack('<H', field_count))
        for field, t, cc, pack in obj.fields:
            if not pack:
                continue
            self._write(struct.pack('<H', cc))
            self.dump_by_type(t, getattr(obj, field))
        return offset

    def dump_union(self, tys, obj):
        assert type(obj) in tys
        offset = self._write(struct.pack('<H', obj.discriminator))
        self.dump_struct(type(obj), obj)
        return offset

    def dump_array(self, t, objs):
        offset = self._write(struct.pack('<L', len(objs)))
        for obj in objs:
            self.dump_by_type(t, obj)
        return offset

    def dump_table(self, tkey, tvalue, table):
        offset = self._write(struct.pack('<L', len(table)))
        for key, value in table.items():
            self.dump_by_type(tkey, key)
            self.dump_by_type(tvalue, value)
        return offset

    def dump_blob(self, obj):
        return self._write(struct.pack('<LLL', *self.blob_infos.popleft()))


class ArchiveReader:
    def __init__(self, fileobj, closefd=True):
        self.fileobj = fileobj
        self.closefd = closefd
        if isinstance(fileobj, io.BytesIO):
            self._mapping = None
            self.mmap = fileobj.getbuffer()
        else:
            self._mapping = mmap.mmap(self.fileobj.fileno(), 0,
                                      access=mmap.ACCESS_READ)
            self.mmap = memoryview(self._mapping)
        self.handlers = {
            Fmt._bool: self.load_fmt('?'),
            Fmt._u8: self.load_fmt('B'),
            Fmt._u16: self.load_fmt('H'),
            Fmt._u32: self.load_fmt('L'),
            Fmt._i8: self.load_fmt('b'),
            Fmt._i16: self.load_fmt('h'),
            Fmt._i32: self.load_fmt('l'),
            Fmt._str: self.load_string,
            Fmt._blob: self.load_blob,
            Fmt._array: self.load_array,
            Fmt._table: self.load_table,
            Fmt._struct: self.load_struct,
            Fmt._union: self.load_union,
        }

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def close(self):
        self.mmap.release()
        self.mmap = None
        if self._mapping is not None:
            self._mapping.close()
            self._mapping = None
        if self.closefd:
            self.fileobj.close()

    def load(self):
        archive = Archive()
        entry_off, entry_len, entry_crc = self.load_header()

        while entry_off != 0:
            # load the next entry. This method does its own CRC checking
            (sym_off, sym_len, sym_crc,
             entry_off, entry_len, entry_crc,
             name) = self.load_entry(entry_off, entry_len, entry_crc)

            # load the named symbol
            assert sym_crc == zlib.crc32(self.mmap[sym_off:sym_off+sym_len])
            sym_end, symbol = self.load_union([Symbol], sym_off)
            assert sym_end == sym_off+sym_len
            archive.symbols[name] = symbol

        return archive

    def load_header(self):
        magic, entry_off, entry_len, entry_crc = struct.unpack_from(
            '<8s3L', self.mmap, 0)
        if magic != ARCHIVE_MAGIC:
            # Header did not match
            # TODO attempt to diagnose.
            raise ArchiveError("File is not a valid blum archive")
        return entry_off, entry_len, entry_crc

    def load_entry(self, offset, sz, crc):
        assert crc == zlib.crc32(self.mmap[offset:offset+sz])
        fmt = '<6Ll'
        (data_off, data_len, data_crc,
         next_off, next_len, next_crc,
         name_len) = struct.unpack_from(fmt, self.mmap, offset)
        name_start = offset + struct.calcsize(fmt)
        name_end = name_start + name_len
        assert name_end <= offset+sz
        with self.mmap[name_start:name_end] as bview:
            name = bytes(bview).decode('utf8')
        return data_off, data_len, data_crc, next_off, next_len, next_crc, name

    def load_by_type(self, t, off):
        return self.handlers[t[0]](*t[1:], off)

    def load_string(self, off):
        off, sz = self.load_fmt('l', off)
        compressed = sz < 0
        end = off + abs(sz)

        with self.mmap[off:end] as bview:
            if compressed:
                dc = zlib.decompressobj()
                bdata = dc.decompress(bview, max_length=MAX_STRING_SIZE)
                if len(dc.unconsumed_tail) > 0:
                    warnings.warn("Truncated large (>2 GiB) string in archive")
            else:
                bdata = bytes(bview)
            return end, bdata.decode('utf8')

    def load_fmt(self, fmt, *args):
        fmt = '<' + fmt
        sz = struct.calcsize(fmt)

        def load_fmt_inner(off):
            val, = struct.unpack_from(fmt, self.mmap, off)
            return off+sz, val
        if len(args) > 0:
            return load_fmt_inner(*args)
        return load_fmt_inner

    def load_struct(self, ty, *args):
        def load_struct_inner(off):
            field_map = {cc: (field, ft) for field, ft, cc, _ in ty.fields}
            off, field_count = self.load_fmt('H', off)
            obj = ty._empty()
            for _ in range(field_count):
                off, cc = self.load_fmt('H', off)
                field, ft = field_map[cc]
                off, val = self.load_by_type(ft, off)
                try:
                    setattr(obj, field, val)
                except AttributeError as ex:
                    raise ArchiveError(
                        "Can't set {} on {}".format(field, type(obj))) from ex
            obj.validate()
            return off, obj
        if len(args) > 0:
            return load_struct_inner(*args)
        return load_struct_inner

    def load_union(self, types, *args):
        def load_union_inner(off):
            off, disc = self.load_fmt('H', off)
            sel = next(t for t in types if t.discriminator == disc)
            return self.load_struct(sel, off)
        if len(args) > 0:
            return load_union_inner(*args)
        return load_union_inner

    def load_array(self, t, off):
        objs = []
        off, sz = self.load_fmt('L', off)
        for _ in range(sz):
            off, val = self.load_by_type(t, off)
            objs.append(val)
        return off, objs

    def load_table(self, tkey, tvalue, off):
        table = collections.OrderedDict()
        off, sz = self.load_fmt('L', off)
        for _ in range(sz):
            off, key = self.load_by_type(tkey, off)
            off, val = self.load_by_type(tvalue, off)
            table[key] = val
        return off, table

    def load_blob(self, off):
        fmt = '<LLL'
        blob_off, blob_len, blob_crc = struct.unpack_from(
            fmt, self.mmap, off)
        off += struct.calcsize(fmt)
        with self.mmap[blob_off:blob_off+blob_len] as bview:
            assert blob_crc == zlib.crc32(bview)
            return off, bytes(bview)
