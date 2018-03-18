.PHONY: all antlr check

all: antlr

antlr: jeff65/gold/grammar/Gold.py

jeff65/gold/grammar/Gold.py: jeff65/gold/grammar/Gold.g4
	antlr4 -Dlanguage=Python3 $^

check: all
	flake8 jeff65 tests
	nosetests
