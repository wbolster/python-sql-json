.PHONY: all doc test lint dist upload

all: test lint

doc:
	python setup.py build_sphinx

test:
	pytest

lint:
	flake8 src/
	black --check src/* tests/*

dist:
	python setup.py sdist bdist_wheel

upload:
	twine upload dist/*
