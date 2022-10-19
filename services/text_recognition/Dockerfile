FROM ghcr.io/csia-pme/csia-pme-base-image:latest
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

RUN mkdir /app
COPY main.py /app
COPY api /app/api

WORKDIR /app

ENTRYPOINT [ "python3", "/app/main.py" ]
