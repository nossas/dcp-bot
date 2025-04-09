FROM docker.io/rasa/rasa:3.2.6
USER root
COPY . /app
WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt
RUN chgrp -R 0 /app && chmod -R g=u /app
USER 1001
RUN rasa train

