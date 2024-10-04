# Generated by Django 4.2.2 on 2024-10-04 11:22

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('product_management', '0001_initial'),
        ('commerce', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='productpointaccount',
            name='product',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='product_point_account', to='product_management.product'),
        ),
        migrations.AddField(
            model_name='pointtransaction',
            name='account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='org_transactions', to='commerce.organisationpointaccount'),
        ),
        migrations.AddField(
            model_name='pointtransaction',
            name='product_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_transactions', to='commerce.productpointaccount'),
        ),
        migrations.AddField(
            model_name='pointtransaction',
            name='sales_order',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='point_transactions', to='commerce.salesorder'),
        ),
        migrations.AddField(
            model_name='pointorder',
            name='bounty',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='point_orders', to='product_management.bounty'),
        ),
        migrations.AddField(
            model_name='pointorder',
            name='product_account',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='point_orders', to='commerce.productpointaccount'),
        ),
    ]
