import os
import pathlib
import sys
import tempfile
import pytest
import jeff65


def compile_run_dump(path):
    """Gets a memory dump from running a given program.

    Compiles the given gold-syntax file, runs it in VICE, then dumps the
    emulator memory just before the program terminates, returning the memory as
    a bytes object.
    """

    # This doesn't work on all platforms, so we import it locally to give the
    # decorator a chance to decide if we're even going to run the test.
    import vicectl

    try:
        fd, outpath = tempfile.mkstemp()
        os.close(fd)

        # perform the compilation. We don't shell out for this so that code
        # coverage works.
        jeff65.main(["compile", "-o", outpath, str(path)])

        # Run the program under VICE, and use the monitor to dump the machine
        # memory
        with vicectl.Vice(outpath, 0x0810) as vice:
            assert vice.wait_for_break() == 0x0810
            mem = vice.dump()
            assert len(mem) == 0x10000
            assert vice.quit() == 0
            return mem

    finally:
        os.remove(outpath)


@pytest.fixture
def mem_dump(path):
    if sys.platform != "linux":
        pytest.skip("VICE-based tests are Linux-only")

    fullpath = pathlib.Path(__file__).parent / path
    return compile_run_dump(fullpath)


@pytest.mark.vice
@pytest.mark.parametrize("path", ["heart.gold"])
def test_heart_gold(mem_dump):
    # Check if there's a heart in the corner. reading from color RAM (0xd800)
    # doesn't actually produce anything useful, so we can't check that it's
    # red.
    assert mem_dump[0x0400] == 0x53
