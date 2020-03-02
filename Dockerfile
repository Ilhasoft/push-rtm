FROM python:3.6

ARG COMPRESS_ENABLED

ENV PYTHONUNBUFFERED 1
ENV COMPRESS_ENABLED=$COMPRESS_ENABLED
ENV COMPRESS_OFFLINE=true

WORKDIR /app

RUN apt-get update -y
RUN apt-get install -y supervisor gdal-bin

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

RUN sed -i 's/\r$//g' ./start
RUN chmod +x ./start

EXPOSE 8000

ENTRYPOINT ["./start"]
