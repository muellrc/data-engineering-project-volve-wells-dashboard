from logging import root
import pandas as pd
import luigi
from luigi.util import requires, inherits, common_params
from luigi.contrib import postgres
from sqlalchemy import create_engine
import luigi.contrib.postgres
from lxml.etree import Element, XMLParser, parse
from typing import Any
from urllib.request import urlopen
import csv
import psycopg2
import os


# ========================================WELLBORES========================================

class extract_data_wellbores(luigi.Task):
    def run(self):

        filenames = ['app/source-files/VolveF.edm.1.xml', 'app/source-files/VolveF.edm.2.xml', 'app/source-files/VolveF.edm.3.xml', 
        'app/source-files/VolveF.edm.4.xml', 'app/source-files/VolveF.edm.5.xml', 'app/source-files/VolveF.edm.6.xml']
        with self.output().open(mode="w") as f:
            for fname in filenames:
                 with open(fname) as infile:
                    for line in infile:
                        f.write(line)
    def output(self):
        return luigi.LocalTarget(self.task_id + ".xml")

@requires(extract_data_wellbores)
class transform_data_wellbores(luigi.Task):
    """Step 1: Wells"""

    def run(self):

        with self.input().open() as f:
            p = XMLParser(huge_tree=True)
            tree = parse(f, parser=p)
            root = tree.getroot()

        # create list to hold Wellbores
        wellbore_id = []

        # get actual surveys for valid wellbores
        for child in root:
            if child.tag == 'CD_DEFINITIVE_SURVEY_HEADER':
                if child.attrib['phase'] == 'ACTUAL':
                    wellbore_id.append(child.attrib['wellbore_id'])

        # create a list of wellbore names for the ids found
        wellbore_name = []

        for child in root:
            if child.tag == 'CD_WELLBORE':
                if child.attrib['wellbore_id'] in wellbore_id:
                    wellbore_name.append(
                        child.attrib['well_legal_name'].replace('/', '-'))

        # make a dictionary holding wellbore ids as keys and wellbore names as values
        id_name_dict = dict(zip(wellbore_id, wellbore_name))

        wellbores = pd.DataFrame(
            list(id_name_dict.items()), columns=['wellbore_key', 'wellbore_name'])
        list_wellbores = wellbores.values.tolist()

        with self.output().open(mode="w") as f:
            writer = csv.writer(f, delimiter="\t")
            writer.writerows(list_wellbores[1:])

    def output(self):
        return luigi.LocalTarget(self.task_id + ".tsv")


@requires(transform_data_wellbores)
class load_data_wellbores(luigi.Task):

    def run(self):

        with self.input().open() as f:

            reader = csv.reader(f,delimiter="\t")
            wellbores = pd.DataFrame(
            reader, columns=['wellbore_key', 'wellbore_name'])

            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            wellbores.to_sql(
                'wellbores_clean',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'wellbores_clean', '1'))




# ==================================END OF WELLBORES==========================================




# ========================================RUN PIPELINE========================================


class workflow(luigi.Task):
    def run(self):
    #RunPipelines

        #1 - Wellbores
        luigi.build([load_data_wellbores()])

        #2 - Trajectories
        #luigi.build([load_data_trajectories()])

# =======================================================================================
