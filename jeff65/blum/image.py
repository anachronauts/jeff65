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
from ..gold import ast

# Header for PRG files. Identifies the load location in memory, in this case
# 0x0801, which is the load location for BASIC programs.
prg_header = struct.pack("<H", 0x0801)


def make_startup_for(name, version):
    return ast.AstNode('unit', None, children=[
        ast.AstNode('fun_symbol', None, attrs={
            'name': '__start',
            'relocations': [
                # Relocation for the address of 'main'
                (0x000d, '{}.main'.format(name)),
            ],
            'text': struct.pack(
                # Defines a simple startup header. Note that in theory, we
                # could simply make the target of the SYS instruction be our
                # main function, but our relocation system isn't smart enough
                # for that and we may wish to add more complicated startup code
                # in the future. It is assumed that main() will RTS.
                "<HHB4sxHBH",
                0x080b,         # 0x0000 0x0801 (H)    addr of next BASIC line
                version,        # 0x0002 0x0803 (H)    BASIC line number
                0x9e, b'2061',  # 0x0004 0x0805 (B4sx) SYS2061 (0x080d)
                0x0000,         # 0x000a 0x080b (H)    BASIC end-of-program
                0x4c, 0xffff,   # 0x000c 0x080d (BH)   jmp $ffff
            ),
        })
    ])


class Image:
    m_reloc = re.compile(r'^([^+-]+)([+-]\d+)?(,lo|,hi)?$')

    def __init__(self):
        self.symbols = {}
        self.base_address = 0x0801
        self.start_symbol = '$startup.__start'

    def add_unit(self, name, unit):
        """Adds the symbols for a unit to the symbols table."""
        for symbol in unit.children:
            sym_name = symbol.attrs['name']
            self.symbols["{}.{}".format(name, sym_name)] = symbol

    def compute_relocation(self, offsets, name, reloc):
        """Computes the address for a relocation based on an offset table.

        Returns the result as a little-endian bytestring. If the relocation
        ends in ',lo' or ',hi' then the bytestring will be one byte long;
        otherwise, two.
        """
        m = self.m_reloc.match(reloc)
        sym = m.group(1)
        if sym == '.':
            sym = name
        inc = int(m.group(2) or 0)
        part = m.group(3)
        offset = self.base_address + offsets[sym] + inc
        addr = struct.pack("<H", offset)
        if part == ',lo':
            return addr[0:1]
        elif part == ',hi':
            return addr[1:2]
        return addr

    def link(self, fileobj):
        """Links the image, writing it out to a file."""
        # write out the prg header
        fileobj.write(prg_header)

        # write out the text sections, starting with our start symbol
        offsets = {}
        sym = self.symbols[self.start_symbol]
        offsets[self.start_symbol] = fileobj.tell() - 2
        fileobj.write(sym.attrs['text'])

        # the rest of the symbols
        for name, sym in self.symbols.items():
            if name == self.start_symbol:
                continue

            if 'text' in sym.attrs:
                offsets[name] = fileobj.tell() - 2
                fileobj.write(sym.attrs['text'])

                if 'return_addr' in sym.attrs:
                    addr = offsets[name] + sym.attrs['return_addr']
                    offsets[name + '/return_addr'] = addr

        # perform relocations
        for name, sym in self.symbols.items():
            if 'relocations' not in sym.attrs:
                continue

            for sym_off, reloc in sym.attrs['relocations']:
                fileobj.seek(offsets[name] + sym_off + 2)
                addr = self.compute_relocation(offsets, name, reloc)
                fileobj.write(addr)
