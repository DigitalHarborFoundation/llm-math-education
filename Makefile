.PHONY: help install ensure-poetry install-precommits install-kernel test run-streamlit build-docker run-docker

help:
	@echo "Relevant targets are 'install' and 'test'."

install:
	@$(MAKE) ensure-poetry
	@$(MAKE) install-precommits
	@$(MAKE) install-kernel

ensure-poetry:
	@if [ "$(shell which poetry)" = "" ]; then \
		echo "Did you activate the outer conda environment? Run: conda activate llm-math-education"; \
		exit 1; \
	else \
		echo "Found existing Poetry installation at $(shell which poetry)."; \
	fi
	@poetry install

install-precommits:
	@poetry run pre-commit autoupdate
	@poetry run pre-commit install --overwrite --install-hooks

install-kernel:
	@poetry run ipython kernel install --user --name=llm-math-education

jupyter:
	@echo "Assuming Jupyter lab is installed and configured globally."
	@jupyter lab

test:
	@poetry run pytest --cov=src --cov-report term-missing

build-docker:
	@poetry build
	@poetry export --without-hashes --format=requirements.txt > streamlit-requirements.txt
	@docker build -t rori_streamlit -f Dockerfile.streamlit .

run-docker:
	@docker run \
	--name rori_streamlit_container \
	-p 8502:8502 \
	-v ./.env:/usr/app/.env \
	-v ./.streamlit:/usr/app/.streamlit \
	rori_streamlit:latest

remove-docker:
	@docker remove --volumes rori_streamlit_container

run-streamlit:
	@streamlit run src/🤖_Math_QA.py --
