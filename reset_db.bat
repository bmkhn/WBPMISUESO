@echo off
REM Batch script to reset Django DB and test assets


REM Delete the SQLite database
if exist db.sqlite3 del db.sqlite3

REM Delete all migrations
py delete_all_migrations.py

REM Make new migrations
py manage.py makemigrations

REM Apply migrations
py manage.py migrate

REM Create test assets
py manage.py create_test_assets

REM More test assets
py manage.py more_assets

echo Database reset and test assets created.
pause
