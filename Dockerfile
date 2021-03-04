FROM tiangolo/uwsgi-nginx-flask:python3.8

# RUN apt-get update && apt-get install nano

COPY ./deployment/requirements.txt /requirements.txt
RUN pip3 install -r /requirements.txt

ENV STATIC_PATH /app/app/static

COPY ./app /app
# COPY .env /app/.env
COPY ./deployment/uwsgi.ini /app

EXPOSE 80