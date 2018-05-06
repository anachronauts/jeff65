import io
from nose.tools import (
    assert_equal)
from jeff65.blum import image, symbol


def link(*archives):
    with io.BytesIO() as fileobj:
        im = image.Image(fileobj)
        for archive in archives:
            im.add_archive(archive)
        im.link()
        return (im, fileobj.getvalue())


def test_empty_image():
    archive = symbol.Archive()
    archive.symbols['$startup.__start'] = symbol.Symbol('startup', b'')
    _, bs = link(archive)
    assert_equal(bytes([0x01, 0x08]), bs)


def test_image_with_startup():
    archive = symbol.Archive()
    archive.symbols['$test.main'] = symbol.Symbol('text', b'')
    _, bs = link(
        image.make_startup_for('$test.main', 0x0001),
        archive)
    assert_equal(bytes([
        0x01, 0x08,  # .prg header
        0x0b, 0x08,  # addr of next BASIC line
        0x01, 0x00,  # number of BASIC line
        0x9e, 0x32, 0x30, 0x36, 0x31, 0x00,  # SYS2061
        0x00, 0x00,  # BASIC end-of-program
        0x4c, 0x10, 0x08,  # jmp $0810
    ]), bs)


def test_image_relocation_simple():
    base_address = 0xca00
    offsets = {'eggs': 0x00fe, 'spam': 0x00ca}

    reloc = symbol.Relocation('eggs').bind('spam')
    assert_equal(0xcafe, reloc.compute_value(base_address, offsets))
    assert_equal(b'\xfe\xca', reloc.compute_bin(base_address, offsets))


def test_image_relocation_forward():
    base_address = 0xca00
    offsets = {'eggs': 0x00fe, 'spam': 0x00ca}

    reloc = symbol.Relocation('eggs', 2).bind('spam')
    assert_equal(0xcb00, reloc.compute_value(base_address, offsets))
    assert_equal(b'\x00\xcb', reloc.compute_bin(base_address, offsets))


def test_image_relocation_backward():
    base_address = 0xca00
    offsets = {'eggs': 0x00fe, 'spam': 0x00ca}

    reloc = symbol.Relocation('eggs', -2).bind('spam')
    assert_equal(0xcafc, reloc.compute_value(base_address, offsets))
    assert_equal(b'\xfc\xca', reloc.compute_bin(base_address, offsets))


def test_image_relocation_self():
    base_address = 0xca00
    offsets = {'eggs': 0x00fe, 'spam': 0x00ca}

    reloc = symbol.Relocation(None).bind('spam')
    assert_equal(0xcaca, reloc.compute_value(base_address, offsets))
    assert_equal(b'\xca\xca', reloc.compute_bin(base_address, offsets))


def test_image_relocation_lo():
    base_address = 0xca00
    offsets = {'eggs': 0x00fe, 'spam': 0x00ca}

    reloc = symbol.Relocation('eggs', byte=symbol.Relocation.lo).bind('spam')
    assert_equal(0xfe, reloc.compute_value(base_address, offsets))
    assert_equal(b'\xfe', reloc.compute_bin(base_address, offsets))


def test_image_relocation_hi():
    base_address = 0xca00
    offsets = {'eggs': 0x00fe, 'spam': 0x00ca}

    reloc = symbol.Relocation('eggs', byte=symbol.Relocation.hi).bind('spam')
    assert_equal(0xca, reloc.compute_value(base_address, offsets))
    assert_equal(b'\xca', reloc.compute_bin(base_address, offsets))


def test_image_relocation_complex():
    base_address = 0xca00
    offsets = {'eggs': 0x00fe, 'spam': 0x00ca}

    reloc = symbol.Relocation('eggs', -2, symbol.Relocation.lo).bind('spam')
    assert_equal(0xfc, reloc.compute_value(base_address, offsets))
    assert_equal(b'\xfc', reloc.compute_bin(base_address, offsets))
