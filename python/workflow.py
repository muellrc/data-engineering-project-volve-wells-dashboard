# Imports
from ctypes.wintypes import FLOAT
from datetime import datetime
from logging import root
import pandas as pd
import luigi
from luigi.util import requires
from sqlalchemy import create_engine
import luigi.contrib.postgres
from lxml.etree import Element, XMLParser, parse
from typing import Any
import csv

# Generic function to get all attributes for a specific EDM entity within the XML file


def get_all_attributes(filename, tag):

    # Parse XML and get root
    p = XMLParser(huge_tree=True)
    tree = parse(filename, parser=p)
    root = tree.getroot()

    # Return list of atttributes
    result_values = [dict(n.attrib) for n in root.findall(tag)]

    # Retrieve unique keys for columns
    keys = list({k for dct in result_values for k in dct})

    return result_values, keys


# Luigi task for extracting production data from Volve Production csv file
class extract_production_data(luigi.Task):
    def run(self):
        # Read source data (csv production export)
        filename = 'app/source-files/Volve production data.csv'
        with self.output().open(mode="w") as f:
            with open(filename) as infile:
                for line in infile:
                    f.write(line)

    # Standard Luigi output creation to be used as input in next workflow action
    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")

# Luigi task for extracting production data from Volve Production csv file


@requires(extract_production_data)
class transform_production_data(luigi.Task):
    def run(self):

        # Standard Luigi input handling, based on previous workflow action's output
        with self.input().open() as f:

            # Convert csv file into pandas dataframe
            original_data = pd.read_csv(f, delimiter=";")

            # Define column names for dataframe
            COLUMN_NAMES = ['productiontime', 'wellbore', 'boreoilvol',
                            'boregasvol', 'borewatvol', 'flowkind', 'welltype', 'borewivol']
            data = pd.DataFrame(columns=COLUMN_NAMES)

            # convert datatypes and make sure correct Wellbore names are used
            data['productiontime'] = pd.to_datetime(original_data['DATEPRD'])
            data['wellbore'] = 'NO ' + \
                original_data['NPD_WELL_BORE_NAME'].astype(str)
            data['flowkind'] = original_data['FLOW_KIND'].astype(str)
            data['welltype'] = original_data['WELL_TYPE'].astype(str)

            # Remove spaces / clean badly formatted data and ensure consistency in formatting
            original_data['BORE_OIL_VOL'] = original_data['BORE_OIL_VOL'].str.replace(
                " ", "")
            original_data['BORE_GAS_VOL'] = original_data['BORE_GAS_VOL'].str.replace(
                " ", "")
            original_data['BORE_WAT_VOL'] = original_data['BORE_WAT_VOL'].str.replace(
                " ", "")
            original_data['BORE_WI_VOL'] = original_data['BORE_WI_VOL'].str.replace(
                " ", "")

            data['boreoilvol'] = original_data['BORE_OIL_VOL'].astype(float)
            data['boregasvol'] = original_data['BORE_GAS_VOL'].astype(float)
            data['borewatvol'] = original_data['BORE_WAT_VOL'].astype(float)
            data['borewivol'] = original_data['BORE_WI_VOL'].astype(float)

            # Convert results to list so they can be used in Luigi's output action
            list_data = data.values.tolist()
            list_header = data.columns.to_list()

        # export transformed data
        with self.output().open(mode="w") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(list_header)
            writer.writerows(list_data[1:])

    # Standard Luigi output creation to be used as input in next workflow action

    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")


@requires(transform_production_data)
class load_data_production(luigi.Task):

    def run(self):
        # Standard Luigi input handling, based on previous workflow action's output
        with self.input().open() as f:

            data = pd.read_csv(f, delimiter=";")

            # convert to sql and build postgres connection
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'production_data',
                engine,
                index=False,
                if_exists='replace'
            )

    # Standard Luigi output writing to postgres
    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'production_data', '1'))

# Luigi task for extracting Well Technical Data from Volve database export (xml file)


class extract_edm_data(luigi.Task):
    def run(self):
        # Read source data (EDM Database Export) as one XML file instead of the intermediate files
        filenames = ['app/source-files/VolveF.edm.1.xml', 'app/source-files/VolveF.edm.2.xml', 'app/source-files/VolveF.edm.3.xml',
                     'app/source-files/VolveF.edm.4.xml']
        with self.output().open(mode="w") as f:
            for fname in filenames:
                with open(fname) as infile:
                    for line in infile:
                        f.write(line)

    # Standard Luigi output creation to be used as input in next workflow action
    def output(self):
        return luigi.LocalTarget(self.task_id + ".xml")

# Luigi task for transforming Well Technical Data


