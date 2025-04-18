# Generated by Django 5.1.3 on 2025-04-18 14:51

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('actor', '0003_country_customuser_is_subscribed_bank_rib'),
        ('transaction', '0005_alter_transaction_receiver_alter_transaction_sender'),
    ]

    operations = [
        migrations.CreateModel(
            name='Fee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_type', models.CharField(choices=[('send_money', "Envoi d'argent"), ('topup', 'Rechargement'), ('merchant_payment', 'Paiement marchand')], max_length=30)),
                ('percentage', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('fixed_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                ('is_active', models.BooleanField(default=True)),
                ('bank', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='actor.bank')),
                ('merchant', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='actor.merchant')),
            ],
        ),
    ]
