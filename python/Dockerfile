FROM python

RUN pip install luigi
RUN pip install psycopg2-binary
RUN pip install pandas
RUN pip install sqlalchemy
RUN pip install lxml
RUN pip install requests
RUN mkdir app
COPY . app
RUN cd app

CMD ["python -m luigi --module workflow extract_data --local-scheduler"]
