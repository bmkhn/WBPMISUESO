# Generated manually for activity budget and expense linking

from django.db import migrations, models
import django.db.models.deletion


def _column_exists(schema_editor, table_name: str, column_name: str) -> bool:
    try:
        with schema_editor.connection.cursor() as cursor:
            description = schema_editor.connection.introspection.get_table_description(cursor, table_name)
        existing = {col.name for col in description}
        return column_name in existing
    except Exception:
        return False


def _add_missing_columns(apps, schema_editor):
    """Idempotently apply the DB changes for this migration.

    Some environments already have these columns (manual DB edits / prior migrations),
    so blindly adding them can raise sqlite3.OperationalError: duplicate column name.
    """
    ProjectEvent = apps.get_model('projects', 'ProjectEvent')
    ProjectExpense = apps.get_model('projects', 'ProjectExpense')

    # 1) ProjectEvent.allocated_budget
    event_table = ProjectEvent._meta.db_table
    if not _column_exists(schema_editor, event_table, 'allocated_budget'):
        field = ProjectEvent._meta.get_field('allocated_budget')
        schema_editor.add_field(ProjectEvent, field)

    # 2) ProjectExpense.event (FK -> ProjectEvent)
    expense_table = ProjectExpense._meta.db_table
    if not _column_exists(schema_editor, expense_table, 'event_id'):
        field = ProjectExpense._meta.get_field('event')
        schema_editor.add_field(ProjectExpense, field)


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0002_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(_add_missing_columns, migrations.RunPython.noop),
            ],
            state_operations=[
                migrations.AddField(
                    model_name="projectevent",
                    name="allocated_budget",
                    field=models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        default=0,
                        help_text="Budget allocated for this activity",
                        max_digits=12,
                        null=True,
                    ),
                ),
                migrations.AddField(
                    model_name="projectexpense",
                    name="event",
                    field=models.ForeignKey(
                        blank=True,
                        help_text="Optional: Link expense to a specific activity",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="expenses",
                        to="projects.projectevent",
                    ),
                ),
            ],
        ),
    ]

