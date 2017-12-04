import argparse

from . import lexer, parser

arg_parser = argparse.ArgumentParser()
arg_parser.add_argument("input_file", help="the file to compile")
args = arg_parser.parse_args()

with open(args.input_file, 'r') as input_file:
    for ast in parser.parse(lexer.lex(input_file)):
        print(repr(ast))
