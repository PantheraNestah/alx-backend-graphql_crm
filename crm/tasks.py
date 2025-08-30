import datetime
from celery import shared_task
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime
import requests

@shared_task
def generate_crm_report():
    """
    A Celery task that queries the GraphQL endpoint for CRM statistics
    and logs them to a report file.
    """
    log_file_path = "/tmp/crm_report_log.txt"
    graphql_endpoint_url = "http://localhost:8000/graphql"
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # GraphQL query to fetch the aggregate data from our new schema fields.
    report_query = gql("""
        query CrmReport {
          totalCustomers
          totalOrders
          totalRevenue
        }
    """)

    try:
        # Set up the GraphQL client
        transport = RequestsHTTPTransport(url=graphql_endpoint_url, retries=3)
        client = Client(transport=transport, fetch_schema_from_transport=True)

        # Execute the query
        result = client.execute(report_query)

        customers = result['totalCustomers']
        orders = result['totalOrders']
        revenue = result['totalRevenue']

        # Format the report string
        report_string = (
            f"{timestamp} - Report: {customers} customers, {orders} orders, "
            f"${revenue:,.2f} revenue.\n"
        )

        # Append the report to the log file
        with open(log_file_path, "a") as log_file:
            log_file.write(report_string)
        
        return f"Report generated successfully: {report_string}"

    except Exception as e:
        error_message = f"{timestamp} - ERROR: Failed to generate CRM report. Reason: {e}\n"
        with open(log_file_path, "a") as log_file:
            log_file.write(error_message)
        return error_message