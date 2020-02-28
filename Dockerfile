FROM python:3.6

ARG COMPRESS_ENABLED

ENV PYTHONUNBUFFERED 1
WORKDIR /app

RUN apt-get update -y && \
    apt-get upgrade -y

RUN apt-get install -y \
  postgresql-client \
  postgresql \
  gettext \
  nodejs \
  npm \
  git \
  software-properties-common \
  curl \
  supervisor

RUN npm i npm@latest -g \
  npm install --global --unsafe-perm \
  coffeescript \
  less \
  yarn

RUN npm install

COPY ./requirements.txt /app
RUN pip install --no-cache-dir -r requirements.txt

COPY start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start

EXPOSE 8000

ENTRYPOINT ["/start"]
