# jeff65 linker core functions
# Copyright (C) 2018  jeff65 maintainers
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

import os
import pathlib
import tempfile
from . import image


def link(name, archive, output_path):
    if not isinstance(output_path, pathlib.Path):
        output_path = pathlib.PurePath(output_path)

    # Create a temporary file to write to so that if we have a link error, we
    # don't clobber the existing program image. We create this in the same
    # directory to avoid cross-device renaming problems.
    im_fd, im_tmp = tempfile.mkstemp(prefix=output_path.name,
                                     dir=output_path.parent)
    try:
        with open(im_fd, 'wb') as im_file:
            im = image.Image(im_file)
            im.add_archive(image.make_startup_for(name, 0x0100))
            im.add_archive(archive)
            im.link()
        os.replace(im_tmp, output_path)
    except BaseException:
        # linking failed, remove the temporary file
        os.remove(im_tmp)
        raise
