# Generated by Django 4.2.5 on 2023-11-07 07:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('registration', '0004_wallettransaction'),
    ]

    operations = [
        migrations.DeleteModel(
            name='WalletTransaction',
        ),
    ]