@requires(extract_edm_data)
class transform_data_wells(luigi.Task):
    def run(self):
        # parse EDM XML file
        # Standard Luigi input handling, based on previous workflow action's output
        with self.input().open() as f:
            result_values, keys = get_all_attributes(f, ".//CD_WELL")

            # Remove invalid wells that have no Legal Name registered
            result_filtered = [
                item for item in result_values if 'well_legal_name' in item]
            original_data = pd.DataFrame(result_filtered)

            # Define column names for dataframe
            COLUMN_NAMES = ['geo_offset_east', 'well_legal_name', 'geo_longitude',
                            'wellhead_depth', 'geo_latitude', 'geo_offset_north', 'water_depth']

            # Convert to pandas dataframe
            data = pd.DataFrame(columns=COLUMN_NAMES)

            # Convert datatypes and make sure numeric formats are consistent
            data['well_legal_name'] = original_data['well_legal_name'].astype(
                str)
            data['geo_offset_east'] = original_data['geo_offset_east'].astype(
                float)
            data['geo_longitude'] = original_data['geo_longitude'].astype(
                float)
            data['geo_latitude'] = original_data['geo_latitude'].astype(float)
            data['geo_offset_north'] = original_data['geo_offset_north'].astype(
                float)
            data['water_depth'] = original_data['water_depth'].astype(float)
            data['wellhead_depth'] = original_data['wellhead_depth'].astype(
                float)

            # Convert results to list so they can be used in Luigi's output action
            list_data = data.values.tolist()
            list_header = data.columns.to_list()

        with self.output().open(mode="w") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(list_header)
            writer.writerows(list_data[1:])

    # Standard Luigi output creation to be used as input in next workflow action
    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")


@requires(transform_data_wells)
class load_data_wells(luigi.Task):

    def run(self):
        # Standard Luigi input handling, based on previous workflow action's output
        with self.input().open() as f:

            data = pd.read_csv(f, delimiter=";")

            # convert to sql and build postgres connection
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'wells_data',
                engine,
                index=False,
                if_exists='replace'
            )

    # Standard Luigi output writing to postgres
    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'wells_data', '1'))


@requires(extract_edm_data)
class transform_data_wellbores(luigi.Task):
    def run(self):
        # parse EDM XML file
        # Standard Luigi input handling, based on previous workflow action's output
        with self.input().open() as f:

            # call xml parsing and filtering function and filter by Wellbore tag
            result_values, keys = get_all_attributes(f, ".//CD_WELLBORE")

            # remove invalid wells that have no Legal Name registered
            result_filtered = [
                item for item in result_values if 'wellbore_name' in item]
            original_data = pd.DataFrame(result_filtered)

            # Define column names for dataframe
            COLUMN_NAMES = ['geo_latitude_ko', 'geo_longitude_ko', 'geo_latitude_bh', 'geo_longitude_bh', 'geo_offset_east_bh', 'geo_offset_north_ko', 'geo_offset_east_ko', 'geo_offset_north_bh',
                            'ko_md', 'bh_md', 'rig_name', 'wellbore_name', 'well_legal_name']

            # Convert to pandas dataframe
            data = pd.DataFrame(columns=COLUMN_NAMES)

            # Convert datatypes and make sure numeric formats are consistent
            data['well_legal_name'] = original_data['well_legal_name'].astype(
                str)
            data['wellbore_name'] = original_data['wellbore_name'].astype(str)
            data['rig_name'] = original_data['rig_name'].astype(str)
            data['geo_offset_east_bh'] = original_data['geo_offset_east_bh'].astype(
                float)
            data['geo_longitude_bh'] = original_data['geo_longitude_bh'].astype(
                float)
            data['geo_latitude_bh'] = original_data['geo_latitude_bh'].astype(
                float)
            data['geo_offset_north_bh'] = original_data['geo_offset_north_bh'].astype(
                float)
            data['geo_offset_east_ko'] = original_data['geo_offset_east_ko'].astype(
                float)
            data['geo_longitude_ko'] = original_data['geo_longitude_ko'].astype(
                float)
            data['geo_latitude_ko'] = original_data['geo_latitude_ko'].astype(
                float)
            data['geo_offset_north_ko'] = original_data['geo_offset_north_ko'].astype(
                float)
            data['bh_md'] = original_data['bh_md'].astype(float)
            data['ko_md'] = original_data['ko_md'].astype(float)

            # Convert results to list so they can be used in Luigi's output action
            list_data = data.values.tolist()
            list_header = data.columns.to_list()

        with self.output().open(mode="w") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(list_header)
            writer.writerows(list_data[1:])

    # Standard Luigi output creation to be used as input in next workflow action
    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")


@requires(transform_data_wellbores)
class load_data_wellbores(luigi.Task):

    def run(self):
        # Standard Luigi input handling, based on previous workflow action's output
        with self.input().open() as f:

            data = pd.read_csv(f, delimiter=";")

            # convert to sql and build postgres connection
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'wellbores_data',
                engine,
                index=False,
                if_exists='replace'
            )

    # Standard Luigi output writing to postgres
    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'wellbores_data', '1'))


# Task Manager for Luigi workflows and entry point

class workflow(luigi.Task):
    def run(self):

        # RunPipelines

        # Run Production Data
        luigi.build([load_data_production()])

        # Run Wells
        luigi.build([load_data_wells()])

        # Run Wellbores
        luigi.build([load_data_wellbores()])
