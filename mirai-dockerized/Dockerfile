FROM ubuntu:bionic

WORKDIR /mirai
RUN apt-get upgrade -y && apt-get update -y
RUN apt install apt-transport-https ca-certificates -y
COPY sources.list /etc/apt/sources.list
RUN apt-get update -y
RUN apt-get install default-jre default-jdk -y
ENTRYPOINT java -Dfile.encoding=UTF-8 -jar ./mirai-console-wrapper.jar
