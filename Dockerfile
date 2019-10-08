FROM python:buster

RUN apt-get update && apt-get install -y git nano 
RUN 