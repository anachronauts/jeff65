import functools
import os
import pathlib
import tempfile
from nose.tools import (assert_equal)
import jeff65
from . import vicectl


def compile_run_dump(path):
    """Gets a memory dump from running a given program.

    Compiles the given gold-syntax file, runs it in VICE, then dumps the
    emulator memory just before the program terminates, returning the memory as
    a bytes object.
    """
    try:
        fd, outpath = tempfile.mkstemp()
        os.close(fd)

        # perform the compilation. We don't shell out for this so that code
        # coverage works.
        jeff65.main(["compile", "-o", outpath, str(path)])

        # Run the program under VICE, and use the monitor to dump the machine
        # memory
        with vicectl.Vice(outpath, 0x0810) as vice:
            assert_equal(0x0810, vice.wait_for_break())
            mem = vice.dump()
            assert_equal(0x10000, len(mem))
            assert_equal(0, vice.quit())
            return mem

    finally:
        os.remove(outpath)


def with_dump_of(path):
    def _decorate_test(f):
        def _test_with_dump():
            fullpath = pathlib.Path(__file__).parent / path
            return f(compile_run_dump(fullpath))
        functools.update_wrapper(_test_with_dump, f)
        return _test_with_dump
    return _decorate_test


@with_dump_of("heart.gold")
def test_heart_gold(mem):
    # Check if there's a heart in the corner. reading from color RAM (0xd800)
    # doesn't actually produce anything useful, so we can't check that it's
    # red.
    assert_equal(0x53, mem[0x0400])
