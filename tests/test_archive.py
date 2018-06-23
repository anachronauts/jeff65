import io
import struct
import zlib
from hypothesis import given
import hypothesis.strategies as hs
from nose.tools import (
    assert_equal)
from jeff65.blum import symbol, types
from jeff65.blum.fmt import Fmt


def pack_by_type(t, obj):
    with io.BytesIO() as f:
        with symbol.ArchiveWriter(f, closefd=False) as writer:
            writer.dump_by_type(t, obj)
            return f.getvalue()


def unpack_by_type(t, bs):
    with io.BytesIO(bs) as f:
        with symbol.ArchiveReader(f, closefd=False) as reader:
            end, val = reader.load_by_type(t, 0)
            assert_equal(len(bs), end)
            return val


def unpack_entry(bs):
    reader = symbol.ArchiveReader()
    _, entry = reader.load_entry(bs, 0)
    return entry._name, entry


def generate_packed_string(s):
    enc = s.encode('utf8')
    data = struct.pack('<l', len(enc)) + enc
    return data


@given(hs.text(max_size=symbol.MAX_STRING_SIZE))
def test_pack_string(s):
    packed = generate_packed_string(s)
    assert_equal(packed, pack_by_type(Fmt.str, s))


@given(hs.text(max_size=symbol.MAX_STRING_SIZE))
def test_unpack_uncompressed_string(s):
    packed = generate_packed_string(s)
    assert_equal(s, unpack_by_type(Fmt.str, packed))


@given(hs.text(max_size=symbol.MAX_STRING_SIZE))
def test_unpack_compressed_string(s):
    enc = zlib.compress(s.encode('utf8'))
    packed = struct.pack('<l', -len(enc)) + enc
    assert_equal(s, unpack_by_type(Fmt.str, packed))


@given(hs.text(max_size=symbol.MAX_STRING_SIZE))
def test_roundtrip_string(s):
    packed = pack_by_type(Fmt.str, s)
    unpacked = unpack_by_type(Fmt.str, packed)
    assert_equal(s, unpacked)


def test_pack_relocation():
    reloc = symbol.Relocation('spam', 0x42)
    packed = pack_by_type(Fmt.struct(symbol.Relocation), reloc)
    assert_equal(
        b'\x03\x00sy\x04\x00\x00\x00spamic\x42\x00byw',
        packed)


def test_unpack_relocation():
    reloc = unpack_by_type(
        Fmt.struct(symbol.Relocation),
        b'\x03\x00sy\x04\x00\x00\x00spamic\x42\x00byw')
    assert_equal('spam', reloc.symbol)
    assert_equal(0x42, reloc.increment)
    assert_equal(symbol.Relocation.full, reloc.byte)


@hs.composite
def relocations(draw):
    return symbol.Relocation(
        draw(hs.text(max_size=symbol.MAX_STRING_SIZE)),
        draw(hs.integers(min_value=-(1 << 15), max_value=(1 << 15)-1)),
        draw(hs.sampled_from([symbol.Relocation.full,
                              symbol.Relocation.hi,
                              symbol.Relocation.lo])))


@given(relocations())
def test_roundtrip_relocation(reloc):
    t = Fmt.struct(symbol.Relocation)
    packed = pack_by_type(t, reloc)
    unpacked = unpack_by_type(t, packed)
    assert_equal(reloc, unpacked)


def test_pack_type_phantom():
    assert_equal(b'Ph\x00\x00',
                 pack_by_type(types.fmt_type_info, types.phantom))


def test_unpack_type_phantom():
    assert_equal(types.phantom,
                 unpack_by_type(types.fmt_type_info, b'Ph\x00\x00'))


def test_pack_type_void():
    assert_equal(b'Vd\x00\x00', pack_by_type(types.fmt_type_info, types.void))


def test_unpack_type_void():
    assert_equal(types.void,
                 unpack_by_type(types.fmt_type_info, b'Vd\x00\x00'))


