import psycopg2
from config import PASSWORD
import json
from datetime import datetime
# import sys
# import boto3
# import os

ENDPOINT="defillama.c4ckxetzn16n.us-east-2.rds.amazonaws.com"
PORT="5432"
USER="defiadmin"
REGION="us-east-2"
DBNAME="defillama"
# os.environ['LIBMYSQL_ENABLE_CLEARTEXT_PLUGIN'] = '1'

# Get the credentials from .aws/credentials
# session = boto3.Session(profile_name='RDSCreds')
# client = session.client('rds')

# token = client.generate_db_auth_token(
#     DBHostname=ENDPOINT, 
#     Port=PORT, 
#     DBUsername=USER, 
#     Region=REGION)

# Even though I ran aws config from within the virtual env
# it still couldn't find a config file with my keys...
# -- actually I probably needed to install aws in the venv 
# then run aws config 

def connect():
    """Returns the connection cursor"""

    try:
        conn = psycopg2.connect(
            database='postgres', # NOT THE DBNAME!
            user=USER,
            password=PASSWORD,
            host=ENDPOINT,
            port=PORT
        )

        cur = conn.cursor()
        cur.execute("""SELECT now()""")
        query_results = cur.fetchone()
        print(query_results)
        return cur, conn
    
    except Exception as e:
        print(f"Database connection failed due to {e}")  

  
def create_tables(cur) -> None:
    
    # Protocols tabls
    cur.execute(
        """CREATE TABLE IF NOT EXISTS 
        protocols(
            name varchar PRIMARY KEY,
            address varchar,
            twitter varchar,
            tvl float,
            chains varchar[]
        );"""
    )
    # chain_tvl  -- omitted
    
    # To build the tables for individual protocols I need to get the 
    # list of chains so I can make each chain into its own column

    with open('defi/data.json', 'r') as f:
        data = f.read()
        data = json.loads(data)
        # [ {'name': 'Curve', ... 'chains': [] } ]
    
    for item in data:
        protocol_name = item['name'].lower().replace(' ', '_')
        chains = item['chains']
        
        # Grab each chain out of the list and use as a column name
        chain_columns = ''
        for chain in chains:
            chain_columns += f'{chain.lower()} varchar,'
        
        # Remove final ","
        chain_columns = chain_columns[:-1]
        
        print(protocol_name, chain_columns,'\n')
        sql_string = f"""CREATE TABLE IF NOT EXISTS
            {protocol_name}(
                date date PRIMARY KEY,
                {chain_columns}
            );"""

        cur.execute(sql_string)
    

def print_tables(cur) -> None:
    """Just a test to make sure everything worked. Table 
    names are saved to 'postgres_tables.txt'"""
    
    cur.execute(
        """SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = 'public'
        ORDER BY table_name;"""
    )
    
    list_tables = cur.fetchall()
    
    with open('postgres_tables.txt', 'w+') as f:
        for t_name_table in list_tables:
            f.write(t_name_table[0])
            f.write('\n')


def insert_protocol_data(cur, requested_protocol:str) -> None:
    """Load a protocol's data from the json file
    into postgres"""
    
    requested_protocol = requested_protocol.lower()
    
    with open('defi/data.json', 'r') as f:
        data = f.read()
        data = json.loads(data)
        # [ {'name': 'Curve', ... 'chains': [] } ]
    
    for item in data:
        protocol_name = item['name'].lower().replace(' ', '_')
        chain_tvls = item['chain_tvls'] # {}
        chains = item['chains']
        
        # Only proceed if this item is what's requested
        if protocol_name != requested_protocol:
            continue
        
        # Make columns string from list
        columns = ''
        for chain in chains:
            columns += chain + ','
        
        # Remove final ","
        columns = columns[:-1]
        
        # Make correct number of parameterized place holders
        value_params = ''
        values = chain_tvls.values()
        for _ in values:
            value_params += '%s,'
        
        # Substite last "," for ")"
        value_params = value_params[:-1]
        # print(value_params)
    
        # When I made the tables I forgot I hadn't save the years
        # of historical data so I actually don't have any dates. 
        # (and date is the primary key) Will just need to add it in...
        cur.execute(f"""INSERT INTO {protocol_name} 
                    (date, {columns}) values (
                    '{datetime.now().date()}',{value_params})""",
                    tuple(values))    
                

def query_table(cur, table:str):
    """Just grab everything"""
    
    cur.execute(f"SELECT * FROM {table.lower()}")
    return cur.fetchall()
    
    
cur, conn = connect()
# create_tables(cur)
# insert_protocol_data(cur, 'Lido')
# print(query_table(cur, 'lido'))

conn.commit()
cur.close()
conn.close()