import collections
import logging
import os
import os.path
import pty
import subprocess
import struct
import tempfile
import threading
import time
import xvfbwrapper


logger = logging.getLogger(__name__)


class Vice:
    """Communicates with a VICE instance via the monitor."""

    def __init__(self, program, initbreak):
        # we don't want VICE windows popping up all over, so we'll go ahead and
        # start up a virtual framebuffer
        self.vdisplay = xvfbwrapper.Xvfb()
        self.vdisplay.start()

        # If we're using the GTK frontend for VICE on a Wayland system, this
        # forces it to actually use our framebuffer.
        env = dict(os.environ)
        env["GDK_BACKEND"] = "x11"

        # VICE refuses to activate the monitor unless it's connected to a TTY,
        # so we'll create a pseudoterminal to keep it happy. THIS IS VERY VERY
        # LINUX-ONLY RIGHT NOW, SORRY
        self.dom, sub = pty.openpty()
        self.proc = subprocess.Popen(
            ["x64", "-initbreak", str(initbreak), str(program)],
            stdin=sub,
            stdout=sub,
            stderr=subprocess.PIPE,
            env=env,
        )
        os.close(sub)

        # we could avoid having to pump stderr by just letting it attach to our
        # tty, but WOW is VICE noisy, so we'll log it instead
        t = threading.Thread(target=self._log_stderr)
        t.daemon = True
        t.start()

        self.linebuf = collections.deque()
        self.obuf = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    def _log_stderr(self):
        for line in iter(self.proc.stderr.readline, b""):
            logger.debug("VICE stderr: %s", line.decode())

    def _readline(self, cond=None):
        while (cond is None or not cond("".join(self.obuf))) and (
            len(self.linebuf) == 0 or self.proc.poll()
        ):
            block = os.read(self.dom, 4096).decode()
            left = 0
            while True:
                right = block.find("\n", left)
                if right == -1:
                    self.obuf.append(block[left:])
                    break
                self.obuf.append(block[left : right + 1])
                self.linebuf.append("".join(self.obuf))
                logger.debug("VICE stdout: %s", self.linebuf[-1])
                self.obuf.clear()
                left = right + 1

        if len(self.linebuf) > 0:
            return self.linebuf.popleft()
        return None

    def wait_for_break(self):
        while True:
            line = self._readline()
            if line.startswith(".C"):
                return int(line[3:7], 16)

    def dump(self, start=0, end=0x10000, timeout=5):
        try:
            fd, outpath = tempfile.mkstemp()
            os.close(fd)
            cmd = f'save "{outpath}" 0 {start:x} {end-1:x}\n'
            os.write(self.dom, cmd.encode())

            # wait for the prompt, because we have to keep the IO moving
            while self._readline(lambda line: line.startswith("(C:$")) is not None:
                pass

            # waiting for the prompt doesn't actually work -- VICE will happily
            # print out the prompt before it finishes writing the file. So
            # instead we wait until the file is the expected size. This is,
            # admittedly, terrible.
            starttime = time.perf_counter()
            while time.perf_counter() - starttime < timeout:
                time.sleep(0)
                if os.path.getsize(outpath) >= (end - start + 2):
                    break
            else:
                raise TimeoutError("VICE was too slow")

            with open(outpath, "rb") as f:
                hdr, = struct.unpack("<H", f.read(2))
                assert hdr == start, f"{hdr} != {start}"
                return f.read()
        finally:
            os.remove(outpath)

    def quit(self):
        os.write(self.dom, b"quit\n")
        return self.proc.wait()

    def close(self):
        if self.proc is not None:
            if self.proc.returncode is None:
                self.proc.kill()
            self.proc = None
        if self.dom is not None:
            os.close(self.dom)
            self.dom = None
        if self.vdisplay is not None:
            self.vdisplay.stop()
            self.vdisplay = None

    def __del__(self):
        self.close()
