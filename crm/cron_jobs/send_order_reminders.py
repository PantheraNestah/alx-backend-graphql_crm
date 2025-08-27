import datetime
import time
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# --- Configuration ---
# The GraphQL endpoint for your Django application
GRAPHQL_URL = "http://localhost:8000/graphql"

# Log file path
LOG_FILE = "/tmp/order_reminders_log.txt"

# --- GraphQL Query ---
# This query is specifically tailored to your schema:
# - It uses 'allOrders', which is a DjangoFilterConnectionField.
# - It filters using 'orderDateGte', the camelCase version of 'order_date_gte' from your OrderFilter.
# - It traverses the Relay-style connection structure ('edges' and 'node') to get the order details.
GET_RECENT_ORDERS_QUERY = """
query GetRecentOrders($sevenDaysAgo: DateTime!) {
  allOrders(orderDateGte: $sevenDaysAgo) {
    edges {
      node {
        id
        customer {
          email
        }
      }
    }
  }
}
"""

def fetch_and_log_reminders():
    """
    Connects to the GraphQL endpoint, fetches recent orders,
    and logs reminder information to a file.
    """
    # Set up the GraphQL client
    transport = RequestsHTTPTransport(url=GRAPHQL_URL)
    client = Client(transport=transport, fetch_schema_from_transport=True)

    # Calculate the date for one week ago in UTC
    seven_days_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=7)

    # Prepare the variables for the query. The key 'sevenDaysAgo' must match the variable name in the query.
    params = {"sevenDaysAgo": seven_days_ago.isoformat()}

    try:
        # Execute the GraphQL query
        query = gql(GET_RECENT_ORDERS_QUERY)
        result = client.execute(query, variable_values=params)

        # Get the current timestamp for logging
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")

        with open(LOG_FILE, "a") as log_file:
            # Check if the response contains the expected data structure
            if result.get('allOrders') and result['allOrders'].get('edges'):
                orders = result['allOrders']['edges']
                if not orders:
                    log_file.write(f"[{timestamp}] No pending orders found within the last 7 days.\n")
                else:
                    for edge in orders:
                        order_node = edge.get('node', {})
                        order_id = order_node.get('id')
                        customer_email = order_node.get('customer', {}).get('email')
                        if order_id and customer_email:
                            log_message = f"[{timestamp}] Reminder for Order ID: {order_id}, Customer: {customer_email}\n"
                            log_file.write(log_message)
            else:
                log_file.write(f"[{timestamp}] Received an unexpected response structure from GraphQL.\n")

        print("Order reminders processed!")

    except Exception as e:
        # Log any errors that occur during the process
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        error_message = f"[{timestamp}] ERROR: An error occurred while processing order reminders: {e}\n"
        with open(LOG_FILE, "a") as log_file:
            log_file.write(error_message)
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    fetch_and_log_reminders()