import pandas
import luigi
from sqlalchemy import create_engine
from get_data_db import get_data_db
import luigi.contrib.postgres


class extract_data(luigi.Task):

    def run(self):
        data = pandas.read_csv('records_0.csv')
        engine = create_engine('postgresql://postgres:31101997@localhost:5432/zomato')
        data.to_sql(
            'zomato_dataset',
            engine,
            index=False,
            if_exists='replace'
            )

    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('localhost','zomato','postgres','31101997','zomato_dataset','1'))

class transform_data(luigi.Task):

    def output(self):
        return luigi.LocalTarget('records_2.csv')

    def run(self):

        dataset = get_data_db('localhost', 'zomato', 'postgres', '31101997')
        dataset['cost_for_two'].fillna(0, inplace = True)

        def get_hours(hour):
        
            hour = str(hour)
            split = hour.split(' ')
            
            if "Opens" not in split:
                split = str(split[0])
                split = split.replace('h','')
                return split
            
            elif split[0] == 'Opens' and split[1] == 'tomorrow':
                split = str(split[3])
                split = split.replace('h','')
                return split
            
            elif split[0] == 'Opens' and split[1] == 'on':
                split = str(split[-1])
                split = split.replace('h','')
                return split
            
            elif split[0] == 'Opens' and split[1] == 'at':
                split = str(split[2])
                split = split.replace('h','')
                return split
        
        def get_open_categorical(date_categorical):
            morning = ['6','7','8','9','10','11']
            afternoon = ['12','13','14','15','16','17','18']
            evening = ['19','20','21','22']

            if date_categorical in morning:
                return 'Morning'
            elif date_categorical in afternoon:
                return 'Afternoon'
            elif date_categorical in evening:
                return 'Evening'
        
        def count_cuisines(cuisines):
            """
            Try to count type's of cuisines in each row.
            """
            to_string = str(cuisines).strip() # change into string and removing all spacing 
            split_cuisines = to_string.split(',') # split string by ','
            final = str(len(split_cuisines)) # count the number of values that exist in a list
            return final
        
        def count_facilities(facilities):
            """
            Try to count facilities in each row.
            """
            to_string = str(facilities).strip() # change into string and removing all spacing 
            split_facilities = to_string.split('\n') # split string by ','
            final = str(len(split_facilities)) # count the number of values that exist in a list
            return final
            
        def change_facilities(facilities_changed):
            """
            Try to split facilities using ','
            """
            to_string = str(facilities_changed).strip()
            replacing = to_string.replace('\n',',')
            return replacing

        def change_int(x):
            if x == 'Null':
                return x
            else:
                x = str(x).strip()
                x = x.replace('.','')
                x = int(x)
                return x
        
        dataset['hours_int'] = dataset['hours'].apply(lambda x: get_hours(x))
        dataset['hours_categorical'] = dataset['hours_int'].apply(lambda x: get_open_categorical(x))
        dataset['amount_cuisines'] = dataset['cuisines'].apply(lambda x: count_cuisines(x))
        dataset['amount_facilities'] = dataset['facilities'].apply(lambda x: count_facilities(x))
        dataset['facilities'] = dataset['facilities'].apply(lambda x: change_facilities(x))
        dataset['cost_for_two'] = dataset['cost_for_two'].apply(lambda x: change_int(x))
        
        dataset.to_csv(r'/Users/macbookpro/Documents/ETL_Proj_Zomato/records_2.csv', index = False)


class load_data(luigi.Task):
    def requires(self):
        return [transform_data()]

    def run(self):
        data = pandas.read_csv('records_2.csv')
        engine = create_engine('postgresql://postgres:31101997@localhost:5432/zomato_clean')
        data.to_sql(
            'zomato_dataset_clean',
            engine,
            index=False,
            if_exists='replace'
            )
    
    def output(self):
        return(luigi.contrib.postgres.PostgresTarget('localhost','zomato_clean','postgres','31101997','zomato_dataset_clean','1'))


if __name__ == '__main__':
    luigi.run()