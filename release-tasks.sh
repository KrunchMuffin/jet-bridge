#!/bin/sh

apt install g++
apt install unixodbc unixodbc-dev
# for PostgreSQL
pip install psycopg2-binary==2.8.3
# for MySQL
pip install mysqlclient
# for Microsoft SQL
pip install pyodbc
