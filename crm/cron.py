import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport, TransportQueryError

def log_crm_heartbeat():
    """
    A cron job function managed by django-crontab.
    It logs a heartbeat message and optionally checks the GraphQL endpoint.
    """
    # --- Basic Heartbeat Logging ---
    timestamp = datetime.datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    log_file_path = "/tmp/crm_heartbeat_log.txt"
    heartbeat_message = f"{timestamp} CRM is alive"

    # --- Optional: GraphQL Health Check ---
    graphql_endpoint_url = "http://localhost:8000/graphql" # Adjust if your URL is different
    
    try:
        # Set up a simple GQL client
        transport = RequestsHTTPTransport(url=graphql_endpoint_url, retries=2)
        client = Client(transport=transport, fetch_schema_from_transport=False)
        
        # A simple query to test if the endpoint is responsive.
        # Assuming you have a 'hello' or similar test field in your schema.
        # If not, you can query for something simple like '__typename'.
        test_query = gql("{ __typename }")
        client.execute(test_query)
        
        # If the query succeeds, append a success message.
        graphql_status = "GraphQL endpoint is responsive."

    except TransportQueryError as e:
        # Handle cases where the server returns a GraphQL error (e.g., syntax error)
        graphql_status = f"GraphQL endpoint returned an error: {e}"
    except Exception as e:
        # Handle network errors or other exceptions (e.g., server is down)
        graphql_status = f"GraphQL endpoint is not accessible. Error: {e}"

    # --- Write to Log File ---
    try:
        # Open the log file in append mode ('a')
        with open(log_file_path, "a") as log_file:
            log_file.write(f"{heartbeat_message} | {graphql_status}\n")
    except IOError as e:
        # If logging fails, print an error to the cron output
        print(f"Failed to write to heartbeat log file: {e}")