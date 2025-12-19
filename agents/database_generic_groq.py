import os
import pandas as pd
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import create_sql_agent
from urllib.parse import quote_plus
from schema_metadata import bike_store_metadata, bank_metadata
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

# Load environment variables
load_dotenv()

def get_db_connection_uri():
    db_type = os.getenv("DB_TYPE", "postgres").lower()
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT")
    dbname = os.getenv("DB_NAME")
    
    encoded_password = quote_plus(password)

    if db_type in ["postgres", "postgresql"]:
        port = port or "5432"
        return f"postgresql://{user}:{encoded_password}@{host}:{port}/{dbname}"
    
    elif db_type == "mysql":
        port = port or "3306"
        # Requires mysql-connector-python or pymysql
        return f"mysql+mysqlconnector://{user}:{encoded_password}@{host}:{port}/{dbname}"

    elif db_type == "mssql":
        port = port or "1433"
        # Requires pyodbc
        return f"mssql+pyodbc://{user}:{encoded_password}@{host}:{port}/{dbname}?driver=ODBC+Driver+17+for+SQL+Server"

    elif db_type == "sqlite":
        # For SQLite, DB_NAME should be the full path to the file
        return f"sqlite:///{dbname}"

    else:
        raise ValueError(f"Unsupported DB_TYPE: {db_type}")


def get_agent():
    # LLM Setup for Groq
    api_key = os.getenv("GROQ_API_KEY")
    # Using Llama 3 70B for strong reasoning capabilities
    model_name = os.getenv("LLM_MODEL", "openai/gpt-oss-120b") 
    
    if not api_key:
        print("Warning: GROQ_API_KEY not found in environment variables.")

    llm = ChatGroq(
        model=model_name,
        groq_api_key=api_key,
        temperature=0,
    )

    db_uri = get_db_connection_uri()
    # No longer passing custom_table_info needed, we will inspect dynamically
    db = SQLDatabase.from_uri(db_uri)

    # Determine which metadata to use based on DB_NAME
    dbname = os.getenv("DB_NAME", "")
    metadata_map = {
        "bike_store": bike_store_metadata,
        "massive-bank": bank_metadata
    }
    
    selected_metadata = metadata_map.get(dbname)
    
    if selected_metadata:
        # Format curated metadata for system prompt
        schema_description = f"Here is the Database Schema for {dbname} you must use:\n"
        for table, description in selected_metadata.items():
            schema_description += f"\nTable: {table}\n{description}\n"
    else:
        # Fallback to dynamic inspection
        schema_description = f"Here is the schema of the database you are connected to:\n{db.get_table_info()}"

    # Custom Prompt Template
    # We explicitly tell Llama how to behave and where the schema is.
    system_prefix = f"""You are an expert Database Agent.
    
    {schema_description}

    CRITICAL RULES:
    1. You MUST use the EXACT table names and column names from the schema above.
    2. DO NOT hallucinate tables or columns.
    3. If you need a column that isn't in a table, check the Foreign Keys to join with the related table.
    4. Start by listing tables if you are unsure, but TRUST the schema above first.
    5. Always LIMIT results to 10 unless specified otherwise.
    6. Double check your query logic before executing.
    """

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prefix),
        ("placeholder", "{chat_history}"),
        ("human", "{input}"),
        MessagesPlaceholder("agent_scratchpad"),
    ])

    # Create SQL Agent
    agent_executor = create_sql_agent(
        llm=llm,
        db=db,
        prompt=prompt, # Inject our custom prompt
        verbose=True,
        agent_type="openai-tools",
        agent_executor_kwargs={"return_intermediate_steps": True},
    )
    
    return agent_executor

from langchain_community.chat_message_histories import ChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory

# Global store for chat histories
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = ChatMessageHistory()
    return store[session_id]

def log_query(question, sql_query, answer, log_file="query_history.txt"):
    with open(log_file, "a") as f:
        f.write(f"Timestamp: {pd.Timestamp.now()}\n")
        f.write(f"Question: {question}\n")
        f.write(f"SQL Query: {sql_query}\n")
        f.write(f"Answer: {answer}\n")
        f.write("-" * 50 + "\n")

if __name__ == "__main__":
    agent = get_agent()
    
    # Wrap agent with memory
    agent_with_history = RunnableWithMessageHistory(
        agent,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
    )
    
    print("SQL Agent initialized. Type 'exit' to quit.")
    session_id = "user_session"
    
    while True:
        user_query = input("\nAsk a question: ")
        if user_query.lower() in ['exit', 'quit']:
            break
        
        try:
            # Invoke with session config
            response = agent_with_history.invoke(
                {"input": user_query},
                config={"configurable": {"session_id": session_id}}
            )
            
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
