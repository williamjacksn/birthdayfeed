FROM python:3.7-alpine

EXPOSE 8080

COPY requirements.txt /app/requirements.txt

RUN /usr/local/bin/pip install --no-cache-dir --upgrade pip \
 && /usr/local/bin/pip install --no-cache-dir --requirement /app/requirements.txt

COPY . /app

ENTRYPOINT ["/usr/local/bin/python"]
CMD ["/app/run.py"]