def test_pack_types_integral():
    assert_equal(
        b'In\x02\x00wd\x01sg\x00',
        pack_by_type(types.fmt_type_info, types.u8))
    assert_equal(
        b'In\x02\x00wd\x02sg\x00',
        pack_by_type(types.fmt_type_info, types.u16))
    assert_equal(
        b'In\x02\x00wd\x03sg\x00',
        pack_by_type(types.fmt_type_info, types.u24))
    assert_equal(
        b'In\x02\x00wd\x04sg\x00',
        pack_by_type(types.fmt_type_info, types.u32))
    assert_equal(
        b'In\x02\x00wd\x01sg\x01',
        pack_by_type(types.fmt_type_info, types.i8))
    assert_equal(
        b'In\x02\x00wd\x02sg\x01',
        pack_by_type(types.fmt_type_info, types.i16))
    assert_equal(
        b'In\x02\x00wd\x03sg\x01',
        pack_by_type(types.fmt_type_info, types.i24))
    assert_equal(
        b'In\x02\x00wd\x04sg\x01',
        pack_by_type(types.fmt_type_info, types.i32))


def test_unpack_types_integral():
    assert_equal(
        types.u8,
        unpack_by_type(types.fmt_type_info, b'In\x02\x00wd\x01sg\x00'))
    assert_equal(
        types.u16,
        unpack_by_type(types.fmt_type_info, b'In\x02\x00wd\x02sg\x00'))
    assert_equal(
        types.u24,
        unpack_by_type(types.fmt_type_info, b'In\x02\x00wd\x03sg\x00'))
    assert_equal(
        types.u32,
        unpack_by_type(types.fmt_type_info, b'In\x02\x00wd\x04sg\x00'))
    assert_equal(
        types.i8,
        unpack_by_type(types.fmt_type_info, b'In\x02\x00wd\x01sg\x01'))
    assert_equal(
        types.i16,
        unpack_by_type(types.fmt_type_info, b'In\x02\x00wd\x02sg\x01'))
    assert_equal(
        types.i24,
        unpack_by_type(types.fmt_type_info, b'In\x02\x00wd\x03sg\x01'))
    assert_equal(
        types.i32,
        unpack_by_type(types.fmt_type_info, b'In\x02\x00wd\x04sg\x01'))


def test_pack_type_ref():
    assert_equal(
        b'Rf\x01\x00tgPh\x00\x00',
        pack_by_type(types.fmt_type_info, types.ptr))
    assert_equal(
        b'Rf\x01\x00tgIn\x02\x00wd\x02sg\x01',
        pack_by_type(types.fmt_type_info, types.RefType(types.i16)))
    assert_equal(
        b'Rf\x01\x00tgRf\x01\x00tgIn\x02\x00wd\x02sg\x01',
        pack_by_type(types.fmt_type_info,
                     types.RefType(types.RefType(types.i16))))


def test_unpack_type_ref():
    assert_equal(
        types.ptr,
        unpack_by_type(types.fmt_type_info, b'Rf\x01\x00tgPh\x00\x00'))
    assert_equal(
        types.RefType(types.i16),
        unpack_by_type(types.fmt_type_info,
                       b'Rf\x01\x00tgIn\x02\x00wd\x02sg\x01'))
    assert_equal(
        types.RefType(types.RefType(types.i16)),
        unpack_by_type(types.fmt_type_info,
                       b'Rf\x01\x00tgRf\x01\x00tgIn\x02\x00wd\x02sg\x01'))


def test_pack_type_fun():
    assert_equal(
        b'Fn\x02\x00rtVd\x00\x00as\x00\x00\x00\x00',
        pack_by_type(types.fmt_type_info, types.FunctionType(types.void)))
    assert_equal(
        b'Fn\x02\x00' +
        b'rtIn\x02\x00wd\x02sg\x00' +
        b'as\x02\x00\x00\x00' +
        b'In\x02\x00wd\x01sg\x01' +
        b'Rf\x01\x00tgIn\x02\x00wd\x03sg\x00',
        pack_by_type(types.fmt_type_info, types.FunctionType(
            types.u16, types.i8, types.RefType(types.u24))))


def test_unpack_type_fun():
    assert_equal(
        types.FunctionType(types.void),
        unpack_by_type(types.fmt_type_info,
                       b'Fn\x02\x00rtVd\x00\x00as\x00\x00\x00\x00'))
    assert_equal(
        types.FunctionType(types.u16, types.i8, types.RefType(types.u24)),
        unpack_by_type(
            types.fmt_type_info,
            b'Fn\x02\x00' +
            b'rtIn\x02\x00wd\x02sg\x00' +
            b'as\x02\x00\x00\x00' +
            b'In\x02\x00wd\x01sg\x01' +
            b'Rf\x01\x00tgIn\x02\x00wd\x03sg\x00'))


