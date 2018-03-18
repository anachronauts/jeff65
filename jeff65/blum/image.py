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
from ..gold import ast

# Header for PRG files. Identifies the load location in memory, in this case
# 0x0801, which is the load location for BASIC programs.
prg_header = bytes([0x01, 0x08])

exe_header = bytes([
    0x0b, 0x08,              # 0x0801:  pointer 0x080b to next line of BASIC
    0x00, 0x03,              # 0x0803:  BASIC line number (786) 0x0300
    0x9e,                    # 0x0805:  BASIC SYS token
    0x32, 0x30, 0x36, 0x31,  # 0x0806:  PETSCII for 2061 (0x080d)
    0x00, 0x00, 0x00,        # 0x0809:  padding
                             # 0x080d:  program text starts here
])


def make_startup_for(name):
    return ast.AstNode('unit', None, children=[
        ast.AstNode('fun_symbol', None, attrs={
            'name': '__start',
            'relocations': [
                # Relocations for the address of 'main'
                (0x000b, '{}.main'.format(name)),

                # Relocations for the address for 'main' to return to
                (0x0001, '.+13,lo'),
                (0x0006, '.+13,hi'),

                # Relocations for the return address slot for 'main'
                (0x0003, '{}.main/return_addr'.format(name)),
                (0x0008, '{}.main/return_addr+1'.format(name)),
            ],
            'text': bytes([
                0xa9, 0xff,        # 0x0000:  lda #$ff
                0x8d, 0xff, 0xff,  # 0x0002:  sta $ffff
                0xa9, 0xff,        # 0x0005:  lda #$ff
                0x8d, 0xff, 0xff,  # 0x0007:  sta $ffff
                0x4c, 0xff, 0xff,  # 0x000a:  jmp $ffff
                0x60,              # 0x000d:  rts
            ])
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
        assert offset < 0x10000
        lo = offset & 0xff
        hi = (offset >> 8) & 0xff
        if part == ',lo':
            return bytes([lo])
        elif part == ',hi':
            return bytes([hi])
        return bytes([lo, hi])

    def link(self, fileobj):
        """Links the image, writing it out to a file."""
        # write out the prg header
        fileobj.write(bytes([0x01, 0x08]))

        # write out the header
        fileobj.write(exe_header)

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
