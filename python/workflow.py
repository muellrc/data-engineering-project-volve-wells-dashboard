from logging import root
import pandas as pd
import luigi
from luigi.util import requires
from sqlalchemy import create_engine
import luigi.contrib.postgres
from lxml.etree import Element, XMLParser, parse
from typing import Any
from urllib.request import urlopen
import csv

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

class extract_production_data(luigi.Task):
    def run(self):
        # Read source data (EDM Database Export) as one XML file instead of the intermediate files
        filename = 'app/source-files/Volve production data.csv'
        with self.output().open(mode="w") as f:
            with open(filename) as infile:
                for line in infile:
                    f.write(line)
    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")


@requires(extract_production_data)
class transform_production_data(luigi.Task):
    def run(self):

        with self.input().open() as f:
            data = pd.read_csv(f, delimiter=";") 
            data['NPD_WELL_BORE_NAME'] = 'NO ' + data['NPD_WELL_BORE_NAME'].astype(str)
            list_data = data.values.tolist()
            list_header = data.columns.to_list()

        with self.output().open(mode="w") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(list_header)
            writer.writerows(list_data[1:])

    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")
            

@requires(transform_production_data)
class load_data_production(luigi.Task):

    def run(self):

        with self.input().open() as f:
            
            data = pd.read_csv(f, delimiter=";") 

            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'production_data',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'production_data', '1'))


class extract_edm_data(luigi.Task):
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


@requires(extract_edm_data)
class transform_data_wells(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f: 
            result_values, keys = get_all_attributes(f, ".//CD_WELL")
            
            # remove invalid wells that have no Legal Name registered
            result_filtered = [item for item in result_values if 'well_legal_name' in item]


        with self.output().open(mode="w") as f:
            # WRITE TO CSV VIA DICTWRITER
            dw = csv.DictWriter(f, fieldnames=keys)
            dw.writeheader()
            dw.writerows(result_filtered)

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
                'wells',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'wells', '1'))


@requires(extract_edm_data)
class transform_data_wellbores(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f: 
            result_values, keys = get_all_attributes(f, ".//CD_WELLBORE")
            
            # remove invalid wells that have no Legal Name registered
            result_filtered = [item for item in result_values if 'well_legal_name' in item]


        with self.output().open(mode="w") as f:
            # WRITE TO CSV VIA DICTWRITER
            dw = csv.DictWriter(f, fieldnames=keys)
            dw.writeheader()
            dw.writerows(result_filtered)

    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")

@requires(transform_data_wellbores)
class load_data_wellbores(luigi.Task):

    def run(self):

        with self.input().open() as f:
            
            data = pd.read_csv(f) 

            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'wellbores',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'wellbores', '1'))


@requires(extract_edm_data)
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
                'datum',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'datum', '1'))


@requires(extract_edm_data)
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
                'scenario',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'scenario', '1'))


@requires(extract_edm_data)
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
                'definitive_survey_header',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'definitive_survey_header', '1'))


@requires(extract_edm_data)
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
                'definitive_survey_station',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'definitive_survey_station', '1'))


@requires(extract_edm_data)
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
                'survey_header',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'survey_header', '1'))


@requires(extract_edm_data)
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
                'survey_station',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'survey_station', '1'))


@requires(extract_edm_data)
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
                'assembly',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'assembly', '1'))


@requires(extract_edm_data)
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
                'policy',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'policy', '1'))


@requires(extract_edm_data)
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
                'project',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'project', '1'))


@requires(extract_edm_data)
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
                'site',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'site', '1'))


class workflow(luigi.Task):
    def run(self):
    #RunPipelines

        # Production Data
        luigi.build([load_data_production()])

        # Wells
        luigi.build([load_data_wells()])

        # Wellbores
        luigi.build([load_data_wellbores()])

        # Datum
        luigi.build([load_data_datum()])

        # Scenario
        luigi.build([load_data_scenario()])

        # Definitive survey header
        luigi.build([load_data_definitive_survey_header()])

        # Definitive survey station
        luigi.build([load_data_definitive_survey_station()])

        # Survey header
        luigi.build([load_data_survey_header()])

        # Survey station
        luigi.build([load_data_survey_station()])

        # Assembly
        luigi.build([load_data_assembly()])

        # Policy
        luigi.build([load_data_policy()])

        # Project
        luigi.build([load_data_project()])

        # Site
        luigi.build([load_data_site()])



