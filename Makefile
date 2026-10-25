.PHONY: help install install-precommits install-kernel test run-streamlit run-hint-generation-streamlit build-docker run-docker

help:
	@echo "Relevant targets are 'install' and 'test'."

install:
	@uv sync
	@$(MAKE) install-precommits
	@$(MAKE) install-kernel

install-precommits:
	@uv run pre-commit install --overwrite --install-hooks

install-kernel:
	@uv run ipython kernel install --user --name=llm-math-education

jupyter:
	@uv run jupyter lab

test:
	@uv run pytest --cov=src --cov-report term-missing

build-docker:
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
	@uv run streamlit run src/🤖_Math_QA.py --

run-hint-generation-streamlit:
	@uv run streamlit run src/hint_generation/app.py --
