FROM tailordev/pandas
COPY src/ /src
COPY requirements.txt /src/requirements.txt
RUN pip install -r /src/requirements.txt
CMD python /src/app.py