# syntax=docker/dockerfile:1

FROM python:3.9

WORKDIR /coffeeCam

RUN apt-get update && apt-get install ffmpeg libsm6 libxext6  -y

COPY . .

RUN pip install --no-cache --upgrade -r /coffeeCam/requirements.txt

CMD ["python", "main.py"]
