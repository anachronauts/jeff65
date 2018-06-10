import io
from nose.tools import (
    assert_equal)
from jeff65.blum import symbol, types


def pack_by_type(t, obj):
    writer = symbol.ArchiveWriter()
    with io.BytesIO() as f:
        writer.dump_by_type(t, f, obj)
        return f.getvalue()


def unpack_by_type(t, bs):
    reader = symbol.ArchiveReader()
    _, val = reader.load_by_type(t, bs, 0)
    return val


def pack_constant(name, obj):
    writer = symbol.ArchiveWriter()
    with io.BytesIO() as f:
        writer.dump_constant(f, name, obj)
        return f.getvalue()


def unpack_entry(bs):
    reader = symbol.ArchiveReader()
    _, entry = reader.load_entry(bs, 0)
    return entry._name, entry


def test_pack_string():
    assert_equal(b'\x05\x00\x00\x00hello', pack_by_type('str', 'hello'))


def test_unpack_string():
    assert_equal('hello', unpack_by_type('str', b'\x05\x00\x00\x00hello'))


def test_pack_relocation():
    reloc = symbol.Relocation('spam', 0x42)
    assert_equal(
        b'\x03\x00sy\x04\x00\x00\x00spamic\x42\x00byw',
        pack_by_type('relocation', reloc))


def test_unpack_relocation():
    reloc = unpack_by_type(
        'relocation', b'\x03\x00sy\x04\x00\x00\x00spamic\x42\x00byw')
    assert_equal('spam', reloc.symbol)
    assert_equal(0x42, reloc.increment)
    assert_equal(symbol.Relocation.full, reloc.byte)


def test_pack_type_phantom():
    assert_equal(b'Ph\x00\x00', pack_by_type('type_info', types.phantom))


def test_unpack_type_phantom():
    assert_equal(types.phantom, unpack_by_type('type_info', b'Ph\x00\x00'))


def test_pack_type_void():
    assert_equal(b'Vd\x00\x00', pack_by_type('type_info', types.void))


def test_unpack_type_void():
    assert_equal(types.void, unpack_by_type('type_info', b'Vd\x00\x00'))


def test_pack_types_integral():
    assert_equal(
        b'In\x02\x00wd\x01sg\x00',
        pack_by_type('type_info', types.u8))
    assert_equal(
        b'In\x02\x00wd\x02sg\x00',
        pack_by_type('type_info', types.u16))
    assert_equal(
        b'In\x02\x00wd\x03sg\x00',
        pack_by_type('type_info', types.u24))
    assert_equal(
        b'In\x02\x00wd\x04sg\x00',
        pack_by_type('type_info', types.u32))
    assert_equal(
        b'In\x02\x00wd\x01sg\x01',
        pack_by_type('type_info', types.i8))
    assert_equal(
        b'In\x02\x00wd\x02sg\x01',
        pack_by_type('type_info', types.i16))
    assert_equal(
        b'In\x02\x00wd\x03sg\x01',
        pack_by_type('type_info', types.i24))
    assert_equal(
        b'In\x02\x00wd\x04sg\x01',
        pack_by_type('type_info', types.i32))


def test_unpack_types_integral():
    assert_equal(
        types.u8,
        unpack_by_type('type_info', b'In\x02\x00wd\x01sg\x00'))
    assert_equal(
        types.u16,
        unpack_by_type('type_info', b'In\x02\x00wd\x02sg\x00'))
    assert_equal(
        types.u24,
        unpack_by_type('type_info', b'In\x02\x00wd\x03sg\x00'))
    assert_equal(
        types.u32,
        unpack_by_type('type_info', b'In\x02\x00wd\x04sg\x00'))
    assert_equal(
        types.i8,
        unpack_by_type('type_info', b'In\x02\x00wd\x01sg\x01'))
    assert_equal(
        types.i16,
        unpack_by_type('type_info', b'In\x02\x00wd\x02sg\x01'))
    assert_equal(
        types.i24,
        unpack_by_type('type_info', b'In\x02\x00wd\x03sg\x01'))
    assert_equal(
        types.i32,
        unpack_by_type('type_info', b'In\x02\x00wd\x04sg\x01'))


def test_pack_type_ref():
    assert_equal(
        b'Rf\x01\x00tgPh\x00\x00',
        pack_by_type('type_info', types.ptr))
    assert_equal(
        b'Rf\x01\x00tgIn\x02\x00wd\x02sg\x01',
        pack_by_type('type_info', types.RefType(types.i16)))
    assert_equal(
        b'Rf\x01\x00tgRf\x01\x00tgIn\x02\x00wd\x02sg\x01',
        pack_by_type('type_info', types.RefType(types.RefType(types.i16))))


def test_unpack_type_ref():
    assert_equal(
        types.ptr,
        unpack_by_type('type_info', b'Rf\x01\x00tgPh\x00\x00'))
    assert_equal(
        types.RefType(types.i16),
        unpack_by_type('type_info', b'Rf\x01\x00tgIn\x02\x00wd\x02sg\x01'))
    assert_equal(
        types.RefType(types.RefType(types.i16)),
        unpack_by_type('type_info',
                       b'Rf\x01\x00tgRf\x01\x00tgIn\x02\x00wd\x02sg\x01'))


