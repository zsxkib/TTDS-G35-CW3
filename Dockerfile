FROM ubuntu

WORKDIR /usr/src/app

ENV PORT 310
ENV HOST 0.0.0.0 

COPY main.py ./
COPY source ./

RUN apt update
RUN apt upgrade
RUN apt install python3

RUN python3 main.py