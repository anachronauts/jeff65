# jeff65 linker image manager
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

import re
import struct
from . import symbol


def make_startup_for(main, version):
    archive = symbol.Archive()
    archive.symbols['$startup.__start'] = symbol.Symbol(
        'startup',
        struct.pack(
            # Defines a simple startup header. Note that in theory, we could
            # simply make the target of the SYS instruction be our main
            # function, but our relocation system isn't smart enough for that
            # and we may wish to add more complicated startup code in the
            # future. It is assumed that main() will RTS.
            "<HHB4sxHBH",
            0x080b,         # 0x0000 0x0801 (H)    addr of next BASIC line
            version,        # 0x0002 0x0803 (H)    BASIC line number
            0x9e, b'2061',  # 0x0004 0x0805 (B4sx) SYS2061 (0x080d)
            0x0000,         # 0x000a 0x080b (H)    BASIC end-of-program
            0x4c, 0xffff,   # 0x000c 0x080d (BH)   jmp $ffff
        ),
        relocations=[
            # Relocation for the address of 'main'
            (0x000d, main),
        ])
    return archive


class Image:
    m_reloc = re.compile(r'^([^+-]+)([+-]\d+)?(,lo|,hi)?$')

    def __init__(self, fileobj, base_address=0x0801):
        self.fileobj = fileobj
        self.offsets = {}
        self.archive = symbol.Archive()
        self.base_address = base_address
        self.start_symbol = '$startup.__start'

        # Header for PRG files. Identifies the load location in memory.
        # 0x0801 is the load location for BASIC programs.
        self.prg_header = struct.pack("<H", self.base_address)

    def add_archive(self, archive):
        self.archive.update(archive)

    def compute_relocation(self, name, reloc, binary=False):
        """Computes the address for a relocation based on an offset table.

        If binary is True, then returns the result as a little-endian
        bytestring. If the relocation ends in ',lo' or ',hi' then the
        bytestring will be one byte long; otherwise, two.
        """
        m = self.m_reloc.match(reloc)
        sym = m.group(1)
        if sym == '.':
            sym = name
        inc = int(m.group(2) or 0)
        part = m.group(3)
        offset = self.base_address + self.offsets[sym] + inc
        addr = struct.pack("<H", offset)
        if binary:
            if part == ',lo':
                return addr[0:1]
            elif part == ',hi':
                return addr[1:2]
            return addr
        else:
            if part == ',lo':
                return addr[0]
            elif part == ',hi':
                return addr[1]
            return offset

    def current_offset(self):
        return self.fileobj.tell() - len(self.prg_header)

    def seek_to_offset(self, name, inc):
        self.fileobj.seek(self.offsets[name] + inc + len(self.prg_header))

    def _emit_sym(self, name, sym):
        self.offsets[name] = self.current_offset()
        self.fileobj.write(sym.data)

    def link(self):
        """Links the image, writing it out to a file."""
        # write out the prg header
        self.fileobj.write(self.prg_header)

        # write out the startup section
        startup = self.archive.find_section('startup')
        assert len(startup) == 1
        for name, sym in startup:
            self._emit_sym(name, sym)

        # write out the text section
        for name, sym in self.archive.find_section('text'):
            self._emit_sym(name, sym)

        # resolve constants
        for name, const in self.archive.constants.items():
            if type(const.reloc) is int:
                self.offsets[name] = const.reloc

            self.offsets[name] = self.compute_relocation(name, const.reloc)

        # perform relocations
        for name, offset, reloc in self.archive.relocations():
            if name not in self.offsets:
                continue

            self.seek_to_offset(name, offset)
            addr = self.compute_relocation(name, reloc, binary=True)
            self.fileobj.write(addr)
