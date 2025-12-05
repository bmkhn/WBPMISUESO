@echo off

REM Delete all migrations
py delete_all_migrations.py

REM Delete media files
py manage.py clean_media

REM Delete/Reset Database
if exist db.sqlite3 del db.sqlite3
py manage.py reset_database

REM Make new migrations
py manage.py makemigrations

REM Apply migrations
py manage.py migrate

REM Create test assets
py manage.py create_test_assets

REM Create local assets
py manage.py local_assets

echo Database reset and test assets created.

pause


@REM railway run python delete_all_migrations.py
@REM railway run python manage.py makemigrations
@REM railway run python manage.py migrate
@REM railway run python manage.py clean_media
@REM railway run python manage.py collectstatic --noinput
@REM railway run python manage.py reset_database
@REM railway run python manage.py create_test_assets