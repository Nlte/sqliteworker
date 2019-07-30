install:
	pip install .

clean-build:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info

clean:
	flake8

test: 
	pytest -v

.PHONY: init test
