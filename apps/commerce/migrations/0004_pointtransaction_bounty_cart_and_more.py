# Generated by Django 4.2.2 on 2024-10-03 13:47

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('product_management', '0052_remove_bounty_is_active_remove_challenge_reward_type_and_more'),
        ('commerce', '0003_bountycart_bountycartitem_organisationpointaccount_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='pointtransaction',
            name='bounty_cart',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='point_transactions', to='commerce.bountycart'),
        ),
        migrations.AlterField(
            model_name='pointtransaction',
            name='account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='org_transactions', to='commerce.organisationpointaccount'),
        ),
        migrations.AlterField(
            model_name='pointtransaction',
            name='amount',
            field=models.PositiveIntegerField(),
        ),
        migrations.AlterField(
            model_name='pointtransaction',
            name='transaction_type',
            field=models.CharField(choices=[('GRANT', 'Grant'), ('USE', 'Use'), ('REFUND', 'Refund'), ('TRANSFER', 'Transfer')], max_length=10),
        ),
        migrations.CreateModel(
            name='ProductPointAccount',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('balance', models.PositiveIntegerField(default=0)),
                ('product', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='product_point_account', to='product_management.product')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='pointtransaction',
            name='product_account',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='product_transactions', to='commerce.productpointaccount'),
        ),
    ]
