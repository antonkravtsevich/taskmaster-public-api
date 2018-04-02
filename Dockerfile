FROM alpine:3.5
RUN apk add --update python3
COPY src/ /src
COPY requirements.txt /src/requirements.txt
RUN pip3 install -r /src/requirements.txt
CMD python3 /src/app.py