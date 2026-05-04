from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("challenges", "0007_add_complexity_metrics_to_challengeattempt"),
    ]

    operations = [
        migrations.AddField(
            model_name="challenge",
            name="reference_solution",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Canonical solution used as timing baseline for efficiency ratio. For benchmark fixtures, drawn directly from source dataset.",
            ),
        ),
        migrations.AddField(
            model_name="historicalchallenge",
            name="reference_solution",
            field=models.TextField(
                blank=True,
                default="",
                help_text="Canonical solution used as timing baseline for efficiency ratio. For benchmark fixtures, drawn directly from source dataset.",
            ),
        ),
        migrations.AddField(
            model_name="challengeattempt",
            name="efficiency_ratio",
            field=models.FloatField(
                blank=True,
                null=True,
                help_text="Participant solution time / reference solution time. 1.0 = matched reference; >1 = slower.",
            ),
        ),
    ]
