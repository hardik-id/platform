# Generated by Django 5.1.1 on 2024-10-09 18:01

import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Bounty",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                ("title", models.CharField(max_length=400)),
                ("description", models.TextField()),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Draft", "Draft"),
                            ("Open", "Open"),
                            ("In Progress", "In Progress"),
                            ("In Review", "In Review"),
                            ("Completed", "Completed"),
                            ("Cancelled", "Cancelled"),
                        ],
                        default="Draft",
                        max_length=20,
                    ),
                ),
                (
                    "reward_type",
                    models.CharField(choices=[("Points", "Points"), ("USD", "Usd")], default="Points", max_length=10),
                ),
                (
                    "reward_amount",
                    models.PositiveIntegerField(
                        default=0,
                        help_text="Amount in points if reward_type is POINTS, or cents if reward_type is USD",
                    ),
                ),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="Bug",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                ("title", models.CharField(max_length=256)),
                ("description", models.TextField()),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Challenge",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False)),
                ("title", models.TextField()),
                ("description", models.TextField()),
                ("short_description", models.TextField(max_length=256)),
                (
                    "status",
                    models.CharField(
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
                ("blocked", models.BooleanField(default=False)),
                ("featured", models.BooleanField(default=False)),
                (
                    "priority",
                    models.CharField(
                        choices=[("High", "High"), ("Medium", "Medium"), ("Low", "Low")], default="High", max_length=50
                    ),
                ),
                ("auto_approve_bounty_claims", models.BooleanField(default=False)),
                ("video_url", models.URLField(blank=True, null=True)),
            ],
            options={
                "verbose_name_plural": "Challenges",
            },
        ),
        migrations.CreateModel(
            name="ChallengeDependency",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
            ],
            options={
                "db_table": "product_management_challenge_dependencies",
            },
        ),
        migrations.CreateModel(
            name="Competition",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField()),
                ("short_description", models.CharField(max_length=256)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Draft", "Draft"),
                            ("Active", "Active"),
                            ("Entries Closed", "Entries Closed"),
                            ("Judging", "Judging"),
                            ("Completed", "Completed"),
                            ("Cancelled", "Cancelled"),
                        ],
                        default="Draft",
                        max_length=20,
                    ),
                ),
                ("entry_deadline", models.DateTimeField()),
                ("judging_deadline", models.DateTimeField()),
                ("max_entries", models.PositiveIntegerField(blank=True, null=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CompetitionEntry",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False)),
                ("content", models.TextField()),
                ("entry_time", models.DateTimeField(auto_now_add=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Submitted", "Submitted"),
                            ("Finalist", "Finalist"),
                            ("Winner", "Winner"),
                            ("Rejected", "Rejected"),
                        ],
                        default="Submitted",
                        max_length=20,
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="CompetitionEntryRating",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False)),
                ("rating", models.PositiveSmallIntegerField(help_text="Rating from 1 to 5")),
                ("comment", models.TextField(blank=True)),
            ],
        ),
        migrations.CreateModel(
            name="ContributorGuide",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=60, unique=True)),
                ("description", models.TextField(blank=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="FileAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file", models.FileField(upload_to="attachments")),
            ],
        ),
        migrations.CreateModel(
            name="Idea",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                ("title", models.CharField(max_length=256)),
                ("description", models.TextField()),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="IdeaVote",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name="Initiative",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False)),
                ("name", models.TextField()),
                ("description", models.TextField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("Draft", "Draft"),
                            ("Active", "Active"),
                            ("Completed", "Completed"),
                            ("Cancelled", "Cancelled"),
                        ],
                        default="Active",
                        max_length=255,
                    ),
                ),
                ("video_url", models.URLField(blank=True, null=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="Product",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                ("uuid", models.UUIDField(default=uuid.uuid4, editable=False)),
                ("photo", models.ImageField(blank=True, null=True, upload_to="products/")),
                ("name", models.TextField()),
                ("short_description", models.TextField()),
                ("full_description", models.TextField()),
                ("website", models.CharField(blank=True, max_length=512, null=True)),
                ("detail_url", models.URLField(blank=True, null=True)),
                ("video_url", models.URLField(blank=True, null=True)),
                ("slug", models.SlugField(unique=True)),
                ("is_private", models.BooleanField(default=False)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ProductArea",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("path", models.CharField(max_length=255, unique=True)),
                ("depth", models.PositiveIntegerField()),
                ("numchild", models.PositiveIntegerField(default=0)),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="", max_length=1000, null=True)),
                ("video_link", models.URLField(blank=True, max_length=255, null=True)),
                ("video_name", models.CharField(blank=True, max_length=255, null=True)),
                ("video_duration", models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ProductContributorAgreement",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                ("accepted_at", models.DateTimeField(auto_now_add=True, null=True)),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="ProductContributorAgreementTemplate",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                ("title", models.CharField(max_length=256)),
                ("content", models.TextField()),
                ("effective_date", models.DateField()),
            ],
            options={
                "ordering": ("-created_at",),
            },
        ),
        migrations.CreateModel(
            name="ProductTree",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, null=True)),
                ("updated_at", models.DateTimeField(auto_now=True, null=True)),
                ("name", models.CharField(max_length=255, unique=True)),
                ("session_id", models.CharField(blank=True, max_length=255, null=True)),
            ],
            options={
                "ordering": ("-created_at",),
                "abstract": False,
            },
        ),
    ]
