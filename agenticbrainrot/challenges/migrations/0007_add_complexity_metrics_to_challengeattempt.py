from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("challenges", "0006_add_run_count_to_challengeattempt"),
    ]

    operations = [
        migrations.AddField(
            model_name="challengeattempt",
            name="complexity_metrics",
            field=models.JSONField(
                blank=True,
                null=True,
                help_text="AST-derived complexity metrics computed client-side at submission time.",
            ),
        ),
    ]
