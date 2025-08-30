# CRM Reporting with Celery and GraphQL

This document outlines the steps to set up and run the automated weekly CRM report generation feature. This system uses Celery for task queuing and Celery Beat for scheduling.

## 1. Prerequisites

Before starting, ensure you have **Redis** installed and running on its default port (`6379`).

**On macOS (using Homebrew):**
```
brew install redis
brew services start redis
```

**On Ubuntu/Debian:**
```
sudo apt-get update
sudo apt-get install redis-server
sudo systemctl enable redis-server.service
```

## 2. Installation

First, install all required Python packages from the requirements.txt file.
```
pip install -r requirements.txt
```

## 3. Database Migrations

Celery Beat requires its own database tables to store the schedule. Run the Django migrations to create them.
```
python manage.py migrate
```

## 4. Running the Services

To run the reporting system, you need to start three separate processes in three different terminal windows: the Django development server, the Celery worker, and the Celery Beat scheduler.

**Terminal 1: Start the Django Server**
This makes the GraphQL API available for the Celery task to query.
```
python manage.py runserver
```
**Terminal 2: Start the Celery Worker**
The worker listens for tasks (like report generation) and executes them.
```
celery -A crm worker -l info
```
**Terminal 3: Start the Celery Beat Scheduler**
The scheduler sends tasks to the worker at their scheduled time.
```
celery -A crm beat -l info
```

## 5. Verification

The `generate_crm_report` task is scheduled to run every Monday at 6:00 AM.

To verify that the system is working, you can monitor the log file where the reports are saved:
```
tail -f /tmp/crm_report_log.txt
```

You should see a new report entry each time the task runs, formatted as follows:

`YYYY-MM-DD HH:MM:SS - Report: X customers, Y orders, $Z.00 revenue.`
