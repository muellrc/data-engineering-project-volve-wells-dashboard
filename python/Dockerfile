FROM python

RUN pip install luigi

RUN pip install psycopg2-binary

RUN mkdir -p /home/app

COPY . /home/app

CMD ["python", "/home/app/workflow.py"]