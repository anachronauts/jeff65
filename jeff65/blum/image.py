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
from . import symbol, types


def make_startup_for(main, version):
    archive = symbol.Archive()
    archive.symbols['$startup.__start'] = symbol.Symbol(
        section='startup',
        data=struct.pack(
            # Defines a simple startup header. Note that in theory, we could
            # simply make the target of the SYS instruction be our main
            # function, but our relocation system isn't smart enough for that
            # and we may wish to add more complicated startup code in the
            # future. We could assume that main exits using RTS and save one
            # byte and a few cycles, but for now it's convenient to have a
            # well-known address to break on.
            "<HHB4sxHBHB",
            0x080b,         # 0x0000 0x0801 (H)    addr of next BASIC line
            version,        # 0x0002 0x0803 (H)    BASIC line number
            0x9e, b'2061',  # 0x0004 0x0805 (B4sx) SYS2061 (0x080d)
            0x0000,         # 0x000a 0x080b (H)    BASIC end-of-program
            0x20, 0xffff,   # 0x000c 0x080d (BH)   jsr $ffff
            0x60,           # 0x000f 0x0810 (B)    rts
        ),
        type_info=types.phantom,
        relocations={
            # Relocation for the address of 'main'
            0x000d: symbol.Relocation(main),
        })
    return archive


class Image:
    m_reloc = re.compile(r'^([^,+-]+)([+-]\d+)?(,lo|,hi)?$')

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

        # perform relocations
        for name, offset, reloc in self.archive.relocations():
            if name not in self.offsets:
                continue

            self.seek_to_offset(name, offset)
            addr = reloc.bind(name).compute_bin(
                self.base_address, self.offsets)
            self.fileobj.write(addr)
