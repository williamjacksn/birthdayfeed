FROM python:3.7.0-alpine3.8

COPY requirements-docker.txt /birthdayfeed/requirements-docker.txt

RUN /usr/local/bin/pip install --no-cache-dir --requirement /birthdayfeed/requirements-docker.txt

COPY . /birthdayfeed

ENTRYPOINT ["/usr/local/bin/python"]
CMD ["/birthdayfeed/run.py"]

ENV PYTHONUNBUFFERED 1

LABEL maintainer=william@subtlecoolness.com \
      org.label-schema.schema-version=1.0 \
      org.label-schema.version=1.0.3
