from logging import root
import pandas as pd
import luigi
from sqlalchemy import create_engine
import luigi.contrib.postgres
from lxml.etree import Element, XMLParser, parse
from typing import Any
from urllib.request import urlopen
import requests

# ========================================EXTRACT========================================


class extract_data(luigi.Task):

    def output(self):
        return(luigi.local_target("Volve F.edm.xml"))

    def run(self):

        def get_confirm_token(response):
            for key, value in response.cookies.items():
                if key.startswith('download_warning'):
                    return value
            return None

        def save_response_content(response):
            CHUNK_SIZE = 32768
            # Write the downloaded XML to the Luigi output destination for the Extract step
            with self.output().open('w') as f:
                for chunk in response.iter_content(CHUNK_SIZE):
                    if chunk:
                        f.write(chunk)

        def download_file_from_google_drive(id):
            URL = "https://drive.google.com/uc?export=download&confirm=yTib"

            session = requests.Session()

            response = session.get(URL, params={'id': id}, stream=True)
            token = get_confirm_token(response)

            if token:
                params = {'id': id, 'confirm': token}
                response = session.get(URL, params=params, stream=True)

            save_response_content(response)

        # Download EDM xml file from Google Drive

        file_id = '1HubrQY1zUw_vDflNvXnhKgv5bJXQZ9kd'
        download_file_from_google_drive(file_id)


# =======================================================================================


# ========================================TRANSFORM========================================

# Step 1: Wells
class transform_data_wellbores(luigi.Task):

    def requires(self):
        return [extract_data()]

    def output(self):
        return luigi.LocalTarget('wellbores.csv')

    def run(self):

        # parse EDM xml file
        p = XMLParser(huge_tree=True)
        with self.input().open('r') as infile:
            tree = parse(infile, parser=p)
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

        id_name_dict

        wellbores = pd.DataFrame(
            list(id_name_dict.items()), columns=['key', 'name'])
        wellbores.to_csv('wellbores.csv', sep=';', index=False)


# Step 2: Trajectories


class transform_data_trajectories(luigi.Task):

    def requires(self):
        return [extract_data()]

    def output(self):
        return luigi.LocalTarget('trajectories.csv')

    def run(self):
        # create a function to extract trajectory data from the database

        def get_wellpath(dct):
            survey_header = []
        # consider only actual wellbores
            for child in root:
                if child.tag == 'CD_DEFINITIVE_SURVEY_HEADER':
                    if child.attrib['phase'] == 'ACTUAL':
                        survey_header.append(
                            child.attrib['def_survey_header_id'])

            # for loop to collect data for every wellbore in the dictionary that was created earlier
            for key in dct:
                # append wellpath data to corresponding lists
                for item in survey_header:
                    azimuth = []
                    inclination = []
                    md = []
                    tvd = []
                    easting = []
                    northing = []
            for child in root:
                if child.tag == 'CD_DEFINITIVE_SURVEY_STATION':
                    if child.attrib['wellbore_id'] == key:
                        if child.attrib['def_survey_header_id'] == item:
                            azimuth.append(float(child.attrib['azimuth']))
                            inclination.append(
                                float(child.attrib['inclination']))
                            md.append(float(child.attrib['md']) * 0.3048)
                            tvd.append(float(child.attrib['tvd']) * 0.3048)
                            easting.append(
                                float(child.attrib['offset_east']) * 0.3048)
                            northing.append(
                                float(child.attrib['offset_north']) * 0.3048)

                            # create a dataframe and save the dataframe as csv file
                            if md:
                                wellpath = pd.DataFrame(list(zip(key, md, azimuth, inclination)), columns=[
                                                        'Wellbore', 'Measured Depth', 'Azimuth', 'Inclination'])
                                wellpath.sort_values(
                                    'Measured Depth', inplace=True)
                                wellpath = wellpath.reset_index(drop=True)
                                wellpath = wellpath.round(
                                    {'Measured Depth': 0, 'Azimuth': 2, 'Inclination': 2})
                                wellpath.to_csv(
                                    'trajectories.csv', sep=';', index=False)


# =======================================================================================

# ========================================LOAD========================================
# Step 1: Wells

class load_data_wellbores(luigi.Task):
    def requires(self):
        return [transform_data_wellbores()]

    def run(self):
        data = pd.read_csv('wellbores.csv')
        engine = create_engine(
            'postgresql://postgres:postgres@localhost:5432/wellbores_clean')

        data.to_sql(
            'wellbores_clean',
            engine,
            index=False,
            if_exists='replace'
        )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('localhost', 'wellbores_clean', 'postgres', 'postgres', 'wellbores_clean', '1'))

# Step 2: Trajectories


class load_data_trajectories(luigi.Task):
    def requires(self):
        return [transform_data_trajectories()]

    def run(self):
        data = pd.read_csv('trajectories.csv')
        engine = create_engine(
            'postgresql://postgres:postgres@localhost:5432/trajectories_clean')

        data.to_sql(
            'trajectories_clean',
            engine,
            index=False,
            if_exists='replace'
        )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('localhost', 'trajectories_clean', 'postgres', 'postgres', 'trajectories_clean', '1'))

# =======================================================================================

# ========================================RUN PIPELINE========================================


if __name__ == '__main__':
    luigi.run()

# =======================================================================================
