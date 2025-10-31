from django.db import migrations


def add_column_if_missing(apps, schema_editor):
    connection = schema_editor.connection
    vendor = connection.vendor
    table_name = 'projects_project'
    column_name = 'has_final_submission'

    try:
        columns = [c.name for c in connection.introspection.get_table_description(connection.cursor(), table_name)]
    except Exception:
        columns = []

    if column_name in columns:
        return

    if vendor == 'sqlite':
        schema_editor.execute("ALTER TABLE projects_project ADD COLUMN has_final_submission BOOLEAN NOT NULL DEFAULT 0")
    elif vendor == 'postgresql':
        schema_editor.execute("ALTER TABLE projects_project ADD COLUMN has_final_submission BOOLEAN NOT NULL DEFAULT FALSE")
    else:
        schema_editor.execute("ALTER TABLE projects_project ADD COLUMN has_final_submission BOOLEAN NOT NULL DEFAULT 0")


class Migration(migrations.Migration):
    dependencies = [
        ('projects', '0002_initial'),
    ]

    operations = [
        migrations.RunPython(add_column_if_missing, migrations.RunPython.noop),
    ]


