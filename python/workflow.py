from fileinput import filename
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

#Generic function to get all attributes for a specific EDM entity

def get_all_attributes(filename, tag):
    p = XMLParser(huge_tree=True) 
    tree = parse(filename, parser=p) 
    root = tree.getroot() 

    # RETURN LIST OF ATTRIBUTE DICTIONARIES
    result_values = [dict(n.attrib) for n in root.findall(tag)]

    # RETRIEVE UNIQUE KEYS FOR COLUMN HEADERS
    keys = list({k for dct in result_values for k in dct})

    return result_values, keys

class extract_data(luigi.Task):
    def run(self):
        # Read source data (EDM Database Export) as one XML file instead of the intermediate files
        filenames = ['app/source-files/VolveF.edm.1.xml', 'app/source-files/VolveF.edm.2.xml', 'app/source-files/VolveF.edm.3.xml', 
        'app/source-files/VolveF.edm.4.xml', 'app/source-files/VolveF.edm.5.xml', 'app/source-files/VolveF.edm.6.xml']
        with self.output().open(mode="w") as f:
            for fname in filenames:
                 with open(fname) as infile:
                    for line in infile:
                        f.write(line)
    def output(self):
        return luigi.LocalTarget(self.task_id + ".xml")

# ========================================WELLS========================================

@requires(extract_data)
class transform_data_wells(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f: 

            result_values, keys = get_all_attributes(f, ".//CD_WELL")

        with self.output().open(mode="w") as f:
            # WRITE TO CSV VIA DICTWRITER
            dw = csv.DictWriter(f, fieldnames=keys)
            dw.writeheader()
            dw.writerows(result_values)

    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")


@requires(transform_data_wells)
class load_data_wells(luigi.Task):

    def run(self):

        with self.input().open() as f:
            
            data = pd.read_csv(f) 

            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'wells_clean',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'wells_clean', '1'))

# ==================================END OF WELLS==========================================

        
# ========================================WELLBORES========================================

@requires(extract_data)
class transform_data_wellbores(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f:
            p = XMLParser(huge_tree=True)
            tree = parse(f, parser=p)
            root = tree.getroot()

        # create list to hold Wellbores
        wellbore_id = []

        # get only actual surveys for valid wellbores
        for child_node in root:
            if child_node.tag == 'CD_DEFINITIVE_SURVEY_HEADER':
                if child_node.attrib['phase'] == 'ACTUAL':
                    wellbore_id.append(child_node.attrib['wellbore_id'])

        # create a list of wellbore legal names for the ids identified based on CD_WELLBORE table in EDM
        wellbore_name = []
        for child_node in root:
            if child_node.tag == 'CD_WELLBORE':
                if child_node.attrib['wellbore_id'] in wellbore_id:
                    wellbore_name.append(
                        child_node.attrib['well_legal_name'].replace('/', '-'))

        # make a dictionary of wellbore ids and names
        id_name_dict = dict(zip(wellbore_id, wellbore_name))

        # write data to luigi output
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
            # read tsv file holding valid Wellbores
            reader = csv.reader(f,delimiter="\t")
            # create dataframe
            wellbores = pd.DataFrame(
            reader, columns=['wellbore_key', 'wellbore_name'])
            # write to postgres
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

# ========================================DATUM========================================

@requires(extract_data)
class transform_data_datum(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f: 

            result_values, keys = get_all_attributes(f, ".//CD_DATUM")

        with self.output().open(mode="w") as f:
            # WRITE TO CSV VIA DICTWRITER
            dw = csv.DictWriter(f, fieldnames=keys)
            dw.writeheader()
            dw.writerows(result_values)

    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")


@requires(transform_data_datum)
class load_data_datum(luigi.Task):

    def run(self):

        with self.input().open() as f:
            
            data = pd.read_csv(f) 

            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'datum_clean',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'datum_clean', '1'))

# ==================================END OF DATUM==========================================

# ========================================SCENARIO========================================

@requires(extract_data)
class transform_data_scenario(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f: 

            result_values, keys = get_all_attributes(f, ".//CD_SCENARIO")

        with self.output().open(mode="w") as f:
            # WRITE TO CSV VIA DICTWRITER
            dw = csv.DictWriter(f, fieldnames=keys)
            dw.writeheader()
            dw.writerows(result_values)

    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")


@requires(transform_data_scenario)
class load_data_scenario(luigi.Task):

    def run(self):

        with self.input().open() as f:
            
            data = pd.read_csv(f) 

            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'scenario_clean',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'scenario_clean', '1'))

# ==================================END OF SCENARIO==========================================

# ========================================DEFINITIVE SURVEY HEADER========================================

@requires(extract_data)
class transform_data_definitive_survey_header(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f: 

            result_values, keys = get_all_attributes(f, ".//CD_DEFINITIVE_SURVEY_HEADER")

        with self.output().open(mode="w") as f:
            # WRITE TO CSV VIA DICTWRITER
            dw = csv.DictWriter(f, fieldnames=keys)
            dw.writeheader()
            dw.writerows(result_values)

    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")


@requires(transform_data_definitive_survey_header)
class load_data_definitive_survey_header(luigi.Task):

    def run(self):

        with self.input().open() as f:
            
            data = pd.read_csv(f) 

            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'definitive_survey_header_clean',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'definitive_survey_header_clean', '1'))

# ==================================END OF DEFINITIVE SURVEY HEADER==========================================

# ========================================DEFINITIVE SURVEY STATION========================================