def test_pack_type_fun():
    assert_equal(
        b'Fn\x02\x00rtVd\x00\x00as\x00\x00\x00\x00',
        pack_by_type('type_info', types.FunctionType(types.void)))
    assert_equal(
        b'Fn\x02\x00' +
        b'rtIn\x02\x00wd\x02sg\x00' +
        b'as\x02\x00\x00\x00' +
        b'In\x02\x00wd\x01sg\x01' +
        b'Rf\x01\x00tgIn\x02\x00wd\x03sg\x00',
        pack_by_type('type_info', types.FunctionType(
            types.u16, types.i8, types.RefType(types.u24))))


def test_unpack_type_fun():
    assert_equal(
        types.FunctionType(types.void),
        unpack_by_type('type_info',
                       b'Fn\x02\x00rtVd\x00\x00as\x00\x00\x00\x00'))
    assert_equal(
        types.FunctionType(types.u16, types.i8, types.RefType(types.u24)),
        unpack_by_type(
            'type_info',
            b'Fn\x02\x00' +
            b'rtIn\x02\x00wd\x02sg\x00' +
            b'as\x02\x00\x00\x00' +
            b'In\x02\x00wd\x01sg\x01' +
            b'Rf\x01\x00tgIn\x02\x00wd\x03sg\x00'))


def test_pack_constant():
    assert_equal(
        b'Cn\x03\x00nm\x04\x00\x00\x00spam' +
        b'tyIn\x02\x00wd\x01sg\x01' +
        b'vl\xf9\xff\xff\xff\xff\xff\xff\xff',
        pack_constant('spam', symbol.Constant(-7, types.i8)))
    assert_equal(
        b'Cn\x03\x00nm\x04\x00\x00\x00eggs' +
        b'tyRf\x01\x00tgIn\x02\x00wd\x03sg\x00' +
        b'vl\xfe\xca\x00\x00\x00\x00\x00\x00',
        pack_constant('eggs',
                      symbol.Constant(0xcafe, types.RefType(types.u24))))


def test_unpack_constant():
    assert_equal(
        ('spam', symbol.Constant(-7, types.i8)),
        unpack_entry(
            b'Cn\x03\x00nm\x04\x00\x00\x00spam' +
            b'tyIn\x02\x00wd\x01sg\x01' +
            b'vl\xf9\xff\xff\xff\xff\xff\xff\xff'))
    assert_equal(
        ('eggs', symbol.Constant(0xcafe, types.RefType(types.u24))),
        unpack_entry(
            b'Cn\x03\x00nm\x04\x00\x00\x00eggs' +
            b'tyRf\x01\x00tgIn\x02\x00wd\x03sg\x00' +
            b'vl\xfe\xca\x00\x00\x00\x00\x00\x00'))


def test_pack_symbol():
    archive = symbol.Archive()
    archive.symbols['eggs'] = symbol.Symbol(
        section='text',
        data=b'spam',
        type_info=types.u32,
        relocations={
            0xcafe: symbol.Relocation('beans', 7)
        })
    writer = symbol.ArchiveWriter()
    with io.BytesIO() as f:
        writer.dump(archive, f)
        assert_equal(
            b'\x93Blm\x0d\x0a\x1a\x0a\x01\x00\x00\x00Sy\x05\x00' +
            b'nm\x04\x00\x00\x00eggs' +
            b'sc\x04\x00\x00\x00text' +
            b'tyIn\x02\x00wd\x04sg\x00' +
            b're\x01\x00\x00\x00\xfe\xca' +
            b'\x03\x00sy\x05\x00\x00\x00beansic\x07\x00byw' +
            b'da\x54\x00\x00\x00\x04\x00' +
            b'spam',
            f.getvalue())


def test_unpack_symbol():
    data = (b'\x93Blm\x0d\x0a\x1a\x0a\x01\x00\x00\x00Sy\x05\x00' +
            b'nm\x04\x00\x00\x00eggs' +
            b'sc\x04\x00\x00\x00text' +
            b'tyIn\x02\x00wd\x04sg\x00' +
            b're\x01\x00\x00\x00\xfe\xca' +
            b'\x03\x00sy\x05\x00\x00\x00beansic\x07\x00byw' +
            b'da\x54\x00\x00\x00\x04\x00' +
            b'spam')
    reader = symbol.ArchiveReader()
    reader.loadb(data)
    assert_equal(['eggs'], list(reader.archive.symbols))
    sym = reader.archive.symbols['eggs']
    assert_equal('text', sym.section)
    assert_equal(b'spam', sym.data)
    assert_equal(types.u32, sym.type_info)
    assert_equal([0xcafe], list(sym.relocations))
    reloc = sym.relocations[0xcafe]
    assert_equal('beans', reloc.symbol)
    assert_equal(7, reloc.increment)
    assert_equal(symbol.Relocation.full, reloc.byte)
