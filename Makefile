RUNTEST=python -m unittest -v -b
TESTS=$(wildcard tests/*.py)

install:
	pip install .

clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

clean:
	flake8

test: $(TESTS)
	@echo $^
	${RUNTEST} $^

.PHONY: init test
