FROM python

WORKDIR /work
COPY . /work
RUN pip install requests flask psycopg2

CMD [ "python3","app.py" ]