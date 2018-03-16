.PHONY: all antlr

all: antlr

antlr: jeff65/gold/grammar/Gold.g4
	antlr4 -Dlanguage=Python3 $^
