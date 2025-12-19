import pandas as pd
from sqlalchemy import create_engine
import os
import glob


from urllib.parse import quote_plus

def upload_excel_to_postgres(excel_file_path, db_config):
    """
    Uploads an Excel file (with multiple sheets) to a PostgreSQL database.
    Each sheet is treated as a separate table.
    
    :param excel_file_path: Path to the .xlsx file.
    :param db_config: Dictionary containing 'user', 'password', 'host', 'port', and 'database'.
    """
    # Create the connection string
    connection_string = (
        f"postgresql://{db_config['user']}:{quote_plus(db_config['password'])}@"
        f"{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    
    # Create SQLAlchemy engine
    engine = create_engine(connection_string)
    
    try:
        print(f"Reading Excel file: {excel_file_path}...")
        # Read all sheets from the Excel file
        # sheet_name=None returns a dictionary {sheet_name: dataframe}
        all_sheets = pd.read_excel(excel_file_path, sheet_name=None)
        
        for sheet_name, df in all_sheets.items():
            # Clean table name: lowercase, replace spaces with underscores, remove special chars
            table_name = sheet_name.lower().replace(' ', '_').replace('-', '_')
            
            print(f"Uploading sheet '{sheet_name}' to table '{table_name}'...")
            
            # Upload to PostgreSQL
            df.to_sql(table_name, engine, if_exists='replace', index=False)
            
            print(f"Successfully uploaded table: {table_name}")
            
        print("All sheets uploaded successfully.")
        
    except Exception as e:
        print(f"Error: {e}")

# Configuration
config = {
    'user': 'postgres',
    'password': 'Luffy@135790',
    'host': 'localhost',
    'port': '5432',
    'database': 'massive-bank'
}

# Assuming there is one main excel file in the directory
excel_files = glob.glob('./bankdataset2.xlsx')

if excel_files:
    # Take the first excel file found
    target_file = excel_files[0]
    upload_excel_to_postgres(target_file, config)
else:
    print("No .xlsx file found in ./bankdataset2.xlsx")