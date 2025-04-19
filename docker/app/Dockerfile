FROM python:3.12.6-bookworm as python-base
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYSETUP_PATH="/opt/pysetup" \
    VENV_PATH="/opt/pysetup/.venv"

ENV PATH="$POETRY_HOME/bin:$VENV_PATH/bin:$PATH"

ENV WAIT_VERSION 2.11.0
ADD https://github.com/ufoscout/docker-compose-wait/releases/download/$WAIT_VERSION/wait /wait
RUN chmod +x /wait
COPY docker/app/wait-for-postgres.sh /wait-for-postgres.sh
RUN chmod +x /wait-for-postgres.sh


FROM python-base as builder-base
RUN apt-get update \
    && apt-get install --no-install-recommends -y \
        curl \
        build-essential

ENV POETRY_VERSION=2.1.1
RUN curl -sSL https://install.python-poetry.org | python3 -

WORKDIR $PYSETUP_PATH
COPY ./poetry.lock ./pyproject.toml ./
RUN poetry install --without=dev


FROM python-base as development
ENV TARGET_ENV=development

COPY --from=builder-base $POETRY_HOME $POETRY_HOME
COPY --from=builder-base $PYSETUP_PATH $PYSETUP_PATH

COPY docker/app/docker-entrypoint_dev.sh /docker-entrypoint_dev.sh
RUN chmod +x /docker-entrypoint_dev.sh

WORKDIR $PYSETUP_PATH
RUN poetry install --with=dev

WORKDIR /app
COPY fastapi-application .

EXPOSE 8000
ENTRYPOINT /docker-entrypoint_dev.sh $0 $@


FROM python-base as production
ENV TARGET_ENV=production

COPY --from=builder-base $VENV_PATH $VENV_PATH

COPY docker/app/docker-entrypoint.sh /docker-entrypoint.sh
RUN chmod +x /docker-entrypoint.sh

WORKDIR /app
COPY fastapi-application .

EXPOSE 8000
ENTRYPOINT /docker-entrypoint.sh $0 $@
