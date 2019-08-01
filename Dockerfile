FROM python:3.7.4-alpine3.10

COPY requirements.txt /birthdayfeed/requirements.txt

RUN /usr/local/bin/pip install --no-cache-dir --requirement /birthdayfeed/requirements.txt

COPY . /birthdayfeed

ENTRYPOINT ["/usr/local/bin/python"]
CMD ["/birthdayfeed/run.py"]

HEALTHCHECK CMD ["wget", "--spider", "--quiet", "http://localhost:8080/"]

ENV PYTHONUNBUFFERED 1

LABEL org.opencontainers.image.authors="William Jackson <william@subtlecoolness.com>" \
      org.opencontainers.image.source="https://github.com/williamjacksn/birthdayfeed" \
      org.opencontainers.image.version=1.0.12
