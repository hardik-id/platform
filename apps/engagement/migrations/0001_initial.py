# Generated by Django 4.2.2 on 2024-10-05 12:12

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='EmailNotification',
            fields=[
                ('event_type', models.IntegerField(choices=[(0, 'Bounty Claimed'), (1, 'Challenge Comment'), (2, 'Submission Approved'), (3, 'Submission Rejected'), (4, 'Bug Rejected'), (5, 'Idea Rejected'), (6, 'Bug Created'), (7, 'Idea Created'), (8, 'Bug Created For Members'), (9, 'Idea Created For Members'), (10, 'Task Status Changed'), (11, 'Bounty In Review'), (12, 'Generic Comment'), (13, 'Bounty Submission Made'), (14, 'Task Ready To Review'), (15, 'Task Delivery Attempt Created'), (16, 'Contributor Abandoned Bounty'), (17, 'Submission Revision Requested')], primary_key=True, serialize=False)),
                ('permitted_params', models.CharField(max_length=500)),
                ('title', models.CharField(max_length=400)),
                ('template', models.CharField(max_length=4000)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
