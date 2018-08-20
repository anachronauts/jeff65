.PHONY: all antlr check demo develop install

all:


install: all
	pip install .

develop: all
	pip install -Ur requirements.txt
	pip install -e .

check: all
	flake8 jeff65 tests
	python setup.py nosetests -a "!vice"

demo: examples/heart.prg
	x64 $<

examples/heart.prg: examples/heart.gold
	python -m jeff65 compile $<
