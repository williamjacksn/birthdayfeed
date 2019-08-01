FROM python:3.7.4-alpine3.10

COPY requirements.txt /birthdayfeed/requirements.txt

RUN /usr/local/bin/pip install --no-cache-dir --requirement /birthdayfeed/requirements.txt

COPY . /birthdayfeed

ENTRYPOINT ["/usr/local/bin/python"]
CMD ["/birthdayfeed/run.py"]

HEALTHCHECK CMD ["wget", "--spider", "--quiet", "http://localhost:8080/"]

ENV PYTHONUNBUFFERED 1

LABEL maintainer=william@subtlecoolness.com \
      org.label-schema.schema-version=1.0 \
      org.label-schema.version=1.0.12
