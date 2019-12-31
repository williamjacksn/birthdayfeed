FROM python:3.8.1-alpine3.10

COPY requirements.txt /birthdayfeed/requirements.txt

RUN /usr/local/bin/pip install --no-cache-dir --requirement /birthdayfeed/requirements.txt

COPY . /birthdayfeed

ENTRYPOINT ["/usr/local/bin/python"]
CMD ["/birthdayfeed/run.py"]

HEALTHCHECK CMD ["wget", "--spider", "--quiet", "http://localhost:8080/"]

ENV APP_VERSION="1.1.1" \
    PYTHONUNBUFFERED="1"

LABEL org.opencontainers.image.authors="William Jackson <william@subtlecoolness.com>" \
      org.opencontainers.image.source="https://github.com/williamjacksn/birthdayfeed" \
      org.opencontainers.image.version="${APP_VERSION}"
