# Generated by Django 5.1.1 on 2024-10-11 18:10

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("commerce", "0002_initial"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("product_management", "0002_initial"),
        ("talent", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="cart",
            name="user",
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name="cartlineitem",
            name="bounty",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="product_management.bounty"
            ),
        ),
        migrations.AddField(
            model_name="cartlineitem",
            name="cart",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="items", to="commerce.cart"
            ),
        ),
        migrations.AddField(
            model_name="cartlineitem",
            name="polymorphic_ctype",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="polymorphic_%(app_label)s.%(class)s_set+",
                to="contenttypes.contenttype",
            ),
        ),
        migrations.AddField(
            model_name="cartlineitem",
            name="related_bounty_bid",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="talent.bountybid"
            ),
        ),
        migrations.AddField(
            model_name="cart",
            name="organisation",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="commerce.organisation"
            ),
        ),
        migrations.AddField(
            model_name="organisationpointaccount",
            name="organisation",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, related_name="point_account", to="commerce.organisation"
            ),
        ),
        migrations.AddField(
            model_name="organisationpointgrant",
            name="granted_by",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="granted_points",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="organisationpointgrant",
            name="organisation",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="point_grants", to="commerce.organisation"
            ),
        ),
        migrations.AddField(
            model_name="organisationwallet",
            name="organisation",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, related_name="wallet", to="commerce.organisation"
            ),
        ),
        migrations.AddField(
            model_name="organisationwallettransaction",
            name="wallet",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="transactions",
                to="commerce.organisationwallet",
            ),
        ),
        migrations.AddField(
            model_name="pointorder",
            name="cart",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE, related_name="point_order", to="commerce.cart"
            ),
        ),
        migrations.AddField(
            model_name="pointorder",
            name="parent_order",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="adjustments",
                to="commerce.pointorder",
            ),
        ),
        migrations.AddField(
            model_name="pointtransaction",
            name="account",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="org_transactions",
                to="commerce.organisationpointaccount",
            ),
        ),
        migrations.AddField(
            model_name="productpointaccount",
            name="product",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="product_point_account",
                to="product_management.product",
            ),
        ),
        migrations.AddField(
            model_name="pointtransaction",
            name="product_account",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="product_transactions",
                to="commerce.productpointaccount",
            ),
        ),
        migrations.AddField(
            model_name="pointorder",
            name="product_account",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="point_orders",
                to="commerce.productpointaccount",
            ),
        ),
        migrations.AddField(
            model_name="salesorder",
            name="cart",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.PROTECT, related_name="sales_order", to="commerce.cart"
            ),
        ),
        migrations.AddField(
            model_name="salesorder",
            name="parent_sales_order",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="adjustments",
                to="commerce.salesorder",
            ),
        ),
        migrations.AddField(
            model_name="organisationwallettransaction",
            name="related_order",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="commerce.salesorder"
            ),
        ),
        migrations.AddField(
            model_name="salesorderlineitem",
            name="bounty",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="product_management.bounty"
            ),
        ),
        migrations.AddField(
            model_name="salesorderlineitem",
            name="polymorphic_ctype",
            field=models.ForeignKey(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="polymorphic_%(app_label)s.%(class)s_set+",
                to="contenttypes.contenttype",
            ),
        ),
        migrations.AddField(
            model_name="salesorderlineitem",
            name="related_bounty_bid",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="talent.bountybid"
            ),
        ),
        migrations.AddField(
            model_name="salesorderlineitem",
            name="sales_order",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE, related_name="line_items", to="commerce.salesorder"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="cartlineitem",
            unique_together={("cart", "bounty")},
        ),
    ]
