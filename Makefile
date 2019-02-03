.PHONY: check checkall demo democlean develop format install _check _checkall _format

check:
	pipenv run make _check

checkall:
	pipenv run make _checkall

format:
	pipenv run make _format

_check:
	black --check --diff src tests
	flake8 src tests
	nosetests -a "!vice"

_checkall:
	black --check --diff src tests
	flake8 src tests
	nosetests

_format:
	black src tests

install:
	pipenv sync

develop:
	pipenv sync --dev

demo: examples/heart.prg
	x64 $<

democlean:
	-rm examples/*.blum examples/*.prg

examples/heart.prg: examples/heart.gold
	pipenv run jeff65 compile $<