@requires(extract_data)
class transform_data_definitive_survey_station(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f: 

            result_values, keys = get_all_attributes(f, ".//CD_DEFINITIVE_SURVEY_STATION")

        with self.output().open(mode="w") as f:
            # WRITE TO CSV VIA DICTWRITER
            dw = csv.DictWriter(f, fieldnames=keys)
            dw.writeheader()
            dw.writerows(result_values)

    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")


@requires(transform_data_definitive_survey_station)
class load_data_definitive_survey_station(luigi.Task):

    def run(self):

        with self.input().open() as f:
            
            data = pd.read_csv(f) 

            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'definitive_survey_station_clean',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'definitive_survey_station_clean', '1'))

# ==================================END OF DEFINITIVE SURVEY STATION==========================================

# ========================================SURVEY HEADER========================================

@requires(extract_data)
class transform_data_survey_header(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f: 

            result_values, keys = get_all_attributes(f, ".//CD_SURVEY_HEADER")

        with self.output().open(mode="w") as f:
            # WRITE TO CSV VIA DICTWRITER
            dw = csv.DictWriter(f, fieldnames=keys)
            dw.writeheader()
            dw.writerows(result_values)

    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")


@requires(transform_data_survey_header)
class load_data_survey_header(luigi.Task):

    def run(self):

        with self.input().open() as f:
            
            data = pd.read_csv(f) 

            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'survey_header_clean',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'survey_header_clean', '1'))

# ==================================END OF SURVEY HEADER==========================================

# ========================================SURVEY STATION========================================

@requires(extract_data)
class transform_data_survey_station(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f: 

            result_values, keys = get_all_attributes(f, ".//CD_SURVEY_STATION")

        with self.output().open(mode="w") as f:
            # WRITE TO CSV VIA DICTWRITER
            dw = csv.DictWriter(f, fieldnames=keys)
            dw.writeheader()
            dw.writerows(result_values)

    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")


@requires(transform_data_survey_station)
class load_data_survey_station(luigi.Task):

    def run(self):

        with self.input().open() as f:
            
            data = pd.read_csv(f) 

            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'survey_station_clean',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'survey_station_clean', '1'))

# ==================================END OF SURVEY STATION==========================================

# ========================================ASSEMBLY========================================

@requires(extract_data)
class transform_data_assembly(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f: 

            result_values, keys = get_all_attributes(f, ".//CD_ASSEMBLY")

        with self.output().open(mode="w") as f:
            # WRITE TO CSV VIA DICTWRITER
            dw = csv.DictWriter(f, fieldnames=keys)
            dw.writeheader()
            dw.writerows(result_values)

    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")


@requires(transform_data_assembly)
class load_data_assembly(luigi.Task):

    def run(self):

        with self.input().open() as f:
            
            data = pd.read_csv(f) 

            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'assembly_clean',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'assembly_clean', '1'))

# ==================================END OF ASSEMBLY==========================================

# ========================================POLICY========================================

@requires(extract_data)
class transform_data_policy(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f: 

            result_values, keys = get_all_attributes(f, ".//CD_POLICY")

        with self.output().open(mode="w") as f:
            # WRITE TO CSV VIA DICTWRITER
            dw = csv.DictWriter(f, fieldnames=keys)
            dw.writeheader()
            dw.writerows(result_values)

    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")


@requires(transform_data_policy)
class load_data_policy(luigi.Task):

    def run(self):

        with self.input().open() as f:
            
            data = pd.read_csv(f) 

            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'policy_clean',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'policy_clean', '1'))

# ==================================END OF POLICY==========================================

# ========================================PROJECT========================================

@requires(extract_data)
class transform_data_project(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f: 

            result_values, keys = get_all_attributes(f, ".//CD_PROJECT")

        with self.output().open(mode="w") as f:
            # WRITE TO CSV VIA DICTWRITER
            dw = csv.DictWriter(f, fieldnames=keys)
            dw.writeheader()
            dw.writerows(result_values)

    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")


@requires(transform_data_project)
class load_data_project(luigi.Task):

    def run(self):

        with self.input().open() as f:
            
            data = pd.read_csv(f) 

            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'project_clean',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'project_clean', '1'))

# ==================================END OF PROJECT==========================================

# ========================================SITE========================================

@requires(extract_data)
class transform_data_site(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f: 

            result_values, keys = get_all_attributes(f, ".//CD_SITE")

        with self.output().open(mode="w") as f:
            # WRITE TO CSV VIA DICTWRITER
            dw = csv.DictWriter(f, fieldnames=keys)
            dw.writeheader()
            dw.writerows(result_values)

    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")


@requires(transform_data_site)
class load_data_site(luigi.Task):

    def run(self):

        with self.input().open() as f:
            
            data = pd.read_csv(f) 

            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'site_clean',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'site_clean', '1'))

# ==================================END OF SITE==========================================

# ========================================RUN PIPELINE========================================

class workflow(luigi.Task):
    def run(self):
    #RunPipelines

        #1 - Wells
        luigi.build([load_data_wells()])

        #2 - Wellbores
        luigi.build([load_data_wellbores()])

        #3 - Datum
        luigi.build([load_data_datum()])

        #4 - Scenario
        luigi.build([load_data_scenario()])

        #5 - Definitive survey header
        luigi.build([load_data_definitive_survey_header()])

        #6 - Definitive survey station
        luigi.build([load_data_definitive_survey_station()])

        #7 - Survey header
        luigi.build([load_data_survey_header()])

        #8 - Survey station
        luigi.build([load_data_survey_station()])

        #9 - Assembly
        luigi.build([load_data_assembly()])

        #10 - Policy
        luigi.build([load_data_policy()])

        #11 - Project
        luigi.build([load_data_project()])

        #12 - Site
        luigi.build([load_data_site()])


# =======================================================================================
