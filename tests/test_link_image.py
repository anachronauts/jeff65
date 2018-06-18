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
    archive = symbol.Archive()
    archive.symbols['$test.main'] = symbol.Symbol('text', b'')
    im, _ = link(
        image.make_startup_for('$test.main', 0x0001),
        archive)

    assert_equal(0x0810, im.compute_relocation('spam', '$test.main'))
    assert_equal(b'\x10\x08', im.compute_relocation('spam', '$test.main',
                                                    binary=True))


def test_image_relocation_forward():
    archive = symbol.Archive()
    archive.symbols['$test.main'] = symbol.Symbol('text', b'')
    im, _ = link(
        image.make_startup_for('$test.main', 0x0001),
        archive)

    assert_equal(0x0815, im.compute_relocation('spam', '$test.main+5'))
    assert_equal(b'\x15\x08', im.compute_relocation('spam', '$test.main+5',
                                                    binary=True))


def test_image_relocation_backward():
    archive = symbol.Archive()
    archive.symbols['$test.main'] = symbol.Symbol('text', b'')
    im, _ = link(
        image.make_startup_for('$test.main', 0x0001),
        archive)

    assert_equal(0x080b, im.compute_relocation('spam', '$test.main-5'))
    assert_equal(b'\x0b\x08', im.compute_relocation('spam', '$test.main-5',
                                                    binary=True))


def test_image_relocation_self():
    archive = symbol.Archive()
    archive.symbols['$test.main'] = symbol.Symbol('text', b'')
    im, _ = link(
        image.make_startup_for('$test.main', 0x0001),
        archive)

    assert_equal(0x0810, im.compute_relocation('$test.main', '.'))
    assert_equal(b'\x10\x08', im.compute_relocation('$test.main', '.',
                                                    binary=True))


def test_image_relocation_lo():
    archive = symbol.Archive()
    archive.symbols['$test.main'] = symbol.Symbol('text', b'')
    im, _ = link(
        image.make_startup_for('$test.main', 0x0001),
        archive)

    assert_equal(0x10, im.compute_relocation('spam', '$test.main,lo'))
    assert_equal(b'\x10', im.compute_relocation('spam', '$test.main,lo',
                                                binary=True))


def test_image_relocation_hi():
    archive = symbol.Archive()
    archive.symbols['$test.main'] = symbol.Symbol('text', b'')
    im, _ = link(
        image.make_startup_for('$test.main', 0x0001),
        archive)

    assert_equal(0x08, im.compute_relocation('spam', '$test.main,hi'))
    assert_equal(b'\x08', im.compute_relocation('spam', '$test.main,hi',
                                                binary=True))


def test_image_relocation_complex():
    archive = symbol.Archive()
    archive.symbols['$test.main'] = symbol.Symbol('text', b'')
    im, _ = link(
        image.make_startup_for('$test.main', 0x0001),
        archive)

    assert_equal(0x15, im.compute_relocation('spam', '$test.main+5,lo'))
    assert_equal(b'\x15', im.compute_relocation('spam', '$test.main+5,lo',
                                                binary=True))
