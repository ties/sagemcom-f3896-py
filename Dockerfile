FROM python:3.11

WORKDIR /usr/src/app

ENV POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_IN_PROJECT=1 \
    POETRY_VIRTUALENVS_CREATE=1 \
    POETRY_CACHE_DIR=/tmp/poetry_cache

COPY pyproject.toml poetry.lock ./
RUN pip install --no-cache-dir poetry
RUN poetry install --without dev --no-root && rm -rf $POETRY_CACHE_DIR

COPY . .

RUN poetry install --without dev && rm -rf $POETRY_CACHE_DIR

EXPOSE 8080
CMD ["python", "-m", "poetry", "run", "python", "sagemcom_f3896_client/exporter.py", "-v"]
