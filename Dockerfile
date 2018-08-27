FROM python:3.7.0-alpine3.8

COPY requirements.txt /app/requirements.txt

RUN /usr/local/bin/pip install --no-cache-dir --upgrade pip setuptools \
 && /usr/local/bin/pip install --no-cache-dir --requirement /app/requirements.txt

COPY . /app

EXPOSE 8080
ENTRYPOINT ["/usr/local/bin/python"]
CMD ["/app/run.py"]
