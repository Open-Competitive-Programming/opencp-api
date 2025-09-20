# This makefile is used to quickly delete cached files and run tests

clean:
		find . -type d -name "__pycache__" -exec rm -rf {} +

test:
		pytest

