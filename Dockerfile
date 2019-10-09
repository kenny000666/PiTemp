FROM arm32v6/python:3.8-rc-alpine
 
RUN apk update && apk add git nano
RUN git clone https://github.com/kenny000666/PiTemp.git

WORKDIR /PiTemp

RUN pip install -r requirements.txt

ENV MQTT=value

ENTRYPOINT [ "python PiTemp.py" ]