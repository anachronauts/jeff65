.PHONY: all antlr check demo develop install

all: antlr

install: all
	pip install .

develop: all
	pip install -Ur requirements.txt
	pip install -e .

antlr: jeff65/gold/grammar/Gold.py

jeff65/gold/grammar/Gold.py: jeff65/gold/grammar/Gold.g4
	antlr4 -Dlanguage=Python3 $^

check: all
	flake8 jeff65 tests
	nosetests --with-coverage --cover-package jeff65 --cover-erase

demo: examples/heart.prg
	x64 $<

examples/heart.prg: examples/heart.gold
	python -m jeff65 $<
