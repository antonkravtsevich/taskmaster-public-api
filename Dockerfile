FROM python:3.5

ENV PYTHONUNBUFFERED 1

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        libatlas-base-dev gfortran

COPY src/ /src
COPY requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
CMD python /src/app.py