FROM python:slim
#RUN export DEBIAN_FRONTEND=noninteractive; apt update; apt-get -y install python3 python3-pip virtualenv
RUN export DEBIAN_FRONTEND=noninteractive; \
    apt-get update; \
    apt-get -y install sox ffmpeg redis-server

# Copy local code to the container image.
ENV APP_DATA /app
WORKDIR $APP_DATA
COPY . ./

# install requirements
RUN pip3 install -r requirements.txt

# environment vars
#ENV FLASK_APP "TextSpeak"
ENV HOST 0.0.0.0
ENV PORT 8080

# entrypoint
ENTRYPOINT /app/init.sh ${PORT}
