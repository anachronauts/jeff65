import argparse
import sys

from . import lexer, ast

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("input_file", help="the file to compile")
args = arg_parser.parse_args()


def open_input(name):
    if name == "-":
        return sys.stdin
    return open(name, 'r')


with open_input(args.input_file) as input_file:
    tree = ast.parse_all(lexer.lex(input_file))
    print(tree)
