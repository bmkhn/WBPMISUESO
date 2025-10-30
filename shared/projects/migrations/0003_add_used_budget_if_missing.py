from django.db import migrations, connection


def add_used_budget_if_missing(apps, schema_editor):
    with connection.cursor() as cursor:
        cursor.execute("PRAGMA table_info('projects_project')")
        columns = [row[1] for row in cursor.fetchall()]
        if 'used_budget' not in columns:
            cursor.execute(
                "ALTER TABLE projects_project ADD COLUMN used_budget DECIMAL(12,2) DEFAULT 0"
            )


def noop_reverse(apps, schema_editor):
    # No-op reverse; we keep the column
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0002_initial"),
    ]

    operations = [
        migrations.RunPython(add_used_budget_if_missing, reverse_code=noop_reverse),
    ]


