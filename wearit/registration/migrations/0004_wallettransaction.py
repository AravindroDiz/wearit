# Generated by Django 4.2.5 on 2023-11-07 04:42

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0003_remove_order_is_paid_customer_wallet_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='WalletTransaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateTimeField(auto_now_add=True)),
                ('description', models.CharField(max_length=255)),
                ('amount', models.FloatField()),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='wallet_transactions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
