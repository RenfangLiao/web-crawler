FROM python:3.8

RUN apt-get update && apt-get install redis --yes
WORKDIR /app
COPY ./requirements.txt .
RUN pip3 install -r requirements.txt
COPY ./web_crawler_img/server .
COPY ./entrypoint.sh .

ENTRYPOINT ["bash", "./entrypoint.sh"]
