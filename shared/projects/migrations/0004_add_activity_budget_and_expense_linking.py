# Generated manually for activity budget and expense linking

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0003_remove_projectexpense_receipt"),
    ]

    operations = [
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
    ]

