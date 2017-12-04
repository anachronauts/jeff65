import argparse

from .parser import Parser
from .token import Token

def readinput(stream):
    line = 1
    column = 0
    while True:
        c = stream.read(1)
        if len(c) == 0:
            break
        yield (c, (line, column))
        if c == '\n':
            line += 1
            column = 0
        else:
            column += 1


def main():
    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("input_file", help="the file to compile")
    args = arg_parser.parse_args()
    input_file = open(args.input_file, 'r')
    parser = Parser(readinput(input_file))
    for tok in parser.scanner:
        print(tok)
        if tok[0] == Token.eof:
            break
    ast = parser.parse()
    print(repr(ast))
    input_file.close()


if __name__ == "__main__":
    main()