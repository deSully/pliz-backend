# Generated by Django 5.1.3 on 2024-11-18 06:31

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('transaction', '0002_walletbalancehistory'),
    ]

    operations = [
        migrations.AlterField(
            model_name='walletbalancehistory',
            name='transaction',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='balance_histories', to='transaction.transaction'),
        ),
    ]
