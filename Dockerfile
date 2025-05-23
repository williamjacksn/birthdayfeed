FROM ghcr.io/astral-sh/uv:0.7.7 AS uv
FROM python:3.13-slim

COPY --from=uv /uv /bin/uv

RUN /usr/sbin/useradd --create-home --shell /bin/bash --user-group python
USER python

COPY --chown=python:python .python-version /home/python/birthdayfeed/.python-version
COPY --chown=python:python pyproject.toml /home/python/birthdayfeed/pyproject.toml
COPY --chown=python:python uv.lock /home/python/birthdayfeed/uv.lock
WORKDIR /home/python/birthdayfeed
RUN /bin/uv sync --frozen

ENV PYTHONDONTWRITEBYTECODE="1" \
    PYTHONUNBUFFERED="1" \
    TZ="Etc/UTC"

ENTRYPOINT ["/bin/uv", "run", "run.py"]

LABEL org.opencontainers.image.authors="William Jackson <william@subtlecoolness.com>" \
      org.opencontainers.image.source="https://github.com/williamjacksn/birthdayfeed"

COPY --chown=python:python run.py /home/python/birthdayfeed/run.py
COPY --chown=python:python birthdayfeed /home/python/birthdayfeed/birthdayfeed
