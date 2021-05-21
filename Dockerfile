FROM mcr.microsoft.com/playwright:focal

ENV POETRY_VIRTUALENVS_CREATE=false \
    PYTHONFAULTHANDLER=1 \
    PYTHONHASHSEED=random \
    PYTHONUNBUFFERED=1 \
    PIP_DEFAULT_TIMEOUT=100 \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_NO_CACHE_DIR=off

USER root

COPY . /app
WORKDIR /app

RUN apt install -y curl python3.9
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/get-poetry.py | POETRY_HOME=/usr/local/poetry python3.9
RUN /usr/local/poetry/bin/poetry install --no-dev --no-interaction --no-ansi
RUN /usr/local/poetry/bin/poetry run playwright install