@hs.composite
def type_infos(draw):
    @hs.composite
    def integral_types(draw):
        return types.IntType(
            draw(hs.integers(min_value=1, max_value=4)),
            draw(hs.booleans()))

    @hs.composite
    def ref_types(draw, tys):
        return types.RefType(draw(tys))

    @hs.composite
    def fun_types(draw, tys):
        return types.FunctionType(
            draw(tys),
            *draw(hs.lists(tys)))

    return draw(hs.recursive(
        hs.sampled_from([types.phantom, types.void]) | integral_types(),
        lambda children: ref_types(children) | fun_types(children)))


@given(type_infos())
def test_roundtrip_type(ty):
    packed = pack_by_type(types.fmt_type_info, ty)
    unpacked = unpack_by_type(types.fmt_type_info, packed)
    assert_equal(ty, unpacked)


simple_archive = (
    # 0+8: magic
    b'\x93Blm\x0d\x0a\x1a\x0a' +
    # 8+c: e0 offset, e0 len, e0 crc
    b'\x5c\x00\x00\x00\x20\x00\x00\x00\xea\x9c\xfa\xc1' +
    # 14+4: blob0
    b'spam' +
    # 18+4: union+struct info
    b'Sy\x04\x00' +
    # 1c+a: Sy.sc field
    b'sc\x04\x00\x00\x00text' +
    # 26+c: Sy.ty field w/ In union+struct
    b'tyIn\x02\x00wd\x04sg\x00' +
    # 32+a: Sy.re field w/ key and Re struct info
    b're\x01\x00\x00\x00\xfe\xca\x03\x00'
    # 3c+b: Re.sy field
    b'sy\x05\x00\x00\x00beans'
    # 47+7: Re.ic, Re.by fields
    b'ic\x07\x00byw' +
    # 4e+e: Sy.da field
    b'da\x14\x00\x00\x00\x04\x00\x00\x00\x3d\xff\xda\x43' +
    # 5c+c: e0 ...
    b'\x18\x00\x00\x00\x44\x00\x00\x00\x0eu\xf1N' +
    # 68+c: ... e0 ...
    b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' +
    # 74+8: ... e0
    b'\x04\x00\x00\x00eggs')


@hs.composite
def archives(draw):
    @hs.composite
    def symbols(draw):
        return symbol.Symbol(
            section=draw(hs.text()),
            data=draw(hs.binary()),
            type_info=draw(type_infos()),
            relocations=draw(hs.dictionaries(
                hs.integers(min_value=0, max_value=0xffff),
                relocations())))

    archive = symbol.Archive()
    archive.symbols = draw(hs.dictionaries(
        hs.text(),
        symbols()))
    return archive


def test_pack_archive():
    archive = symbol.Archive()
    archive.symbols['eggs'] = symbol.Symbol(
        section='text',
        data=b'spam',
        type_info=types.u32,
        relocations={
            0xcafe: symbol.Relocation('beans', 7)
        })
    with io.BytesIO() as f:
        archive.dump(f)
        assert_equal(simple_archive, f.getvalue())


def test_unpack_archive():
    with io.BytesIO(simple_archive) as f:
        archive = symbol.Archive(f)
    assert_equal(['eggs'], list(archive.symbols))
    sym = archive.symbols['eggs']
    assert_equal('text', sym.section)
    assert_equal(b'spam', sym.data)
    assert_equal(types.u32, sym.type_info)
    assert_equal([0xcafe], list(sym.relocations))
    reloc = sym.relocations[0xcafe]
    assert_equal('beans', reloc.symbol)
    assert_equal(7, reloc.increment)
    assert_equal(symbol.Relocation.full, reloc.byte)


@given(archives())
def test_roundtrip_archive(a):
    with io.BytesIO() as f:
        a.dump(f)
        packed = f.getvalue()

    with io.BytesIO(packed) as f:
        unpacked = symbol.Archive(f)

    assert_equal(a.symbols, unpacked.symbols)
