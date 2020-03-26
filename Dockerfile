FROM python:3.6

ENV PYTHONUNBUFFERED 1

WORKDIR /app

RUN apt-get update -y
RUN apt-get install -y supervisor gdal-bin gunicorn

COPY . .
RUN pip install --no-cache-dir -r requirements.txt

RUN sed -i 's/\r$//g' ./start
RUN chmod +x ./start

EXPOSE 8000

ENTRYPOINT ["./start"]
