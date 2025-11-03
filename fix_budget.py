import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','WBPMISUESO.settings')
import django
django.setup()
from django.db import connection
c=connection.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='budget_collegebudget'")
exists = c.fetchone() is not None
if not exists:
    c.execute("CREATE TABLE budget_collegebudget (id INTEGER PRIMARY KEY AUTOINCREMENT, total_assigned NUMERIC NOT NULL, fiscal_year VARCHAR(10) NOT NULL, status VARCHAR(20) NOT NULL, created_at datetime, updated_at datetime, assigned_by_id bigint, college_id bigint)")
    c.execute("CREATE UNIQUE INDEX IF NOT EXISTS budget_collegebudget_college_fy_uniq ON budget_collegebudget (college_id, fiscal_year)")
    print('created')
else:
    print('exists')
