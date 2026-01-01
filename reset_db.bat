@echo off

REM Delete all migrations
python delete_all_migrations.py

REM Delete media files
python manage.py clean_media

REM Delete/Reset Database
if exist db.sqlite3 del db.sqlite3
python manage.py reset_database

REM Make new migrations
python manage.py makemigrations

REM Apply migrations
python manage.py migrate

REM Create test assets
python manage.py create_test_assets

REM Create local assets
python manage.py local_assets

echo Database reset and test assets created.

pause


@REM railway run python delete_all_migrations.py
@REM railway run python manage.py makemigrations
@REM railway run python manage.py migrate
@REM railway run python manage.py clean_media
@REM railway run python manage.py collectstatic --noinput
@REM railway run python manage.py reset_database
@REM railway run python manage.py create_test_assets