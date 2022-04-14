FROM python
RUN pip install luigi
RUN pip install psycopg2==2.9.3
RUN pip install pandas
RUN pip install sqlalchemy
RUN pip install lxml
RUN pip install requests
RUN mkdir app
COPY . app
CMD PYTHONPATH='./app' luigi --module workflow load_data_wellbores --local-scheduler
