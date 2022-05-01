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
            
            original_data = pd.read_csv(f, delimiter=";") 
            
            COLUMN_NAMES=['productiontime','wellbore','boreoilvol','boregasvol','borewatvol','flowkind', 'welltype', 'borewivol']
            data = pd.DataFrame(columns=COLUMN_NAMES)
            data['productiontime'] = pd.to_datetime(original_data['DATEPRD'])
            data['wellbore'] = 'NO ' + original_data['NPD_WELL_BORE_NAME'].astype(str)
            data['flowkind'] = original_data['FLOW_KIND'].astype(str)
            data['welltype'] = original_data['WELL_TYPE'].astype(str)

            #Remove spaces / clean badly formatted data before converting to values float
            original_data['BORE_OIL_VOL'] = original_data['BORE_OIL_VOL'].str.replace(" ","")
            original_data['BORE_GAS_VOL'] = original_data['BORE_GAS_VOL'].str.replace(" ","")
            original_data['BORE_WAT_VOL'] = original_data['BORE_WAT_VOL'].str.replace(" ","")
            original_data['BORE_WI_VOL'] = original_data['BORE_WI_VOL'].str.replace(" ","")
            

            data['boreoilvol'] = original_data['BORE_OIL_VOL'].astype(float)
            data['boregasvol'] = original_data['BORE_GAS_VOL'].astype(float)
            data['borewatvol'] = original_data['BORE_WAT_VOL'].astype(float)
            data['borewivol'] = original_data['BORE_WI_VOL'].astype(float)

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
            original_data = pd.DataFrame (result_filtered)

            COLUMN_NAMES=['geo_offset_east', 'well_legal_name','geo_longitude','wellhead_depth','geo_latitude','geo_offset_north','water_depth']
            
            data = pd.DataFrame(columns=COLUMN_NAMES)
            
            #data['create_date'] = pd.to_datetime(original_data['create_date'].replace("{ts ", "").replace("}", ""))
            data['well_legal_name'] = original_data['well_legal_name'].astype(str)
            data['geo_offset_east'] = original_data['geo_offset_east'].astype(float)
            data['geo_longitude'] = original_data['geo_longitude'].astype(float)
            data['geo_latitude'] = original_data['geo_latitude'].astype(float)
            data['geo_offset_north'] = original_data['geo_offset_north'].astype(float)
            data['water_depth'] = original_data['water_depth'].astype(float)
            data['wellhead_depth'] = original_data['wellhead_depth'].astype(float)

            list_data = data.values.tolist()
            list_header = data.columns.to_list()


        with self.output().open(mode="w") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(list_header)
            writer.writerows(list_data[1:])

    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")
            

@requires(transform_data_wells)
class load_data_wells(luigi.Task):

    def run(self):

        with self.input().open() as f:
            
            data = pd.read_csv(f, delimiter=";") 

            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'wells_data',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'wells_data', '1'))


@requires(extract_edm_data)
class transform_data_wellbores(luigi.Task):
    def run(self):
        # parse EDM XML file
        with self.input().open() as f: 
            result_values, keys = get_all_attributes(f, ".//CD_WELLBORE")
            
            # remove invalid wells that have no Legal Name registered
            result_filtered = [item for item in result_values if 'wellbore_name' in item]
            original_data = pd.DataFrame (result_filtered)
            
            COLUMN_NAMES=['geo_latitude_ko','geo_longitude_ko','geo_latitude_bh','geo_longitude_bh','geo_offset_east_bh','geo_offset_north_ko', 'geo_offset_east_ko','geo_offset_north_bh',
            'ko_md','bh_md','rig_name','wellbore_name','well_legal_name']

            data = pd.DataFrame(columns=COLUMN_NAMES)
            
            data['well_legal_name'] = original_data['well_legal_name'].astype(str)
            data['wellbore_name'] = original_data['wellbore_name'].astype(str)
            data['rig_name'] = original_data['rig_name'].astype(str)

            data['geo_offset_east_bh'] = original_data['geo_offset_east_bh'].astype(float)
            data['geo_longitude_bh'] = original_data['geo_longitude_bh'].astype(float)
            data['geo_latitude_bh'] = original_data['geo_latitude_bh'].astype(float)
            data['geo_offset_north_bh'] = original_data['geo_offset_north_bh'].astype(float)

            data['geo_offset_east_ko'] = original_data['geo_offset_east_ko'].astype(float)
            data['geo_longitude_ko'] = original_data['geo_longitude_ko'].astype(float)
            data['geo_latitude_ko'] = original_data['geo_latitude_ko'].astype(float)
            data['geo_offset_north_ko'] = original_data['geo_offset_north_ko'].astype(float)

            data['bh_md'] = original_data['bh_md'].astype(float)
            data['ko_md'] = original_data['ko_md'].astype(float)

            list_data = data.values.tolist()
            list_header = data.columns.to_list()


        with self.output().open(mode="w") as f:
            writer = csv.writer(f, delimiter=";")
            writer.writerow(list_header)
            writer.writerows(list_data[1:])

    def output(self):
        return luigi.LocalTarget(self.task_id + ".csv")
            

@requires(transform_data_wellbores)
class load_data_wellbores(luigi.Task):

    def run(self):

        with self.input().open() as f:
            
            data = pd.read_csv(f, delimiter=";") 

            # write to postgres
            engine = create_engine(
                'postgresql://postgres:postgres@dev-postgres-db:5432/postgres')
            data.to_sql(
                'wellbores_data',
                engine,
                index=False,
                if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('dev-postgres-db', 'postgres', 'postgres', 'postgres', 'wellbores_data', '1'))

class workflow(luigi.Task):
    def run(self):

    #RunPipelines

        # Production Data
        luigi.build([load_data_production()])

        # Wells
        luigi.build([load_data_wells()])

        # Wellbores
        luigi.build([load_data_wellbores()])


