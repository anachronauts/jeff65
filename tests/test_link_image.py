import io
from nose.tools import assert_equal
from jeff65.blum import image, symbol, types


def link(*archives):
    with io.BytesIO() as fileobj:
        im = image.Image(fileobj)
        for archive in archives:
            im.add_archive(archive)
        im.link()
        return (im, fileobj.getvalue())


def test_empty_image():
    archive = symbol.Archive()
    archive.symbols["$startup.__start"] = symbol.Symbol("startup", b"", types.phantom)
    _, bs = link(archive)
    assert_equal(bytes([0x01, 0x08]), bs)


def test_image_with_startup():
    archive = symbol.Archive()
    archive.symbols["$test.main"] = symbol.Symbol("text", b"", types.FunctionType(None))
    _, bs = link(image.make_startup_for("$test.main", 0x0001), archive)
    assert_equal(
        bytes(
            [
                0x01,
                0x08,  # .prg header
                0x0B,
                0x08,  # addr of next BASIC line
                0x01,
                0x00,  # number of BASIC line
                0x9E,
                0x32,
                0x30,
                0x36,
                0x31,
                0x00,  # SYS2061
                0x00,
                0x00,  # BASIC end-of-program
                0x20,
                0x11,
                0x08,  # jsr $0811
                0x60,  # rts
            ]
        ),
        bs,
    )


def test_image_relocation_simple():
    base_address = 0xCA00
    offsets = {"eggs": 0x00FE, "spam": 0x00CA}

    reloc = symbol.Relocation("eggs").bind("spam")
    assert_equal(0xCAFE, reloc.compute_value(base_address, offsets))
    assert_equal(b"\xfe\xca", reloc.compute_bin(base_address, offsets))


def test_image_relocation_forward():
    base_address = 0xCA00
    offsets = {"eggs": 0x00FE, "spam": 0x00CA}

    reloc = symbol.Relocation("eggs", 2).bind("spam")
    assert_equal(0xCB00, reloc.compute_value(base_address, offsets))
    assert_equal(b"\x00\xcb", reloc.compute_bin(base_address, offsets))


def test_image_relocation_backward():
    base_address = 0xCA00
    offsets = {"eggs": 0x00FE, "spam": 0x00CA}

    reloc = symbol.Relocation("eggs", -2).bind("spam")
    assert_equal(0xCAFC, reloc.compute_value(base_address, offsets))
    assert_equal(b"\xfc\xca", reloc.compute_bin(base_address, offsets))


def test_image_relocation_self():
    base_address = 0xCA00
    offsets = {"eggs": 0x00FE, "spam": 0x00CA}

    reloc = symbol.Relocation(None).bind("spam")
    assert_equal(0xCACA, reloc.compute_value(base_address, offsets))
    assert_equal(b"\xca\xca", reloc.compute_bin(base_address, offsets))


def test_image_relocation_lo():
    base_address = 0xCA00
    offsets = {"eggs": 0x00FE, "spam": 0x00CA}

    reloc = symbol.Relocation("eggs", byte=symbol.Relocation.lo).bind("spam")
    assert_equal(0xFE, reloc.compute_value(base_address, offsets))
    assert_equal(b"\xfe", reloc.compute_bin(base_address, offsets))


def test_image_relocation_hi():
    base_address = 0xCA00
    offsets = {"eggs": 0x00FE, "spam": 0x00CA}

    reloc = symbol.Relocation("eggs", byte=symbol.Relocation.hi).bind("spam")
    assert_equal(0xCA, reloc.compute_value(base_address, offsets))
    assert_equal(b"\xca", reloc.compute_bin(base_address, offsets))


def test_image_relocation_complex():
    base_address = 0xCA00
    offsets = {"eggs": 0x00FE, "spam": 0x00CA}

    reloc = symbol.Relocation("eggs", -2, symbol.Relocation.lo).bind("spam")
    assert_equal(0xFC, reloc.compute_value(base_address, offsets))
    assert_equal(b"\xfc", reloc.compute_bin(base_address, offsets))
