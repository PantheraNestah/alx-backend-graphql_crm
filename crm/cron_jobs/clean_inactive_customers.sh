#!/bin/bash

# Navigate to the Django project's root directory
# IMPORTANT: You may need to adjust this path depending on where your manage.py file is located
# and from where you run the cron job. A common approach is to use an absolute path.
# For this example, we'll assume the script is run from a context where this relative path is valid.
# A more robust solution is to determine the script's own directory.
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$SCRIPT_DIR/../.." # Adjust this if your directory structure is different
cd "$PROJECT_ROOT"

# The Python command to be executed by Django's shell
PYTHON_COMMAND="
from datetime import datetime, timedelta
from django.utils import timezone
from customers.models import Customer # Assuming your customer model is in a 'customers' app

one_year_ago = timezone.now() - timedelta(days=365)
inactive_customers = Customer.objects.filter(order__date__lt=one_year_ago).distinct()
# Further filter to exclude customers who also have recent orders
active_customers_with_old_orders = Customer.objects.filter(order__date__gte=one_year_ago)
customers_to_delete = inactive_customers.exclude(pk__in=active_customers_with_old_orders)

deletion_count = customers_to_delete.count()
customers_to_delete.delete()

print(f'{deletion_count} inactive customers deleted.')
"

#first activate python venv
source /home/nesta/Documents/programming_playground/pyvenv/bin/activate

# Execute the command using manage.py shell and capture the output
DELETED_COUNT_MSG=$(python manage.py shell -c "$PYTHON_COMMAND")

# Log the result with a timestamp
LOG_FILE="/tmp/customer_cleanup_log.txt"
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")

echo "[$TIMESTAMP] $DELETED_COUNT_MSG" >> "$LOG_FILE"