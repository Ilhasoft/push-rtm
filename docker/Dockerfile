FROM python:3.6-alpine

ENV PYTHONUNBUFFERED 1
WORKDIR /app

RUN apk update \
  && apk add --virtual build-deps gcc python3-dev musl-dev \
  && apk add postgresql-client postgresql-dev libxml2-dev libxslt-dev gettext-dev \
  && apk add jpeg-dev zlib-dev freetype-dev lcms2-dev openjpeg-dev tiff-dev tk-dev tcl-dev \
  && apk add libffi-dev py-cffi gettext nodejs npm git build-base

RUN apk add --no-cache -X http://dl-cdn.alpinelinux.org/alpine/edge/testing \
  gdal gdal-dev geos-dev py-gdal \
  && rm -rf /var/cache/apk/*

RUN addgroup -S django \
  && adduser -S -G django django

RUN npm install --global --unsafe-perm \
  coffeescript \
  less \
  yarn

COPY ./package.json /app
RUN npm install

COPY ./requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY ./docker/start.sh /start.sh

RUN sed -i 's/\r$//g' /start.sh
RUN chmod +x /start.sh
RUN chown django /start.sh

RUN chown -R django /app
USER django

EXPOSE 8000
ENTRYPOINT ["/start.sh"]
