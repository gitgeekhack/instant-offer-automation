FROM python:3.9

WORKDIR /instant-offer-automation

RUN apt-get update && apt-get install -y \
    portaudio19-dev \
    python3-pyaudio \
    ffmpeg

COPY . .

RUN pip install --upgrade pip==23.3
RUN pip install -r requirements.txt

EXPOSE 8091

CMD ["python3", "run.py"]
