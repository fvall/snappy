build:
	poetry build
test:
	python -m pytest tests/ --cov=snappy/
install:
	python -m pip install .
install-dev:
	poetry install --with dev
clean:
	poetry env remove --all
