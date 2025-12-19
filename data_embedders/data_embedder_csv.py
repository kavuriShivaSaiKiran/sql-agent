import pandas as pd
from sqlalchemy import create_engine
import os
import glob


from urllib.parse import quote_plus

def upload_csv_to_postgres(csv_files, db_config):
    """
    Uploads a list of CSV files to a PostgreSQL database.
    
    :param csv_files: List of paths to CSV files.
    :param db_config: Dictionary containing 'user', 'password', 'host', 'port', and 'database'.
    """
    # Create the connection string
    # URL encode the password to handle special characters like '@'
    encoded_password = quote_plus(db_config['password'])
    connection_string = (
        f"postgresql://{db_config['user']}:{encoded_password}@"
        f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    
    # Create SQLAlchemy engine
    engine = create_engine(connection_string)
    
    for file_path in csv_files:
        if not os.path.exists(file_path):
            print(f"File not found: {file_path}")
            continue
            
        # Use the filename (without extension) as the table name
        table_name = os.path.splitext(os.path.basename(file_path))[0]
        
        try:
            print(f"Uploading {file_path} to table '{table_name}'...")
            
            # Read CSV in chunks if files are large
            df = pd.read_csv(file_path)
            
            # Upload to SQL
            # if_exists='replace' will drop the table and recreate it
            # if_exists='append' will add data to an existing table
            df.to_sql(table_name, engine, if_exists='replace', index=False)
            
            print(f"Successfully uploaded {table_name}.")
            
        except Exception as e:
            print(f"Error uploading {file_path}: {e}")

# --- Example Usage ---
config = {
    'user': 'postgres',
    'password': 'Luffy@135790',
    'host': 'localhost',
    'port': '5432',
    'database': 'bike_store'
}

my_files = glob.glob('./bike-store-data/*.csv')
upload_csv_to_postgres(my_files, config)