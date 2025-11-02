@echo off

REM Delete all migrations
py delete_all_migrations.py

REM Delete/Reset Database
if exist db.sqlite3 del db.sqlite3
py manage.py reset_database

REM Make new migrations
py manage.py makemigrations

REM Apply migrations
py manage.py migrate

REM Create test assets
py manage.py create_test_assets

REM Create accurate assets
py manage.py accurate_assets

echo Database reset and test assets created.

pause
