FROM node

WORKDIR /usr/src/app

ENV PORT 310
ENV HOST 0.0.0.0 

COPY source ./
COPY data ./
COPY source ./

RUN apt update
RUN apt upgrade
RUN apt install python

RUN npm install --only=production
RUN npm run build
RUN npm start