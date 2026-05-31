#!/bin/bash

# Install Microsoft ODBC Driver 18 for SQL Server (required by pyodbc on Azure App Service Linux)
curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add -
curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list
apt-get update -qq
ACCEPT_EULA=Y apt-get install -y msodbcsql18 unixodbc-dev

pip install -r requirements.txt

# Single worker so APScheduler doesn't run duplicate jobs across processes
gunicorn --bind=0.0.0.0:8000 --timeout 600 --workers=1 wsgi:app
