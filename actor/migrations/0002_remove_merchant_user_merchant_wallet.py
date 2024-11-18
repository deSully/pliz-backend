# Generated by Django 5.1.3 on 2024-11-18 11:23

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actor', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='merchant',
            name='user',
        ),
        migrations.AddField(
            model_name='merchant',
            name='wallet',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='merchant_wallet', to='actor.wallet'),
        ),
    ]
