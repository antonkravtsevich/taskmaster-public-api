FROM alpine:3.5
RUN apk add --update python py-pip
COPY src/ /src
COPY requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
CMD python /src/app.py