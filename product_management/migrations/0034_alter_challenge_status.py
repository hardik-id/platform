# Generated by Django 4.2.2 on 2024-05-20 19:26
from django.db import migrations, models


def forward_func(apps, schema_editor):
    Challenge = apps.get_model("product_management", "Challenge")

    for challenge in Challenge.objects.all():
        status = int(challenge.status)
        if status == 0:
            challenge.status = "Draft"
        elif status == 1:
            challenge.status = "Blocked"
        elif status == 2:
            challenge.status = "Active"
        elif status == 4:
            challenge.status = "Completed"
        challenge.save()

    Challenge.objects.filter(status__in=["3", "5", 3, 5]).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("product_management", "0033_alter_bounty_status"),
    ]

    operations = [
        migrations.AlterField(
            model_name="challenge",
            name="status",
            field=models.CharField(
                choices=[
                    ("Draft", "Draft"),
                    ("Blocked", "Blocked"),
                    ("Active", "Active"),
                    ("Completed", "Completed"),
                    ("Cancelled", "Cancelled"),
                ],
                default="Draft",
                max_length=255,
            ),
        ),
        migrations.RunPython(forward_func, migrations.RunPython.noop),
    ]
