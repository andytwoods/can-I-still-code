from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("challenges", "0008_add_reference_solution_and_efficiency_ratio"),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name="challenge",
            name="challenge_difficulty_range",
        ),
        migrations.AddConstraint(
            model_name="challenge",
            constraint=models.CheckConstraint(
                condition=models.Q(difficulty__gte=0, difficulty__lte=5),
                name="challenge_difficulty_range",
            ),
        ),
    ]
