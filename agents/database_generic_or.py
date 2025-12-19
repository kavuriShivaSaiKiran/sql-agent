import os
import pandas as pd
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from urllib.parse import quote_plus
from schema_metadata import table_metadata

# Load environment variables
load_dotenv()

def get_db_connection_uri():
    db_type = os.getenv("DB_TYPE", "postgres").lower()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT")
    dbname = os.getenv("DB_NAME")
    
    encoded_password = quote_plus(password) if password else ""

    if db_type in ["postgres", "postgresql"]:
        port = port or "5432"
        return f"postgresql://{user}:{encoded_password}@{host}:{port}/{dbname}"
    
    elif db_type == "mysql":
        port = port or "3306"
        return f"mysql+mysqlconnector://{user}:{encoded_password}@{host}:{port}/{dbname}"

    elif db_type == "mssql":
        port = port or "1433"
        return f"mssql+pyodbc://{user}:{encoded_password}@{host}:{port}/{dbname}?driver=ODBC+Driver+17+for+SQL+Server"

    elif db_type == "sqlite":
        return f"sqlite:///{dbname}"

    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}")


def get_agent():
    # LLM Setup for OpenRouter
    api_key = os.getenv("OPENROUTER_API_KEY")
    model_name = os.getenv("LLM_MODEL", "google/gemini-2.0-flash-exp:free") # Better default than 20b
    
    if not api_key:
        print("Warning: OPENROUTER_API_KEY not found in environment variables.")

    llm = ChatOpenAI(
        model=model_name,
        openai_api_key=api_key,
        openai_api_base="https://openrouter.ai/api/v1",
        temperature=0,
    )

    db_uri = get_db_connection_uri()
    # Dynamic Inspection
    db = SQLDatabase.from_uri(db_uri)
    
    # Get schema automatically
    schema_description = db.get_table_info()

    # Create SQL Agent
    # System message with embedded dynamic schema
    system_message = f"""You are an expert Database Agent.
    
    Here is the schema of the database to which you are connected:
    {schema_description}

    Guidelines:
        - ALWAYS check the schema provided above before writing a query.
        - Use EXACT table and column names from the schema.
        - Create valid SQL queries to answer the user's question.
        - Always LIMIT results to 10 unless asked for more.
        - DO NOT make assumptions or hallucinate. 
        - If the query fails, rewrite it using the correct column names from the schema.
    """

    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        verbose=True,
        agent_type="openai-tools",
        agent_executor_kwargs={"return_intermediate_steps": True},
        system_message=system_message
    )
    
    return agent_executor

def log_query(question, sql_query, answer, log_file="query_history.txt"):
    with open(log_file, "a") as f:
        f.write(f"Timestamp: {pd.Timestamp.now()}\n")
        f.write(f"Question: {question}\n")
        f.write(f"SQL Query: {sql_query}\n")
        f.write(f"Answer: {answer}\n")
        f.write("-" * 50 + "\n")

if __name__ == "__main__":
    agent = get_agent()
    print("SQL Agent initialized. Type 'exit' to quit.")
    
    while True:
        user_query = input("\nAsk a question: ")
        if user_query.lower() in ['exit', 'quit']:
            break
        
        try:
            response = agent.invoke(user_query)
            
            # Extract SQL query from intermediate steps
            sql_query = "No successful SQL Query generated"
            
            # Iterate through all steps to find the LAST SUCCESSFUL executed query
            for step in response.get("intermediate_steps", []):
                action = step[0]
                observation = step[1] # The result/output of the tool
                
                if action.tool == "sql_db_query":
                    # Check if the query failed
                    if isinstance(observation, str) and "Error" in observation:
                        continue
                        
                    # Handle both string and dictionary inputs
                    if isinstance(action.tool_input, dict):
                         sql_query = action.tool_input.get('query', str(action.tool_input))
                    else:
                        sql_query = str(action.tool_input)
            
            answer = response['output']
            
            # Print to console
            print(f"\nGenerated SQL: {sql_query}")
            print("\nAnswer:", answer)
            
            # Log to file
            log_query(user_query, sql_query, answer)
            print("\n(Logged to query_history.txt)")
            
        except Exception as e:
            print(f"Error: {e}")
