.PHONY: install lint format run test

install:
	conda env create -f environment.yml

format:
	python -m black gamescout/

lint:
	python -m flake8 gamescout/
	python -m black --check gamescout/

run:
	python -m gamescout.main

test:
	python -m pytest tests/