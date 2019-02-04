.PHONY: check checkall demo democlean develop format install _check _checkall _format

check:
	poetry run make _check

checkall:
	poetry run make _checkall

format:
	poetry run make _format

_check:
	black --check --diff src tests
	flake8 src tests
	pytest tests --cov=jeff65 --cov-config=tox.ini -m "not vice"

_checkall:
	black --check --diff src tests
	flake8 src tests
	pytest tests --cov=jeff65 --cov-config=tox.ini

_format:
	black src tests

install:
	poetry install --no-dev

develop:
	poetry install

demo: examples/heart.prg
	x64 $<

democlean:
	-rm examples/*.blum examples/*.prg

examples/heart.prg: examples/heart.gold
	poetry run jeff65 compile $<
