FROM ghcr.io/csia-pme/csia-pme-base-image:latest
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install -r /tmp/requirements.txt

RUN mkdir /app
COPY main.py /app
COPY api /app/api

RUN mkdir -p /root/.deepface/weights
WORKDIR /root/.deepface/weights
RUN wget https://github.com/serengil/deepface_models/releases/download/v1.0/retinaface.h5

WORKDIR /app

ENTRYPOINT [ "python3", "/app/main.py" ]
