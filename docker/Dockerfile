FROM docker.io/rasa/rasa:3.2.6
USER root
RUN apt-get update && apt-get install -y tzdata
ENV TZ=America/Sao_Paulo
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
COPY . /app
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
RUN chgrp -R 0 /app && chmod -R g=u /app
USER 1001
RUN rasa train

