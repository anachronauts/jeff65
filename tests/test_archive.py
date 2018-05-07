import io
from nose.tools import (
    assert_equal)
from jeff65.blum import symbol, types


def pack_by_type(t, obj):
    writer = symbol.ArchiveWriter()
    with io.BytesIO() as f:
        writer.dump_by_type(t, f, obj)
        return f.getvalue()


def pack_constant(name, obj):
    writer = symbol.ArchiveWriter()
    with io.BytesIO() as f:
        writer.dump_constant(f, name, obj)
        return f.getvalue()


def test_pack_string():
    assert_equal(b'\x05\x00\x00\x00hello', pack_by_type('str', 'hello'))


def test_pack_relocation():
    reloc = symbol.Relocation('spam', 0x42)
    assert_equal(
        b'\x03\x00sy\x04\x00\x00\x00spamic\x42\x00byw',
        pack_by_type('relocation', reloc))


def test_pack_type_phantom():
    assert_equal(b'Ph\x00\x00', pack_by_type('type_info', types.phantom))


def test_pack_type_void():
    assert_equal(b'Vd\x00\x00', pack_by_type('type_info', types.void))


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


def test_pack_symbol():
    archive = symbol.Archive()
    archive.symbols['eggs'] = symbol.Symbol('text', b'spam', types.u32)
    writer = symbol.ArchiveWriter()
    with io.BytesIO() as f:
        writer.dump(archive, f)
        assert_equal(
            b'\x93Blm\x0d\x0a\x1a\x0a\x01\x00\x00\x00Sy\x05\x00' +
            b'nm\x04\x00\x00\x00eggs' +
            b'sc\x04\x00\x00\x00text' +
            b'tyIn\x02\x00wd\x04sg\x00' +
            b're\x00\x00\x00\x00' +
            b'da\x3e\x00\x00\x00\x04\x00' +
            b'spam',
            f.getvalue())
