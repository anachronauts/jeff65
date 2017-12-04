#!/bin/sh

# if python3 is not available, we use 'python' and hope for the best
if command -v python3 >/dev/null 2>&1
then PYTHON=python3
else PYTHON=python
fi

$PYTHON -m compiler $*
