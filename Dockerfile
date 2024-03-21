FROM python:3.12-slim

RUN /usr/sbin/useradd --create-home --shell /bin/bash --user-group python

USER python
RUN /usr/local/bin/python -m venv /home/python/venv

COPY --chown=python:python requirements.txt /home/python/birthdayfeed/requirements.txt
RUN /home/python/venv/bin/pip install --no-cache-dir --requirement /home/python/birthdayfeed/requirements.txt

ENV PATH="/home/python/venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE="1" \
    PYTHONUNBUFFERED="1" \
    TZ="Etc/UTC"

ENTRYPOINT ["/home/python/venv/bin/python"]
CMD ["/home/python/birthdayfeed/run.py"]

LABEL org.opencontainers.image.authors="William Jackson <william@subtlecoolness.com>" \
      org.opencontainers.image.source="https://github.com/williamjacksn/birthdayfeed"

COPY --chown=python:python run.py /home/python/birthdayfeed/run.py
COPY --chown=python:python birthdayfeed /home/python/birthdayfeed/birthdayfeed
