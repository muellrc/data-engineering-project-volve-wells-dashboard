import psycopg2
import pandas as pd

def get_data_db(host,database,user,password):
    param_dic = {
    "host"      : str(host),
    "database"  : str(database),
    "user"      : str(user),
    "password"  : str(password)
    }
    ##################################################################
    def connect(params_dic):
        """ Connect to the PostgreSQL database server """
        conn = None
        try:
            # connect to the PostgreSQL server
            print('Connecting to the PostgreSQL database...')
            conn = psycopg2.connect(**params_dic)
        except (Exception, psycopg2.DatabaseError) as error:
            print(error)
        print("Connection successful")
        return conn
    ##################################################################
    def postgresql_to_dataframe(conn, select_query, column_names):
        """
        Tranform a SELECT query into a pandas dataframe
        """
        cursor = conn.cursor()
        try:
            cursor.execute(select_query)
        except (Exception, psycopg2.DatabaseError) as error:
            print("Error: %s" % error)
            cursor.close()
            return 1

        # Naturally we get a list of tupples
        tupples = cursor.fetchall()
        cursor.close()
        
        # We just need to turn it into a pandas dataframe
        df = pd.DataFrame(tupples, columns=column_names)
        return df
    ##################################################################
    conn = connect(param_dic)
    column_names = [
        'url',
        'name',
        'rating',
        'location',
        'address',
        'cuisines',
        'cost_for_two',
        'hours',
        'facilities',
        'phone_number_1',
        'phone_number_2',
        'phone_number_3'
        ]
    # Execute the "SELECT *" query
    df = postgresql_to_dataframe(conn, "select * from zomato_dataset", column_names)
    return df
    # df.to_csv(r'/Users/macbookpro/Documents/ETL_Proj_Zomato/records_1.csv', index = False)
    