FROM python:3.10.6-alpine3.16

RUN /usr/sbin/adduser -g python -D python

USER python
RUN /usr/local/bin/python -m venv /home/python/venv

COPY --chown=python:python requirements.txt /home/python/birthdayfeed/requirements.txt
RUN /home/python/venv/bin/pip install --no-cache-dir --requirement /home/python/birthdayfeed/requirements.txt

ENV APP_VERSION="2021.4" \
    PATH="/home/python/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE="1" \
    PYTHONUNBUFFERED="1" \
    TZ="Etc/UTC"

ENTRYPOINT ["/home/python/venv/bin/python"]
CMD ["/home/python/birthdayfeed/run.py"]

LABEL org.opencontainers.image.authors="William Jackson <william@subtlecoolness.com>" \
      org.opencontainers.image.source="https://github.com/williamjacksn/birthdayfeed" \
      org.opencontainers.image.version="${APP_VERSION}"

COPY --chown=python:python run.py /home/python/birthdayfeed/run.py
COPY --chown=python:python birthdayfeed /home/python/birthdayfeed/birthdayfeed
