# Gold

Gold is a programming language (and cross-compiler) for the Commodore 64. Gold's
syntax is inspired by Lua. The compiler is implemented in Python 3 and generates
6502 assembly code. For now, the recommended assembler is ca65 (part of cc65),
which is capable of producing .d64 disk images.

Gold-lang is not associated with the Gold parser framework.

    usage: python3 -m compiler [-h] input_file

    positional arguments:
      input_file  the file to compile

    optional arguments:
      -h, --help  show this help message and exit

# Blum

Blum is an upcoming fantasy rouge-like (written in Gold) for the Commodore 64.